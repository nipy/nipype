# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ASL module of niftyfit, which wraps the fitting methods in NiftyFit.
"""

from nipype.interfaces.niftyfit.base import NIFTYFITCommandInputSpec, NIFTYFITCommand
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)

#-----------------------------------------------------------
# FitAsl wrapper interface
#-----------------------------------------------------------

# Input spec
class FitAslInputSpec(NIFTYFITCommandInputSpec):
    source_file = File(exists=True, desc='The source 4D image containing the ASL data',
                   argstr='-source %s', mandatory=True)

# Output spec
class FitAslOutputSpec(TraitedSpec):

# FitAsl function
class FitAsl(NIFTYFITCommand):
    """ Use NiftyFit to perform ASL fitting.
    
    Examples
    --------
    
    >>> from nipype.interfaces import niftyfit
    """
    _cmd = 'fit_asl'
    input_spec = FitAslInputSpec
    output_spec = FitAslOutputSpec
    
    _suffix = '_fit_asl'
