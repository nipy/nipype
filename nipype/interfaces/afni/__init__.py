# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The afni module provides classes for interfacing with the `AFNI
<http://www.fmrib.ox.ac.uk/afni/index.html>`_ command line tools.  This
was written to work with AFNI version 4.1.4.

Top-level namespace for afni.  Perhaps should just make afni a package!
"""

from .base import Info
from .preprocess import (To3D, Refit, Resample, TStat, Automask, Volreg, Merge,
                         ZCutUp, Calc, TShift, Warp, Detrend, Despike, Copy,
                         Fourier, Allineate, Maskave, SkullStrip, TCat, Fim,
                         TCorrelate, BrickStat, ROIStats, AutoTcorrelate,
                         BlurInMask, Autobox, TCorrMap, Bandpass)
