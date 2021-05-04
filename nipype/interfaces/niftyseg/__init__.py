# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The niftyseg module provides classes for interfacing with the `NIFTYSEG
<https://sourceforge.net/projects/niftyseg/>`_ command line tools.

Top-level namespace for niftyseg.
"""

from .em import EM
from .label_fusion import LabelFusion, CalcTopNCC
from .lesions import FillLesions
from .maths import UnaryMaths, BinaryMaths, BinaryMathsInteger, TupleMaths, Merge
from .patchmatch import PatchMatch
from .stats import UnaryStats, BinaryStats
