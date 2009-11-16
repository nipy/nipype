.. _tutorial2:

==============================
Using FreeSurfer for smoothing
==============================

This tutorial illustrates how to perform surface-based smoothing of
cortical data using freesurfer and then perform firstlevel model and
contrast estimation using SPM. A surface-based second level glm
illustrates the use of spherical registration and freesurfer's glm
functions. 

Step 0
======
In order to run this tutorial you need to have spm and freesurfer
tools installed and accessible from matlab/command line. Check by
calling mri_info from the command line.

Step 1
======
Link the fsaverage directory for your freesurfer distribution. To do
this type: 

::

  cd nipype-tutorial/fsdata
  ln -s $FREESURFER_HOME/subjects/fsaverage
  cd ..


.. literalinclude:: ../../examples/freesurfer_tutorial.py

.. include:: ../links_names.txt
