#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=================
fMRI: FEEDS - FSL
=================

A pipeline example that data from the FSL FEEDS set. Single subject, two
stimuli.

You can find it at http://www.fmrib.ox.ac.uk/fsl/feeds/doc/index.html

"""

from __future__ import division
from builtins import range

import os  # system functions
from nipype.interfaces import io as nio  # Data i/o
from nipype.interfaces import utility as niu  # Utilities
from nipype.interfaces import fsl  # fsl
from nipype.pipeline import engine as pe  # pypeline engine
from nipype.algorithms import modelgen as model  # model generation
from nipype.workflows.fmri.fsl import (
    create_featreg_preproc, create_modelfit_workflow, create_reg_workflow)
from nipype.interfaces.base import Bunch
"""
Preliminaries
-------------

Setup any package specific configuration. The output file format for FSL
routines is being set to compressed NIFTI.
"""

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')
"""
Experiment specific components
------------------------------

This tutorial does a single subject analysis so we are not using infosource and
iterables
"""

# Specify the location of the FEEDS data. You can find it at http://www.fmrib.ox.ac.uk/fsl/feeds/doc/index.html

inputnode = pe.Node(
    niu.IdentityInterface(fields=['in_data']), name='inputnode')
# Specify the subject directories
# Map field names to individual subject runs.
info = dict(func=[['fmri']], struct=[['structural']])
"""
Now we create a :class:`nipype.interfaces.io.DataSource` object and fill in the
information from above about the layout of our data.  The
:class:`nipype.pipeline.Node` module wraps the interface object and provides
additional housekeeping and pipeline specific functionality.
"""

datasource = pe.Node(
    interface=nio.DataGrabber(outfields=['func', 'struct']), name='datasource')
datasource.inputs.template = 'feeds/data/%s.nii.gz'
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True

preproc = create_featreg_preproc(whichvol='first')
TR = 3.
preproc.inputs.inputspec.fwhm = 5
preproc.inputs.inputspec.highpass = 100. / TR

modelspec = pe.Node(interface=model.SpecifyModel(), name="modelspec")
modelspec.inputs.input_units = 'secs'
modelspec.inputs.time_repetition = TR
modelspec.inputs.high_pass_filter_cutoff = 100
modelspec.inputs.subject_info = [
    Bunch(
        conditions=['Visual', 'Auditory'],
        onsets=[
            list(range(0, int(180 * TR), 60)),
            list(range(0, int(180 * TR), 90))
        ],
        durations=[[30], [45]],
        amplitudes=None,
        tmod=None,
        pmod=None,
        regressor_names=None,
        regressors=None)
]

modelfit = create_modelfit_workflow(f_contrasts=True)
modelfit.inputs.inputspec.interscan_interval = TR
modelfit.inputs.inputspec.model_serial_correlations = True
modelfit.inputs.inputspec.bases = {'dgamma': {'derivs': True}}
cont1 = ['Visual>Baseline', 'T', ['Visual', 'Auditory'], [1, 0]]
cont2 = ['Auditory>Baseline', 'T', ['Visual', 'Auditory'], [0, 1]]
cont3 = ['Task', 'F', [cont1, cont2]]
modelfit.inputs.inputspec.contrasts = [cont1, cont2, cont3]

registration = create_reg_workflow()
registration.inputs.inputspec.target_image = fsl.Info.standard_image(
    'MNI152_T1_2mm.nii.gz')
registration.inputs.inputspec.target_image_brain = fsl.Info.standard_image(
    'MNI152_T1_2mm_brain.nii.gz')
registration.inputs.inputspec.config_file = 'T1_2_MNI152_2mm'
"""
Set up complete workflow
========================
"""

l1pipeline = pe.Workflow(name="level1")
l1pipeline.base_dir = os.path.abspath('./fsl_feeds/workingdir')
l1pipeline.config = {
    "execution": {
        "crashdump_dir": os.path.abspath('./fsl_feeds/crashdumps')
    }
}

l1pipeline.connect(inputnode, 'in_data', datasource, 'base_directory')
l1pipeline.connect(datasource, 'func', preproc, 'inputspec.func')
l1pipeline.connect(preproc, 'outputspec.highpassed_files', modelspec,
                   'functional_runs')
l1pipeline.connect(preproc, 'outputspec.motion_parameters', modelspec,
                   'realignment_parameters')
l1pipeline.connect(modelspec, 'session_info', modelfit,
                   'inputspec.session_info')
l1pipeline.connect(preproc, 'outputspec.highpassed_files', modelfit,
                   'inputspec.functional_data')
l1pipeline.connect(preproc, 'outputspec.mean', registration,
                   'inputspec.mean_image')
l1pipeline.connect(datasource, 'struct', registration,
                   'inputspec.anatomical_image')
l1pipeline.connect(modelfit, 'outputspec.zfiles', registration,
                   'inputspec.source_files')
"""
Setup the datasink
"""

datasink = pe.Node(
    interface=nio.DataSink(parameterization=False), name="datasink")
datasink.inputs.base_directory = os.path.abspath('./fsl_feeds/l1out')
datasink.inputs.substitutions = [
    ('fmri_dtype_mcf_mask_smooth_mask_gms_mean_warp', 'meanfunc')
]
# store relevant outputs from various stages of the 1st level analysis
l1pipeline.connect(registration, 'outputspec.transformed_files', datasink,
                   'level1.@Z')
l1pipeline.connect(registration, 'outputspec.transformed_mean', datasink,
                   'meanfunc')
"""
Execute the pipeline
--------------------

The code discussed above sets up all the necessary data structures with
appropriate parameters and the connectivity between the processes, but does not
generate any output. To actually run the analysis on the data the
``nipype.pipeline.engine.Pipeline.Run`` function needs to be called.
"""

if __name__ == '__main__':
    l1pipeline.inputs.inputnode.in_data = os.path.abspath('feeds/data')
    l1pipeline.run()
