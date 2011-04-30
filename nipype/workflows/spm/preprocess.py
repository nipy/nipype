# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.pipeline.engine as pe

import nipype.interfaces.spm as spm
import nipype.algorithms.rapidart as ra
import nipype.interfaces.utility as niu

from nipype.workflows.freesurfer.utils import create_getmask_flow

def create_spm_preproc(name='preproc'):
    """Create an spm preprocessing workflow with freesurfer registration and
    artifact detection.

    The workflow realigns and smooths and registers the functional images with
    the subject's freesurfer space.

    Example
    -------

    >>> preproc = create_spm_preproc()
    >>> preproc.base_dir = '.'
    >>> preproc.inputs.inputspec.fwhm = 6
    >>> preproc.inputs.inputspec.subject_id = 's1'
    >>> preproc.inputs.inputspec.subjects_dir = '.'
    >>> preproc.inputs.inputspec.functionals = ['f3.nii', 'f5.nii']
    >>> preproc.inputs.inputspec.norm_threshold = 1
    >>> preproc.inputs.inputspec.zintensity_threshold = 3

    Inputs::

         inputspec.functionals : functional runs use 4d nifti
         inputspec.subject_id : freesurfer subject id
         inputspec.subjects_dir : freesurfer subjects dir
         inputspec.fwhm : smoothing fwhm
         inputspec.norm_threshold : norm threshold for outliers
         inputspec.zintensity_threshold : intensity threshold in z-score

    Outputs::

         outputspec.realignment_parameters : realignment parameter files
         outputspec.smoothed_files : smoothed functional files
         outputspec.outlier_files : list of outliers
         outputspec.outlier_files : statistics of outliers
         outputspec.outlier_files : images of outliers
         outputspec.mask_file : binary mask file in reference image space
         outputspec.reg_file : registration file that maps reference image to
                                 freesurfer space
    """

    """
    Initialize the workflow
    """

    workflow = pe.Workflow(name=name)

    """
    Define the inputs to this workflow
    """

    inputnode = pe.Node(niu.IdentityInterface(fields=['functionals',
                                                      'subject_id',
                                                      'subjects_dir',
                                                      'fwhm',
                                                      'norm_threshold',
                                                      'zintensity_threshold']),
                        name='inputspec')

    """
    Setup the processing nodes and create the mask generation and coregistration
    workflow
    """

    realign = pe.Node(spm.Realign(), name='realign')
    workflow.connect(inputnode, 'functionals', realign, 'in_files')
    maskflow = create_getmask_flow()
    workflow.connect([(inputnode, maskflow, [('subject_id','inputspec.subject_id'),
                                             ('subjects_dir', 'inputspec.subjects_dir')])])
    maskflow.inputs.inputspec.contrast_type = 't2'
    workflow.connect(realign, 'mean_image', maskflow, 'inputspec.source_file')
    smooth = pe.Node(spm.Smooth(), name='smooth')
    workflow.connect(inputnode, 'fwhm', smooth, 'fwhm')
    workflow.connect(realign, 'realigned_files', smooth, 'in_files')
    artdetect = pe.Node(ra.ArtifactDetect(mask_type='file',
                                          parameter_source='SPM',
                                          use_differences=[True,False],
                                          use_norm=True,
                                          save_plot=True),
                        name='artdetect')
    workflow.connect([(inputnode, artdetect,[('norm_threshold', 'norm_threshold'),
                                             ('zintensity_threshold',
                                              'zintensity_threshold')])])
    workflow.connect([(realign, artdetect, [('realigned_files', 'realigned_files'),
                                            ('realignment_parameters',
                                             'realignment_parameters')])])
    workflow.connect(maskflow, 'outputspec.mask_file', artdetect, 'mask_file')

    """
    Define the outputs of the workflow and connect the nodes to the outputnode
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["realignment_parameters",
                                                       "smoothed_files",
                                                       "mask_file",
                                                       "reg_file",
                                                       'outlier_files',
                                                       'outlier_stats',
                                                       'outlier_plots'
                                                       ]),
                         name="outputspec")
    workflow.connect([
            (maskflow, outputnode, [("outputspec.reg_file", "reg_file")]),
            (maskflow, outputnode, [("outputspec.mask_file", "mask_file")]),
            (realign, outputnode, [('realignment_parameters', 'realignment_parameters')]),
            (smooth, outputnode, [('smoothed_files', 'smoothed_files')]),
            (artdetect, outputnode,[('outlier_files', 'outlier_files'),
                                    ('statistic_files','outlier_stats'),
                                    ('plot_files','outlier_plots')])
            ])
    return workflow
