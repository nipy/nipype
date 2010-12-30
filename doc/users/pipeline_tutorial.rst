.. _pipeline_tutorial:

=====================
 Tutorial : Pipeline
=====================

This section presents several tutorials on how to setup and use pipelines. Make
sure that you have the requirements satisfied and go through the steps required
for the analysis tutorials.

Tutorials
=========

.. toctree::
   :maxdepth: 1

   tutorial_101
   tutorial_102
   tutorial_103
   spm_tutorial
   spm_tutorial2
   spm_auditory_tutorial
   spm_face_tutorial
   freesurfer_tutorial
   fsl_tutorial
   fsl_feeds
   fsl_dti_tutorial
   nipy_tutorial
   dartmouth_workshop_2010

Requirements
============

  All tutorials

  - Release 0.3 of nipype and it's dependencies have been installed

  Analysis tutorials

  - FSL_, FreeSurfer_ and MATLAB_ are available and callable from the command line

  - SPM_ 5/8 is installed and callable in matlab

  - 4(? XX) GB of space

Checklist for analysis tutorials
================================

For the analysis tutorials, we will be using a slightly modified version of the
FBIRN Phase I travelling data set. 

Step 0
~~~~~~

Download and extract the `Pipeline tutorial data (429MB). 
<http://cirl.berkeley.edu/nipy/nipype-tutorial-0.2.tar.gz>`_  

(checksum: f91b81050e1262f0508d35135c2369f5)


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
