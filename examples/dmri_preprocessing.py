# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
===================
dMRI: Preprocessing
===================

Introduction
============

This script, dmri_preprocessing.py, demonstrates how to prepare dMRI data
for tractography and connectivity analysis with nipype.

We perform this analysis using the FSL course data, which can be acquired from
here: http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

Can be executed in command line using ``python dmri_preprocessing.py``


Import necessary modules from nipype.
"""

import os  # system functions
import nipype.interfaces.io as nio  # Data i/o
import nipype.interfaces.utility as niu  # utility
import nipype.algorithms.misc as misc

import nipype.pipeline.engine as pe  # pypeline engine

from nipype.interfaces import fsl
from nipype.interfaces import ants
"""
Load specific nipype's workflows for preprocessing of dMRI data:
:class:`nipype.workflows.dmri.preprocess.epi.all_peb_pipeline`,
as data include a *b0* volume with reverse encoding direction
(*P>>>A*, or *y*), in contrast with the general acquisition encoding
that is *A>>>P* or *-y* (in RAS systems).
"""

from nipype.workflows.dmri.fsl.artifacts import all_fsl_pipeline, remove_bias
"""
Map field names into individual subject runs
"""

info = dict(
    dwi=[['subject_id', 'dwidata']],
    bvecs=[['subject_id', 'bvecs']],
    bvals=[['subject_id', 'bvals']],
    dwi_rev=[['subject_id', 'nodif_PA']])

infosource = pe.Node(
    interface=niu.IdentityInterface(fields=['subject_id']), name="infosource")

# Set the subject 1 identifier in subject_list,
# we choose the preproc dataset as it contains uncorrected files.
subject_list = ['subj1_preproc']
"""Here we set up iteration over all the subjects. The following line
is a particular example of the flexibility of the system.  The
``datasource`` attribute ``iterables`` tells the pipeline engine that
it should repeat the analysis on each of the items in the
``subject_list``. In the current example, the entire first level
preprocessing and estimation will be repeated for each subject
contained in subject_list.
"""

infosource.iterables = ('subject_id', subject_list)
"""
Now we create a :class:`nipype.interfaces.io.DataGrabber` object and
fill in the information from above about the layout of our data.  The
:class:`~nipype.pipeline.engine.Node` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = pe.Node(
    nio.DataGrabber(infields=['subject_id'], outfields=list(info.keys())),
    name='datasource')

datasource.inputs.template = "%s/%s"

# This needs to point to the fdt folder you can find after extracting
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
datasource.inputs.base_directory = os.path.abspath('fdt1')
datasource.inputs.field_template = dict(
    dwi='%s/%s.nii.gz', dwi_rev='%s/%s.nii.gz')
datasource.inputs.template_args = info
datasource.inputs.sort_filelist = True
"""
An inputnode is used to pass the data obtained by the data grabber to the
actual processing functions
"""

inputnode = pe.Node(
    niu.IdentityInterface(fields=["dwi", "bvecs", "bvals", "dwi_rev"]),
    name="inputnode")
"""

Setup for dMRI preprocessing
============================

In this section we initialize the appropriate workflow for preprocessing of
diffusion images.

Artifacts correction
--------------------

We will use the combination of ``topup`` and ``eddy`` as suggested by FSL.

In order to configure the susceptibility distortion correction (SDC), we first
write the specific parameters of our echo-planar imaging (EPI) images.

Particularly, we look into the ``acqparams.txt`` file of the selected subject
to gather the encoding direction, acceleration factor (in parallel sequences
it is > 1), and readout time or echospacing.

"""

epi_AP = {'echospacing': 66.5e-3, 'enc_dir': 'y-'}
epi_PA = {'echospacing': 66.5e-3, 'enc_dir': 'y'}
prep = all_fsl_pipeline(epi_params=epi_AP, altepi_params=epi_PA)
"""

Bias field correction
---------------------

Finally, we set up a node to correct for a single multiplicative bias field
from computed on the *b0* image, as suggested in [Jeurissen2014]_.

"""

bias = remove_bias()
"""
Connect nodes in workflow
=========================

We create a higher level workflow to connect the nodes. Please excuse the
author for writing the arguments of the ``connect`` function in a not-standard
style with readability aims.
"""

wf = pe.Workflow(name="dMRI_Preprocessing")
wf.base_dir = os.path.abspath('preprocessing_dmri_tutorial')
wf.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
            (datasource, prep,
             [('dwi', 'inputnode.in_file'), ('dwi_rev', 'inputnode.alt_file'),
              ('bvals', 'inputnode.in_bval'), ('bvecs', 'inputnode.in_bvec')]),
            (prep, bias, [('outputnode.out_file', 'inputnode.in_file'),
                          ('outputnode.out_mask', 'inputnode.in_mask')]),
            (datasource, bias, [('bvals', 'inputnode.in_bval')])])
"""
Run the workflow as command line executable
"""

if __name__ == '__main__':
    wf.run()
    wf.write_graph()
