"""Interfaces for T1Prep – T1-weighted MRI preprocessing pipeline (PyCAT).

T1Prep performs skull-stripping, tissue segmentation, and cortical surface
reconstruction using DeepMriPrep and the CAT-Surface library (via cat-surf).

Sub-module interfaces
---------------------
:class:`T1Prep`
    Full pipeline: skull-strip → segment → surface estimate.  Wraps
    ``python -m t1prep.t1prep``.

:class:`T1PrepSegment`
    Segmentation stage only.  Wraps ``python -m t1prep.segment``.

:class:`T1PrepSurfaceEstimation`
    Surface-estimation stage for one hemisphere.  Wraps
    ``python -m t1prep.surface_estimation``.

:class:`T1PrepCatSurf`
    Surface post-processing via the ``cat_surf`` Python API
    (exposed as ``t1prep.cat_surf``).  Currently wraps heat-kernel
    smoothing of per-vertex data.

The full ``cat_surf`` function surface is also available as individual
interfaces in :mod:`nipype.interfaces.t1prep.cat_surf`, all exported
directly from this package (e.g. :class:`CatSurfVolThicknessPbt`,
:class:`CatSurfSurfDeform`, :class:`CatSurfVolMarchingCubes`, etc.).

References
----------
Lukas Fisch et al., "deepmriprep: Voxel-based Morphometry (VBM)
Preprocessing via Deep Neural Networks", arXiv:2408.10656.

Dahnke R, Yotter RA, Gaser C, "Cortical thickness and central surface
estimation", NeuroImage, 65:226-248, 2013.
"""

from .preprocess import T1Prep, T1PrepSegment
from .surface import T1PrepSurfaceEstimation, T1PrepCatSurf
from .cat_surf import (
    # I/O
    CatSurfReadSurface,
    CatSurfWriteSurface,
    CatSurfReadValues,
    CatSurfWriteValues,
    # Surface geometry
    CatSurfGetArea,
    CatSurfGetAreaNormalized,
    CatSurfEulerCharacteristic,
    CatSurfSphereRadius,
    CatSurfHausdorffDistance,
    CatSurfPointDistance,
    CatSurfPointDistanceMean,
    CatSurfCountIntersections,
    CatSurfRemoveIntersections,
    CatSurfReduceMesh,
    # Surface processing / deformation
    CatSurfSurfDeform,
    CatSurfSurfToPialWhite,
    CatSurfSurfToSphere,
    CatSurfSurfWarp,
    CatSurfSurfAverage,
    CatSurfResampleToSphere,
    CatSurfResampleAnnot,
    # Per-vertex data smoothing / curvature
    CatSurfSmoothHeatkernel,
    CatSurfSmoothMesh,
    CatSurfSmoothedCurvatures,
    CatSurfSurfCurvature,
    CatSurfSulcusDepth,
    CatSurfCorrectThicknessFolding,
    # Volume operations
    CatSurfVolSanlm,
    CatSurfVolMarchingCubes,
    CatSurfVol2Surf,
    CatSurfVolThicknessPbt,
    CatSurfVolAmap,
    CatSurfVolBloodVesselCorrection,
    # Registration
    CatSurfBbreg,
    CatSurfBbregDetectContrast,
    CatSurfVolumeRegisterNmi,
    CatSurfVolumeRegisterRobust,
)

__all__ = [
    "T1Prep",
    "T1PrepSegment",
    "T1PrepSurfaceEstimation",
    "T1PrepCatSurf",
    # I/O
    "CatSurfReadSurface",
    "CatSurfWriteSurface",
    "CatSurfReadValues",
    "CatSurfWriteValues",
    # Surface geometry
    "CatSurfGetArea",
    "CatSurfGetAreaNormalized",
    "CatSurfEulerCharacteristic",
    "CatSurfSphereRadius",
    "CatSurfHausdorffDistance",
    "CatSurfPointDistance",
    "CatSurfPointDistanceMean",
    "CatSurfCountIntersections",
    "CatSurfRemoveIntersections",
    "CatSurfReduceMesh",
    # Surface processing / deformation
    "CatSurfSurfDeform",
    "CatSurfSurfToPialWhite",
    "CatSurfSurfToSphere",
    "CatSurfSurfWarp",
    "CatSurfSurfAverage",
    "CatSurfResampleToSphere",
    "CatSurfResampleAnnot",
    # Per-vertex data smoothing / curvature
    "CatSurfSmoothHeatkernel",
    "CatSurfSmoothMesh",
    "CatSurfSmoothedCurvatures",
    "CatSurfSurfCurvature",
    "CatSurfSulcusDepth",
    "CatSurfCorrectThicknessFolding",
    # Volume operations
    "CatSurfVolSanlm",
    "CatSurfVolMarchingCubes",
    "CatSurfVol2Surf",
    "CatSurfVolThicknessPbt",
    "CatSurfVolAmap",
    "CatSurfVolBloodVesselCorrection",
    # Registration
    "CatSurfBbreg",
    "CatSurfBbregDetectContrast",
    "CatSurfVolumeRegisterNmi",
    "CatSurfVolumeRegisterRobust",
]
