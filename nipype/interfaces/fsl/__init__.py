# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Top-level namespace for fsl.  Perhaps should just make fsl a package!
"""

from nipype.interfaces.fsl.base import (FSLCommand, Info, check_fsl, no_fsl,
                                        no_fsl_course_data)
from nipype.interfaces.fsl.preprocess import (FAST, FLIRT, ApplyXfm,
                                              BET, MCFLIRT, FNIRT, ApplyWarp,
                                              SliceTimer, SUSAN,
                                              PRELUDE, FUGUE)
from nipype.interfaces.fsl.model import (Level1Design, FEAT, FEATModel,
                                         FILMGLS, FEATRegister,
                                         FLAMEO, ContrastMgr,
                                         MultipleRegressDesign,
                                         L2Model, SMM, MELODIC,
                                         SmoothEstimate, Cluster, Randomise)
from nipype.interfaces.fsl.utils import (Smooth, Merge, ExtractROI, Split,
                                         ImageMaths, ImageMeants, ImageStats,
                                         FilterRegressor, Overlay, Slicer,
                                         PlotTimeSeries, PlotMotionParams,
                                         ConvertXFM, SwapDimensions, PowerSpectrum)
from nipype.interfaces.fsl.dti import (EddyCorrect, BEDPOSTX, DTIFit,
                                       ProbTrackX, VecReg, ProjThresh,
                                       FindTheBiggest, DistanceMap,
                                       TractSkeleton, XFibres,
                                       MakeDyadicVectors)
from nipype.interfaces.fsl.maths import (ChangeDataType, Threshold, MeanImage,
                                         ApplyMask, IsotropicSmooth, TemporalFilter,
                                         DilateImage, ErodeImage, SpatialFilter,
                                         UnaryMaths, BinaryMaths, MultiImageMaths)
