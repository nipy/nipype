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

:class:`T1PrepRealignLongitudinal`
    Rigid realignment of longitudinal T1w time-points.  Wraps
    ``python -m t1prep.realign_longitudinal``.

:class:`T1PrepCatSurf`
    Surface post-processing via the ``cat_surf`` Python API
    (exposed as ``t1prep.cat_surf``).  Currently wraps heat-kernel
    smoothing of per-vertex data.

Base classes
------------
:class:`Info`
    T1Prep package version detection.

:class:`T1PrepCommand`
    Base ``CommandLine`` for ``python -m t1prep.<module>`` invocations.

The full ``cat_surf`` function surface is also available as individual
interfaces in :mod:`nipype.interfaces.t1prep.cat_surf`, all exported
directly from this package (e.g. :class:`CatSurfVolThicknessPbt`,
:class:`CatSurfDeform`, :class:`CatSurfVolMarchingCubes`, etc.).

References
----------
Lukas Fisch et al., "deepmriprep: Voxel-based Morphometry (VBM)
Preprocessing via Deep Neural Networks", arXiv:2408.10656.

Dahnke R, Yotter RA, Gaser C, "Cortical thickness and central surface
estimation", NeuroImage, 65:226-248, 2013.
"""

from .base import Info, T1PrepCommand
from .preprocess import T1Prep, T1PrepSegment
from .surface import T1PrepSurfaceEstimation, T1PrepCatSurf
from .longitudinal import T1PrepRealignLongitudinal
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
    CatSurfDeform,
    CatSurfToPialWhite,
    CatSurfToSphere,
    CatSurfWarp,
    CatSurfAverage,
    CatSurfResampleToSphere,
    CatSurfResampleAnnot,
    # Per-vertex data smoothing / curvature
    CatSurfSmoothHeatkernel,
    CatSurfSmoothMesh,
    CatSurfSmoothedCurvatures,
    CatSurfCurvature,
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
    "Info",
    "T1PrepCommand",
    "T1Prep",
    "T1PrepSegment",
    "T1PrepSurfaceEstimation",
    "T1PrepRealignLongitudinal",
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
    "CatSurfDeform",
    "CatSurfToPialWhite",
    "CatSurfToSphere",
    "CatSurfWarp",
    "CatSurfAverage",
    "CatSurfResampleToSphere",
    "CatSurfResampleAnnot",
    # Per-vertex data smoothing / curvature
    "CatSurfSmoothHeatkernel",
    "CatSurfSmoothMesh",
    "CatSurfSmoothedCurvatures",
    "CatSurfCurvature",
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
