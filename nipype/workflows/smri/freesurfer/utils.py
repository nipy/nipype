# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ....pipeline import engine as pe
from ....interfaces import fsl as fsl
from ....interfaces import freesurfer as fs
from ....interfaces import meshfix as mf
from ....interfaces import io as nio
from ....interfaces import utility as niu
from ....algorithms import misc as misc
from ....interfaces.utility import Function
from ....workflows.misc.utils import region_list_from_volume, id_list_from_lookup_table
import os


def get_aparc_aseg(files):
    """Return the aparc+aseg.mgz file"""
    for name in files:
        if 'aparc+aseg' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')


def create_getmask_flow(name='getmask', dilate_mask=True):
    """Registers a source file to freesurfer space and create a brain mask in
    source space

    Requires fsl tools for initializing registration

    Parameters
    ----------

    name : string
        name of workflow
    dilate_mask : boolean
        indicates whether to dilate mask or not

    Example
    -------

    >>> getmask = create_getmask_flow()
    >>> getmask.inputs.inputspec.source_file = 'mean.nii'
    >>> getmask.inputs.inputspec.subject_id = 's1'
    >>> getmask.inputs.inputspec.subjects_dir = '.'
    >>> getmask.inputs.inputspec.contrast_type = 't2'


    Inputs::

           inputspec.source_file : reference image for mask generation
           inputspec.subject_id : freesurfer subject id
           inputspec.subjects_dir : freesurfer subjects directory
           inputspec.contrast_type : MR contrast of reference image

    Outputs::

           outputspec.mask_file : binary mask file in reference image space
           outputspec.reg_file : registration file that maps reference image to
                                 freesurfer space
           outputspec.reg_cost : cost of registration (useful for detecting misalignment)
    """
    """
    Initialize the workflow
    """

    getmask = pe.Workflow(name=name)
    """
    Define the inputs to the workflow.
    """

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'source_file', 'subject_id', 'subjects_dir', 'contrast_type'
        ]),
        name='inputspec')
    """
    Define all the nodes of the workflow:

    fssource: used to retrieve aseg.mgz
    threshold : binarize aseg
    register : coregister source file to freesurfer space
    voltransform: convert binarized aseg to source file space
    """

    fssource = pe.Node(nio.FreeSurferSource(), name='fssource')
    threshold = pe.Node(fs.Binarize(min=0.5, out_type='nii'), name='threshold')
    register = pe.MapNode(
        fs.BBRegister(init='fsl'), iterfield=['source_file'], name='register')
    voltransform = pe.MapNode(
        fs.ApplyVolTransform(inverse=True),
        iterfield=['source_file', 'reg_file'],
        name='transform')
    """
    Connect the nodes
    """

    getmask.connect([(inputnode, fssource, [
        ('subject_id', 'subject_id'), ('subjects_dir', 'subjects_dir')
    ]), (inputnode, register,
         [('source_file', 'source_file'), ('subject_id', 'subject_id'),
          ('subjects_dir', 'subjects_dir'),
          ('contrast_type', 'contrast_type')]), (inputnode, voltransform, [
              ('subjects_dir', 'subjects_dir'), ('source_file', 'source_file')
          ]), (fssource, threshold, [(('aparc_aseg', get_aparc_aseg),
                                      'in_file')]),
                     (register, voltransform, [('out_reg_file', 'reg_file')]),
                     (threshold, voltransform, [('binary_file',
                                                 'target_file')])])
    """
    Add remaining nodes and connections

    dilate : dilate the transformed file in source space
    threshold2 : binarize transformed file
    """

    threshold2 = pe.MapNode(
        fs.Binarize(min=0.5, out_type='nii'),
        iterfield=['in_file'],
        name='threshold2')
    if dilate_mask:
        threshold2.inputs.dilate = 1
    getmask.connect([(voltransform, threshold2, [('transformed_file',
                                                  'in_file')])])
    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["mask_file", "reg_file", "reg_cost"]),
        name="outputspec")
    getmask.connect([
        (register, outputnode, [("out_reg_file", "reg_file")]),
        (register, outputnode, [("min_cost_file", "reg_cost")]),
        (threshold2, outputnode, [("binary_file", "mask_file")]),
    ])
    return getmask


