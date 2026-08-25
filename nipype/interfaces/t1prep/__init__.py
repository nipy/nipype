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

Base classes
------------
:class:`Info`
    T1Prep package version detection.

:class:`T1PrepCommand`
    Base ``CommandLine`` for ``python -m t1prep.<module>`` invocations.

A focused subset of the ``cat_surf`` API — the volume-denoising and volume/
boundary registration interfaces needed to replace FreeSurfer / FSL (bbreg) /
ANTs in an fMRIPrep-style pipeline — is exported directly from this package
(:class:`CatSurfVolSanlm`, :class:`CatSurfBbreg`, :class:`CatSurfBbregDetectContrast`,
:class:`CatSurfVolumeRegisterNmi`, :class:`CatSurfVolumeRegisterRobust`).  The
full per-function interface set is archived for reference in the CAT-Surface
repository under ``cat_surface_cython/examples/nipype/``.

"""

from .base import Info, T1PrepCommand
from .preprocess import T1Prep, T1PrepSegment
from .surface import T1PrepSurfaceEstimation
from .longitudinal import T1PrepRealignLongitudinal
from .cat_surf import (
    # Volume operations
    CatSurfVolSanlm,
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
    # Volume operations
    "CatSurfVolSanlm",
    # Registration
    "CatSurfBbreg",
    "CatSurfBbregDetectContrast",
    "CatSurfVolumeRegisterNmi",
    "CatSurfVolumeRegisterRobust",
]
