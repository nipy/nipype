.. _available_modules:

=================
Available modules
=================

SPM
---

#.  Realign

#.  Coregister

#.  Normalize

#.  Segment

#.  Smooth

#.  Level 1 - Model Specification

#.  Level 1 - Model Estimation

#.  Level 1 - Contrast Estimation

#.  Level 2

    #. One Sample t-test
    #. Two Sample t-test


FSL
---

#.  Bet

#.  FAST

#.  FLIRT

#.  FNIRT

#.  MCFLIRT


FreeSurfer
----------

#.  Dicom2Nifti - converts dicom to nifti files using mri_convert (knows
    a lot of siemens specific fields)

#.  Recon-all

#.  Resample - allows one to upsample or downsample data

#.  BBregister

#.  Smooth - integrated volume + surface smoothing


Misc
----

#. ArtifactDetection - detects outliers in functional runs based on
   motion and intensity.

#. IO - these are generic routines for structuring data into and out of
   the pipelines

  #.  DataSource
  #.  DataSink
  #.  DataGrabber

.. include:: ../links_names.txt
