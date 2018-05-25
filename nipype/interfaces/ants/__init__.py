# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for ants."""

# Registraiton programs
from .registration import (ANTS, Registration, RegistrationSynQuick,
                           MeasureImageSimilarity)

# Resampling Programs
from .resampling import (ApplyTransforms, ApplyTransformsToPoints,
                         WarpImageMultiTransform,
                         WarpTimeSeriesImageMultiTransform)

# Segmentation Programs
from .segmentation import (Atropos, LaplacianThickness, N4BiasFieldCorrection,
                           JointFusion, CorticalThickness, BrainExtraction,
                           DenoiseImage, AntsJointFusion)

# Visualization Programs
from .visualization import ConvertScalarImageToRGB, CreateTiledMosaic

# Utility Programs
from .utils import (AverageAffineTransform, AverageImages, MultiplyImages,
                    CreateJacobianDeterminantImage, AffineInitializer,
                    ComposeMultiTransform, LabelGeometry)
