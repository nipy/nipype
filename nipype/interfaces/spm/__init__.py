"""Top-level namespace for spm."""

from nipype.interfaces.spm.base import (SpmInfo, SpmMatlabCommandLine,
                                        NEW_Info, NEW_SPMCommand, logger,
                                        scans_for_fname, scans_for_fnames)
from nipype.interfaces.spm.preprocess import (SliceTiming, Realign, Coregister,
                                              Normalize, Segment, Smooth,
                                              NEW_Realign)
from nipype.interfaces.spm.model import (Level1Design, EstimateModel,
                                         EstimateContrast, OneSampleTTest,
                                         TwoSampleTTest, MultipleRegression)

