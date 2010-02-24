.. _tutorial_freesurfer:

==============================
Using FreeSurfer for smoothing
==============================

This tutorial illustrates how to perform surface-based smoothing of
cortical data using FreeSurfer_ and then perform firstlevel model and
contrast estimation using SPM_. A surface-based second level glm
illustrates the use of spherical registration and freesurfer's glm
functions. 

Step 0
======
In order to run this tutorial you need to have SPM_ and FreeSurfer_
tools installed and accessible from matlab/command line. Check by
calling mri_info from the command line.

Step 1
======
Link the *fsaverage* directory for your freesurfer distribution. To do
this type: 

::

  cd nipype-tutorial/fsdata
  ln -s $FREESURFER_HOME/subjects/fsaverage
  cd ..


.. include:: ../examples/freesurfer_tutorial.rst

.. include:: ../links_names.txt
