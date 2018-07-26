#!/usr/bin/env python
"""
================
sMRI: FSReconAll
================

This script, smri_fsreconall.py, demonstrates the ability to use the
create_reconall_workflow function to create a workflow and then run it on a
set of subjects and then make an average subject::

    python smri_fsreconall.py

For an example on how to call FreeSurfer's reconall script in Nipype
see smri_freesurfer.py.

Import necessary modules from nipype.
"""

import os

import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.workflows.smri.freesurfer import create_reconall_workflow
from nipype.interfaces.freesurfer.utils import MakeAverageSubject
from nipype.interfaces.utility import IdentityInterface
"""
Assign the tutorial directory
"""

tutorial_dir = os.path.abspath('smri_fsreconall_tutorial')
if not os.path.isdir(tutorial_dir):
    os.mkdir(tutorial_dir)
"""
Define the workflow directories
"""

subject_list = ['s1', 's3']
data_dir = os.path.abspath('data')
subjects_dir = os.path.join(tutorial_dir, 'subjects_dir')
if not os.path.exists(subjects_dir):
    os.mkdir(subjects_dir)

wf = pe.Workflow(name="l1workflow")
wf.base_dir = os.path.join(tutorial_dir, 'workdir')
"""
Create inputspec
"""

inputspec = pe.Node(
    interface=IdentityInterface(['subject_id']), name="inputspec")
inputspec.iterables = ("subject_id", subject_list)
"""
Grab data
"""

datasource = pe.Node(
    interface=nio.DataGrabber(infields=['subject_id'], outfields=['struct']),
    name='datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = dict(struct=[['subject_id', 'struct']])
datasource.inputs.subject_id = subject_list
datasource.inputs.sort_filelist = True

wf.connect(inputspec, 'subject_id', datasource, 'subject_id')
"""
Run recon-all
"""

recon_all = create_reconall_workflow()
recon_all.inputs.inputspec.subjects_dir = subjects_dir

wf.connect(datasource, 'struct', recon_all, 'inputspec.T1_files')
wf.connect(inputspec, 'subject_id', recon_all, 'inputspec.subject_id')
"""
Make average subject
"""

average = pe.JoinNode(
    interface=MakeAverageSubject(),
    joinsource="inputspec",
    joinfield="subjects_ids",
    name="average")
average.inputs.subjects_dir = subjects_dir

wf.connect(recon_all, 'postdatasink_outputspec.subject_id', average,
           'subjects_ids')

wf.run("MultiProc", plugin_args={'n_procs': 4})
