# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The QT1 module of niftyfit, which wraps the Multi-Echo T1 fitting methods in NiftyFit.
"""

from nipype.interfaces.niftyfit.base import getNiftyFitPath,NIFTYFITCommandInputSpec, NIFTYFITCommand
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)

#-----------------------------------------------------------
# FitAsl wrapper interface
#-----------------------------------------------------------

# Input spec
class FitQt1InputSpec(NIFTYFITCommandInputSpec):

    source_file = File(exists=True, desc='Filename of the 4D Multi-Echo T1 source image (mandatory)',
                       argstr='-source %s', mandatory=True)

# *** Output options:
    t1map = File(genfile=True, exists=True, desc='Filename of the estimated output T1 map (in ms).',
                 argstr='-t1map %s', name_source=['source_file'], name_template='%s_t1map')
    m0map = File(genfile=True, exists=True, desc='Filename of the estimated input M0 map.',
                 argstr='-m0map %s', name_source=['source_file'], name_template='%s_m0map')
    mcmap = File(genfile=True, exists=True, desc='Filename of the estimated output multi-parameter map.',
                 argstr='-mcmap %s', name_source=['source_file'], name_template='%s_mcmap')
    error_file = File(genfile=True, exists=True, desc='Filename of the error map (symmetric matrix, [Diag,OffDiag]).',
                      argstr='-error %s', name_source=['source_file'], name_template='%s_error')
    syn_file = File(genfile=True, exists=True, desc='Filename of the synthetic ASL data.',
                    argstr='-syn %s', name_source=['source_file'], name_template='%s_syn')
    res_file = File(genfile=True, exists=True, desc='Filename of the model fit residuals',
                    argstr='-res %s', name_source=['source_file'], name_template='%s_res')

# *** Experimental options (Choose those suitable for the model!):
    mask = File(exists=True, desc='Filename of image mask.',
                argstr='-mask %s')
    prior = File(exists=True, desc='Filename of parameter prior.',
                 argstr='-prior %s')
    TE = traits.Float(desc='TE Echo Time [0ms!].', argstr='-TE %f')
    TR = traits.Float(desc='TR Repetition Time [10s!].', argstr='-TR %f')

# IR options:

    SR = traits.Bool(desc='Saturation Recovery fitting [default].', argstr='-SR')
    IR = traits.Bool(desc='Inversion Recovery fitting [default].', argstr='-SR')
    T1s = traits.ListFloat(desc='Inversion times for T1 data as a list (in s)', argstr='-T1s %f %f %f')
    T1Lists = traits.File(exists=True, desc='Filename of list of pre-defined TIs', argstr='-T1List %s')

# SPGR options
    SPGR = traits.Bool(desc='Spoiled Gradient Echo fitting', argstr='-SPGR')

# Output spec
class FitQt1OutputSpec(TraitedSpec):
    t1map = File(exists=True, desc='Filename of the estimated output T1 map (in ms)')
    m0map = File(exists=True, desc='Filename of the m0 map')
    mcmap = File(exists=True, desc='Filename of the estimated output multi-parameter map')
    error_file = File(exists=True, desc='Filename of the error map (symmetric matrix, [Diag,OffDiag])')
    syn_file = File(exists=True, desc='Filename of the synthetic ASL data')
    res_file = File(exists=True, desc='Filename of the model fit residuals')

# FitAsl function
class FitQt1(NIFTYFITCommand):
    """ Use NiftyFit to perform ASL fitting.
    
    Examples
    --------
    
    >>> from nipype.interfaces import niftyfit
    """
    _cmd = getNiftyFitPath('fit_qt1')
    input_spec = FitQt1InputSpec
    output_spec = FitQt1OutputSpec
    
    _suffix = '_fit_qt1'