def create_get_stats_flow(name='getstats', withreg=False):
    """Retrieves stats from labels

    Parameters
    ----------

    name : string
        name of workflow
    withreg : boolean
        indicates whether to register source to label

    Example
    -------


    Inputs::

           inputspec.source_file : reference image for mask generation
           inputspec.label_file : label file from which to get ROIs

           (optionally with registration)
           inputspec.reg_file : bbreg file (assumes reg from source to label
           inputspec.inverse : boolean whether to invert the registration
           inputspec.subjects_dir : freesurfer subjects directory

    Outputs::

           outputspec.stats_file : stats file
    """
    """
    Initialize the workflow
    """

    getstats = pe.Workflow(name=name)
    """
    Define the inputs to the workflow.
    """

    if withreg:
        inputnode = pe.Node(
            niu.IdentityInterface(fields=[
                'source_file', 'label_file', 'reg_file', 'subjects_dir'
            ]),
            name='inputspec')
    else:
        inputnode = pe.Node(
            niu.IdentityInterface(fields=['source_file', 'label_file']),
            name='inputspec')

    statnode = pe.MapNode(
        fs.SegStats(),
        iterfield=['segmentation_file', 'in_file'],
        name='segstats')
    """
    Convert between source and label spaces if registration info is provided

    """
    if withreg:
        voltransform = pe.MapNode(
            fs.ApplyVolTransform(inverse=True),
            iterfield=['source_file', 'reg_file'],
            name='transform')
        getstats.connect(inputnode, 'reg_file', voltransform, 'reg_file')
        getstats.connect(inputnode, 'source_file', voltransform, 'source_file')
        getstats.connect(inputnode, 'label_file', voltransform, 'target_file')
        getstats.connect(inputnode, 'subjects_dir', voltransform,
                         'subjects_dir')

        def switch_labels(inverse, transform_output, source_file, label_file):
            if inverse:
                return transform_output, source_file
            else:
                return label_file, transform_output

        chooser = pe.MapNode(
            niu.Function(
                input_names=[
                    'inverse', 'transform_output', 'source_file', 'label_file'
                ],
                output_names=['label_file', 'source_file'],
                function=switch_labels),
            iterfield=['transform_output', 'source_file'],
            name='chooser')
        getstats.connect(inputnode, 'source_file', chooser, 'source_file')
        getstats.connect(inputnode, 'label_file', chooser, 'label_file')
        getstats.connect(inputnode, 'inverse', chooser, 'inverse')
        getstats.connect(voltransform, 'transformed_file', chooser,
                         'transform_output')
        getstats.connect(chooser, 'label_file', statnode, 'segmentation_file')
        getstats.connect(chooser, 'source_file', statnode, 'in_file')
    else:
        getstats.connect(inputnode, 'label_file', statnode,
                         'segmentation_file')
        getstats.connect(inputnode, 'source_file', statnode, 'in_file')
    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["stats_file"]), name="outputspec")
    getstats.connect([
        (statnode, outputnode, [("summary_file", "stats_file")]),
    ])
    return getstats


