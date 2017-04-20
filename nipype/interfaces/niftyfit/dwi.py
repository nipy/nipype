# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The dwi module of niftyfit, which wraps the fitting methods in NiftyFit.

Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

from ..base import TraitedSpec, traits, isdefined, CommandLineInputSpec
from .base import NiftyFitCommand, get_custom_path


class FitDwiInputSpec(CommandLineInputSpec):
    """ Input Spec for FitDwi. """
    # Inputs options
    source_file = traits.File(position=1,
                              exists=True,
                              argstr='-source %s',
                              mandatory=True,
                              desc='The source image containing the dwi data.')
    desc = 'The file containing the bvalues of the source DWI.'
    bval_file = traits.File(position=2,
                            exists=True,
                            argstr='-bval %s',
                            mandatory=True,
                            desc=desc)
    desc = 'The file containing the bvectors of the source DWI.'
    bvec_file = traits.File(position=3,
                            exists=True,
                            argstr='-bvec %s',
                            mandatory=True,
                            desc=desc)
    te_file = traits.File(exists=True,
                          argstr='-TE %s',
                          desc='Filename of TEs (ms).',
                          xor=['te_file'])
    te_value = traits.File(exists=True,
                           argstr='-TE %s',
                           desc='Value of TEs (ms).',
                           xor=['te_file'])
    mask_file = traits.File(exists=True,
                            desc='The image mask',
                            argstr='-mask %s')
    desc = 'Filename of parameter priors for -ball and -nod.'
    prior_file = traits.File(exists=True,
                             argstr='-prior %s',
                             desc=desc)
    desc = 'Rotate the output tensors according to the q/s form of the image \
(resulting tensors will be in mm coordinates, default: 0).'
    rot_sform_flag = traits.Int(desc=desc,
                                argstr='-rotsform %d')

    # generic output options:
    error_file = traits.File(desc='Filename of parameter error maps.',
                             argstr='-error %s',
                             genfile=True)
    res_file = traits.File(desc='Filename of model residual map.',
                           argstr='-res %s',
                           genfile=True)
    syn_file = traits.File(desc='Filename of synthetic image.',
                           argstr='-syn %s',
                           genfile=True)
    nodiff_file = traits.File(desc='Filename of average no diffusion image.',
                              argstr='-nodiff %s',
                              genfile=True)

    # Output options, with templated output names based on the source image
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc,
                             argstr='-mcmap %s',
                             requires=['nodv_flag'],
                             genfile=True)

    # Model Specific Output options:
    mdmap_file = traits.File(desc='Filename of MD map/ADC',
                             argstr='-mdmap %s',
                             genfile=True)
    famap_file = traits.File(desc='Filename of FA map',
                             argstr='-famap %s',
                             genfile=True)
    v1map_file = traits.File(desc='Filename of PDD map [x,y,z]',
                             argstr='-v1map %s',
                             genfile=True)
    rgbmap_file = traits.File(desc='Filename of colour-coded FA map',
                              argstr='-rgbmap %s',
                              genfile=True,
                              requires=['dti_flag'])

    desc = 'Use lower triangular (tenmap2) or diagonal, off-diagonal tensor \
format'
    ten_type = traits.Enum('lower-tri', 'diag-off-diag', desc=desc,
                           usedefault=True)

    tenmap_file = traits.File(desc='Filename of tensor map [diag,offdiag].',
                              argstr='-tenmap %s',
                              genfile=True,
                              requires=['dti_flag'])
    tenmap2_file = traits.File(desc='Filename of tensor map [lower tri]',
                               argstr='-tenmap2 %s',
                               genfile=True,
                               requires=['dti_flag'])
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod).'
    mcmap_file = traits.File(desc=desc,
                             argstr='-mcmap %s',
                             genfile=True)

    # Methods options
    desc = 'Fit single exponential to non-directional data [default with \
no b-vectors]'
    mono_flag = traits.Bool(desc=desc,
                            argstr='-mono',
                            position=4,
                            xor=['ivim_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    ivim_flag = traits.Bool(desc='Fit IVIM model to non-directional data.',
                            argstr='-ivim',
                            position=4,
                            xor=['mono_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    desc = 'Fit the tensor model [default with b-vectors].'
    dti_flag = traits.Bool(desc=desc,
                           argstr='-dti',
                           position=4,
                           xor=['mono_flag', 'ivim_flag', 'ball_flag',
                                'ballv_flag', 'nod_flag', 'nodv_flag'])
    ball_flag = traits.Bool(desc='Fit the ball and stick model.',
                            argstr='-ball',
                            position=4,
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    desc = 'Fit the ball and stick model with optimised PDD.'
    ballv_flag = traits.Bool(desc=desc,
                             argstr='-ballv',
                             position=4,
                             xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                  'ball_flag', 'nod_flag', 'nodv_flag'])
    nod_flag = traits.Bool(desc='Fit the NODDI model',
                           argstr='-nod',
                           position=4,
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'ball_flag', 'ballv_flag', 'nodv_flag'])
    nodv_flag = traits.Bool(desc='Fit the NODDI model with optimised PDD',
                            argstr='-nodv',
                            position=4,
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ball_flag', 'ballv_flag', 'nod_flag'])

    # Experimental options
    desc = 'Maximum number of non-linear LSQR iterations [100x2 passes])'
    maxit_val = traits.Int(desc=desc, argstr='-maxit %d', requires=['gn_flag'])
    desc = 'LM parameters (initial value, decrease rate) [100,1.2].'
    lm_vals = traits.Tuple(traits.Float, traits.Float,
                           argstr='-lm %f %f',
                           requires=['gn_flag'],
                           desc=desc)
    desc = 'Use Gauss-Newton algorithm [Levenberg-Marquardt].'
    gn_flag = traits.Bool(desc=desc, argstr='-gn', xor=['wls_flag'])
    desc = 'Use Variational Bayes fitting with known prior (currently \
identity covariance...).'
    vb_flag = traits.Bool(desc=desc, argstr='-vb')
    cov_file = traits.File(exists=True,
                           desc='Filename of ithe nc*nc covariance matrix [I]',
                           argstr='-cov %s')
    wls_flag = traits.Bool(desc=desc, argstr='-wls', xor=['gn_flag'])
    desc = 'Use location-weighted least squares for DTI fitting [3x3 Gaussian]'
    swls_val = traits.Float(desc=desc, argstr='-swls %f')
    slice_no = traits.Int(desc='Fit to single slice number.',
                          argstr='-slice %d')
    voxel = traits.Tuple(traits.Int, traits.Int, traits.Int,
                         desc='Fit to single voxel only.',
                         argstr='-voxel %d %d %d')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]',
                            argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].',
                           argstr='-dpr %f')
    wm_t2_val = traits.Float(desc='White matter T2 value [80ms].',
                             argstr='-wmT2 %f')
    csf_t2_val = traits.Float(desc='CSF T2 value [400ms].',
                              argstr='-csfT2 %f')
    desc = 'Threshold for perfusion/diffsuion effects [100].'
    perf_thr = traits.Float(desc=desc, argstr='-perfthreshold %f')

    # MCMC options:
    mcout = traits.File(exists=True,
                        desc='Filename of mc samples (ascii text file)',
                        argstr='-mcout %s')
    mcsamples = traits.Int(desc='Number of samples to keep [100].',
                           argstr='-mcsamples %d')
    mcmaxit = traits.Int(desc='Number of iterations to run [10,000].',
                         argstr='-mcmaxit %d')
    acceptance = traits.Float(desc='Fraction of iterations to accept [0.23].',
                              argstr='-accpetance %f')


