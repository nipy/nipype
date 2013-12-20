# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The afni module provides classes for interfacing with the `AFNI
<http://afni.nimh.nih.gov/afni>`_ command line tools.

Top-level namespace for afni.
"""

from .base import Info
from .preprocess import (To3D, Refit, Resample, TStat, Automask, Volreg, Merge,
                         ZCutUp, Calc, TShift, Warp, Detrend, Despike, Copy,
                         Fourier, Allineate, Maskave, SkullStrip, TCat, Fim,
                         BlurInMask, Autobox, TCorrMap, Bandpass, Retroicor,
                         TCorrelate, TCorr1D, BrickStat, ROIStats, AutoTcorrelate,
                         AFNItoNIFTI)
