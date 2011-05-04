# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.pipeline.engine as pe

import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu

def create_getmask_flow(name='getmask', dilate_mask=True):
    """Registers a source file to freesurfer space and create a brain mask in
    source space

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
    register = pe.Node(fs.BBRegister(init='fsl'), name='register')
    voltransform = pe.Node(fs.ApplyVolTransform(inverse=True), name='transform')

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
            (fssource, threshold, [('aseg', 'in_file')]),
            (register, voltransform, [('out_reg_file','reg_file')]),
            (threshold, voltransform, [('binary_file','target_file')])
            ])


    """
    Add remaining nodes and connections

    dilate : dilate the transformed file in source space
    threshold2 : binarize transformed file
    """
    
    threshold2 = pe.Node(fs.Binarize(min=0.5, out_type='nii'),
                        name='threshold2')
    if dilate_mask:
        dilate = pe.Node(fsl.maths.DilateImage(operation='max'),
                         name='dilate')
        getmask.connect([
            (voltransform, dilate, [('transformed_file', 'in_file')]),
            (dilate, threshold2, [('out_file', 'in_file')]),
            ])
    else:
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