class FitDwiOutputSpec(TraitedSpec):
    """ Output Spec for FitDwi. """
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc)
    error_file = traits.File(desc='Filename of parameter error maps')
    res_file = traits.File(desc='Filename of model residual map')
    syn_file = traits.File(desc='Filename of synthetic image')
    nodiff_file = traits.File(desc='Filename of average no diffusion image.')
    mdmap_file = traits.File(desc='Filename of MD map/ADC')
    famap_file = traits.File(desc='Filename of FA map')
    v1map_file = traits.File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = traits.File(desc='Filename of colour FA map')
    tenmap_file = traits.File(desc='Filename of tensor map')
    tenmap2_file = traits.File(desc='Filename of tensor map [lower tri]')
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod).'
    mcmap_file = traits.File(desc=desc)
    mcout = traits.File(desc='Filename of mc samples (ascii text file)')


class FitDwi(NiftyFitCommand):
    """Interface for executable fit_dwi from Niftyfit platform.

    Use NiftyFit to perform diffusion model fitting.

    Diffusion-weighted MR Fitting.
    Fits DWI parameter maps to multi-shell, multi-directional data.

    For source code, see https://cmiclab.cs.ucl.ac.uk/CMIC/NiftyFit-Release

    Examples
    --------

    >>> from nipype.interfaces import niftyfit
    >>> fit_dwi = niftyfit.FitDwi(dti_flag=True)
    >>> fit_dwi.inputs.source_file = 'dwi.nii.gz'
    >>> fit_dwi.inputs.bvec_file = 'bvecs'
    >>> fit_dwi.inputs.bval_file = 'bvals'
    >>> fit_dwi.inputs.rgbmap_file = 'rgb.nii.gz'
    >>> fit_dwi.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'fit_dwi -source dwi.nii.gz -bval bvals -bvec bvecs -dti \
-error .../dwi_error.nii.gz -famap .../dwi_famap.nii.gz \
-mcmap .../dwi_mcmap.nii.gz -mdmap .../dwi_mdmap.nii.gz \
-nodiff .../dwi_no_diff.nii.gz -res .../dwi_resmap.nii.gz \
-rgbmap rgb.nii.gz -syn .../dwi_syn.nii.gz -tenmap2 .../dwi_tenmap2.nii.gz  \
-v1map .../dwi_v1map.nii.gz'

    """
    _cmd = get_custom_path('fit_dwi')
    input_spec = FitDwiInputSpec
    output_spec = FitDwiOutputSpec
    _suffix = '_fit_dwi'

    def _format_arg(self, name, trait_spec, value):
        if name == 'tenmap_file' and self.inputs.ten_type != 'diag-off-diag':
            return ""
        if name == 'tenmap2_file' and self.inputs.ten_type != 'lower-tri':
            return ""
        return super(FitDwi, self)._format_arg(name, trait_spec, value)

    def _gen_filename(self, name):
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'error_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_error', ext='.nii.gz')
        if name == 'res_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_resmap', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'nodiff_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_no_diff', ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mdmap', ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_famap', ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_v1map', ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_rgbmap', ext='.nii.gz')
        if name == 'tenmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_tenmap', ext='.nii.gz')
        if name == 'tenmap2_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_tenmap2', ext='.nii.gz')
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'mcout':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mcout', ext='.txt')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

        if isdefined(self.inputs.error_file):
            outputs['error_file'] = self.inputs.error_file
        else:
            outputs['error_file'] = self._gen_filename('error_file')

        if isdefined(self.inputs.res_file):
            outputs['res_file'] = self.inputs.res_file
        else:
            outputs['res_file'] = self._gen_filename('res_file')

        if isdefined(self.inputs.syn_file):
            outputs['syn_file'] = self.inputs.syn_file
        else:
            outputs['syn_file'] = self._gen_filename('syn_file')

        if isdefined(self.inputs.mdmap_file):
            outputs['mdmap_file'] = self.inputs.mdmap_file
        else:
            outputs['mdmap_file'] = self._gen_filename('mdmap_file')

        if isdefined(self.inputs.famap_file):
            outputs['famap_file'] = self.inputs.famap_file
        else:
            outputs['famap_file'] = self._gen_filename('famap_file')

        if isdefined(self.inputs.v1map_file):
            outputs['v1map_file'] = self.inputs.v1map_file
        else:
            outputs['v1map_file'] = self._gen_filename('v1map_file')

        if isdefined(self.inputs.rgbmap_file):
            outputs['rgbmap_file'] = self.inputs.rgbmap_file
        else:
            outputs['rgbmap_file'] = self._gen_filename('rgbmap_file')

        if isdefined(self.inputs.tenmap_file):
            outputs['tenmap_file'] = self.inputs.tenmap_file
        else:
            outputs['tenmap_file'] = self._gen_filename('tenmap_file')

        if isdefined(self.inputs.tenmap2_file):
            outputs['tenmap2_file'] = self.inputs.tenmap2_file
        else:
            outputs['tenmap2_file'] = self._gen_filename('tenmap2_file')

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

        if isdefined(self.inputs.mcout):
            outputs['mcout'] = self.inputs.mcout
        else:
            outputs['mcout'] = self._gen_filename('mcout')

        return outputs


