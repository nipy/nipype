# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""SPM is a software package for the analysis of brain imaging data sequences."""
from .base import Info, SPMCommand, logger, no_spm, scans_for_fname, scans_for_fnames
from .preprocess import (
    FieldMap,
    SliceTiming,
    Realign,
    RealignUnwarp,
    Coregister,
    Normalize,
    Normalize12,
    Segment,
    Smooth,
    NewSegment,
    MultiChannelNewSegment,
    DARTEL,
    DARTELNorm2MNI,
    CreateWarped,
    VBMSegment,
)
from .model import (
    Level1Design,
    EstimateModel,
    EstimateContrast,
    Threshold,
    OneSampleTTestDesign,
    TwoSampleTTestDesign,
    PairedTTestDesign,
    MultipleRegressionDesign,
)
from .utils import (
    Analyze2nii,
    CalcCoregAffine,
    ApplyTransform,
    Reslice,
    ApplyInverseDeformation,
    ResliceToReference,
    DicomImport,
)
