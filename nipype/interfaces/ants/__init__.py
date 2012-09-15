# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""Top-level namespace for ants."""

# Registraiton programs
from .registration import ANTS, antsRegistration
# deprecated
from .legacy import antsIntroduction, ApplyTransforms, buildtemplateparallel

# Resampling Programs
from resampling import antsApplyTransforms, WarpImageMultiTransform, WarpTimeSeriesImageMultiTransform


# Segmentation Programs
from .segmentation import Atropos, N4BiasFieldCorrection

# Utility Programs
from .utils import AverageAffineTransform, AverageImages, MultiplyImages
