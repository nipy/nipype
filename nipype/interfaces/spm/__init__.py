# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Top-level namespace for spm."""

from nipype.interfaces.spm.base import (Info, SPMCommand, logger, no_spm,
                                        scans_for_fname, scans_for_fnames)
from nipype.interfaces.spm.preprocess import (SliceTiming, Realign, Coregister,
                                              Normalize, Segment, Smooth,
                                              NewSegment)
from nipype.interfaces.spm.model import (Level1Design, EstimateModel,
                                         EstimateContrast, OneSampleTTest,
                                         TwoSampleTTest, MultipleRegression,
                                         Threshold,
                                         OneSampleTTestDesign, TwoSampleTTestDesign,
                                         PairedTTestDesign, MultipleRegressionDesign
                                         )

from nipype.interfaces.spm.utils import Analyze2nii