class DwiToolInputSpec(CommandLineInputSpec):
    """ Input Spec for DwiTool. """
    desc = 'The source image containing the fitted model.'
    source_file = traits.File(position=1,
                              exists=True,
                              desc=desc,
                              argstr='-source %s',
                              mandatory=True)
    desc = 'The file containing the bvalues of the source DWI.'
    bval_file = traits.File(position=2,
                            exists=True,
                            desc=desc,
                            argstr='-bval %s',
                            mandatory=True)
    desc = 'The file containing the bvectors of the source DWI.'
    bvec_file = traits.File(position=3,
                            exists=True,
                            desc=desc,
                            argstr='-bvec %s')
    b0_file = traits.File(position=4,
                          exists=True,
                          desc='The B0 image corresponding to the source DWI',
                          argstr='-b0 %s')
    mask_file = traits.File(position=5,
                            exists=True,
                            desc='The image mask',
                            argstr='-mask %s')

    # Output options, with templated output names based on the source image
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc,
                             argstr='-mcmap %s',
                             genfile=True)
    desc = 'Filename of synthetic image. Requires: bvec_file/b0_file.'
    syn_file = traits.File(desc=desc,
                           argstr='-syn %s',
                           requires=['bvec_file', 'b0_file'],
                           genfile=True)
    mdmap_file = traits.File(desc='Filename of MD map/ADC',
                             argstr='-mdmap %s',
                             genfile=True)
    famap_file = traits.File(desc='Filename of FA map',
                             argstr='-famap %s',
                             genfile=True)
    v1map_file = traits.File(desc='Filename of PDD map [x,y,z]',
                             argstr='-v1map %s',
                             genfile=True)
    rgbmap_file = traits.File(desc='Filename of colour FA map.',
                              argstr='-rgbmap %s',
                              requires=['dti_flag'],
                              genfile=True)
    logdti_file = traits.File(desc='Filename of output logdti map.',
                              argstr='-logdti2 %s',
                              requires=['dti_flag'],
                              genfile=True)

    # Methods options
    desc = 'Input is a single exponential to non-directional data \
[default with no b-vectors]'
    mono_flag = traits.Bool(desc=desc,
                            position=6,
                            argstr='-mono',
                            xor=['ivim_flag', 'dti_flag', 'dti_flag2',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    desc = 'Inputs is an IVIM model to non-directional data.'
    ivim_flag = traits.Bool(desc=desc,
                            position=6,
                            argstr='-ivim',
                            xor=['mono_flag', 'dti_flag', 'dti_flag2',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    dti_flag = traits.Bool(desc='Input is a tensor model diag/off-diag.',
                           position=6,
                           argstr='-dti',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag2',
                                'ball_flag', 'ballv_flag', 'nod_flag',
                                'nodv_flag'])
    dti_flag2 = traits.Bool(desc='Input is a tensor model lower triangular',
                            position=6,
                            argstr='-dti2',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    ball_flag = traits.Bool(desc='Input is a ball and stick model.',
                            position=6,
                            argstr='-ball',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'dti_flag2', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    desc = 'Input is a ball and stick model with optimised PDD.'
    ballv_flag = traits.Bool(desc=desc,
                             position=6,
                             argstr='-ballv',
                             xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                  'dti_flag2', 'ball_flag', 'nod_flag',
                                  'nodv_flag'])
    nod_flag = traits.Bool(desc='Input is a NODDI model',
                           position=6,
                           argstr='-nod',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'dti_flag2', 'ball_flag', 'ballv_flag',
                                'nodv_flag'])
    nodv_flag = traits.Bool(desc='Input is a NODDI model with optimised PDD',
                            position=6,
                            argstr='-nodv',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'dti_flag2', 'ball_flag', 'ballv_flag',
                                 'nod_flag'])

    # Experimental options
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]',
                            argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].',
                           argstr='-dpr %f')


