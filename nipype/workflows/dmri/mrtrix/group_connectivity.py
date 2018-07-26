# -*- coding: utf-8 -*-
import os.path as op
import warnings

from ....interfaces import io as nio  # Data i/o
from ....interfaces import utility as util  # utility
from ....interfaces import cmtk as cmtk
from ....algorithms import misc as misc
from ....pipeline import engine as pe  # pipeline engine
from ....utils.misc import package_check
from .connectivity_mapping import create_connectivity_pipeline

try:
    package_check('cmp')
except Exception as e:
    warnings.warn('cmp not installed')
else:
    import cmp


def create_group_connectivity_pipeline(group_list,
                                       group_id,
                                       data_dir,
                                       subjects_dir,
                                       output_dir,
                                       template_args_dict=0):
    """Creates a pipeline that performs MRtrix structural connectivity processing
    on groups of subjects. Given a diffusion-weighted image, and text files containing
    the associated b-values and b-vectors, the workflow will return each subjects' connectomes
    in a Connectome File Format (CFF) file, for use in Connectome Viewer (http://www.cmtk.org).

    Example
    -------

    >>> import nipype.interfaces.freesurfer as fs
    >>> import nipype.workflows.dmri.mrtrix.group_connectivity as groupwork
    >>> import cmp # doctest: +SKIP
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> fs.FSCommand.set_default_subjects_dir(subjects_dir)
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> template_args = dict(dwi=[['subject_id', 'dwi']], bvecs=[['subject_id', 'bvecs']], bvals=[['subject_id', 'bvals']])
    >>> group_id = 'group1'
    >>> l1pipeline = groupwork.create_group_connectivity_pipeline(group_list, group_id, data_dir, subjects_dir, output_dir, template_args)
    >>> parcellation_name = 'scale500'
    >>> l1pipeline.inputs.connectivity.mapping.Parcellate.parcellation_name = parcellation_name
    >>> cmp_config = cmp.configuration.PipelineConfiguration() # doctest: +SKIP
    >>> cmp_config.parcellation_scheme = "Lausanne2008" # doctest: +SKIP
    >>> l1pipeline.inputs.connectivity.mapping.inputnode_within.resolution_network_file = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml'] # doctest: +SKIP
    >>> l1pipeline.run()                 # doctest: +SKIP


    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        group_id: String containing the group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
        template_args_dict: Dictionary of template arguments for the connectivity pipeline datasource
                                e.g.    info = dict(dwi=[['subject_id', 'dwi']],
                                                bvecs=[['subject_id','bvecs']],
                                                bvals=[['subject_id','bvals']])
    """
    group_infosource = pe.Node(
        interface=util.IdentityInterface(fields=['group_id']),
        name="group_infosource")
    group_infosource.inputs.group_id = group_id
    subject_list = group_list[group_id]
    subj_infosource = pe.Node(
        interface=util.IdentityInterface(fields=['subject_id']),
        name="subj_infosource")
    subj_infosource.iterables = ('subject_id', subject_list)

    if template_args_dict == 0:
        info = dict(
            dwi=[['subject_id', 'dwi']],
            bvecs=[['subject_id', 'bvecs']],
            bvals=[['subject_id', 'bvals']])
    else:
        info = template_args_dict

    datasource = pe.Node(
        interface=nio.DataGrabber(
            infields=['subject_id'], outfields=list(info.keys())),
        name='datasource')

    datasource.inputs.template = "%s/%s"
    datasource.inputs.base_directory = data_dir
    datasource.inputs.field_template = dict(dwi='%s/%s.nii')
    datasource.inputs.template_args = info
    datasource.inputs.sort_filelist = True
    """
    Create a connectivity mapping workflow
    """
    conmapper = create_connectivity_pipeline("nipype_conmap")
    conmapper.inputs.inputnode.subjects_dir = subjects_dir
    conmapper.base_dir = op.abspath('conmapper')

    datasink = pe.Node(interface=nio.DataSink(), name="datasink")
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = group_id

    l1pipeline = pe.Workflow(name="l1pipeline_" + group_id)
    l1pipeline.base_dir = output_dir
    l1pipeline.base_output_dir = group_id
    l1pipeline.connect([(subj_infosource, conmapper,
                         [('subject_id', 'inputnode.subject_id')])])
    l1pipeline.connect([(subj_infosource, datasource, [('subject_id',
                                                        'subject_id')])])
    l1pipeline.connect([(datasource, conmapper, [
        ("dwi", "inputnode.dwi"),
        ("bvals", "inputnode.bvals"),
        ("bvecs", "inputnode.bvecs"),
    ])])
    l1pipeline.connect([(conmapper, datasink, [
        ("outputnode.connectome", "@l1output.cff"),
        ("outputnode.nxstatscff", "@l1output.nxstatscff"),
        ("outputnode.nxmatlab", "@l1output.nxmatlab"),
        ("outputnode.nxcsv", "@l1output.nxcsv"),
        ("outputnode.fiber_csv", "@l1output.fiber_csv"),
        ("outputnode.cmatrices_csv", "@l1output.cmatrices_csv"),
        ("outputnode.fa", "@l1output.fa"),
        ("outputnode.filtered_tracts", "@l1output.filtered_tracts"),
        ("outputnode.cmatrix", "@l1output.cmatrix"),
        ("outputnode.rois", "@l1output.rois"),
        ("outputnode.odfs", "@l1output.odfs"),
        ("outputnode.struct", "@l1output.struct"),
        ("outputnode.networks", "@l1output.networks"),
        ("outputnode.mean_fiber_length", "@l1output.mean_fiber_length"),
        ("outputnode.fiber_length_std", "@l1output.fiber_length_std"),
    ])])
    l1pipeline.connect([(group_infosource, datasink, [('group_id',
                                                       '@group_id')])])
    return l1pipeline
