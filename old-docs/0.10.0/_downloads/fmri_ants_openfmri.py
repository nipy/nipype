#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=============================================
fMRI: OpenfMRI.org data, FSL, ANTS, c3daffine
=============================================

A growing number of datasets are available on `OpenfMRI <http://openfmri.org>`_.
This script demonstrates how to use nipype to analyze a data set.

    python fmri_ants_openfmri.py --datasetdir ds107
"""

from nipype import config
config.enable_provenance()
from nipype.external import six


from glob import glob
import os

import nipype.pipeline.engine as pe
import nipype.algorithms.modelgen as model
import nipype.algorithms.rapidart as ra
import nipype.interfaces.fsl as fsl
import nipype.interfaces.ants as ants
from nipype.interfaces.c3 import C3dAffineTool
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
from nipype.workflows.fmri.fsl import (create_featreg_preproc,
                                       create_modelfit_workflow,
                                       create_fixed_effects_flow)

from nipype import LooseVersion

version = 0
if fsl.Info.version() and \
    LooseVersion(fsl.Info.version()) > LooseVersion('5.0.6'):
    version = 507

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


def create_reg_workflow(name='registration'):
    """Create a FEAT preprocessing workflow together with freesurfer

    Parameters
    ----------

    ::

        name : name of workflow (default: 'registration')

    Inputs::

        inputspec.source_files : files (filename or list of filenames to register)
        inputspec.mean_image : reference image to use
        inputspec.anatomical_image : anatomical image to coregister to
        inputspec.target_image : registration target

    Outputs::

        outputspec.func2anat_transform : FLIRT transform
        outputspec.anat2target_transform : FLIRT+FNIRT transform
        outputspec.transformed_files : transformed files in target space
        outputspec.transformed_mean : mean image in target space

    Example
    -------

    """

    register = pe.Workflow(name=name)

    inputnode = pe.Node(interface=niu.IdentityInterface(fields=['source_files',
                                                                 'mean_image',
                                                                 'anatomical_image',
                                                                 'target_image',
                                                                 'target_image_brain',
                                                                 'config_file']),
                        name='inputspec')
    outputnode = pe.Node(interface=niu.IdentityInterface(fields=['func2anat_transform',
                                                              'anat2target_transform',
                                                              'transformed_files',
                                                              'transformed_mean',
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

    binarize = pe.Node(fsl.ImageMaths(op_string='-nan -thr 0.5 -bin'),
                       name='binarize')
    pickindex = lambda x, i: x[i]
    register.connect(fast, ('partial_volume_files', pickindex, 2),
                     binarize, 'in_file')

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
    mean2anatbbr.inputs.schedule = os.path.join(os.getenv('FSLDIR'),
                                                'etc/flirtsch/bbr.sch')
    register.connect(inputnode, 'mean_image', mean2anatbbr, 'in_file')
    register.connect(binarize, 'out_file', mean2anatbbr, 'wm_seg')
    register.connect(inputnode, 'anatomical_image', mean2anatbbr, 'reference')
    register.connect(mean2anat, 'out_matrix_file',
                     mean2anatbbr, 'in_matrix_file')
    """
    Convert the BBRegister transformation to ANTS ITK format
    """

    convert2itk = pe.Node(C3dAffineTool(),
                          name='convert2itk')
    convert2itk.inputs.fsl2ras = True
    convert2itk.inputs.itk_transform = True
    register.connect(mean2anatbbr, 'out_matrix_file', convert2itk, 'transform_file')
    register.connect(inputnode, 'mean_image',convert2itk, 'source_file')
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
    reg.inputs.transform_parameters = [(0.1,), (0.1,), (0.2, 3.0, 0.0)]
    #reg.inputs.number_of_iterations = ([[10000, 111110, 11110]] * 2 + [[100, 50, 30]])
    reg.inputs.number_of_iterations = [[10000, 11110, 11110]] * 2 + [[100, 30, 20]]
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
    reg.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 3
    reg.inputs.use_histogram_matching = [False] * 2 + [True]
    reg.inputs.winsorize_lower_quantile = 0.005
    reg.inputs.winsorize_upper_quantile = 0.995
    reg.inputs.args = '--float'
    reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    reg.inputs.num_threads = 4
    reg.plugin_args = {'qsub_args': '-l nodes=1:ppn=4'}
    register.connect(stripper, 'out_file', reg, 'moving_image')
    register.connect(inputnode,'target_image_brain', reg,'fixed_image')


    """
    Concatenate the affine and ants transforms into a list
    """

    pickfirst = lambda x: x[0]

    merge = pe.Node(niu.Merge(2), iterfield=['in2'], name='mergexfm')
    register.connect(convert2itk, 'itk_transform', merge, 'in2')
    register.connect(reg, ('composite_transform', pickfirst), merge, 'in1')


    """
    Transform the mean image. First to anatomical and then to target
    """
    warpmean = pe.Node(ants.ApplyTransforms(),
                       name='warpmean')
    warpmean.inputs.input_image_type = 3
    warpmean.inputs.interpolation = 'BSpline'
    warpmean.inputs.invert_transform_flags = [False, False]
    warpmean.inputs.terminal_output = 'file'

    register.connect(inputnode,'target_image_brain', warpmean,'reference_image')
    register.connect(inputnode, 'mean_image', warpmean, 'input_image')
    register.connect(merge, 'out', warpmean, 'transforms')

    """
    Transform the remaining images. First to anatomical and then to target
    """

    warpall = pe.MapNode(ants.ApplyTransforms(),
                         iterfield=['input_image'],
                         name='warpall')
    warpall.inputs.input_image_type = 3
    warpall.inputs.interpolation = 'BSpline'
    warpall.inputs.invert_transform_flags = [False, False]
    warpall.inputs.terminal_output = 'file'

    register.connect(inputnode,'target_image_brain',warpall,'reference_image')
    register.connect(inputnode,'source_files', warpall, 'input_image')
    register.connect(merge, 'out', warpall, 'transforms')


    """
    Assign all the output files
    """

    register.connect(warpmean, 'output_image', outputnode, 'transformed_mean')
    register.connect(warpall, 'output_image', outputnode, 'transformed_files')
    register.connect(mean2anatbbr, 'out_matrix_file',
                     outputnode, 'func2anat_transform')
    register.connect(reg, 'composite_transform',
                     outputnode, 'anat2target_transform')

    return register

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
        conds.append([condition.replace(' ', '_') for condition
                      in taskinfo[taskidx[0], 2]])
        files = glob(os.path.join(base_dir,
                                  subject_id,
                                  'BOLD',
                                  'task%03d_run*' % (idx + 1)))
        run_ids.insert(idx, range(1, len(files) + 1))
    TR = np.genfromtxt(os.path.join(base_dir, 'scan_key.txt'))[1]
    return run_ids[task_id - 1], conds[task_id - 1], TR


def analyze_openfmri_dataset(data_dir, subject=None, model_id=None,
                             task_id=None, output_dir=None, subj_prefix='*',
                             hpcutoff=120., use_derivatives=True,
                             fwhm=6.0):
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
    registration = create_reg_workflow()

    """
    Remove the plotting connection so that plot iterables don't propagate
    to the model stage
    """

    preproc.disconnect(preproc.get_node('plot_motion'), 'out_file',
                       preproc.get_node('outputspec'), 'motion_plots')

    """
    Set up openfmri data specific components
    """

    subjects = sorted([path.split(os.path.sep)[-1] for path in
                       glob(os.path.join(data_dir, subj_prefix))])

    infosource = pe.Node(niu.IdentityInterface(fields=['subject_id',
                                                       'model_id',
                                                       'task_id']),
                         name='infosource')
    if len(subject) == 0:
        infosource.iterables = [('subject_id', subjects),
                                ('model_id', [model_id]),
                                ('task_id', task_id)]
    else:
        infosource.iterables = [('subject_id',
                                 [subjects[subjects.index(subj)] for subj in subject]),
                                ('model_id', [model_id]),
                                ('task_id', task_id)]

    subjinfo = pe.Node(niu.Function(input_names=['subject_id', 'base_dir',
                                                 'task_id', 'model_id'],
                                    output_names=['run_id', 'conds', 'TR'],
                                    function=get_subjectinfo),
                       name='subjectinfo')
    subjinfo.inputs.base_dir = data_dir

    """
    Return data components as anat, bold and behav
    """

    datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'run_id',
                                                   'task_id', 'model_id'],
                                         outfields=['anat', 'bold', 'behav',
                                                    'contrasts']),
                         name='datasource')
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template = '*'
    datasource.inputs.field_template = {'anat': '%s/anatomy/highres001.nii.gz',
                                'bold': '%s/BOLD/task%03d_r*/bold.nii.gz',
                                'behav': ('%s/model/model%03d/onsets/task%03d_'
                                          'run%03d/cond*.txt'),
                                'contrasts': ('models/model%03d/'
                                              'task_contrasts.txt')}
    datasource.inputs.template_args = {'anat': [['subject_id']],
                                       'bold': [['subject_id', 'task_id']],
                                       'behav': [['subject_id', 'model_id',
                                                  'task_id', 'run_id']],
                                       'contrasts': [['model_id']]}
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
    wf.connect([(datasource, preproc, [('bold', 'inputspec.func')]),
                ])

    def get_highpass(TR, hpcutoff):
        return hpcutoff / (2 * TR)
    gethighpass = pe.Node(niu.Function(input_names=['TR', 'hpcutoff'],
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
        contrast_def = np.genfromtxt(contrast_file, dtype=object)
        if len(contrast_def.shape) == 1:
            contrast_def = contrast_def[None, :]
        contrasts = []
        for row in contrast_def:
            if row[0] != 'task%03d' % task_id:
                continue
            con = [row[1], 'T', ['cond%03d' % (i + 1)  for i in range(len(conds))],
                   row[2:].astype(float).tolist()]
            contrasts.append(con)
        # add auto contrasts for each column
        for i, cond in enumerate(conds):
            con = [cond, 'T', ['cond%03d' % (i + 1)], [1]]
            contrasts.append(con)
        return contrasts

    contrastgen = pe.Node(niu.Function(input_names=['contrast_file',
                                                    'task_id', 'conds'],
                                       output_names=['contrasts'],
                                       function=get_contrasts),
                          name='contrastgen')

    art = pe.MapNode(interface=ra.ArtifactDetect(use_differences=[True, False],
                                                 use_norm=True,
                                                 norm_threshold=1,
                                                 zintensity_threshold=3,
                                                 parameter_source='FSL',
                                                 mask_type='file'),
                     iterfield=['realigned_files', 'realignment_parameters',
                                'mask_file'],
                     name="art")

    modelspec = pe.Node(interface=model.SpecifyModel(),
                           name="modelspec")
    modelspec.inputs.input_units = 'secs'

    def check_behav_list(behav):
        out_behav = []
        if isinstance(behav, six.string_types):
            behav = [behav]
        for val in behav:
            if not isinstance(val, list):
                out_behav.append([val])
            else:
                out_behav.append(val)
        return out_behav

    wf.connect(subjinfo, 'TR', modelspec, 'time_repetition')
    wf.connect(datasource, ('behav', check_behav_list), modelspec, 'event_files')
    wf.connect(subjinfo, 'TR', modelfit, 'inputspec.interscan_interval')
    wf.connect(subjinfo, 'conds', contrastgen, 'conds')
    wf.connect(datasource, 'contrasts', contrastgen, 'contrast_file')
    wf.connect(infosource, 'task_id', contrastgen, 'task_id')
    wf.connect(contrastgen, 'contrasts', modelfit, 'inputspec.contrasts')

    wf.connect([(preproc, art, [('outputspec.motion_parameters',
                                 'realignment_parameters'),
                                ('outputspec.realigned_files',
                                 'realigned_files'),
                                ('outputspec.mask', 'mask_file')]),
                (preproc, modelspec, [('outputspec.highpassed_files',
                                       'functional_runs'),
                                      ('outputspec.motion_parameters',
                                       'realignment_parameters')]),
                (art, modelspec, [('outlier_files', 'outlier_files')]),
                (modelspec, modelfit, [('session_info',
                                        'inputspec.session_info')]),
                (preproc, modelfit, [('outputspec.highpassed_files',
                                      'inputspec.functional_data')])
                ])

    """
    Reorder the copes so that now it combines across runs
    """

    def sort_copes(files):
        numelements = len(files[0])
        outfiles = []
        for i in range(numelements):
            outfiles.insert(i, [])
            for j, elements in enumerate(files):
                outfiles[i].append(elements[i])
        return outfiles

    def num_copes(files):
        return len(files)

    pickfirst = lambda x: x[0]

    wf.connect([(preproc, fixed_fx, [(('outputspec.mask', pickfirst),
                                      'flameo.mask_file')]),
                (modelfit, fixed_fx, [(('outputspec.copes', sort_copes),
                                       'inputspec.copes'),
                                       ('outputspec.dof_file',
                                        'inputspec.dof_files'),
                                       (('outputspec.varcopes',
                                         sort_copes),
                                        'inputspec.varcopes'),
                                       (('outputspec.copes', num_copes),
                                        'l2model.num_copes'),
                                       ])
                ])

    wf.connect(preproc, 'outputspec.mean', registration, 'inputspec.mean_image')
    wf.connect(datasource, 'anat', registration, 'inputspec.anatomical_image')
    registration.inputs.inputspec.target_image = fsl.Info.standard_image('MNI152_T1_2mm.nii.gz')
    registration.inputs.inputspec.target_image_brain = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
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

    mergefunc = pe.Node(niu.Function(input_names=['copes', 'varcopes',
                                                  'zstats'],
                                   output_names=['out_files', 'splits'],
                                   function=merge_files),
                      name='merge_files')
    wf.connect([(fixed_fx.get_node('outputspec'), mergefunc,
                                 [('copes', 'copes'),
                                  ('varcopes', 'varcopes'),
                                  ('zstats', 'zstats'),
                                  ])])
    wf.connect(mergefunc, 'out_files', registration, 'inputspec.source_files')

    def split_files(in_files, splits):
        copes = in_files[:splits[0]]
        varcopes = in_files[splits[0]:(splits[0] + splits[1])]
        zstats = in_files[(splits[0] + splits[1]):]
        return copes, varcopes, zstats

    splitfunc = pe.Node(niu.Function(input_names=['in_files', 'splits'],
                                     output_names=['copes', 'varcopes',
                                                   'zstats'],
                                     function=split_files),
                      name='split_files')
    wf.connect(mergefunc, 'splits', splitfunc, 'splits')
    wf.connect(registration, 'outputspec.transformed_files',
               splitfunc, 'in_files')


    """
    Connect to a datasink
    """

    def get_subs(subject_id, conds, model_id, task_id):
        subs = [('_subject_id_%s_' % subject_id, '')]
        subs.append(('_model_id_%d' % model_id, 'model%03d' %model_id))
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
            subs.append(('_warpall%d/cope1_warp.' % i,
                         'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_warp.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_warp.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
            subs.append(('_warpall%d/cope1_trans.' % i,
                         'cope%02d.' % (i + 1)))
            subs.append(('_warpall%d/varcope1_trans.' % (len(conds) + i),
                         'varcope%02d.' % (i + 1)))
            subs.append(('_warpall%d/zstat1_trans.' % (2 * len(conds) + i),
                         'zstat%02d.' % (i + 1)))
        return subs

    subsgen = pe.Node(niu.Function(input_names=['subject_id', 'conds',
                                                'model_id', 'task_id'],
                                   output_names=['substitutions'],
                                   function=get_subs),
                      name='subsgen')

    datasink = pe.Node(interface=nio.DataSink(),
                       name="datasink")
    wf.connect(infosource, 'subject_id', datasink, 'container')
    wf.connect(infosource, 'subject_id', subsgen, 'subject_id')
    wf.connect(infosource, 'model_id', subsgen, 'model_id')
    wf.connect(infosource, 'task_id', subsgen, 'task_id')
    wf.connect(contrastgen, 'contrasts', subsgen, 'conds')
    wf.connect(subsgen, 'substitutions', datasink, 'substitutions')
    wf.connect([(fixed_fx.get_node('outputspec'), datasink,
                                 [('res4d', 'res4d'),
                                  ('copes', 'copes'),
                                  ('varcopes', 'varcopes'),
                                  ('zstats', 'zstats'),
                                  ('tstats', 'tstats')])
                                 ])
    wf.connect([(splitfunc, datasink,
                 [('copes', 'copes.mni'),
                  ('varcopes', 'varcopes.mni'),
                  ('zstats', 'zstats.mni'),
                  ])])
    wf.connect(registration, 'outputspec.transformed_mean', datasink, 'mean.mni')
    wf.connect(registration, 'outputspec.func2anat_transform', datasink, 'xfm.mean2anat')
    wf.connect(registration, 'outputspec.anat2target_transform', datasink, 'xfm.anat2target')

    """
    Set processing parameters
    """
    preproc.inputs.inputspec.fwhm = fwhm
    gethighpass.inputs.hpcutoff = hpcutoff
    modelspec.inputs.high_pass_filter_cutoff = hpcutoff
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': use_derivatives}}
    modelfit.inputs.inputspec.model_serial_correlations = True
    if version < 507:
        modelfit.inputs.inputspec.film_threshold = 1000
    else:
        modelfit.inputs.inputspec.film_threshold = -1000

    datasink.inputs.base_directory = output_dir
    return wf

if __name__ == '__main__':
    import argparse
    defstr = ' (default %(default)s)'
    parser = argparse.ArgumentParser(prog='fmri_openfmri.py',
                                     description=__doc__)
    parser.add_argument('-d', '--datasetdir', required=True)
    parser.add_argument('-s', '--subject', default=[],
                        nargs='+', type=str,
                        help="Subject name (e.g. 'sub001')")
    parser.add_argument('-m', '--model', default=1,
                        help="Model index" + defstr)
    parser.add_argument('-x', '--subjectprefix', default='sub*',
                        help="Subject prefix" + defstr)
    parser.add_argument('-t', '--task', default=1, #nargs='+',
                        type=int, help="Task index" + defstr)
    parser.add_argument('--hpfilter', default=120.,
                        type=float, help="High pass filter cutoff (in secs)" + defstr)
    parser.add_argument('--fwhm', default=6.,
                        type=float, help="Spatial FWHM" + defstr)
    parser.add_argument('--derivatives', action="store_true",
                        help="Use derivatives" + defstr)
    parser.add_argument("-o", "--output_dir", dest="outdir",
                        help="Output directory base")
    parser.add_argument("-w", "--work_dir", dest="work_dir",
                        help="Output directory base")
    parser.add_argument("-p", "--plugin", dest="plugin",
                        default='Linear',
                        help="Plugin to use")
    parser.add_argument("--plugin_args", dest="plugin_args",
                        help="Plugin arguments")
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
    wf = analyze_openfmri_dataset(data_dir=os.path.abspath(args.datasetdir),
                             subject=args.subject,
                             model_id=int(args.model),
                             task_id=[int(args.task)],
                             subj_prefix=args.subjectprefix,
                             output_dir=outdir,
                             hpcutoff=args.hpfilter,
                             use_derivatives=derivatives,
                             fwhm=args.fwhm)
    wf.base_dir = work_dir
    if args.plugin_args:
        wf.run(args.plugin, plugin_args=eval(args.plugin_args))
    else:
        wf.run(args.plugin)
