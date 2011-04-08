# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The Camino2Trackvis module provides classes for interfacing with the Camino2Trackvis Diffusion Toolbox
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import CommandLine, traits, CommandLineInputSpec
from nipype.utils.misc import isdefined
