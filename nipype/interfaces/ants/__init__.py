# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for ants."""

# Registration programs
from .registration import (
    ANTS,
    CompositeTransformUtil,
    MeasureImageSimilarity,
    Registration,
    RegistrationSynQuick,
)

# Resampling Programs
from .resampling import (
    ApplyTransforms,
    ApplyTransformsToPoints,
    WarpImageMultiTransform,
    WarpTimeSeriesImageMultiTransform,
)

# Segmentation Programs
from .segmentation import (
    AntsJointFusion,
    Atropos,
    BrainExtraction,
    CorticalThickness,
    DenoiseImage,
    JointFusion,
    LaplacianThickness,
    N4BiasFieldCorrection,
)

# Visualization Programs
from .visualization import ConvertScalarImageToRGB, CreateTiledMosaic

# Utility Programs
from .utils import (
    AffineInitializer,
    AI,
    AverageAffineTransform,
    AverageImages,
    ComposeMultiTransform,
    CreateJacobianDeterminantImage,
    ImageMath,
    LabelGeometry,
    MultiplyImages,
    ResampleImageBySpacing,
    ThresholdImage,
)

__all__ = [
    "AffineInitializer",
    "AI",
    "ANTS",
    "AntsJointFusion",
    "ApplyTransforms",
    "ApplyTransformsToPoints",
    "Atropos",
    "AverageAffineTransform",
    "AverageImages",
    "BrainExtraction",
    "ComposeMultiTransform",
    "CompositeTransformUtil",
    "ConvertScalarImageToRGB",
    "CorticalThickness",
    "CreateJacobianDeterminantImage",
    "CreateTiledMosaic",
    "DenoiseImage",
    "ImageMath",
    "JointFusion",
    "LabelGeometry",
    "LaplacianThickness",
    "MeasureImageSimilarity",
    "MultiplyImages",
    "N4BiasFieldCorrection",
    "Registration",
    "RegistrationSynQuick",
    "ResampleImageBySpacing",
    "ThresholdImage",
    "WarpImageMultiTransform",
    "WarpTimeSeriesImageMultiTransform",
]
