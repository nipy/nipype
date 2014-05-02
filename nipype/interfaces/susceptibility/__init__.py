# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The niftyseg module provides classes for interfacing with the `NIFTYSEG
<http://www.fmrib.ox.ac.uk/niftyseg/index.html>`_ command line tools.

Top-level namespace for niftyseg.
"""

from .base import (NIFTYSEGCommand, Info, check_niftyseg, no_niftyseg, no_niftyseg_course_data)
from .maths import ( UnaryMaths, BinaryMaths)
from .stats import ( UnaryStats, BinaryStats)
from .gif import ( Gif )
