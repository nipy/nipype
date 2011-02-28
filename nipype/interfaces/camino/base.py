# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The Camino module provides classes for interfacing with the Camino Diffusion Toolbox
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
    """Handle camino info
    """

class CaminoCommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all FSL Commands

    All command support specifying FSLOUTPUTTYPE dynamically
    via output_type.
    
    Example
    -------
    fsl.ExtractRoi(tmin=42, tsize=1, output_type='NIFTI')
    
    output_type =  traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='FSL output type')
	"""
    
class CaminoCommand(CommandLine):
    """Base support for Camino commands.
    
    """
    
input_spec = CaminoCommandInputSpec
    #_output_type = None

#    def __init__(self):
#        super(CaminoCommand, self)

def __init__(self, **inputs):
        super(CaminoCommand, self).__init__(**inputs)
