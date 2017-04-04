# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The QT1 module of niftyfit, which wraps the Multi-Echo T1 fitting methods
in NiftyFit.

Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

from ..base import TraitedSpec, File, traits, isdefined, CommandLineInputSpec
from .base import get_custom_path, NiftyFitCommand


class FitQt1InputSpec(CommandLineInputSpec):
    """ Input Spec for FitQt1. """
    desc = 'Filename of the 4D Multi-Echo T1 source image.'
    source_file = File(position=1,
                       exists=True,
                       desc=desc,
                       argstr='-source %s',
                       mandatory=True)

    # Output options:
    t1map_file = File(genfile=True,
                      argstr='-t1map %s',
                      desc='Filename of the estimated output T1 map (in ms).')
    m0map_file = File(genfile=True,
                      argstr='-m0map %s',
                      desc='Filename of the estimated input M0 map.')
    desc = 'Filename of the estimated output multi-parameter map.'
    mcmap_file = File(genfile=True,
                      argstr='-mcmap %s',
                      desc=desc)
    comp_file = File(genfile=True,
                     argstr='-comp %s',
                     desc='Filename of the estimated multi-component T1 map.')
    desc = 'Filename of the error map (symmetric matrix, [Diag,OffDiag]).'
    error_file = File(genfile=True,
                      argstr='-error %s',
                      desc=desc)
    syn_file = File(genfile=True,
                    argstr='-syn %s',
                    desc='Filename of the synthetic ASL data.')
    res_file = File(genfile=True,
                    argstr='-res %s',
                    desc='Filename of the model fit residuals')

    # Other options:
    mask = File(position=2,
                exists=True,
                desc='Filename of image mask.',
                argstr='-mask %s')
    prior = File(position=3,
                 exists=True,
                 desc='Filename of parameter prior.',
                 argstr='-prior %s')
    te_value = traits.Float(desc='TE Echo Time [0ms!].', argstr='-TE %f',
                            position=4)
    tr_value = traits.Float(desc='TR Repetition Time [10s!].', argstr='-TR %f',
                            position=5)
    desc = 'Number of components to fit [1] (currently IR/SR only)'
    # set position to be ahead of TIs
    nb_comp = traits.Int(desc=desc, position=6, argstr='-nc %d')
    desc = 'Set LM parameters (initial value, decrease rate) [100,1.2].'
    lm_val = traits.Tuple(traits.Float, traits.Float,
                          desc=desc, argstr='-lm %f %f', position=7)
    desc = 'Use Gauss-Newton algorithm [Levenberg-Marquardt].'
    gn_flag = traits.Bool(desc=desc, argstr='-gn', position=8)
    slice_no = traits.Int(desc='Fit to single slice number.',
                          argstr='-slice %d', position=9)
    voxel = traits.Tuple(traits.Int, traits.Int, traits.Int,
                         desc='Fit to single voxel only.',
                         argstr='-voxel %d %d %d', position=10)
    maxit = traits.Int(desc='NLSQR iterations [100].', argstr='-maxit %d',
                       position=11)

    # IR options:
    sr_flag = traits.Bool(desc='Saturation Recovery fitting [default].',
                          argstr='-SR', position=12)
    ir_flag = traits.Bool(desc='Inversion Recovery fitting [default].',
                          argstr='-IR', position=13)
    tis = traits.List(traits.Float,
                      position=14,
                      desc='Inversion times for T1 data [1s,2s,5s].',
                      argstr='-TIs %s',
                      sep=' ')
    tis_list = traits.File(exists=True,
                           argstr='-TIlist %s',
                           desc='Filename of list of pre-defined TIs.')
    t1_list = traits.File(exists=True,
                          argstr='-T1list %s',
                          desc='Filename of list of pre-defined T1s')
    t1min = traits.Float(desc='Minimum tissue T1 value [400ms].',
                         argstr='-T1min %f')
    t1max = traits.Float(desc='Maximum tissue T1 value [4000ms].',
                         argstr='-T1max %f')

    # SPGR options
    spgr = traits.Bool(desc='Spoiled Gradient Echo fitting', argstr='-SPGR')
    flips = traits.List(traits.Float,
                        desc='Flip angles',
                        argstr='-flips %s',
                        sep=' ')
    desc = 'Filename of list of pre-defined flip angles (deg).'
    flips_list = traits.File(exists=True,
                             argstr='-fliplist %s',
                             desc=desc)
    desc = 'Filename of B1 estimate for fitting (or include in prior).'
    b1map = traits.File(exists=True,
                        argstr='-b1map %s',
                        desc=desc)

    # MCMC options:
    mcout = traits.File(exists=True,
                        desc='Filename of mc samples (ascii text file)',
                        argstr='-mcout %s')
    mcsamples = traits.Int(desc='Number of samples to keep [100].',
                           argstr='-mcsamples %d')
    mcmaxit = traits.Int(desc='Number of iterations to run [10,000].',
                         argstr='-mcmaxit %d')
    acceptance = traits.Float(desc='Fraction of iterations to accept [0.23].',
                              argstr='-acceptance %f')


