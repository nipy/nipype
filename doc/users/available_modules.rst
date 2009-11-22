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

#. FSLSmooth

#. Level1Design

#. FSFL1Maker


FreeSurfer
----------

#.  Dicom2Nifti - converts dicom to nifti files using mri_convert (knows
    a lot of siemens specific fields)

#.  Recon-all

#.  Resample - allows one to upsample or downsample data

#.  BBregister

#.  Smooth - integrated volume + surface smoothing

#.  SurfConcat - projects and concatenates con images to a surface for a second level surface-based glm

#.  OneSampleTTest - surface based glm for second level analysis


Misc
----

#. ArtifactDetection - detects outliers in functional runs based on  motion and intensity.

#. StimulusCorrelation -  detects if stimulus schedule is correlated with motion or intensity

#. IO - these are generic routines for structuring data into and out of the pipelines

  #.  DataSource
  #.  DataSink
  #.  DataGrabber

.. include:: ../links_names.txt
