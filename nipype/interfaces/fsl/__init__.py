# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.

Top-level namespace for fsl.
"""

from .base import (FSLCommand, Info, check_fsl, no_fsl, no_fsl_course_data)
from .preprocess import (FAST, FLIRT, ApplyXFM, BET, MCFLIRT, FNIRT, ApplyWarp,
                         SliceTimer, SUSAN, PRELUDE, FUGUE, FIRST)
from .model import (Level1Design, FEAT, FEATModel, FILMGLS, FEATRegister,
                    FLAMEO, ContrastMgr, MultipleRegressDesign, L2Model, SMM,
                    MELODIC, SmoothEstimate, Cluster, Randomise, GLM)
from .utils import (
    AvScale, Smooth, Slice, Merge, ExtractROI, Split, ImageMaths, ImageMeants,
    ImageStats, FilterRegressor, Overlay, Slicer, PlotTimeSeries,
    PlotMotionParams, ConvertXFM, SwapDimensions, PowerSpectrum, Reorient2Std,
    Complex, InvWarp, WarpUtils, ConvertWarp, WarpPoints, WarpPointsToStd,
    WarpPointsFromStd, RobustFOV, CopyGeom, MotionOutliers)

from .epi import (PrepareFieldmap, TOPUP, ApplyTOPUP, Eddy, EPIDeWarp, SigLoss,
                  EddyCorrect, EpiReg)
from .dti import (BEDPOSTX, XFibres, DTIFit, ProbTrackX, ProbTrackX2, VecReg,
                  ProjThresh, FindTheBiggest, DistanceMap, TractSkeleton,
                  MakeDyadicVectors, BEDPOSTX5, XFibres5)
from .maths import (ChangeDataType, Threshold, MeanImage, ApplyMask,
                    IsotropicSmooth, TemporalFilter, DilateImage, ErodeImage,
                    SpatialFilter, UnaryMaths, BinaryMaths, MultiImageMaths,
                    MaxnImage, MinImage, MedianImage, PercentileImage,
                    AR1Image)
from .possum import B0Calc
from .fix import (AccuracyTester, Classifier, Cleaner, FeatureExtractor,
                  Training, TrainingSetCreator)
from .aroma import ICA_AROMA
