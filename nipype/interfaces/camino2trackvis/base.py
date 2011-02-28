# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The Camino2Trackvis module provides classes for interfacing with the Camino-Trackvis conversion toolbox
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import CommandLine, traits, CommandLineInputSpec
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class Info(object):
    """Handle camino2trackvis info
    """

class Camino2TrackvisCommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all Camino2Trackvis Commands

	"""
    
class Camino2TrackvisCommand(CommandLine):
    """Base support for Camino2Trackvis commands.
    
    """
    
input_spec = Camino2TrackvisCommandInputSpec

def __init__(self, **inputs):
        super(Camino2TrackvisCommand, self).__init__(**inputs)
