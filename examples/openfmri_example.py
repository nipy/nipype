# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
================================
Analyzing data from openfMRI.org
================================

A growing number of datasets are available on openfmri.org. This script
demonstrates how to use nipype to analyze a data set.

    python openfmri_example.py ds107
"""

from glob import glob
import os

import nipype.pipeline.engine as pe
import nipype.algorithms.modelgen as model
import nipype.algorithms.rapidart as ra
import nipype.interfaces.fsl as fsl
import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu
from nipype.workflows.fsl import (create_featreg_preproc,
                                  create_modelfit_workflow,
                                  create_fixed_effects_flow)

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


def get_subjectinfo(subject_id, base_dir, task_id):
    """Get info for a given subject

    Parameters
    ----------
    subject_id : string
        Subject identifier (e.g., sub001)
    base_dir : string
        Path to base directory of the dataset
    task_id : int
        Which task to process

    Returns
    -------
    run_ids : list of ints
        Run numbers
    num_conds : int
        Number of conditions for the task
    TR : float
        Repetition time
    """
    from glob import glob
    import os
    import numpy as np
    taskinfo = np.genfromtxt(os.path.join(base_dir,
                                         subject_id,
                                         'condition_key.txt'),
                             usecols=[0, 1],
                             dtype='str')
    n_tasks = len(np.unique(taskinfo[:, 0]))
    n_conds = []
    run_ids = []
    if task_id > n_tasks:
        raise ValueError('Task id %d does not exist' % task_id)
    for idx in range(n_tasks):
        taskidx = np.where(taskinfo[:, 0] == 'task%03d' % (idx + 1))
        n_conds.insert(idx, len(np.unique(taskinfo[taskidx[0], 1])))
        files = glob(os.path.join(base_dir,
                                  subject_id,
                                  'BOLD',
                                  'task%03d_run*' % (idx + 1)))
        run_ids.insert(idx, range(1, len(files) + 1))
    TR = np.genfromtxt(os.path.join(base_dir,
                                    subject_id,
                                    'scan_key.txt'))[1]
    return run_ids[task_id - 1], n_conds[task_id - 1], TR


def analyze_openfmri_dataset(data_dir, work_dir=None):
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

    """
    Remove the plotting connection so that plot iterables don't propagate
    to the model stage
    """

    preproc.disconnect(preproc.get_node('plot_motion'), 'out_file',
                       preproc.get_node('outputspec'), 'motion_plots')

    """
    Set up openfmri data specific components
    """

    subjects = [path.split(os.path.sep)[-1] for path in
                glob(os.path.join(data_dir, 'sub*'))]

    infosource = pe.Node(niu.IdentityInterface(fields=['subject_id']),
                         name='infosource')
    infosource.iterables = ('subject_id', subjects[:1])

    subjinfo = pe.Node(niu.Function(input_names=['subject_id', 'base_dir',
                                                 'task_id'],
                                    output_names=['run_id', 'n_conds', 'TR'],
                                    function=get_subjectinfo),
                       name='subjectinfo')
    subjinfo.inputs.base_dir = data_dir

    """
    Return data components as anat, bold and behav
    """
    datasource = pe.Node(nio.DataGrabber(infields=['subject_id', 'run_id'],
                                         outfields=['anat', 'bold', 'behav']),
                         name='datasource')
    datasource.inputs.base_directory = data_dir
    datasource.inputs.template = '*'
    datasource.inputs.field_template = {'anat': '%s/anatomy/highres001.nii.gz',
                                'bold': '%s/BOLD/task001_r*/bold.nii.gz',
                                'behav': '%s/behav/task001_run%03d/cond*.txt'}
    datasource.inputs.template_args = {'anat': [['subject_id']],
                                       'bold': [['subject_id']],
                                       'behav': [['subject_id', 'run_id']]}
    datasource.inputs.sorted = True

    """
    Create meta workflow
    """

    wf = pe.Workflow(name='openfmri')
    wf.connect(infosource, 'subject_id', subjinfo, 'subject_id')
    wf.connect(infosource, 'subject_id', datasource, 'subject_id')
    wf.connect(subjinfo, 'run_id', datasource, 'run_id')

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

    def get_contrasts(n_conds):
        return [['Cond%02d' % (i + 1), 'T',
                 ['cond%03d' % (i + 1)], [1.0]] for i in range(n_conds)]

    contrastgen = pe.Node(niu.Function(input_names=['n_conds'],
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

    wf.connect(subjinfo, 'TR', modelspec, 'time_repetition')
    wf.connect(datasource, 'behav', modelspec, 'event_files')
    wf.connect(subjinfo, 'TR', modelfit, 'inputspec.interscan_interval')
    wf.connect(subjinfo, 'n_conds', contrastgen, 'n_conds')
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
    wf.connect([(datasource, preproc, [('bold', 'inputspec.func')]),
                ])

    """
    Set processing parameters
    """

    hpcutoff = 120.
    subjinfo.inputs.task_id = 1
    preproc.inputs.inputspec.fwhm = 6.0
    gethighpass.inputs.hpcutoff = hpcutoff
    modelspec.inputs.high_pass_filter_cutoff = hpcutoff
    modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': True}}
    modelfit.inputs.inputspec.model_serial_correlations = True
    modelfit.inputs.inputspec.film_threshold = 1000

    if work_dir is None:
        work_dir = os.path.join(os.getcwd(), 'working')
    wf.base_dir = work_dir
    wf.config['execution'] = dict(crashdump_dir=os.path.join(workdir,
                                                             'crashdumps'),
                                  stop_on_first_crash=True)

if __name__ == '__main__':
    data_dir = '/software/temp/openfmri/ds107'
    analyze_openfmri_dataset(data_dir=data_dir)
