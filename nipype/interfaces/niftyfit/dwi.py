# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The dwi module of niftyfit, which wraps the fitting methods in NiftyFit.
"""

from nipype.interfaces.niftyfit.base import NiftyFitCommand, get_custom_path
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    CommandLineInputSpec)


class FitDwiInputSpec(CommandLineInputSpec):
    # Input options
    source_file = File(exists=True, argstr='-source %s', mandatory=True,
                       desc='The source image containing the dwi data')
    bval_file = File(exists=True, argstr='-bval %s', mandatory=True,
                     desc='The file containing the bvalues of the source DWI')
    bvec_file = File(exists=True, argstr='-bvec %s', mandatory=True,
                     desc='The file containing the bvectors of the source DWI')
    mask_file = File(exists=True, desc='The image mask',
                     argstr='-mask %s', mandatory=False)
    prior_file = File(exists=True, argstr='-prior %s', mandatory=False,
                      desc='Filename of parameter priors for -ball and -nod')
    rotsform_flag = traits.Int(
        0, desc='Rotate the output tensors according to the q/s form of \
the image (resulting tensors will be in mm coordinates, default: 0).',
        argstr='-rotsform %d', mandatory=False, usedefault=False)
    bvallowthreshold = traits.Float(
        20, argstr='-bvallowthreshold %f', mandatory=False, usedefault=False,
        desc='B-value threshold used for detection of B0 and DWI images \
[default: 20]')

    # Output options, with templated output names based on the source image
    mcmap_file = File(genfile=True, desc='Filename of multi-compartment model \
parameter map (-ivim,-ball,-nod)', argstr='-mcmap %s', requires=['nodv_flag'])
    error_file = File(genfile=True, desc='Filename of parameter error maps',
                      argstr='-error %s')
    res_file = File(genfile=True, desc='Filename of model residual map',
                    argstr='-res %s')
    syn_file = File(genfile=True, desc='Filename of synthetic image',
                    argstr='-syn %s')
    mdmap_file = File(genfile=True, desc='Filename of MD map/ADC',
                      argstr='-mdmap %s')
    famap_file = File(genfile=True, desc='Filename of FA map',
                      argstr='-famap %s')
    v1map_file = File(genfile=True, desc='Filename of PDD map [x,y,z]',
                      argstr='-v1map %s')
    rgbmap_file = File(genfile=True, desc='Filename of colour FA map',
                       argstr='-rgbmap %s', requires=['dti_flag'])
    tenmap_file = File(genfile=True, desc='Filename of tensor map in lower \
triangular format', argstr='-tenmap2 %s', requires=['dti_flag'])

    # Methods options
    mono_flag = traits.Bool(desc='Fit single exponential to non-directional \
data [default with no b-vectors]', argstr='-mono',
                            xor=['ivim_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    ivim_flag = traits.Bool(desc='Fit IVIM model to non-directional data.',
                            argstr='-ivim ',
                            xor=['mono_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    dti_flag = traits.Bool(
        desc='Fit the tensor model [default with b-vectors].', argstr='-dti ',
        xor=['mono_flag', 'ivim_flag', 'ball_flag',
             'ballv_flag', 'nod_flag', 'nodv_flag'])
    ball_flag = traits.Bool(desc='Fit the ball and stick model.',
                            argstr='-ball ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    ballv_flag = traits.Bool(desc='Fit the ball and stick model with optimised \
PDD.', argstr='-ballv ', xor=['mono_flag', 'ivim_flag', 'dti_flag',
                              'ball_flag', 'nod_flag', 'nodv_flag'])
    nod_flag = traits.Bool(desc='Fit the NODDI model', argstr='-nod ',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'ball_flag', 'ballv_flag', 'nodv_flag'])
    nodv_flag = traits.Bool(desc='Fit the NODDI model with optimised PDD',
                            argstr='-nodv ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ball_flag', 'ballv_flag', 'nod_flag'])

    # Experimental options
    maxit_val = traits.Int(
        desc='Maximum number of non-linear LSQR iterations [100x2 passes])',
        argstr='-maxit %i', requires=['gn_flag'])
    lm_vals = traits.Tuple(
        traits.Float, traits.Float, argstr='-lm %f $f', requires=['gn_flag'],
        desc='LM parameters (initial value, decrease rate) [100,1.2]')
    gn_flag = traits.Bool(
        desc='Use Gauss-Newton algorithm [Levenberg-Marquardt].',
        argstr='-gn', xor=['wls_flag'],  default=False)
    wls_flag = traits.Bool(
        desc='Use variance-weighted least squares for DTI fitting',
        argstr='-wls', xor=['gn_flag'], default=False)
    slice_no = traits.Int(desc='Fit to single slice number',
                          argstr='-slice %i')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]',
                            argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].',
                           argstr='-dpr %f')
    perf_thr = traits.Float(
        desc='Threshold for perfusion/diffsuion effects [100].',
        argstr='-perfusionthreshold %f')


# Output spec
class FitDwiOutputSpec(TraitedSpec):
    mcmap_file = File(desc='Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)')
    error_file = File(desc='Filename of parameter error maps')
    res_file = File(desc='Filename of model residual map')
    syn_file = File(desc='Filename of synthetic image')
    mdmap_file = File(desc='Filename of MD map/ADC')
    famap_file = File(desc='Filename of FA map')
    v1map_file = File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = File(desc='Filename of colour FA map')
    tenmap_file = File(desc='Filename of tensor map')


# FitDwi function
# TODO: Add functionality to selectivitly generate outputs images
# as currently all possible images will be generated
class FitDwi(NiftyFitCommand):
    """ Use NiftyFit to perform diffusion model fitting.

    Examples
    --------

    >>> from nipype.interfaces import niftyfit
    >>> fit_dwi = niftyfit.FitDwi()
    >>> fit_dwi.inputs.source_file =
    >>> fit_dwi.inputs.bvec_file =
    >>> fit_dwi.inputs.bval_file =
    >>> fit_dwi.inputs.dti_flag = True
    >>> fit_dwi.inputs.rgbmap_file = 'rgb_map.nii.gz'
    >>> fit_dwi.run()
    """
    _cmd = get_custom_path('fit_dwi')
    input_spec = FitDwiInputSpec
    output_spec = FitDwiOutputSpec

    _suffix = '_fit_dwi'

    def _gen_filename(self, name):
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_mcmap',
                                   ext='.nii.gz')
        if name == 'error_file':
            return self._gen_fname(self.inputs.source_file, suffix='_error',
                                   ext='.nii.gz')
        if name == 'res_file':
            return self._gen_fname(self.inputs.source_file, suffix='_resmap',
                                   ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file, suffix='_syn',
                                   ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_mdmap',
                                   ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_famap',
                                   ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.source_file, suffix='_v1map',
                                   ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_rgbmap',
                                   ext='.nii.gz')
        if name == 'tenmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_tenmap2',
                                   ext='.nii.gz')
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

        if isdefined(self.inputs.mcmap_file):
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

        return outputs


# Input spec
class DwiToolInputSpec(CommandLineInputSpec):
    # Input options
    source_file = File(
        exists=True, desc='The source image containing the fitted model',
        argstr='-source %s', mandatory=True)
    bval_file = File(
        exists=True, desc='The file containing the bvalues of the source DWI',
        argstr='-bval %s', mandatory=False)
    bvec_file = File(
        exists=True, desc='The file containing the bvectors of the source DWI',
        argstr='-bvec %s', mandatory=False)
    mask_file = File(exists=True, desc='The image mask',
                     argstr='-mask %s', mandatory=False)
    b0_file = File(exists=True, desc='The B0 image corresponding to the',
                   argstr='-b0 %s', mandatory=False)

    # Output options, with templated output names based on the source image
    mcmap_file = File(genfile=True, desc='Filename of multi-compartment model \
parameter map (-ivim,-ball,-nod)', argstr='-mcmap %s')
    syn_file = File(genfile=True, desc='Filename of synthetic image',
                    argstr='-syn %s')
    mdmap_file = File(genfile=True, desc='Filename of MD map/ADC',
                      argstr='-mdmap %s')
    famap_file = File(genfile=True, desc='Filename of FA map',
                      argstr='-famap %s')
    v1map_file = File(genfile=True, desc='Filename of PDD map [x,y,z]',
                      argstr='-v1map %s')
    rgbmap_file = File(genfile=True, desc='Filename of colour FA map',
                       argstr='-rgbmap %s', requires=['dti_flag'])
    logdti_file = File(genfile=True, desc='Filename of output logdti map',
                       argstr='-logdti2 %s', requires=['dti_flag'])
    bvallowthreshold = traits.Float(
        10, desc='B-value threshold used for detection of B0 and DWI images \
[default: 10]', argstr='-bvallowthreshold %f', mandatory=False,
        usedefault=False)

    # Methods options
    mono_flag = traits.Bool(
        desc='Input is a single exponential to non-directional data \
[default with no b-vectors]', argstr='-mono',
        xor=['ivim_flag', 'dti_flag', 'dti_flag2',
             'ball_flag', 'ballv_flag', 'nod_flag', 'nodv_flag'])
    ivim_flag = traits.Bool(
        desc='Inputs is an IVIM model to non-directional data.',
        argstr='-ivim ', xor=['mono_flag', 'dti_flag', 'dti_flag2',
                              'ball_flag', 'ballv_flag', 'nod_flag',
                              'nodv_flag'])
    dti_flag = traits.Bool(desc='Input is a tensor model diag/off-diag.',
                           argstr='-dti ',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag2',
                                'ball_flag', 'ballv_flag', 'nod_flag',
                                'nodv_flag'])
    dti_flag2 = traits.Bool(desc='Input is a tensor model lower triangular',
                            argstr='-dti2 ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    ball_flag = traits.Bool(desc='Input is a ball and stick model.',
                            argstr='-ball ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'dti_flag2', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    ballv_flag = traits.Bool(
        desc='Input is a ball and stick model with optimised PDD.',
        argstr='-ballv ', xor=['mono_flag', 'ivim_flag', 'dti_flag',
                               'dti_flag2', 'ball_flag', 'nod_flag',
                               'nodv_flag'])
    nod_flag = traits.Bool(desc='Input is a NODDI model',
                           argstr='-nod ',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'dti_flag2', 'ball_flag', 'ballv_flag',
                                'nodv_flag'])
    nodv_flag = traits.Bool(desc='Input is a NODDI model with optimised PDD',
                            argstr='-nodv ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'dti_flag2', 'ball_flag', 'ballv_flag',
                                 'nod_flag'])

    # Experimental options
    slice_no = traits.Int(desc='Fit to single slice number',
                          argstr='-slice %i')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]',
                            argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].',
                           argstr='-dpr %f')
    perf_thr = traits.Float(desc='Threshold for perfusion/diffsuion effects \
[100].', argstr='-perfusionthreshold %f')


# Output spec
class DwiToolOutputSpec(TraitedSpec):
    mcmap_file = File(desc='Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)')
    syn_file = File(desc='Filename of synthetic image')
    mdmap_file = File(desc='Filename of MD map/ADC')
    famap_file = File(desc='Filename of FA map')
    v1map_file = File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = File(desc='Filename of colour FA map')
    logdti_file = File(desc='Filename of output logdti map')


# DwiTool command
class DwiTool(NiftyFitCommand):
    """ Use DwiTool

    Examples
    --------

    >>> from nipype.interfaces import niftyfit
    >>> dwi_tool = niftyfit.DwiTool()
    >>> dwi_tool.inputs.source_file =
    >>> dwi_tool.inputs.bvec_file =
    >>> dwi_tool.inputs.bval_file =
    >>> dwi_tool.inputs.dti_flag = True
    >>> dwi_tool.inputs.rgbmap_file = 'rgb_map.nii.gz'
    >>> dwi_tool.run()
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
            else:
                return trait_spec.argstr % value
        return super(DwiTool, self)._format_arg(name, trait_spec, value)

    def _gen_filename(self, name):
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_mcmap',
                                   ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file, suffix='_syn',
                                   ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_mdmap',
                                   ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_famap',
                                   ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.source_file, suffix='_v1map',
                                   ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.source_file, suffix='_rgbmap',
                                   ext='.nii.gz')
        if name == 'logdti_file':
            return self._gen_fname(self.inputs.source_file, suffix='_logdti2',
                                   ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

        if isdefined(self.inputs.mcmap_file):
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

        if isdefined(self.inputs.logdti_file):
            outputs['logdti_file'] = self.inputs.logdti_file
        else:
            outputs['logdti_file'] = self._gen_filename('logdti_file')

        return outputs
