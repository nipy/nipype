"""Top-level namespace for spm."""

from nipype.interfaces.spm.base import (Info, SPMCommand, logger,
                                        scans_for_fname, scans_for_fnames)
from nipype.interfaces.spm.preprocess import (SliceTiming, Realign, Coregister,
                                              Normalize, Segment, Smooth,
                                              NewSegment)
from nipype.interfaces.spm.model import (Level1Design, EstimateModel,
                                         EstimateContrast, OneSampleTTest,
                                         TwoSampleTTest, MultipleRegression,
                                         Threshold)

