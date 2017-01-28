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

  - SPM_ 5/8/12 is installed and callable in matlab

  - Space: 3-10 GB

Checklist for analysis tutorials
================================

For the analysis tutorials, we will be using a slightly modified version of the
FBIRN Phase I travelling data set.

1. Download and extract the `Pipeline tutorial data (429MB).
<https://figshare.com/articles/nipype_tutorial_data/3395806>`_
(md5: d175083784c5167de4ea11b43b37c166)

2. Ensure that all programs are available by calling ``bet``, ``matlab``
and then ``which spm`` within matlab to ensure you have spm5/8/12 in your
matlab path.

.. include:: ../links_names.txt
