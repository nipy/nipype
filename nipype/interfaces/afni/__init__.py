# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The afni module provides classes for interfacing with the `AFNI
<http://afni.nimh.nih.gov/afni>`_ command line tools.

Top-level namespace for afni.
"""

from .base import Info
from .preprocess import (AFNItoNIFTI, Allineate, AutoTcorrelate, Autobox,
                         Automask, Bandpass, BlurInMask, BlurToFWHM, BrickStat,
                         Calc, ClipLevel, Copy, DegreeCentrality, Despike,
                         Detrend, ECM, Eval, FWHMx, Fim, Fourier, Hist, LFCD,
                         MaskTool, Maskave, Means, Merge, Notes, OutlierCount,
                         QualityIndex, ROIStats, Refit, Resample, Retroicor,
                         Seg, SkullStrip, TCat, TCorr1D, TCorrMap, TCorrelate,
                         TShift, TStat, To3D, Volreg, Warp, ZCutUp)
from .svm import (SVMTest, SVMTrain)
