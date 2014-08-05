# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The niftyreg module provides classes for interfacing with the `NiftyFit`_ command line tools.

Top-level namespace for niftyfit
"""

from .base import (Info)
from .dwi import (FitDwi, DwiTool)
from .asl import (FitAsl)
