# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
NiftyFit is a software package for multi-parametric model-fitting of 4D MRI.

The niftyfit module provides classes for interfacing with the `NiftyFit
<https://cmiclab.cs.ucl.ac.uk/CMIC/NiftyFit-Release>`__ command line tools.

"""
from .asl import FitAsl
from .dwi import FitDwi, DwiTool
from .qt1 import FitQt1
