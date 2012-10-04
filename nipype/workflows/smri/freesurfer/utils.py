# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.meshfix as mf
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
import nipype.algorithms.misc as misc
from nipype.interfaces.utility import Function
from nipype.workflows.misc.utils import region_list_from_volume, id_list_from_lookup_table
import os, os.path as op


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

    inputnode = pe.Node(niu.IdentityInterface(fields=['source_file',
                                                      'subject_id',
                                                      'subjects_dir',
                                                      'contrast_type']),
                        name='inputspec')

    """
    Define all the nodes of the workflow:

    fssource: used to retrieve aseg.mgz
    threshold : binarize aseg
    register : coregister source file to freesurfer space
    voltransform: convert binarized aseg to source file space
    """

    fssource = pe.Node(nio.FreeSurferSource(),
        name = 'fssource')
    threshold = pe.Node(fs.Binarize(min=0.5, out_type='nii'),
        name='threshold')
    register = pe.MapNode(fs.BBRegister(init='fsl'),
        iterfield=['source_file'],
        name='register')
    voltransform = pe.MapNode(fs.ApplyVolTransform(inverse=True),
        iterfield=['source_file', 'reg_file'],
        name='transform')

    """
    Connect the nodes
    """

    getmask.connect([
        (inputnode, fssource, [('subject_id','subject_id'),
            ('subjects_dir','subjects_dir')]),
        (inputnode, register, [('source_file', 'source_file'),
            ('subject_id', 'subject_id'),
            ('subjects_dir', 'subjects_dir'),
            ('contrast_type', 'contrast_type')]),
        (inputnode, voltransform, [('subjects_dir', 'subjects_dir'),
            ('source_file', 'source_file')]),
        (fssource, threshold, [(('aparc_aseg', get_aparc_aseg), 'in_file')]),
        (register, voltransform, [('out_reg_file','reg_file')]),
        (threshold, voltransform, [('binary_file','target_file')])
    ])


    """
    Add remaining nodes and connections

    dilate : dilate the transformed file in source space
    threshold2 : binarize transformed file
    """

    threshold2 = pe.MapNode(fs.Binarize(min=0.5, out_type='nii'),
        iterfield=['in_file'],
        name='threshold2')
    if dilate_mask:
        threshold2.inputs.dilate = 1
    getmask.connect([
        (voltransform, threshold2, [('transformed_file', 'in_file')])
    ])

    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["mask_file",
                                                       "reg_file",
                                                       "reg_cost"
    ]),
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
        inputnode = pe.Node(niu.IdentityInterface(fields=['source_file',
                                                          'label_file',
                                                          'reg_file',
                                                          'subjects_dir']),
                            name='inputspec')
    else:
        inputnode = pe.Node(niu.IdentityInterface(fields=['source_file',
                                                          'label_file']),
                            name='inputspec')


    statnode = pe.MapNode(fs.SegStats(),
                          iterfield=['segmentation_file','in_file'],
                          name='segstats')

    """
    Convert between source and label spaces if registration info is provided

    """
    if withreg:
        voltransform = pe.MapNode(fs.ApplyVolTransform(inverse=True),
                                  iterfield=['source_file', 'reg_file'],
                                  name='transform')
        getstats.connect(inputnode, 'reg_file', voltransform, 'reg_file')
        getstats.connect(inputnode, 'source_file', voltransform, 'source_file')
        getstats.connect(inputnode, 'label_file', voltransform, 'target_file')
        getstats.connect(inputnode, 'subjects_dir', voltransform, 'subjects_dir')

        def switch_labels(inverse, transform_output, source_file, label_file):
            if inverse:
                return transform_output, source_file
            else:
                return label_file, transform_output

        chooser = pe.MapNode(niu.Function(input_names = ['inverse',
                                                         'transform_output',
                                                         'source_file',
                                                         'label_file'],
                                          output_names = ['label_file',
                                                          'source_file'],
                                          function=switch_labels),
                             iterfield=['transform_output','source_file'],
                             name='chooser')
        getstats.connect(inputnode,'source_file', chooser, 'source_file')
        getstats.connect(inputnode,'label_file', chooser, 'label_file')
        getstats.connect(inputnode,'inverse', chooser, 'inverse')
        getstats.connect(voltransform, 'transformed_file', chooser, 'transform_output')
        getstats.connect(chooser, 'label_file', statnode, 'segmentation_file')
        getstats.connect(chooser, 'source_file', statnode, 'in_file')
    else:
        getstats.connect(inputnode, 'label_file', statnode, 'segmentation_file')
        getstats.connect(inputnode, 'source_file', statnode, 'in_file')

    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["stats_file"
                                                        ]),
                         name="outputspec")
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

    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                      'subjects_dir',
                                                      'lookup_file']),
                        name='inputspec')

    """
    Define all the nodes of the workflow:

      fssource: used to retrieve aseg.mgz
      mri_convert : converts aseg.mgz to aseg.nii
      tessellate : tessellates regions in aseg.mgz
      surfconvert : converts regions to stereolithographic (.stl) format
      smoother: smooths the tessellated regions

    """

    fssource = pe.Node(nio.FreeSurferSource(),
                       name = 'fssource')
    volconvert = pe.Node(fs.MRIConvert(out_type='nii'),
                       name = 'volconvert')
    tessellate = pe.MapNode(fs.MRIMarchingCubes(),
                        iterfield=['label_value','out_file'],
                        name='tessellate')
    surfconvert = pe.MapNode(fs.MRIsConvert(out_datatype='stl'),
                          iterfield=['in_file'],
                          name='surfconvert')
    smoother = pe.MapNode(mf.MeshFix(),
			  iterfield=['in_file1'],
                          name='smoother')
    if out_format == 'gii':
	stl_to_gifti = pe.MapNode(fs.MRIsConvert(out_datatype=out_format),
			      iterfield=['in_file'],
			      name='stl_to_gifti')
    smoother.inputs.save_as_stl = True
    smoother.inputs.laplacian_smoothing_steps = 1

    region_list_from_volume_interface = Function(input_names=["in_file"],
                             output_names=["region_list"],
                             function=region_list_from_volume)

    id_list_from_lookup_table_interface = Function(input_names=["lookup_file", "region_list"],
                             output_names=["id_list"],
                             function=id_list_from_lookup_table)

    region_list_from_volume_node = pe.Node(interface=region_list_from_volume_interface, name='region_list_from_volume_node')
    id_list_from_lookup_table_node = pe.Node(interface=id_list_from_lookup_table_interface, name='id_list_from_lookup_table_node')

    """
    Connect the nodes
    """

    tessflow.connect([
            (inputnode, fssource, [('subject_id','subject_id'),
                                   ('subjects_dir','subjects_dir')]),
            (fssource, volconvert, [('aseg', 'in_file')]),
            (volconvert, region_list_from_volume_node, [('out_file', 'in_file')]),
            (region_list_from_volume_node, tessellate, [('region_list', 'label_value')]),
            (region_list_from_volume_node, id_list_from_lookup_table_node, [('region_list', 'region_list')]),
            (inputnode, id_list_from_lookup_table_node, [('lookup_file', 'lookup_file')]),
            (id_list_from_lookup_table_node, tessellate, [('id_list', 'out_file')]),
            (fssource, tessellate, [('aseg', 'in_file')]),
            (tessellate, surfconvert, [('surface','in_file')]),
	    (surfconvert, smoother, [('converted','in_file1')]),
            ])

    """
    Setup an outputnode that defines relevant inputs of the workflow.
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["meshes"]),
			 name="outputspec")

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
