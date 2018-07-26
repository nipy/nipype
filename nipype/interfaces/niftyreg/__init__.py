# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The niftyreg module provides classes for interfacing with the `NiftyReg
<http://sourceforge.net/projects/niftyreg/>`_ command line tools.

Top-level namespace for niftyreg.
"""

from .base import get_custom_path
from .reg import RegAladin, RegF3D
from .regutils import (RegResample, RegJacobian, RegAverage, RegTools,
                       RegTransform, RegMeasure)
