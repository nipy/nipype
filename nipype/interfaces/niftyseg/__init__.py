# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The niftyseg module provides classes for interfacing with the `NIFTYSEG
<https://sourceforge.net/projects/niftyseg/>`_ command line tools.

Top-level namespace for niftyseg.
"""

from .base import no_niftyseg, get_custom_path
from .maths import (UnaryMaths, BinaryMaths, BinaryMathsInteger,
                    Merge, TupleMaths)
from .stats import UnaryStats, BinaryStats
from .steps import STEPS, CalcTopNCC
from .patchmatch import PatchMatch
from .lesions import FillLesions
from .em import EM
