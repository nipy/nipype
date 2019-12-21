# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""MRTrix version 2 (DEPRECATED) -- tools to perform various types of diffusion MRI analyses."""
from .tracking import (
    Tracks2Prob,
    FilterTracks,
    StreamlineTrack,
    DiffusionTensorStreamlineTrack,
    SphericallyDeconvolutedStreamlineTrack,
    ProbabilisticSphericallyDeconvolutedStreamlineTrack,
)
from .tensors import (
    FSL2MRTrix,
    ConstrainedSphericalDeconvolution,
    DWI2SphericalHarmonicsImage,
    EstimateResponseForSH,
    GenerateDirections,
    FindShPeaks,
    Directions2Amplitude,
)
from .preprocess import (
    MRConvert,
    MRMultiply,
    MRTrixViewer,
    MRTrixInfo,
    GenerateWhiteMatterMask,
    DWI2Tensor,
    Tensor2ApparentDiffusion,
    Tensor2FractionalAnisotropy,
    Tensor2Vector,
    MedianFilter3D,
    Erode,
    Threshold,
)
from .convert import MRTrix2TrackVis
