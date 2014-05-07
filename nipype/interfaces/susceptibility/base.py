# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The susceptibility module provides for classes for interfacing with 
    the susceptivility tools provides by Pankaj Daga.
    
    These are the base tools for working with the susceptibility tools,
    the interface to all the tools is contained in susceptibility_tools.py
    
    Currently these tools are supported:
    
    * gen_fm : Generate a fieldmap
    * pm_scale : Scale a phase image
    *
    
    Examples
    --------
    See the docstrings of the individual classes for examples.
    
    """

import os
import warnings
from exceptions import NotImplementedError

from ...utils.filemanip import fname_presuffix
from ..base import (CommandLine, traits, CommandLineInputSpec, isdefined)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Info(object):
    """Handle fsl output type and version information.
        
        version refers to the version of fsl on the system
        
        output type refers to the type of file fsl defaults to writing
        eg, NIFTI, NIFTI_GZ
        
        """
    
    ftypes = {'NIFTI': '.nii',
        'NIFTI_PAIR': '.img',
        'NIFTI_GZ': '.nii.gz',
        'NIFTI_PAIR_GZ': '.img.gz'}
    
    @staticmethod
    def version():
        """Check for susceptibility tools version on system
            
            Parameters
            ----------
            None
            
            Returns
            -------
            version : str
            Version number as string or None if niftyreg not found
            
            """
        raise NotImplementedError("Waiting for Susceptibility tools version fix before "
                                  "implementing this")
    
    @classmethod
    def output_type_to_ext(cls, output_type):
        """Get the file extension for the given output type.
            
            Parameters
            ----------
            output_type : {'NIFTI', 'NIFTI_GZ', 'NIFTI_PAIR', 'NIFTI_PAIR_GZ'}
            String specifying the output type.
            
            Returns
            -------
            extension : str
            The file extension for the output type.
            """
        
        try:
            return cls.ftypes[output_type]
        except KeyError:
            msg = 'Invalid SusceptibilityToolsOutputType: ', output_type
            raise KeyError(msg)

class SusceptibilityToolsCommandInputSpec(CommandLineInputSpec):
    """
        Base Input Specification for all NiftyReg Commands
        
        All command support specifying the output type dynamically
        via output_type.
        """
    output_type = traits.Enum('NIFTI_GZ', Info.ftypes.keys(),
                              desc='SusceptibilityTools output type')

def no_susceptibility_tools():
    """Checks if niftyreg is NOT installed
        """
    raise NotImplementedError("Waiting for version fix")