def create_tessellation_flow(name='tessellate', out_format='stl'):
    """Tessellates the input subject's aseg.mgz volume and returns
    the surfaces for each region in stereolithic (.stl) format

    Example
    -------
    >>> from nipype.workflows.smri.freesurfer import create_tessellation_flow
    >>> tessflow = create_tessellation_flow()
    >>> tessflow.inputs.inputspec.subject_id = 'subj1'
    >>> tessflow.inputs.inputspec.subjects_dir = '.'
    >>> tessflow.inputs.inputspec.lookup_file = 'FreeSurferColorLUT.txt' # doctest: +SKIP
    >>> tessflow.run()  # doctest: +SKIP


    Inputs::

           inputspec.subject_id : freesurfer subject id
           inputspec.subjects_dir : freesurfer subjects directory
           inputspec.lookup_file : lookup file from freesurfer directory

    Outputs::

           outputspec.meshes : output region meshes in (by default) stereolithographic (.stl) format
    """
    """
    Initialize the workflow
    """

    tessflow = pe.Workflow(name=name)
    """
    Define the inputs to the workflow.
    """

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['subject_id', 'subjects_dir', 'lookup_file']),
        name='inputspec')
    """
    Define all the nodes of the workflow:

      fssource: used to retrieve aseg.mgz
      mri_convert : converts aseg.mgz to aseg.nii
      tessellate : tessellates regions in aseg.mgz
      surfconvert : converts regions to stereolithographic (.stl) format
      smoother: smooths the tessellated regions

    """

    fssource = pe.Node(nio.FreeSurferSource(), name='fssource')
    volconvert = pe.Node(fs.MRIConvert(out_type='nii'), name='volconvert')
    tessellate = pe.MapNode(
        fs.MRIMarchingCubes(),
        iterfield=['label_value', 'out_file'],
        name='tessellate')
    surfconvert = pe.MapNode(
        fs.MRIsConvert(out_datatype='stl'),
        iterfield=['in_file'],
        name='surfconvert')
    smoother = pe.MapNode(
        mf.MeshFix(), iterfield=['in_file1'], name='smoother')
    if out_format == 'gii':
        stl_to_gifti = pe.MapNode(
            fs.MRIsConvert(out_datatype=out_format),
            iterfield=['in_file'],
            name='stl_to_gifti')
    smoother.inputs.save_as_stl = True
    smoother.inputs.laplacian_smoothing_steps = 1

    region_list_from_volume_interface = Function(
        input_names=["in_file"],
        output_names=["region_list"],
        function=region_list_from_volume)

    id_list_from_lookup_table_interface = Function(
        input_names=["lookup_file", "region_list"],
        output_names=["id_list"],
        function=id_list_from_lookup_table)

    region_list_from_volume_node = pe.Node(
        interface=region_list_from_volume_interface,
        name='region_list_from_volume_node')
    id_list_from_lookup_table_node = pe.Node(
        interface=id_list_from_lookup_table_interface,
        name='id_list_from_lookup_table_node')
    """
    Connect the nodes
    """

    tessflow.connect([
        (inputnode, fssource, [('subject_id', 'subject_id'),
                               ('subjects_dir', 'subjects_dir')]),
        (fssource, volconvert, [('aseg', 'in_file')]),
        (volconvert, region_list_from_volume_node, [('out_file', 'in_file')]),
        (region_list_from_volume_node, tessellate, [('region_list',
                                                     'label_value')]),
        (region_list_from_volume_node, id_list_from_lookup_table_node,
         [('region_list', 'region_list')]),
        (inputnode, id_list_from_lookup_table_node, [('lookup_file',
                                                      'lookup_file')]),
        (id_list_from_lookup_table_node, tessellate, [('id_list',
                                                       'out_file')]),
        (fssource, tessellate, [('aseg', 'in_file')]),
        (tessellate, surfconvert, [('surface', 'in_file')]),
        (surfconvert, smoother, [('converted', 'in_file1')]),
    ])
    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(
        niu.IdentityInterface(fields=["meshes"]), name="outputspec")

    if out_format == 'gii':
        tessflow.connect([
            (smoother, stl_to_gifti, [("mesh_file", "in_file")]),
        ])
        tessflow.connect([
            (stl_to_gifti, outputnode, [("converted", "meshes")]),
        ])
    else:
        tessflow.connect([
            (smoother, outputnode, [("mesh_file", "meshes")]),
        ])
    return tessflow


def copy_files(in_files, out_files):
    """
    Create a function to copy a file that can be modified by a following node
    without changing the original file
    """
    import shutil
    import sys
    if len(in_files) != len(out_files):
        print(
            "ERROR: Length of input files must be identical to the length of "
            + "outrput files to be copied")
        sys.exit(-1)
    for i, in_file in enumerate(in_files):
        out_file = out_files[i]
        print("copying {0} to {1}".format(in_file, out_file))
        shutil.copy(in_file, out_file)
    return out_files


