:orphan:

.. _interfaces:

========================
Interfaces and Workflows
========================
:Release: |version|
:Date: |today|

Previous versions: `1.4.2 <http://nipype.readthedocs.io/en/1.4.2/>`_ `1.4.1 <http://nipype.readthedocs.io/en/1.4.1/>`_

Workflows
---------
.. important::

  The workflows that used to live as a module under
  ``nipype.workflows`` have been migrated to the
  new project `NiFlows <https://github.com/niflows>`__.
  These may be installed with the
  `niflow-nipype1-examples <https://pypi.org/project/niflow-nipype1-workflows/>`__
  package, but their continued use is discouraged.

Interfaces
----------
An index of all nipype interfaces is found below.
Nipype provides some *in-house* interfaces to help with workflow
management tasks, basic image manipulations, and filesystem/storage
interfaces:

    * `Algorithms <api/generated/nipype.algorithms.html>`__
    * `Image manipulation <api/generated/nipype.interfaces.image.html>`__
    * `I/O Operations <api/generated/nipype.interfaces.io.html>`__
    * `Self-reporting interfaces <api/generated/nipype.interfaces.mixins.html>`__
    * `Utilities <api/generated/nipype.interfaces.utility.html>`__

Nipype provides interfaces for the following **third-party** tools:

  * `AFNI <api/generated/nipype.interfaces.afni.html>`__
    (Analysis of Functional NeuroImages) is a leading software suite of C, Python,
    R programs and shell scripts primarily developed for the analysis and display of
    anatomical and functional MRI (fMRI) data.
  * `ANTs <api/generated/nipype.interfaces.ants.html>`__
    (Advanced Normalization ToolS) computes high-dimensional mappings to capture
    the statistics of brain structure and function.
  * `BrainSuite <api/generated/nipype.interfaces.brainsuite.html>`__
    is a collection of open source software tools that enable largely
    automated processing of magnetic resonance images (MRI) of the human brain.
  * `BRU2NII <api/generated/nipype.interfaces.bru2nii.html>`__
    is a simple tool for converting Bruker ParaVision MRI data to NIfTI.
  * `Convert3D <api/generated/nipype.interfaces.c3.html>`__
    is a command-line tool for converting 3D images between common file formats.
  * `Camino <api/generated/nipype.interfaces.camino.html>`__
    is an open-source software toolkit for diffusion MRI processing.
  * `Camino-TrackVis <api/generated/nipype.interfaces.camino2trackvis.html>`__
    allows interoperability between Camino and TrackVis.
  * `Connectome Mapper (CMP) <api/generated/nipype.interfaces.cmtk.html>`__
    implements a full processing pipeline for creating multi-variate and
    multi-resolution connectomes with dMRI data.
  * `dcm2nii <api/generated/nipype.interfaces.dcm2nii.html>`__
    converts images from the proprietary scanner DICOM format to NIfTI
  * `DCMStack <api/generated/nipype.interfaces.dcmstack.html>`__
    allows series of DICOM images to be stacked into multi-dimensional arrays.
  * `Diffusion Toolkit <api/generated/nipype.interfaces.diffusion_toolkit.html>`__
    is a set of command-line tools with a GUI frontend that performs data reconstruction
    and fiber tracking on diffusion MR images.
  * `DIPY <api/generated/nipype.interfaces.dipy.html>`__
    is a free and open source software project for computational neuroanatomy,
    focusing mainly on diffusion magnetic resonance imaging (dMRI) analysis.
  * `DTITK <api/generated/nipype.interfaces.dtitk.html>`__
    is a spatial normalization and atlas construction toolkit optimized for examining
    white matter morphometry using DTI data.
  * `Elastix <api/generated/nipype.interfaces.elastix.html>`__
    is a toolbox for rigid and nonrigid registration of images.
  * `FreeSurfer <api/generated/nipype.interfaces.freesurfer.html>`__
    is an open source software suite for processing and analyzing (human) brain MRI images.
  * `FSL <api/generated/nipype.interfaces.fsl.html>`__
    is a comprehensive library of analysis tools for fMRI, MRI and DTI brain imaging data.
  * Matlab `script wrapper <api/generated/nipype.interfaces.matlab.html>`__
    provides interfaces to integrate matlab scripts within workflows.
  * `MeshFix <api/generated/nipype.interfaces.meshfix.html>`__
    converts a raw digitized polygon mesh to a clean mesh where all the occurrences
    of a specific set of "defects" are corrected.
  * `MINC Toolkit <api/generated/nipype.interfaces.minc.html>`__
    contains the most commonly used tools developed at the McConnell Brain Imaging Centre,
    Montreal Neurological Institute.
  * `MIPAV (Medical Image Processing, Analysis, and Visualization) <api/generated/nipype.interfaces.mipav.html>`__
    enables quantitative analysis and visualization of medical images of numerous
    modalities such as PET, MRI, CT, or microscopy.
  * `MNE <api/generated/nipype.interfaces.mne.html>`__
    is a software for exploring, visualizing, and analyzing human neurophysiological
    data: MEG, EEG, sEEG, ECoG, and more.
  * MRTrix is a set of tools to perform various types of diffusion MRI analyses, from various
    forms of tractography through to next-generation group-level analyses
    (`MRTrix3 <api/generated/nipype.interfaces.mrtrix3.html>`__, and the deprecated
    `MRTrix version 2 <api/generated/nipype.interfaces.mrtrix.html>`__).
  * Nifty Tools:
    `NiftyFit <api/generated/nipype.interfaces.niftyfit.html>`__
    is a software package for multi-parametric model-fitting of 4D MRI;
    `NiftyReg <api/generated/nipype.interfaces.niftyreg.html>`__
    is an open-source software for efficient medical image registration; and
    `NiftySeg <api/generated/nipype.interfaces.niftyseg.html>`__
    contains programs to perform EM based segmentation of images in NIfTI or Analyze format.
  * `NiLearn <api/generated/nipype.interfaces.nilearn.html>`__
    is a Python library for fast and easy statistical learning on NeuroImaging data.
  * `NiPy <api/generated/nipype.interfaces.nipy.html>`__
    is a Python project for analysis of structural and functional neuroimaging data.
  * `Nitime <api/generated/nipype.interfaces.nitime.html>`__
    is a library for time-series analysis of data from neuroscience experiments.
  * `PETPVC <api/generated/nipype.interfaces.petpvc.html>`__
    is toolbox for :abbr:`PVC (partial volume correction)` of
    :abbr:`PET (positron emission tomography)` imaging.
  * `QuickShear <api/generated/nipype.interfaces.quickshear.html>`__
    uses a skull-stripped version of an anatomical images as a reference to deface the
    unaltered anatomical image.
  * `SEM Tools <api/generated/nipype.interfaces.semtools.html>`__
    are useful tools for Structural Equation Modeling.
  * `SPM <api/generated/nipype.interfaces.spm.html>`__
    (Statistical Parametric Mapping) is a software package for the analysis of brain
    imaging data sequences.
  * `VistaSoft <api/generated/nipype.interfaces.vista.html>`__
    contains Matlab code to perform a variety of analysis on MRI data, including
    functional MRI and diffusion MRI.
  * `Connectome Workbench <api/generated/nipype.interfaces.workbench.html>`__
    is an open source, freely available visualization and discovery tool used to map neuroimaging data,
    especially data generated by the Human Connectome Project.
  * `3D Slicer <api/generated/nipype.interfaces.slicer.html>`__
    is an open source software platform for medical image informatics,
    image processing, and three-dimensional visualization.

Index of Interfaces
~~~~~~~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 3

    api/generated/nipype.algorithms
    api/generated/nipype.interfaces
