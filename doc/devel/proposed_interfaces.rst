===============================
 Proposed Interfaces - OUTDATED
===============================

Below is a brief list of interfaces we plan to implement.  This
document should be temporary and eventually go into the documentation.

List of interfaces
------------------

SPM
^^^
#. realignment
    #. realign (estimate, or estimate_write)
    #. realign_unwarp
#. coregistration
    #. coregister(estimate, estimate_write)
#. reslice
    #. (via coreg or realign)
#. normalization (traditional + dartel)
#. smoothing
#. first level estimation
#. 2nd level analysis (1sample-ttest, 2sample-ttest, anova,
   correlations, etc.,.) - satra
#. PPI
#. fieldmap correction
#. first level analysis using surface smoothed data
#. DCM

FSL
^^^
#. bet
#. flirt
#. fnirt
#. feat
#. melodic
#. fugue
#. tbss (essentially a DTI pipeline)
#. first
#. possum

FreeSurfer
^^^^^^^^^^
#. mri_convert (DICOM to nifti, among other things. It's really tuned
   to our Siemens scanners)
#. recon-all (surface extraction)
#. bbregister (very nice program to coregister partial/full epi to
   surfaces, i.e., structurals. This works better than most things
   I've seen)
#. parcellation
#. smoothing using surfaces
#. group analysis from surface data
#. motion correction using bbregister
#. atlas training
#. template creation

Afni
^^^^
#. to3d
#. 3drefit
#. 3dresample
#. 3dTstat
#. 3dAutomask
#. 3dvolreg
#. 3dmerge
#. 3dZcutup
#. 3dSkullStrip



