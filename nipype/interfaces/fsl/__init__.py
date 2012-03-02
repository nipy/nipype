# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.

Top-level namespace for fsl.
"""

from .base import (FSLCommand, Info, check_fsl, no_fsl, no_fsl_course_data)
from .preprocess import (FAST, FLIRT, ApplyXfm, BET, MCFLIRT, FNIRT, ApplyWarp,
                         SliceTimer, SUSAN, PRELUDE, FUGUE, FIRST)
from .model import (Level1Design, FEAT, FEATModel, FILMGLS, FEATRegister,
                    FLAMEO, ContrastMgr, MultipleRegressDesign, L2Model, SMM,
                    MELODIC, SmoothEstimate, Cluster, Randomise)
from .utils import (Smooth, Merge, ExtractROI, Split, ImageMaths, ImageMeants,
                    ImageStats, FilterRegressor, Overlay, Slicer,
                    PlotTimeSeries, PlotMotionParams, ConvertXFM,
                    SwapDimensions, PowerSpectrum)
from .dti import (EddyCorrect, BEDPOSTX, DTIFit, ProbTrackX, VecReg, ProjThresh,
                  FindTheBiggest, DistanceMap, TractSkeleton, XFibres,
                  MakeDyadicVectors)
from .maths import (ChangeDataType, Threshold, MeanImage, ApplyMask,
                    IsotropicSmooth, TemporalFilter, DilateImage, ErodeImage,
                    SpatialFilter, UnaryMaths, BinaryMaths, MultiImageMaths)
