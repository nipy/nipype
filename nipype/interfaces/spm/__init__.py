# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for spm."""

from .base import (Info, SPMCommand, logger, no_spm, scans_for_fname,
                   scans_for_fnames)
from .preprocess import (SliceTiming, Realign, Coregister, Normalize, Segment,
                         Smooth, NewSegment, DARTEL, DARTELNorm2MNI,
                         CreateWarped)
from .model import (Level1Design, EstimateModel, EstimateContrast, Threshold,
                    OneSampleTTestDesign, TwoSampleTTestDesign,
                    PairedTTestDesign, MultipleRegressionDesign)

from .utils import Analyze2nii, CalcCoregAffine, ApplyTransform, Reslice
