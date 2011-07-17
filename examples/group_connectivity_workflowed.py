"""
==================================================
Using Camino and CMTK for group connectivity analysis
==================================================

Introduction
============

This script, group_connectivity.py, runs group-based connectivity analysis using
the connectivity mapping Nipype workflow. Further detail on the processing can be
found in connectivity_tutorial.py. This tutorial can be run using:

    python group_connectivity.py

We perform this analysis using two healthy subjects: subj1 (from the FSL course data) and subj2.
We also use three coma patients who suffer from traumatic brain damage (resulting in diffuse axonal injury),
anoxic damage, and general atrophy, respectively. The whole package (roughly 1.4 GB zipped, 2.2 unzipped),
including the Freesurfer directories for these subjects, can be acquired from here:

    http://dl.dropbox.com/u/315714/groupcondatapackage.zip?dl=1

Along with Camino (http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Main.HomePage),
Camino-Trackvis (http://www.nitrc.org/projects/camino-trackvis/), FSL (http://www.fmrib.ox.ac.uk/fsl/),
and Freesurfer (http://surfer.nmr.mgh.harvard.edu/), you must also have the Connectome File Format
library installed as well as the Connectome Mapper.

    http://www.cmtk.org/

Or on github at:

    CFFlib: https://github.com/LTS5/cfflib
    CMP: https://github.com/LTS5/cmp

Output data can be visualized in the ConnectomeViewer

    ConnectomeViewer: https://github.com/LTS5/connectomeviewer

First, we import the necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.cmtk as cmtk
import os, os.path as op                      # system functions
from nipype.workflows.camino.connectivity_mapping import create_connectivity_pipeline
from nipype.workflows.camino.group_connectivity import create_group_cff_pipeline_part1, create_group_cff_pipeline_part2, create_group_cff_pipeline_part3, create_group_cff_pipeline_part4

fs_dir = op.abspath('/usr/local/freesurfer')
subjects_dir = op.abspath('groupcondatapackage/subjects/')
data_dir = op.abspath('groupcondatapackage/data/')
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
Here we define the groups for this study. We would like to search for differences between the healthy subject and the two
vegetative patients. The group list is defined as a Python dictionary (see http://docs.python.org/tutorial/datastructures.html),
with group IDs ('controls', 'coma') as keys, and subject/patient names as values. We set the main output directory as 'groupcon'.
"""

group_list = {}
group_list['controls']=['subj1', 'subj2']
group_list['coma']=['traumatic','anoxic','atrophic']

global output_dir
output_dir = op.abspath('groupcon_workflowed')

"""
Main processing loop.
"""
title = ''
for idx, group_id in enumerate(group_list.keys()):
    """
    The title for the final grouped-network connectome file is dependent on the group names. The resulting file for this example
    is 'coma-controls.cff'. The following code implements the format a-b-c-...x.cff for an arbitary number of groups.
    """
    title += group_id
    if not idx == len(group_list.keys())-1:
        title += '-'
    info = dict(dwi=[['subject_id', 'dwi']],
                    bvecs=[['subject_id','bvecs']],
                    bvals=[['subject_id','bvals']])
    l1pipeline = create_group_cff_pipeline_part1(group_list, group_id, data_dir, subjects_dir, output_dir, info)
    l1pipeline.run()
    l1pipeline.write_graph(format='eps',graph2use='flat')
    l2pipeline = create_group_cff_pipeline_part2(group_list, group_id, data_dir, subjects_dir, output_dir)
    l2pipeline.run()
    l2pipeline.write_graph(format='eps',graph2use='flat')


l3pipeline = create_group_cff_pipeline_part3(group_list, data_dir, subjects_dir, output_dir, title)
l3pipeline.run()
l3pipeline.write_graph(format='eps',graph2use='flat')
l4pipeline = create_group_cff_pipeline_part4(group_list, data_dir, subjects_dir, output_dir, title)
l4pipeline.run()
l4pipeline.write_graph(format='eps',graph2use='flat')
