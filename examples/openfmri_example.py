# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
================================
Analyzing data from openfMRI.org
================================

A growing number of datasets are available on openfmri.org. This script
demonstrates how to use nipype to analyze a data set.

    python openfmri_example.py
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

def analyze_openfmri_dataset(data_dir):
    """Analyzes an open fmri dataset

    >>> analyze_openfmri_dataset('.') #

    """
preproc = create_featreg_preproc(whichvol='first')
preproc.inputs.inputspec.fwhm = 6.0
preproc.disconnect(preproc.get_node('plot_motion'), 'out_file',
                   preproc.get_node('outputspec'), 'motion_plots')

modelfit = create_modelfit_workflow()

fixed_fx = create_fixed_effects_flow()

data_dir = '/software/temp/openfmri/ds107'

subjects = [path.split(os.path.sep)[-1] for path in
            glob(os.path.join(data_dir, 'sub*'))]

infosource = pe.Node(niu.IdentityInterface(fields=['subject_id']),
                     name='infosource')
infosource.iterables = ('subject_id', subjects[:1])

def get_subjectinfo(subject_id, base_dir, task_id):
    from glob import glob
    import os
    import numpy as np
    taskinfo = np.genfromtxt(os.path.join(base_dir,
                                         subject_id,
                                         'condition_key.txt'),
                             usecols=[0,1],
                             dtype='str')
    n_tasks = len(np.unique(taskinfo[:,0]))
    n_conds = []
    run_ids = []
    if task_id > n_tasks:
        raise ValueError('Task id %d does not exist' % task_id)
    for idx in range(n_tasks):
        taskidx = np.where(taskinfo[:,0]=='task%03d' % (idx + 1))
        n_conds.insert(idx, len(np.unique(taskinfo[taskidx[0],1])))
        files = glob(os.path.join(base_dir,
                                  subject_id,
                                  'BOLD',
                                  'task%03d_run*' % (idx + 1)))
        run_ids.insert(idx, range(1, len(files)+1))
    TR = np.genfromtxt(os.path.join(base_dir,
                                    subject_id,
                                    'scan_key.txt'))[1]
    return run_ids[task_id-1], n_conds[task_id-1], TR

subjinfo = pe.Node(niu.Function(input_names=['subject_id', 'base_dir',
                                             'task_id'],
                                output_names=['run_id', 'n_conds', 'TR'],
                                function=get_subjectinfo),
                   name='subjectinfo')
subjinfo.inputs.base_dir = data_dir
subjinfo.inputs.task_id = 1

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

wf = pe.Workflow(name='openfmri')
wf.connect(infosource, 'subject_id', subjinfo, 'subject_id')
wf.connect(infosource, 'subject_id', datasource, 'subject_id')
wf.connect(subjinfo, 'run_id', datasource, 'run_id')

hpcutoff = 120.
def get_highpass(TR, hpcutoff):
    return hpcutoff/(2*TR)
gethighpass = pe.Node(niu.Function(input_names=['TR', 'hpcutoff'],
                                   output_names=['highpass'],
                                   function=get_highpass),
                      name='gethighpass')
gethighpass.inputs.hpcutoff = hpcutoff
wf.connect(subjinfo, 'TR', gethighpass, 'TR')
wf.connect(gethighpass, 'highpass', preproc, 'inputspec.highpass')


"""
Setup the contrast structure that needs to be evaluated. This is a list of
lists. The inner list specifies the contrasts and has the following format -
[Name,Stat,[list of condition names],[weights on those conditions]. The
condition names must match the `names` listed in the `subjectinfo` function
described above.
"""

def get_contrasts(n_conds):
    return [['Cond%02d' % (i+1), 'T', ['cond%03d' % (i+1)], [1.0]] for i in range(n_conds)]

contrastgen = pe.Node(niu.Function(input_names=['n_conds'],
                                   output_names=['contrasts'],
                                   function=get_contrasts),
                      name='contrastgen')
art = pe.MapNode(interface=ra.ArtifactDetect(use_differences = [True, False],
                                             use_norm = True,
                                             norm_threshold = 1,
                                             zintensity_threshold = 3,
                                             parameter_source = 'FSL',
                                             mask_type = 'file'),
                 iterfield=['realigned_files', 'realignment_parameters', 'mask_file'],
                 name="art")

modelspec = pe.Node(interface=model.SpecifyModel(),
                       name="modelspec")
modelspec.inputs.high_pass_filter_cutoff = hpcutoff
modelspec.inputs.input_units = 'secs'

wf.connect(subjinfo, 'TR', modelspec, 'time_repetition')
wf.connect(datasource, 'behav', modelspec, 'event_files')

wf.connect(subjinfo, 'TR', modelfit, 'inputspec.interscan_interval')

modelfit.inputs.inputspec.bases = {'dgamma':{'derivs': True}}
wf.connect(subjinfo, 'n_conds', contrastgen, 'n_conds')
wf.connect(contrastgen, 'contrasts', modelfit, 'inputspec.contrasts')
modelfit.inputs.inputspec.model_serial_correlations = True
modelfit.inputs.inputspec.film_threshold = 1000

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
            (modelspec, modelfit, [('session_info', 'inputspec.session_info')]),
            (preproc, modelfit, [('outputspec.highpassed_files',
                                  'inputspec.functional_data')])
            ])
"""
Set up first-level workflow
---------------------------

"""

def sort_copes(files):
    numelements = len(files[0])
    outfiles = []
    for i in range(numelements):
        outfiles.insert(i,[])
        for j, elements in enumerate(files):
            outfiles[i].append(elements[i])
    return outfiles

def num_copes(files):
    return len(files)

pickfirst = lambda x : x[0]

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

wf.base_dir = '/software/temp/openfmri/working'
wf.config = dict(crashdump_dir='/software/temp/openfmri/working/crashdumps')
wf.config['execution'] = {'stop_on_first_crash': True}