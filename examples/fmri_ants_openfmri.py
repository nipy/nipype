#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=============================================
fMRI: OpenfMRI.org data, FSL, ANTS, c3daffine
=============================================

A growing number of datasets are available on `OpenfMRI <http://openfmri.org>`_.
This script demonstrates how to use nipype to analyze a data set::

    python fmri_ants_openfmri.py --datasetdir ds107

"""

from __future__ import division, unicode_literals
from builtins import open, range, str, bytes

from glob import glob
import os

from nipype import config
from nipype import LooseVersion
from nipype import Workflow, Node, MapNode
from nipype.utils.filemanip import filename_to_list
import nipype.pipeline.engine as pe
import nipype.algorithms.modelgen as model
import nipype.algorithms.rapidart as ra
from nipype.algorithms.misc import TSNR, CalculateMedian
from nipype.interfaces.c3 import C3dAffineTool
from nipype.interfaces import fsl, Function, ants, freesurfer as fs
import nipype.interfaces.io as nio
from nipype.interfaces.io import FreeSurferSource
import nipype.interfaces.utility as niu
from nipype.interfaces.utility import Merge, IdentityInterface
from nipype.workflows.fmri.fsl import (create_featreg_preproc,
                                       create_modelfit_workflow,
                                       create_fixed_effects_flow)
from nipype.utils import NUMPY_MMAP

config.enable_provenance()
version = 0
if (fsl.Info.version()
        and LooseVersion(fsl.Info.version()) > LooseVersion('5.0.6')):
    version = 507

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

imports = [
    'import os', 'import nibabel as nb', 'import numpy as np',
    'import scipy as sp',
    'from nipype.utils.filemanip import filename_to_list, list_to_filename, split_filename',
    'from scipy.special import legendre'
]


def create_reg_workflow(name='registration'):
    """Create a FEAT preprocessing workflow together with freesurfer

    Parameters
    ----------
        name : name of workflow (default: 'registration')

    Inputs:

        inputspec.source_files : files (filename or list of filenames to register)
        inputspec.mean_image : reference image to use
        inputspec.anatomical_image : anatomical image to coregister to
        inputspec.target_image : registration target

    Outputs:

        outputspec.func2anat_transform : FLIRT transform
        outputspec.anat2target_transform : FLIRT+FNIRT transform
        outputspec.transformed_files : transformed files in target space
        outputspec.transformed_mean : mean image in target space
    """

    register = pe.Workflow(name=name)

    inputnode = pe.Node(
        interface=niu.IdentityInterface(fields=[
            'source_files', 'mean_image', 'anatomical_image', 'target_image',
            'target_image_brain', 'config_file'
        ]),
        name='inputspec')
    outputnode = pe.Node(
        interface=niu.IdentityInterface(fields=[
            'func2anat_transform', 'anat2target_transform',
            'transformed_files', 'transformed_mean', 'anat2target',
            'mean2anat_mask'
        ]),
        name='outputspec')
    """
    Estimate the tissue classes from the anatomical image. But use spm's segment
    as FSL appears to be breaking.
    """

    stripper = pe.Node(fsl.BET(), name='stripper')
    register.connect(inputnode, 'anatomical_image', stripper, 'in_file')
    fast = pe.Node(fsl.FAST(), name='fast')
    register.connect(stripper, 'out_file', fast, 'in_files')
    """
    Binarize the segmentation
    """

    binarize = pe.Node(
        fsl.ImageMaths(op_string='-nan -thr 0.5 -bin'), name='binarize')
    pickindex = lambda x, i: x[i]
    register.connect(fast, ('partial_volume_files', pickindex, 2), binarize,
                     'in_file')
    """
    Calculate rigid transform from mean image to anatomical image
    """

    mean2anat = pe.Node(fsl.FLIRT(), name='mean2anat')
    mean2anat.inputs.dof = 6
    register.connect(inputnode, 'mean_image', mean2anat, 'in_file')
    register.connect(stripper, 'out_file', mean2anat, 'reference')
    """
    Now use bbr cost function to improve the transform
    """

    mean2anatbbr = pe.Node(fsl.FLIRT(), name='mean2anatbbr')
    mean2anatbbr.inputs.dof = 6
    mean2anatbbr.inputs.cost = 'bbr'
    mean2anatbbr.inputs.schedule = os.path.join(
        os.getenv('FSLDIR'), 'etc/flirtsch/bbr.sch')
    register.connect(inputnode, 'mean_image', mean2anatbbr, 'in_file')
    register.connect(binarize, 'out_file', mean2anatbbr, 'wm_seg')
    register.connect(inputnode, 'anatomical_image', mean2anatbbr, 'reference')
    register.connect(mean2anat, 'out_matrix_file', mean2anatbbr,
                     'in_matrix_file')
    """
    Create a mask of the median image coregistered to the anatomical image
    """

    mean2anat_mask = Node(fsl.BET(mask=True), name='mean2anat_mask')
    register.connect(mean2anatbbr, 'out_file', mean2anat_mask, 'in_file')
    """
    Convert the BBRegister transformation to ANTS ITK format
    """

    convert2itk = pe.Node(C3dAffineTool(), name='convert2itk')
    convert2itk.inputs.fsl2ras = True
    convert2itk.inputs.itk_transform = True
    register.connect(mean2anatbbr, 'out_matrix_file', convert2itk,
                     'transform_file')
    register.connect(inputnode, 'mean_image', convert2itk, 'source_file')
    register.connect(stripper, 'out_file', convert2itk, 'reference_file')
    """
    Compute registration between the subject's structural and MNI template
    This is currently set to perform a very quick registration. However, the
    registration can be made significantly more accurate for cortical
    structures by increasing the number of iterations
    All parameters are set using the example from:
    #https://github.com/stnava/ANTs/blob/master/Scripts/newAntsExample.sh
    """

    reg = pe.Node(ants.Registration(), name='antsRegister')
    reg.inputs.output_transform_prefix = "output_"
    reg.inputs.transforms = ['Rigid', 'Affine', 'SyN']
    reg.inputs.transform_parameters = [(0.1, ), (0.1, ), (0.2, 3.0, 0.0)]
    reg.inputs.number_of_iterations = [[10000, 11110, 11110]] * 2 + [[
        100, 30, 20
    ]]
    reg.inputs.dimension = 3
    reg.inputs.write_composite_transform = True
    reg.inputs.collapse_output_transforms = True
    reg.inputs.initial_moving_transform_com = True
    reg.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
    reg.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
    reg.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
    reg.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
    reg.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
    reg.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
    reg.inputs.convergence_window_size = [20] * 2 + [5]
    reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
    reg.inputs.sigma_units = ['vox'] * 3
    reg.inputs.shrink_factors = [[3, 2, 1]] * 2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 3
    reg.inputs.use_histogram_matching = [False] * 2 + [True]
    reg.inputs.winsorize_lower_quantile = 0.005
    reg.inputs.winsorize_upper_quantile = 0.995
    reg.inputs.args = '--float'
    reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    reg.inputs.num_threads = 4
    reg.plugin_args = {
        'qsub_args': '-pe orte 4',
        'sbatch_args': '--mem=6G -c 4'
    }
    register.connect(stripper, 'out_file', reg, 'moving_image')
    register.connect(inputnode, 'target_image_brain', reg, 'fixed_image')
    """
    Concatenate the affine and ants transforms into a list
    """

    merge = pe.Node(niu.Merge(2), iterfield=['in2'], name='mergexfm')
    register.connect(convert2itk, 'itk_transform', merge, 'in2')
    register.connect(reg, 'composite_transform', merge, 'in1')
    """
    Transform the mean image. First to anatomical and then to target
    """

    warpmean = pe.Node(ants.ApplyTransforms(), name='warpmean')
    warpmean.inputs.input_image_type = 0
    warpmean.inputs.interpolation = 'Linear'
    warpmean.inputs.invert_transform_flags = [False, False]
    warpmean.terminal_output = 'file'

    register.connect(inputnode, 'target_image_brain', warpmean,
                     'reference_image')
    register.connect(inputnode, 'mean_image', warpmean, 'input_image')
    register.connect(merge, 'out', warpmean, 'transforms')
    """
    Transform the remaining images. First to anatomical and then to target
    """

    warpall = pe.MapNode(
        ants.ApplyTransforms(), iterfield=['input_image'], name='warpall')
    warpall.inputs.input_image_type = 0
    warpall.inputs.interpolation = 'Linear'
    warpall.inputs.invert_transform_flags = [False, False]
    warpall.terminal_output = 'file'

    register.connect(inputnode, 'target_image_brain', warpall,
                     'reference_image')
    register.connect(inputnode, 'source_files', warpall, 'input_image')
    register.connect(merge, 'out', warpall, 'transforms')
    """
    Assign all the output files
    """

    register.connect(reg, 'warped_image', outputnode, 'anat2target')
    register.connect(warpmean, 'output_image', outputnode, 'transformed_mean')
    register.connect(warpall, 'output_image', outputnode, 'transformed_files')
    register.connect(mean2anatbbr, 'out_matrix_file', outputnode,
                     'func2anat_transform')
    register.connect(mean2anat_mask, 'mask_file', outputnode, 'mean2anat_mask')
    register.connect(reg, 'composite_transform', outputnode,
                     'anat2target_transform')

    return register


def get_aparc_aseg(files):
    """Return the aparc+aseg.mgz file"""
    for name in files:
        if 'aparc+aseg.mgz' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')


def create_fs_reg_workflow(name='registration'):
    """Create a FEAT preprocessing workflow together with freesurfer

    Parameters
    ----------

        name : name of workflow (default: 'registration')

    Inputs::

        inputspec.source_files : files (filename or list of filenames to register)
        inputspec.mean_image : reference image to use
        inputspec.target_image : registration target

    Outputs::

        outputspec.func2anat_transform : FLIRT transform
        outputspec.anat2target_transform : FLIRT+FNIRT transform
        outputspec.transformed_files : transformed files in target space
        outputspec.transformed_mean : mean image in target space
    """

    register = Workflow(name=name)

    inputnode = Node(
        interface=IdentityInterface(fields=[
            'source_files', 'mean_image', 'subject_id', 'subjects_dir',
            'target_image'
        ]),
        name='inputspec')

    outputnode = Node(
        interface=IdentityInterface(fields=[
            'func2anat_transform', 'out_reg_file', 'anat2target_transform',
            'transforms', 'transformed_mean', 'transformed_files',
            'min_cost_file', 'anat2target', 'aparc', 'mean2anat_mask'
        ]),
        name='outputspec')

    # Get the subject's freesurfer source directory
    fssource = Node(FreeSurferSource(), name='fssource')
    fssource.run_without_submitting = True
    register.connect(inputnode, 'subject_id', fssource, 'subject_id')
    register.connect(inputnode, 'subjects_dir', fssource, 'subjects_dir')

    convert = Node(freesurfer.MRIConvert(out_type='nii'), name="convert")
    register.connect(fssource, 'T1', convert, 'in_file')

    # Coregister the median to the surface
    bbregister = Node(
        freesurfer.BBRegister(registered_file=True), name='bbregister')
    bbregister.inputs.init = 'fsl'
    bbregister.inputs.contrast_type = 't2'
    bbregister.inputs.out_fsl_file = True
    bbregister.inputs.epi_mask = True
    register.connect(inputnode, 'subject_id', bbregister, 'subject_id')
    register.connect(inputnode, 'mean_image', bbregister, 'source_file')
    register.connect(inputnode, 'subjects_dir', bbregister, 'subjects_dir')

    # Create a mask of the median coregistered to the anatomical image
    mean2anat_mask = Node(fsl.BET(mask=True), name='mean2anat_mask')
    register.connect(bbregister, 'registered_file', mean2anat_mask, 'in_file')
    """
    use aparc+aseg's brain mask
    """

    binarize = Node(
        fs.Binarize(min=0.5, out_type="nii.gz", dilate=1),
        name="binarize_aparc")
    register.connect(fssource, ("aparc_aseg", get_aparc_aseg), binarize,
                     "in_file")

    stripper = Node(fsl.ApplyMask(), name='stripper')
    register.connect(binarize, "binary_file", stripper, "mask_file")
    register.connect(convert, 'out_file', stripper, 'in_file')
    """
    Apply inverse transform to aparc file
    """

    aparcxfm = Node(
        freesurfer.ApplyVolTransform(inverse=True, interp='nearest'),
        name='aparc_inverse_transform')
    register.connect(inputnode, 'subjects_dir', aparcxfm, 'subjects_dir')
    register.connect(bbregister, 'out_reg_file', aparcxfm, 'reg_file')
    register.connect(fssource, ('aparc_aseg', get_aparc_aseg), aparcxfm,
                     'target_file')
    register.connect(inputnode, 'mean_image', aparcxfm, 'source_file')
    """
    Convert the BBRegister transformation to ANTS ITK format
    """

    convert2itk = Node(C3dAffineTool(), name='convert2itk')
    convert2itk.inputs.fsl2ras = True
    convert2itk.inputs.itk_transform = True
    register.connect(bbregister, 'out_fsl_file', convert2itk, 'transform_file')
    register.connect(inputnode, 'mean_image', convert2itk, 'source_file')
    register.connect(stripper, 'out_file', convert2itk, 'reference_file')
    """
    Compute registration between the subject's structural and MNI template
    This is currently set to perform a very quick registration. However, the
    registration can be made significantly more accurate for cortical
    structures by increasing the number of iterations
    All parameters are set using the example from:
    #https://github.com/stnava/ANTs/blob/master/Scripts/newAntsExample.sh
    """

    reg = Node(ants.Registration(), name='antsRegister')
    reg.inputs.output_transform_prefix = "output_"
    reg.inputs.transforms = ['Rigid', 'Affine', 'SyN']
    reg.inputs.transform_parameters = [(0.1, ), (0.1, ), (0.2, 3.0, 0.0)]
    reg.inputs.number_of_iterations = [[10000, 11110, 11110]] * 2 + [[
        100, 30, 20
    ]]
    reg.inputs.dimension = 3
    reg.inputs.write_composite_transform = True
    reg.inputs.collapse_output_transforms = True
    reg.inputs.initial_moving_transform_com = True
    reg.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
    reg.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
    reg.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
    reg.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
    reg.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
    reg.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
    reg.inputs.convergence_window_size = [20] * 2 + [5]
    reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
    reg.inputs.sigma_units = ['vox'] * 3
    reg.inputs.shrink_factors = [[3, 2, 1]] * 2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 3
    reg.inputs.use_histogram_matching = [False] * 2 + [True]
    reg.inputs.winsorize_lower_quantile = 0.005
    reg.inputs.winsorize_upper_quantile = 0.995
    reg.inputs.float = True
    reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    reg.inputs.num_threads = 4
    reg.plugin_args = {
        'qsub_args': '-pe orte 4',
        'sbatch_args': '--mem=6G -c 4'
    }
    register.connect(stripper, 'out_file', reg, 'moving_image')
    register.connect(inputnode, 'target_image', reg, 'fixed_image')
    """
    Concatenate the affine and ants transforms into a list
    """

    merge = Node(Merge(2), iterfield=['in2'], name='mergexfm')
    register.connect(convert2itk, 'itk_transform', merge, 'in2')
    register.connect(reg, 'composite_transform', merge, 'in1')
    """
    Transform the mean image. First to anatomical and then to target
    """

    warpmean = Node(ants.ApplyTransforms(), name='warpmean')
    warpmean.inputs.input_image_type = 0
    warpmean.inputs.interpolation = 'Linear'
    warpmean.inputs.invert_transform_flags = [False, False]
    warpmean.terminal_output = 'file'
    warpmean.inputs.args = '--float'
    # warpmean.inputs.num_threads = 4
    # warpmean.plugin_args = {'sbatch_args': '--mem=4G -c 4'}
    """
    Transform the remaining images. First to anatomical and then to target
    """

    warpall = pe.MapNode(
        ants.ApplyTransforms(), iterfield=['input_image'], name='warpall')
    warpall.inputs.input_image_type = 0
    warpall.inputs.interpolation = 'Linear'
    warpall.inputs.invert_transform_flags = [False, False]
    warpall.terminal_output = 'file'
    warpall.inputs.args = '--float'
    warpall.inputs.num_threads = 2
    warpall.plugin_args = {'sbatch_args': '--mem=6G -c 2'}
    """
    Assign all the output files
    """

    register.connect(warpmean, 'output_image', outputnode, 'transformed_mean')
    register.connect(warpall, 'output_image', outputnode, 'transformed_files')

    register.connect(inputnode, 'target_image', warpmean, 'reference_image')
    register.connect(inputnode, 'mean_image', warpmean, 'input_image')
    register.connect(merge, 'out', warpmean, 'transforms')
    register.connect(inputnode, 'target_image', warpall, 'reference_image')
    register.connect(inputnode, 'source_files', warpall, 'input_image')
    register.connect(merge, 'out', warpall, 'transforms')
    """
    Assign all the output files
    """

    register.connect(reg, 'warped_image', outputnode, 'anat2target')
    register.connect(aparcxfm, 'transformed_file', outputnode, 'aparc')
    register.connect(bbregister, 'out_fsl_file', outputnode,
                     'func2anat_transform')
    register.connect(bbregister, 'out_reg_file', outputnode, 'out_reg_file')
    register.connect(bbregister, 'min_cost_file', outputnode, 'min_cost_file')
    register.connect(mean2anat_mask, 'mask_file', outputnode, 'mean2anat_mask')
    register.connect(reg, 'composite_transform', outputnode,
                     'anat2target_transform')
    register.connect(merge, 'out', outputnode, 'transforms')

    return register


"""
Get info for a given subject
"""


def get_subjectinfo(subject_id, base_dir, task_id, model_id):
    """Get info for a given subject

    Parameters
    ----------
    subject_id : string
        Subject identifier (e.g., sub001)
    base_dir : string
        Path to base directory of the dataset
    task_id : int
        Which task to process
    model_id : int
        Which model to process

    Returns
    -------
    run_ids : list of ints
        Run numbers
    conds : list of str
        Condition names
    TR : float
        Repetition time
    """
    from glob import glob
    import os
    import numpy as np
    condition_info = []
    cond_file = os.path.join(base_dir, 'models', 'model%03d' % model_id,
                             'condition_key.txt')
    with open(cond_file, 'rt') as fp:
        for line in fp:
            info = line.strip().split()
            condition_info.append([info[0], info[1], ' '.join(info[2:])])
    if len(condition_info) == 0:
        raise ValueError('No condition info found in %s' % cond_file)
    taskinfo = np.array(condition_info)
    n_tasks = len(np.unique(taskinfo[:, 0]))
    conds = []
    run_ids = []
    if task_id > n_tasks:
        raise ValueError('Task id %d does not exist' % task_id)
    for idx in range(n_tasks):
        taskidx = np.where(taskinfo[:, 0] == 'task%03d' % (idx + 1))
        conds.append([
            condition.replace(' ', '_')
            for condition in taskinfo[taskidx[0], 2]
        ])  # if 'junk' not in condition])
        files = sorted(
            glob(
                os.path.join(base_dir, subject_id, 'BOLD',
                             'task%03d_run*' % (idx + 1))))
        runs = [int(val[-3:]) for val in files]
        run_ids.insert(idx, runs)
    json_info = os.path.join(base_dir, subject_id, 'BOLD', 'task%03d_run%03d' %
                             (task_id,
                              run_ids[task_id - 1][0]), 'bold_scaninfo.json')
    if os.path.exists(json_info):
        import json
        with open(json_info, 'rt') as fp:
            data = json.load(fp)
            TR = data['global']['const']['RepetitionTime'] / 1000.
    else:
        task_scan_key = os.path.join(
            base_dir, subject_id, 'BOLD', 'task%03d_run%03d' %
            (task_id, run_ids[task_id - 1][0]), 'scan_key.txt')
        if os.path.exists(task_scan_key):
            TR = np.genfromtxt(task_scan_key)[1]
        else:
            TR = np.genfromtxt(os.path.join(base_dir, 'scan_key.txt'))[1]
    return run_ids[task_id - 1], conds[task_id - 1], TR


"""
Analyzes an open fmri dataset
"""


def analyze_openfmri_dataset(data_dir,
                             subject=None,
                             model_id=None,
                             task_id=None,
                             output_dir=None,
                             subj_prefix='*',
                             hpcutoff=120.,
                             use_derivatives=True,
                             fwhm=6.0,
                             subjects_dir=None,
                             target=None):
    """Analyzes an open fmri dataset

    Parameters
    ----------

    data_dir : str
        Path to the base data directory

    work_dir : str
        Nipype working directory (defaults to cwd)
    """
    """
    Load nipype workflows
    """

    preproc = create_featreg_preproc(whichvol='first')
    modelfit = create_modelfit_workflow()
    fixed_fx = create_fixed_effects_flow()
    if subjects_dir:
        registration = create_fs_reg_workflow()
    else:
        registration = create_reg_workflow()
    """
    Remove the plotting connection so that plot iterables don't propagate
    to the model stage
    """

    preproc.disconnect(
        preproc.get_node('plot_motion'), 'out_file',
        preproc.get_node('outputspec'), 'motion_plots')
    """
    Set up openfmri data specific components
    """

    subjects = sorted([
        path.split(os.path.sep)[-1]
        for path in glob(os.path.join(data_dir, subj_prefix))
    ])

    infosource = pe.Node(
        niu.IdentityInterface(fields=['subject_id', 'model_id', 'task_id']),
        name='infosource')
    if len(subject) == 0:
        infosource.iterables = [('subject_id', subjects),
                                ('model_id', [model_id]), ('task_id', task_id)]
    else:
        infosource.iterables = [('subject_id', [
            subjects[subjects.index(subj)] for subj in subject
        ]), ('model_id', [model_id]), ('task_id', task_id)]

    subjinfo = pe.Node(
        niu.Function(
            input_names=['subject_id', 'base_dir', 'task_id', 'model_id'],
            output_names=['run_id', 'conds', 'TR'],
            function=get_subjectinfo),
        name='subjectinfo')
    subjinfo.inputs.base_dir = data_dir
    """
    Return data components as anat, bold and behav
    """

    contrast_file = os.path.join(data_dir, 'models', 'model%03d' % model_id,
                                 'task_contrasts.txt')
    has_contrast = os.path.exists(contrast_file)
    if has_contrast:
        datasource = pe.Node(
            nio.DataGrabber(
                infields=['subject_id', 'run_id', 'task_id', 'model_id'],
                outfields=['anat', 'bold', 'behav', 'contrasts']),
            name='datasource')
    else:
        datasource = pe.Node(
            nio.DataGrabber(
                infields=['subject_id', 'run_id', 'task_id', 'model_id'],
                outfields=['anat', 'bold', 'behav']),
            name='datasource')
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template = '*'

    if has_contrast:
        datasource.inputs.field_template = {
            'anat': '%s/anatomy/T1_001.nii.gz',
            'bold': '%s/BOLD/task%03d_r*/bold.nii.gz',
            'behav': ('%s/model/model%03d/onsets/task%03d_'
                      'run%03d/cond*.txt'),
            'contrasts': ('models/model%03d/'
                          'task_contrasts.txt')
        }
        datasource.inputs.template_args = {
            'anat': [['subject_id']],
            'bold': [['subject_id', 'task_id']],
            'behav': [['subject_id', 'model_id', 'task_id', 'run_id']],
            'contrasts': [['model_id']]
        }
    else:
        datasource.inputs.field_template = {
            'anat': '%s/anatomy/T1_001.nii.gz',
            'bold': '%s/BOLD/task%03d_r*/bold.nii.gz',
            'behav': ('%s/model/model%03d/onsets/task%03d_'
                      'run%03d/cond*.txt')
        }
        datasource.inputs.template_args = {
            'anat': [['subject_id']],
            'bold': [['subject_id', 'task_id']],
            'behav': [['subject_id', 'model_id', 'task_id', 'run_id']]
        }

    datasource.inputs.sort_filelist = True
    """
    Create meta workflow
    """

    wf = pe.Workflow(name='openfmri')
    wf.connect(infosource, 'subject_id', subjinfo, 'subject_id')
    wf.connect(infosource, 'model_id', subjinfo, 'model_id')
    wf.connect(infosource, 'task_id', subjinfo, 'task_id')
    wf.connect(infosource, 'subject_id', datasource, 'subject_id')
    wf.connect(infosource, 'model_id', datasource, 'model_id')
    wf.connect(infosource, 'task_id', datasource, 'task_id')
    wf.connect(subjinfo, 'run_id', datasource, 'run_id')
    wf.connect([
        (datasource, preproc, [('bold', 'inputspec.func')]),
    ])

    def get_highpass(TR, hpcutoff):
        return hpcutoff / (2. * TR)

    gethighpass = pe.Node(
        niu.Function(
            input_names=['TR', 'hpcutoff'],
            output_names=['highpass'],
            function=get_highpass),
        name='gethighpass')
    wf.connect(subjinfo, 'TR', gethighpass, 'TR')
    wf.connect(gethighpass, 'highpass', preproc, 'inputspec.highpass')
    """
    Setup a basic set of contrasts, a t-test per condition
    """

    def get_contrasts(contrast_file, task_id, conds):
        import numpy as np
        import os
        contrast_def = []
        if os.path.exists(contrast_file):
            with open(contrast_file, 'rt') as fp:
                contrast_def.extend([
                    np.array(row.split()) for row in fp.readlines()
                    if row.strip()
                ])
        contrasts = []
        for row in contrast_def:
            if row[0] != 'task%03d' % task_id:
                continue
            con = [
                row[1], 'T', ['cond%03d' % (i + 1) for i in range(len(conds))],
                row[2:].astype(float).tolist()
            ]
            contrasts.append(con)
        # add auto contrasts for each column
        for i, cond in enumerate(conds):
            con = [cond, 'T', ['cond%03d' % (i + 1)], [1]]
            contrasts.append(con)
        return contrasts

    contrastgen = pe.Node(
        niu.Function(
            input_names=['contrast_file', 'task_id', 'conds'],
            output_names=['contrasts'],
            function=get_contrasts),
        name='contrastgen')

    art = pe.MapNode(
        interface=ra.ArtifactDetect(
            use_differences=[True, False],
            use_norm=True,
            norm_threshold=1,
            zintensity_threshold=3,
            parameter_source='FSL',
            mask_type='file'),
        iterfield=['realigned_files', 'realignment_parameters', 'mask_file'],
        name="art")

    modelspec = pe.Node(interface=model.SpecifyModel(), name="modelspec")
    modelspec.inputs.input_units = 'secs'

    def check_behav_list(behav, run_id, conds):
        import numpy as np
        num_conds = len(conds)
        if isinstance(behav, (str, bytes)):
            behav = [behav]
        behav_array = np.array(behav).flatten()
        num_elements = behav_array.shape[0]
        return behav_array.reshape(int(num_elements / num_conds),
                                   num_conds).tolist()

    reshape_behav = pe.Node(
        niu.Function(
            input_names=['behav', 'run_id', 'conds'],
            output_names=['behav'],
            function=check_behav_list),
        name='reshape_behav')

    wf.connect(subjinfo, 'TR', modelspec, 'time_repetition')
    wf.connect(datasource, 'behav', reshape_behav, 'behav')
    wf.connect(subjinfo, 'run_id', reshape_behav, 'run_id')
    wf.connect(subjinfo, 'conds', reshape_behav, 'conds')
    wf.connect(reshape_behav, 'behav', modelspec, 'event_files')

    wf.connect(subjinfo, 'TR', modelfit, 'inputspec.interscan_interval')
    wf.connect(subjinfo, 'conds', contrastgen, 'conds')
    if has_contrast:
        wf.connect(datasource, 'contrasts', contrastgen, 'contrast_file')
    else:
        contrastgen.inputs.contrast_file = ''
    wf.connect(infosource, 'task_id', contrastgen, 'task_id')
    wf.connect(contrastgen, 'contrasts', modelfit, 'inputspec.contrasts')

    wf.connect([(preproc, art,
                 [('outputspec.motion_parameters', 'realignment_parameters'),
                  ('outputspec.realigned_files',
                   'realigned_files'), ('outputspec.mask', 'mask_file')]),
                (preproc, modelspec,
                 [('outputspec.highpassed_files', 'functional_runs'),
                  ('outputspec.motion_parameters', 'realignment_parameters')]),
                (art, modelspec,
                 [('outlier_files', 'outlier_files')]), (modelspec, modelfit, [
                     ('session_info', 'inputspec.session_info')
                 ]), (preproc, modelfit, [('outputspec.highpassed_files',
                                           'inputspec.functional_data')])])

    # Comute TSNR on realigned data regressing polynomials upto order 2
    tsnr = MapNode(TSNR(regress_poly=2), iterfield=['in_file'], name='tsnr')
    wf.connect(preproc, "outputspec.realigned_files", tsnr, "in_file")

    # Compute the median image across runs
    calc_median = Node(CalculateMedian(), name='median')
    wf.connect(tsnr, 'detrended_file', calc_median, 'in_files')
    """
    Reorder the copes so that now it combines across runs
    """

    def sort_copes(copes, varcopes, contrasts):
        import numpy as np
        if not isinstance(copes, list):
            copes = [copes]
            varcopes = [varcopes]
        num_copes = len(contrasts)
        n_runs = len(copes)
        all_copes = np.array(copes).flatten()
        all_varcopes = np.array(varcopes).flatten()
        outcopes = all_copes.reshape(
            int(len(all_copes) / num_copes), num_copes).T.tolist()
        outvarcopes = all_varcopes.reshape(
            int(len(all_varcopes) / num_copes), num_copes).T.tolist()
        return outcopes, outvarcopes, n_runs

    cope_sorter = pe.Node(
        niu.Function(
            input_names=['copes', 'varcopes', 'contrasts'],
            output_names=['copes', 'varcopes', 'n_runs'],
            function=sort_copes),
        name='cope_sorter')

    pickfirst = lambda x: x[0]

    wf.connect(contrastgen, 'contrasts', cope_sorter, 'contrasts')
    wf.connect([(preproc, fixed_fx,
                 [(('outputspec.mask', pickfirst),
                   'flameo.mask_file')]), (modelfit, cope_sorter,
                                           [('outputspec.copes', 'copes')]),
                (modelfit, cope_sorter, [('outputspec.varcopes', 'varcopes')]),
                (cope_sorter, fixed_fx,
                 [('copes', 'inputspec.copes'), ('varcopes',
                                                 'inputspec.varcopes'),
                  ('n_runs', 'l2model.num_copes')]), (modelfit, fixed_fx, [
                      ('outputspec.dof_file', 'inputspec.dof_files'),
                  ])])

    wf.connect(calc_median, 'median_file', registration,
               'inputspec.mean_image')
    if subjects_dir:
        wf.connect(infosource, 'subject_id', registration,
                   'inputspec.subject_id')
        registration.inputs.inputspec.subjects_dir = subjects_dir
        registration.inputs.inputspec.target_image = fsl.Info.standard_image(
            'MNI152_T1_2mm_brain.nii.gz')
        if target:
            registration.inputs.inputspec.target_image = target
    else:
        wf.connect(datasource, 'anat', registration,
                   'inputspec.anatomical_image')
        registration.inputs.inputspec.target_image = fsl.Info.standard_image(
            'MNI152_T1_2mm.nii.gz')
        registration.inputs.inputspec.target_image_brain = fsl.Info.standard_image(
            'MNI152_T1_2mm_brain.nii.gz')
        registration.inputs.inputspec.config_file = 'T1_2_MNI152_2mm'

    def merge_files(copes, varcopes, zstats):
        out_files = []
        splits = []
        out_files.extend(copes)
        splits.append(len(copes))
        out_files.extend(varcopes)
        splits.append(len(varcopes))
        out_files.extend(zstats)
        splits.append(len(zstats))
        return out_files, splits

    mergefunc = pe.Node(
        niu.Function(
            input_names=['copes', 'varcopes', 'zstats'],
            output_names=['out_files', 'splits'],
            function=merge_files),
        name='merge_files')
    wf.connect([(fixed_fx.get_node('outputspec'), mergefunc, [
        ('copes', 'copes'),
        ('varcopes', 'varcopes'),
        ('zstats', 'zstats'),
    ])])
    wf.connect(mergefunc, 'out_files', registration, 'inputspec.source_files')

    def split_files(in_files, splits):
        copes = in_files[:splits[0]]
        varcopes = in_files[splits[0]:(splits[0] + splits[1])]
        zstats = in_files[(splits[0] + splits[1]):]
        return copes, varcopes, zstats

    splitfunc = pe.Node(
        niu.Function(
            input_names=['in_files', 'splits'],
            output_names=['copes', 'varcopes', 'zstats'],
            function=split_files),
        name='split_files')
    wf.connect(mergefunc, 'splits', splitfunc, 'splits')
    wf.connect(registration, 'outputspec.transformed_files', splitfunc,
               'in_files')

    if subjects_dir:
        get_roi_mean = pe.MapNode(
            fs.SegStats(default_color_table=True),
            iterfield=['in_file'],
            name='get_aparc_means')
        get_roi_mean.inputs.avgwf_txt_file = True
        wf.connect(
            fixed_fx.get_node('outputspec'), 'copes', get_roi_mean, 'in_file')
        wf.connect(registration, 'outputspec.aparc', get_roi_mean,
                   'segmentation_file')

        get_roi_tsnr = pe.MapNode(
            fs.SegStats(default_color_table=True),
            iterfield=['in_file'],
            name='get_aparc_tsnr')
        get_roi_tsnr.inputs.avgwf_txt_file = True
        wf.connect(tsnr, 'tsnr_file', get_roi_tsnr, 'in_file')
        wf.connect(registration, 'outputspec.aparc', get_roi_tsnr,
                   'segmentation_file')
    """
    Connect to a datasink
    """

    def get_subs(subject_id, conds, run_id, model_id, task_id):
        subs = [('_subject_id_%s_' % subject_id, '')]
        subs.append(('_model_id_%d' % model_id, 'model%03d' % model_id))
        subs.append(('task_id_%d/' % task_id, '/task%03d_' % task_id))
        subs.append(('bold_dtype_mcf_mask_smooth_mask_gms_tempfilt_mean_warp',
                     'mean'))
        subs.append(('bold_dtype_mcf_mask_smooth_mask_gms_tempfilt_mean_flirt',
                     'affine'))

        for i in range(len(conds)):
            subs.append(('_flameo%d/cope1.' % i, 'cope%02d.' % (i + 1)))
            subs.append(('_flameo%d/varcope1.' % i, 'varcope%02d.' % (i + 1)))
            subs.append(('_flameo%d/zstat1.' % i, 'zstat%02d.' % (i + 1)))
            subs.append(('_flameo%d/tstat1.' % i, 'tstat%02d.' % (i + 1)))
            subs.append(('_flameo%d/res4d.' % i, 'res4d%02d.' % (i + 1)))
            subs.append(('_warpall%d/cope1_warp.' % i, 'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_warp.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_warp.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
            subs.append(('_warpall%d/cope1_trans.' % i, 'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_trans.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_trans.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
            subs.append(('__get_aparc_means%d/' % i, '/cope%02d_' % (i + 1)))

        for i, run_num in enumerate(run_id):
            subs.append(('__get_aparc_tsnr%d/' % i, '/run%02d_' % run_num))
            subs.append(('__art%d/' % i, '/run%02d_' % run_num))
            subs.append(('__dilatemask%d/' % i, '/run%02d_' % run_num))
            subs.append(('__realign%d/' % i, '/run%02d_' % run_num))
            subs.append(('__modelgen%d/' % i, '/run%02d_' % run_num))
        subs.append(('/model%03d/task%03d/' % (model_id, task_id), '/'))
        subs.append(('/model%03d/task%03d_' % (model_id, task_id), '/'))
        subs.append(('_bold_dtype_mcf_bet_thresh_dil', '_mask'))
        subs.append(('_output_warped_image', '_anat2target'))
        subs.append(('median_flirt_brain_mask', 'median_brain_mask'))
        subs.append(('median_bbreg_brain_mask', 'median_brain_mask'))
        return subs

    subsgen = pe.Node(
        niu.Function(
            input_names=[
                'subject_id', 'conds', 'run_id', 'model_id', 'task_id'
            ],
            output_names=['substitutions'],
            function=get_subs),
        name='subsgen')
    wf.connect(subjinfo, 'run_id', subsgen, 'run_id')

    datasink = pe.Node(interface=nio.DataSink(), name="datasink")
    wf.connect(infosource, 'subject_id', datasink, 'container')
    wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
    wf.connect(infosource, 'model_id', subsgen, 'model_id')
    wf.connect(infosource, 'task_id', subsgen, 'task_id')
    wf.connect(contrastgen, 'contrasts', subsgen, 'conds')
    wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
    wf.connect([(fixed_fx.get_node('outputspec'), datasink,
                 [('res4d', 'res4d'), ('copes', 'copes'), ('varcopes',
                                                           'varcopes'),
                  ('zstats', 'zstats'), ('tstats', 'tstats')])])
    wf.connect([(modelfit.get_node('modelgen'), datasink, [
        ('design_cov', 'qa.model'),
        ('design_image', 'qa.model.@matrix_image'),
        ('design_file', 'qa.model.@matrix'),
    ])])
    wf.connect([(preproc, datasink, [('outputspec.motion_parameters',
                                      'qa.motion'), ('outputspec.motion_plots',
                                                     'qa.motion.plots'),
                                     ('outputspec.mask', 'qa.mask')])])
    wf.connect(registration, 'outputspec.mean2anat_mask', datasink,
               'qa.mask.mean2anat')
    wf.connect(art, 'norm_files', datasink, 'qa.art.@norm')
    wf.connect(art, 'intensity_files', datasink, 'qa.art.@intensity')
    wf.connect(art, 'outlier_files', datasink, 'qa.art.@outlier_files')
    wf.connect(registration, 'outputspec.anat2target', datasink,
               'qa.anat2target')
    wf.connect(tsnr, 'tsnr_file', datasink, 'qa.tsnr.@map')
    if subjects_dir:
        wf.connect(registration, 'outputspec.min_cost_file', datasink,
                   'qa.mincost')
        wf.connect([(get_roi_tsnr, datasink, [('avgwf_txt_file', 'qa.tsnr'),
                                              ('summary_file',
                                               'qa.tsnr.@summary')])])
        wf.connect([(get_roi_mean, datasink, [('avgwf_txt_file', 'copes.roi'),
                                              ('summary_file',
                                               'copes.roi.@summary')])])
    wf.connect([(splitfunc, datasink, [
        ('copes', 'copes.mni'),
        ('varcopes', 'varcopes.mni'),
        ('zstats', 'zstats.mni'),
    ])])
    wf.connect(calc_median, 'median_file', datasink, 'mean')
    wf.connect(registration, 'outputspec.transformed_mean', datasink,
               'mean.mni')
    wf.connect(registration, 'outputspec.func2anat_transform', datasink,
               'xfm.mean2anat')
    wf.connect(registration, 'outputspec.anat2target_transform', datasink,
               'xfm.anat2target')
    """
    Set processing parameters
    """

    preproc.inputs.inputspec.fwhm = fwhm
    gethighpass.inputs.hpcutoff = hpcutoff
    modelspec.inputs.high_pass_filter_cutoff = hpcutoff
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': use_derivatives}}
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.film_threshold = 1000

    datasink.inputs.base_directory = output_dir
    return wf


"""
The following functions run the whole workflow.
"""

if __name__ == '__main__':
    import argparse
    defstr = ' (default %(default)s)'
    parser = argparse.ArgumentParser(
        prog='fmri_openfmri.py', description=__doc__)
    parser.add_argument('-d', '--datasetdir', required=True)
    parser.add_argument(
        '-s',
        '--subject',
        default=[],
        nargs='+',
        type=str,
        help="Subject name (e.g. 'sub001')")
    parser.add_argument(
        '-m', '--model', default=1, help="Model index" + defstr)
    parser.add_argument(
        '-x',
        '--subjectprefix',
        default='sub*',
        help="Subject prefix" + defstr)
    parser.add_argument(
        '-t',
        '--task',
        default=1,  # nargs='+',
        type=int,
        help="Task index" + defstr)
    parser.add_argument(
        '--hpfilter',
        default=120.,
        type=float,
        help="High pass filter cutoff (in secs)" + defstr)
    parser.add_argument(
        '--fwhm', default=6., type=float, help="Spatial FWHM" + defstr)
    parser.add_argument(
        '--derivatives', action="store_true", help="Use derivatives" + defstr)
    parser.add_argument(
        "-o", "--output_dir", dest="outdir", help="Output directory base")
    parser.add_argument(
        "-w", "--work_dir", dest="work_dir", help="Output directory base")
    parser.add_argument(
        "-p",
        "--plugin",
        dest="plugin",
        default='Linear',
        help="Plugin to use")
    parser.add_argument(
        "--plugin_args", dest="plugin_args", help="Plugin arguments")
    parser.add_argument(
        "--sd",
        dest="subjects_dir",
        help="FreeSurfer subjects directory (if available)")
    parser.add_argument(
        "--target",
        dest="target_file",
        help=("Target in MNI space. Best to use the MindBoggle "
              "template - only used with FreeSurfer"
              "OASIS-30_Atropos_template_in_MNI152_2mm.nii.gz"))
    args = parser.parse_args()
    outdir = args.outdir
    work_dir = os.getcwd()
    if args.work_dir:
        work_dir = os.path.abspath(args.work_dir)
    if outdir:
        outdir = os.path.abspath(outdir)
    else:
        outdir = os.path.join(work_dir, 'output')
    outdir = os.path.join(outdir, 'model%02d' % int(args.model),
                          'task%03d' % int(args.task))
    derivatives = args.derivatives
    if derivatives is None:
        derivatives = False
    wf = analyze_openfmri_dataset(
        data_dir=os.path.abspath(args.datasetdir),
        subject=args.subject,
        model_id=int(args.model),
        task_id=[int(args.task)],
        subj_prefix=args.subjectprefix,
        output_dir=outdir,
        hpcutoff=args.hpfilter,
        use_derivatives=derivatives,
        fwhm=args.fwhm,
        subjects_dir=args.subjects_dir,
        target=args.target_file)
    # wf.config['execution']['remove_unnecessary_outputs'] = False

    wf.base_dir = work_dir
    if args.plugin_args:
        wf.run(args.plugin, plugin_args=eval(args.plugin_args))
    else:
        wf.run(args.plugin)