def copy_file(in_file, out_file=None):
    """
    Create a function to copy a file that can be modified by a following node
    without changing the original file.
    """
    import os
    import shutil
    if out_file is None:
        out_file = os.path.join(os.getcwd(), os.path.basename(in_file))
    if type(in_file) is list and len(in_file) == 1:
        in_file = in_file[0]
    out_file = os.path.abspath(out_file)
    in_file = os.path.abspath(in_file)
    print("copying {0} to {1}".format(in_file, out_file))
    shutil.copy(in_file, out_file)
    return out_file


def mkdir_p(path):
    import errno
    import os
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def getdefaultconfig(exitonfail=False, rb_date="2014-08-21"):
    config = {
        'custom_atlas': None,
        'cw256': False,
        'field_strength': '1.5T',
        'fs_home': checkenv(exitonfail),
        'longitudinal': False,
        'long_base': None,
        'openmp': None,
        'plugin_args': None,
        'qcache': False,
        'queue': None,
        'recoding_file': None,
        'src_subject_id': 'fsaverage',
        'th3': True
    }

    config['src_subject_dir'] = os.path.join(config['fs_home'], 'subjects',
                                             config['src_subject_id'])
    config['awk_file'] = os.path.join(config['fs_home'], 'bin',
                                      'extract_talairach_avi_QA.awk')
    config['registration_template'] = os.path.join(
        config['fs_home'], 'average', 'RB_all_{0}.gca'.format(rb_date))
    config['registration_template_withskull'] = os.path.join(
        config['fs_home'], 'average',
        'RB_all_withskull_{0}.gca'.format(rb_date))
    for hemi in ('lh', 'rh'):
        config['{0}_atlas'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.average.curvature.filled.buckner40.tif'.format(hemi))
        config['{0}_classifier'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.curvature.buckner40.filled.desikan_killiany.2010-03-25.gcs'.
            format(hemi))
        config['{0}_classifier2'.format(hemi)] = os.path.join(
            config['fs_home'], 'average',
            '{0}.destrieux.simple.2009-07-29.gcs'.format(hemi))
        config['{0}_classifier3'.format(hemi)] = os.path.join(
            config['fs_home'], 'average', '{0}.DKTatlas40.gcs'.format(hemi))
    config['LookUpTable'] = os.path.join(config['fs_home'], 'ASegStatsLUT.txt')
    config['WMLookUpTable'] = os.path.join(config['fs_home'],
                                           'WMParcStatsLUT.txt')
    config['AvgColorTable'] = os.path.join(config['fs_home'], 'average',
                                           'colortable_BA.txt')

    return config


def checkenv(exitonfail=False):
    """Check for the necessary FS environment variables"""
    import sys
    fs_home = os.environ.get('FREESURFER_HOME')
    path = os.environ.get('PATH')
    print("FREESURFER_HOME: {0}".format(fs_home))
    if fs_home is None:
        msg = "please set FREESURFER_HOME before running the workflow"
    elif not os.path.isdir(fs_home):
        msg = "FREESURFER_HOME must be set to a valid directory before running this workflow"
    elif os.path.join(fs_home, 'bin') not in path.replace('//', '/'):
        print(path)
        msg = "Could not find necessary executable in path"
        setupscript = os.path.join(fs_home, 'SetUpFreeSurfer.sh')
        if os.path.isfile(setupscript):
            print("Please source the setup script before running the workflow:"
                  + "\nsource {0}".format(setupscript))
        else:
            print(
                "Please ensure that FREESURFER_HOME is set to a valid fs " +
                "directory and source the necessary SetUpFreeSurfer.sh script before running "
                + "this workflow")
    else:
        return fs_home

    if exitonfail:
        print("ERROR: " + msg)
        sys.exit(2)
    else:
        print("Warning: " + msg)
