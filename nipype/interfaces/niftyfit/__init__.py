# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The niftyfit module provides classes for interfacing with the `NiftyFit`_
command line tools.

Top-level namespace for niftyfit.
"""

from .asl import FitAsl
from .dwi import FitDwi, DwiTool
from .qt1 import FitQt1
