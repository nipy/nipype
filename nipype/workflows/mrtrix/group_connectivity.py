import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.cmtk as cmtk
import nipype.interfaces.mrtrix as mrtrix
import nipype.algorithms.misc as misc
import inspect
import nibabel as nb
import os, os.path as op
from nipype.utils.misc import package_check
import warnings
try:
    package_check('cmp')
except Exception, e:
    warnings.warn('cmp not installed')
else:
    import cmp
from nipype.workflows.mrtrix.connectivity_mapping import create_connectivity_pipeline
from nipype.workflows.camino.connectivity_mapping import (get_vox_dims, get_data_dims,
 get_affine, select_aparc, select_aparc_annot)
from nipype.workflows.camino.group_connectivity import (get_subj_in_group, getoutdir, get_nsubs)

def create_mrtrix_group_cff_pipeline_part1(group_list, group_id, data_dir, subjects_dir, output_dir, template_args_dict=0):
    """Creates a group-level pipeline that does the same connectivity processing as in the
    connectivity_tutorial_advanced example script and the mrtrix create_connectivity_pipeline workflow. 

    Given a subject id (and completed Freesurfer reconstruction), diffusion-weighted image,
    b-values, and b-vectors, the workflow will return the subject's connectome
    as a Connectome File Format (CFF) file for use in Connectome Viewer (http://www.cmtk.org)
    as well as the outputs of many other stages of the processing.

    Example
    -------

    >>> import os.path as op
    >>> import nipype.interfaces.freesurfer as fs
    >>> from nipype.workflows.mrtrix import create_connectivity_pipeline
    >>> subjects_dir = op.abspath('freesurfer')
    >>> fs.FSCommand.set_default_subjects_dir(subjects_dir)
    >>> cff = cmonwk.create_connectivity_pipeline("mrtrix_cmtk")
    >>> cff.inputs.inputnode.subjects_dir = subjects_dir # doctest: +SKIP
    >>> cff.inputs.inputnode.subject_id = 'subj1'
    >>> cff.inputs.inputnode.dwi = op.abspath('fsl_course_data/fdt/subj1/data.nii.gz')
    >>> cff.inputs.inputnode.bvecs = op.abspath('fsl_course_data/fdt/subj1/bvecs')
    >>> cff.inputs.inputnode.bvals = op.abspath('fsl_course_data/fdt/subj1/bvals')
    >>> cff.run()                 # doctest: +SKIP

    Inputs::

        inputnode.subject_id
        inputnode.subjects_dir
        inputnode.dwi
        inputnode.bvecs
        inputnode.bvals

    Outputs::

        outputnode.connectome
        outputnode.nxstatscff
        outputnode.nxmatlab
        outputnode.nxcsv
        outputnode.fa
        outputnode.tracts
        outputnode.filtered_tractography
        outputnode.cmatrix
        outputnode.b0resampled
        outputnode.rois
        outputnode.rois_orig
        outputnode.odfs
        outputnode.struct
        outputnode.gpickled_network
        outputnode.mean_fiber_length
        outputnode.fiber_length_std
    """
    
    group_infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name="group_infosource")
    group_infosource.inputs.group_id = group_id
    subject_list = group_list[group_id]
    subj_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="subj_infosource")
    subj_infosource.iterables = ('subject_id', subject_list)
    
    if template_args_dict == 0:
        info = dict(dwi=[['subject_id', 'dwi']],
                    bvecs=[['subject_id','bvecs']],
                    bvals=[['subject_id','bvals']])
    else:
        info = template_args_dict
        
    datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                   outfields=info.keys()),
                         name = 'datasource')

    datasource.inputs.template = "%s/%s"
    datasource.inputs.base_directory = data_dir
    datasource.inputs.field_template = dict(dwi='%s/%s.nii')
    datasource.inputs.template_args = info

    """
    Create a connectivity mapping workflow
    """
    conmapper = create_connectivity_pipeline("nipype_conmap")
    conmapper.inputs.inputnode.subjects_dir = subjects_dir
    conmapper.base_dir = op.abspath('conmapper')

    datasink = pe.Node(interface=nio.DataSink(), name="datasink")
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = group_id
    datasink.inputs.cff_dir = getoutdir(group_id, output_dir)

    l1pipeline = pe.Workflow(name="l1pipeline")
    l1pipeline.base_dir = output_dir
    l1pipeline.base_output_dir = group_id
    l1pipeline.connect([(subj_infosource, conmapper,[('subject_id', 'inputnode.subject_id')])])
    l1pipeline.connect([(subj_infosource, datasource,[('subject_id', 'subject_id')])])
    l1pipeline.connect([(datasource, conmapper, [("dwi", "inputnode.dwi"),
                                              ("bvals", "inputnode.bvals"),
                                              ("bvecs", "inputnode.bvecs"),
                                              ])])
    l1pipeline.connect([(conmapper, datasink, [("outputnode.connectome", "@l1output.cff"),
                                              ("outputnode.nxstatscff", "@l1output.nxstatscff"),
                                              ("outputnode.nxmatlab", "@l1output.nxmatlab"),
                                              ("outputnode.nxcsv", "@l1output.nxcsv"),
                                              ("outputnode.cmatrix_csv", "@l1output.cmatrix_csv"),
                                              ("outputnode.meanfib_csv", "@l1output.meanfib_csv"),
                                              ("outputnode.fibstd_csv", "@l1output.fibstd_csv"),
                                              ("outputnode.cmatrices_csv", "@l1output.cmatrices_csv"),
                                              ("outputnode.nxmergedcsv", "@l1output.nxmergedcsv"),
                                              ("outputnode.fa", "@l1output.fa"),
                                              ("outputnode.tracts", "@l1output.tracts"),
                                              ("outputnode.filtered_tracts", "@l1output.filtered_tracts"),
                                              ("outputnode.cmatrix", "@l1output.cmatrix"),
                                              ("outputnode.b0_resampled", "@l1output.b0_resampled"),
                                              ("outputnode.rois", "@l1output.rois"),
                                              ("outputnode.brain_overlay", "@l1output.brain_overlay"),
                                              ("outputnode.GM_overlay", "@l1output.GM_overlay"),
                                              ("outputnode.rois_orig", "@l1output.rois_orig"),
                                              ("outputnode.odfs", "@l1output.odfs"),
                                              ("outputnode.struct", "@l1output.struct"),
                                              ("outputnode.gpickled_network", "@l1output.gpickled_network"),
                                              ("outputnode.mean_fiber_length", "@l1output.mean_fiber_length"),
                                              ("outputnode.fiber_length_std", "@l1output.fiber_length_std"),
                                              ])])
    l1pipeline.connect([(group_infosource, datasink,[('group_id','@group_id')])])
    return l1pipeline