class DwiToolOutputSpec(TraitedSpec):
    """ Output Spec for DwiTool. """
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc)
    syn_file = traits.File(desc='Filename of synthetic image')
    mdmap_file = traits.File(desc='Filename of MD map/ADC')
    famap_file = traits.File(desc='Filename of FA map')
    v1map_file = traits.File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = traits.File(desc='Filename of colour FA map')
    logdti_file = traits.File(desc='Filename of output logdti map')


class DwiTool(NiftyFitCommand):
    """Interface for executable dwi_tool from Niftyfit platform.

    Use DwiTool.

    Diffusion-Weighted MR Prediction.
    Predicts DWI from previously fitted models and calculates model derived
    maps.

    Examples
    --------

    >>> from nipype.interfaces import niftyfit
    >>> dwi_tool = niftyfit.DwiTool(dti_flag=True)
    >>> dwi_tool.inputs.source_file = 'dwi.nii.gz'
    >>> dwi_tool.inputs.bvec_file = 'bvecs'
    >>> dwi_tool.inputs.bval_file = 'bvals'
    >>> dwi_tool.inputs.mask_file = 'mask.nii.gz'
    >>> dwi_tool.inputs.b0_file = 'b0.nii.gz'
    >>> dwi_tool.inputs.rgbmap_file = 'rgb_map.nii.gz'
    >>> dwi_tool.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'dwi_tool -source dwi.nii.gz -bval bvals -bvec bvecs -b0 b0.nii.gz \
-mask mask.nii.gz -dti -famap .../dwi_famap.nii.gz \
-logdti2 .../dwi_logdti2.nii.gz -mcmap .../dwi_mcmap.nii.gz \
-mdmap .../dwi_mdmap.nii.gz -rgbmap rgb_map.nii.gz -syn .../dwi_syn.nii.gz \
-v1map .../dwi_v1map.nii.gz'

    """
    _cmd = get_custom_path('dwi_tool')
    input_spec = DwiToolInputSpec
    output_spec = DwiToolOutputSpec
    _suffix = '_dwi_tool'

    def _format_arg(self, name, trait_spec, value):
        if name == 'syn_file':
            if not isdefined(self.inputs.bvec_file) or \
               not isdefined(self.inputs.b0_file):
                return ""
        if name in ['logdti_file', 'rgbmap_file'] and \
           not isdefined(self.inputs.dti_flag):
            return ""
        return super(DwiTool, self)._format_arg(name, trait_spec, value)

    def _gen_filename(self, name):
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_mdmap', ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_famap', ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_v1map', ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_rgbmap', ext='.nii.gz')
        if name == 'logdti_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_logdti2', ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

        if isdefined(self.inputs.bvec_file) and \
           isdefined(self.inputs.b0_file):
            if isdefined(self.inputs.syn_file):
                outputs['syn_file'] = self.inputs.syn_file
            else:
                outputs['syn_file'] = self._gen_filename('syn_file')

        if isdefined(self.inputs.mdmap_file):
            outputs['mdmap_file'] = self.inputs.mdmap_file
        else:
            outputs['mdmap_file'] = self._gen_filename('mdmap_file')

        if isdefined(self.inputs.famap_file):
            outputs['famap_file'] = self.inputs.famap_file
        else:
            outputs['famap_file'] = self._gen_filename('famap_file')

        if isdefined(self.inputs.v1map_file):
            outputs['v1map_file'] = self.inputs.v1map_file
        else:
            outputs['v1map_file'] = self._gen_filename('v1map_file')

        if isdefined(self.inputs.dti_flag):
            if isdefined(self.inputs.rgbmap_file):
                outputs['rgbmap_file'] = self.inputs.rgbmap_file
            else:
                outputs['rgbmap_file'] = self._gen_filename('rgbmap_file')

            if isdefined(self.inputs.logdti_file):
                outputs['logdti_file'] = self.inputs.logdti_file
            else:
                outputs['logdti_file'] = self._gen_filename('logdti_file')

        return outputs
