# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The QT1 module of niftyfit, which wraps the Multi-Echo T1 fitting methods
in NiftyFit.
"""

from nipype.interfaces.niftyfit.base import get_custom_path, NiftyFitCommand
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    CommandLineInputSpec)

# -----------------------------------------------------------
# FitAsl wrapper interface
# -----------------------------------------------------------


# Input spec
class FitQt1InputSpec(CommandLineInputSpec):
    source_file = File(exists=True, desc='Filename of the 4D Multi-Echo T1 \
source image (mandatory)', argstr='-source %s', mandatory=True, position=2)

    # *** Output options:
    t1map = File(genfile=True, argstr='-t1map %s',
                 desc='Filename of the estimated output T1 map (in ms).')
    m0map = File(genfile=True, argstr='-m0map %s',
                 desc='Filename of the estimated input M0 map.')
    mcmap = File(genfile=True, argstr='-mcmap %s',
                 desc='Filename of the estimated output multi-parameter map.')
    error_file = File(genfile=True, argstr='-error %s',
                      desc='Filename of the error map (symmetric matrix, [Diag,OffDiag]).')
    syn_file = File(genfile=True, argstr='-syn %s',
                    desc='Filename of the synthetic ASL data.')
    res_file = File(genfile=True, argstr='-res %s',
                    desc='Filename of the model fit residuals')

    # *** Experimental options (Choose those suitable for the model!):
    mask = File(exists=True, desc='Filename of image mask.',
                argstr='-mask %s')
    prior = File(exists=True, desc='Filename of parameter prior.',
                 argstr='-prior %s')
    TE = traits.Float(desc='TE Echo Time [0ms!].', argstr='-TE %f')
    TR = traits.Float(desc='TR Repetition Time [10s!].', argstr='-TR %f')

    # IR options:

    SR = traits.Bool(desc='Saturation Recovery fitting [default].',
                     argstr='-SR')
    IR = traits.Bool(desc='Inversion Recovery fitting [default].',
                     argstr='-SR')
    TIs = traits.List(traits.Float, minlen=3, maxlen=3,
                      desc='Inversion times for T1 data as a list (in s)',
                      argstr='-TIs %s', sep=' ')
    T1Lists = traits.File(exists=True, argstr='-T1List %s',
                          desc='Filename of list of pre-defined TIs')

    # SPGR options
    SPGR = traits.Bool(desc='Spoiled Gradient Echo fitting', argstr='-SPGR')


# Output spec
class FitQt1OutputSpec(TraitedSpec):
    t1map = File(desc='Filename of the estimated output T1 map (in ms)')
    m0map = File(desc='Filename of the m0 map')
    mcmap = File(desc='Filename of the estimated output multi-parameter map')
    error_file = File(desc='Filename of the error map (symmetric matrix, [Diag,OffDiag])')
    syn_file = File(desc='Filename of the synthetic ASL data')
    res_file = File(desc='Filename of the model fit residuals')


# FitAsl function
class FitQt1(NiftyFitCommand):
    """ Use NiftyFit to perform ASL fitting.

    Examples
    --------

    >>> from nipype.interfaces import niftyfit
    """
    _cmd = get_custom_path('fit_qt1')
    input_spec = FitQt1InputSpec
    output_spec = FitQt1OutputSpec

    _suffix = '_fit_qt1'

    def _gen_filename(self, name):
        if name == 't1map':
            return self._gen_fname(self.inputs.source_file, suffix='_t1map', ext='.nii.gz')
        if name == 'm0map':
            return self._gen_fname(self.inputs.source_file, suffix='_m0map', ext='.nii.gz')
        if name == 'mcmap':
            return self._gen_fname(self.inputs.source_file, suffix='_mcmap', ext='.nii.gz')
        if name == 'error_file':
            return self._gen_fname(self.inputs.source_file, suffix='_error', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file, suffix='_syn', ext='.nii.gz')
        if name == 'res_file':
            return self._gen_fname(self.inputs.source_file, suffix='_res', ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.t1map):
            outputs['t1map'] = self.inputs.t1map
        else:
            outputs['t1map'] = self._gen_filename('t1map')

        if isdefined(self.inputs.m0map):
            outputs['m0map'] = self.inputs.m0map
        else:
            outputs['m0map'] = self._gen_filename('m0map')

        if isdefined(self.inputs.mcmap):
            outputs['mcmap'] = self.inputs.mcmap
        else:
            outputs['mcmap'] = self._gen_filename('mcmap')

        if isdefined(self.inputs.error_file):
            outputs['error_file'] = self.inputs.error_file
        else:
            outputs['error_file'] = self._gen_filename('error_file')

        if isdefined(self.inputs.syn_file):
            outputs['syn_file'] = self.inputs.syn_file
        else:
            outputs['syn_file'] = self._gen_filename('syn_file')

        if isdefined(self.inputs.res_file):
            outputs['res_file'] = self.inputs.res_file
        else:
            outputs['res_file'] = self._gen_filename('res_file')

        return outputs