class FitQt1OutputSpec(TraitedSpec):
    """ Output Spec for FitQt1. """
    t1map_file = File(desc='Filename of the estimated output T1 map (in ms)')
    m0map_file = File(desc='Filename of the m0 map')
    desc = 'Filename of the estimated output multi-parameter map'
    mcmap_file = File(desc=desc)
    comp_file = File(desc='Filename of the estimated multi-component T1 map.')
    desc = 'Filename of the error map (symmetric matrix, [Diag,OffDiag])'
    error_file = File(desc=desc)
    syn_file = File(desc='Filename of the synthetic ASL data')
    res_file = File(desc='Filename of the model fit residuals')


class FitQt1(NiftyFitCommand):
    """Interface for executable fit_qt1 from Niftyfit platform.

    Use NiftyFit to perform Qt1 fitting.

    T1 Fitting Routine (To inversion recovery or spgr data).
    Fits single component T1 maps in the first instance.

    For source code, see https://cmiclab.cs.ucl.ac.uk/CMIC/NiftyFit-Release

    Examples
    --------

    >>> from nipype.interfaces.niftyfit import FitQt1
    >>> fit_qt1 = FitQt1()
    >>> fit_qt1.inputs.source_file = 'TI4D.nii.gz'
    >>> fit_qt1.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'fit_qt1 -source TI4D.nii.gz -comp .../TI4D_comp.nii.gz \
-error .../TI4D_error.nii.gz -m0map .../TI4D_m0map.nii.gz \
-mcmap .../TI4D_mcmap.nii.gz -res .../TI4D_res.nii.gz \
-syn .../TI4D_syn.nii.gz -t1map .../TI4D_t1map.nii.gz'

    """
    _cmd = get_custom_path('fit_qt1')
    input_spec = FitQt1InputSpec
    output_spec = FitQt1OutputSpec
    _suffix = '_fit_qt1'

    def _gen_filename(self, name):
        if name == 't1map_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_t1map', ext='.nii.gz')
        if name == 'm0map_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_m0map', ext='.nii.gz')
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'comp_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_comp', ext='.nii.gz')
        if name == 'error_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_error', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'res_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_res', ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.t1map_file):
            outputs['t1map_file'] = self.inputs.t1map_file
        else:
            outputs['t1map_file'] = self._gen_filename('t1map_file')

        if isdefined(self.inputs.m0map_file):
            outputs['m0map_file'] = self.inputs.m0map_file
        else:
            outputs['m0map_file'] = self._gen_filename('m0map_file')

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

        if isdefined(self.inputs.comp_file):
            outputs['comp_file'] = self.inputs.comp_file
        else:
            outputs['comp_file'] = self._gen_filename('comp_file')

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
