# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The BROCCOLI module provides classes for interfacing with the `BROCCOLI
<http://github.com/wanderine/BROCCOLI>`_ command line tools.  

Top-level namespace for BROCCOLI.
"""

from .base import (BROCCOLICommand, Info)
from .preprocess import (RegisterTwoVolumes)
from .utils import (GetOpenCLInfo)

