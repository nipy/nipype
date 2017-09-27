.. _pipeline_tutorial:

=====================
 Tutorial : Workflows
=====================

This section presents several tutorials on how to setup and use pipelines. Make
sure that you have the requirements satisfied and go through the steps required
for the analysis tutorials.

Essential reading
=================

.. toctree::
   :maxdepth: 1
   :glob:

   tutorial_101
   tutorial_102
   tutorial_103
   mapnode_and_iterables
   grabbing_and_sinking

Beginner's guide
================

By Michael Notter. `Available here`__

__ http://miykael.github.com/nipype-beginner-s-guide/index.html

Example workflows
=================

.. toctree::
   :maxdepth: 1
   :glob:

   examples/*

Requirements
============

  All tutorials

  - Release 0.4 of nipype and it's dependencies have been installed

  Analysis tutorials

  - FSL_, FreeSurfer_, Camino_, ConnectomeViewer and MATLAB_ are available and
    callable from the command line

  - SPM_ 5/8 is installed and callable in matlab

  - Space: 3-10 GB

Checklist for analysis tutorials
================================

For the analysis tutorials, we will be using a slightly modified version of the
FBIRN Phase I travelling data set. 

Step 0
~~~~~~

Download and extract the `Pipeline tutorial data (429MB). 
<http://sourceforge.net/projects/nipy/files/nipype/nipype-0.2/nipype-tutorial.tar.bz2/download>`_  

(checksum: 56ed4b7e0aac5627d1724e9c10cd26a7)


Step 1.
~~~~~~~

Ensure that all programs are available by calling ``bet``, ``matlab``
and then ``which spm`` within matlab to ensure you have spm5/8 in your
matlab path.

Step 2.
~~~~~~~

You can now run the tutorial by typing ``python tutorial_script.py``
within the nipype-tutorial directory. This will run a full first level
analysis on two subjects following by a 1-sample t-test on their first
level results. The next section goes through each section of the
tutorial script and describes what it is doing.

.. include:: ../links_names.txt
