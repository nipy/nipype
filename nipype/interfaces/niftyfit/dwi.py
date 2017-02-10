# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The dwi module of niftyfit, which wraps the fitting methods in NiftyFit.
"""

import warnings

from ..base import TraitedSpec, traits, isdefined, CommandLineInputSpec
from .base import NiftyFitCommand, get_custom_path


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class FitDwiInputSpec(CommandLineInputSpec):
    """ Input Spec for FitDwi. """
    source_file = traits.File(exists=True,
                              argstr='-source %s',
                              mandatory=True,
                              desc='The source image containing the dwi data.')
    desc = 'The file containing the bvalues of the source DWI.'
    bval_file = traits.File(exists=True,
                            argstr='-bval %s',
                            mandatory=True,
                            desc=desc)
    desc = 'The file containing the bvectors of the source DWI.'
    bvec_file = traits.File(exists=True,
                            argstr='-bvec %s',
                            mandatory=True,
                            desc=desc)

    mask_file = traits.File(exists=True,
                            desc='The image mask',
                            argstr='-mask %s')
    desc = 'Filename of parameter priors for -ball and -nod.'
    prior_file = traits.File(exists=True,
                             argstr='-prior %s',
                             desc=desc)
    desc = 'Rotate the output tensors according to the q/s form of the image \
(resulting tensors will be in mm coordinates, default: 0).'
    rotsform_flag = traits.Int(0,
                               desc=desc,
                               argstr='-rotsform %d',
                               usedefault=True)
    desc = 'B-value threshold used for detection of B0 and DWI images \
[default: 20]'
    bvallowthreshold = traits.Float(20,
                                    argstr='-bvallowthreshold %f',
                                    usedefault=True,
                                    desc=desc)
    op_basename = traits.String('dwifit',
                                desc='Output file basename',
                                usedefault=True)

    # Output options, with templated output names based on the source image
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc,
                             argstr='-mcmap %s',
                             requires=['nodv_flag'],
                             genfile=True)
    error_file = traits.File(desc='Filename of parameter error maps',
                             argstr='-error %s',
                             genfile=True)
    res_file = traits.File(desc='Filename of model residual map',
                           argstr='-res %s',
                           genfile=True)
    syn_file = traits.File(desc='Filename of synthetic image',
                           argstr='-syn %s',
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
    rgbmap_file = traits.File(desc='Filename of colour FA map',
                              argstr='-rgbmap %s',
                              genfile=True,
                              requires=['dti_flag'])
    desc = 'Filename of tensor map in lower triangular format.'
    tenmap_file = traits.File(desc=desc,
                              argstr='-tenmap2 %s',
                              genfile=True,
                              requires=['dti_flag'])

    # Methods options
    desc = 'Fit single exponential to non-directional data [default with \
no b-vectors]'
    mono_flag = traits.Bool(desc=desc,
                            argstr='-mono',
                            xor=['ivim_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    ivim_flag = traits.Bool(desc='Fit IVIM model to non-directional data.',
                            argstr='-ivim ',
                            xor=['mono_flag', 'dti_flag', 'ball_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    desc = 'Fit the tensor model [default with b-vectors].'
    dti_flag = traits.Bool(desc=desc,
                           argstr='-dti ',
                           xor=['mono_flag', 'ivim_flag', 'ball_flag',
                                'ballv_flag', 'nod_flag', 'nodv_flag'])
    ball_flag = traits.Bool(desc='Fit the ball and stick model.',
                            argstr='-ball ',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ballv_flag', 'nod_flag', 'nodv_flag'])
    desc = 'Fit the ball and stick model with optimised PDD.'
    ballv_flag = traits.Bool(desc=desc,
                             argstr='-ballv ',
                             xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                  'ball_flag', 'nod_flag', 'nodv_flag'])
    nod_flag = traits.Bool(desc='Fit the NODDI model',
                           argstr='-nod ',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'ball_flag', 'ballv_flag', 'nodv_flag'])
    nodv_flag = traits.Bool(desc='Fit the NODDI model with optimised PDD',
                            argstr='-nodv ',
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
    desc = 'Use variance-weighted least squares for DTI fitting'
    wls_flag = traits.Bool(desc=desc, argstr='-wls', xor=['gn_flag'])
    slice_no = traits.Int(desc='Fit to single slice number',
                          argstr='-slice %d')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]',
                            argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].',
                           argstr='-dpr %f')
    desc = 'Threshold for perfusion/diffsuion effects [100].'
    perf_thr = traits.Float(desc=desc, argstr='-perfusionthreshold %f')


class FitDwiOutputSpec(TraitedSpec):
    """ Output Spec for FitDwi. """
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc)
    error_file = traits.File(desc='Filename of parameter error maps')
    res_file = traits.File(desc='Filename of model residual map')
    syn_file = traits.File(desc='Filename of synthetic image')
    mdmap_file = traits.File(desc='Filename of MD map/ADC')
    famap_file = traits.File(desc='Filename of FA map')
    v1map_file = traits.File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = traits.File(desc='Filename of colour FA map')
    tenmap_file = traits.File(desc='Filename of tensor map')


class FitDwi(NiftyFitCommand):
    """ Use NiftyFit to perform diffusion model fitting.

    TODO: Add functionality to selectivitly generate outputs images
          as currently all possible images will be generated
    Examples
    --------

    >>> from nipype.interfaces.niftyfit import FitDwi
    >>> fit_dwi = FitDwi()
    >>> fit_dwi.inputs.source_file = 'im1.nii.gz'  # doctest: +SKIP
    >>> fit_dwi.inputs.bvec_file = 'im1.bval'  # doctest: +SKIP
    >>> fit_dwi.inputs.bval_file = 'im1.bvec'  # doctest: +SKIP
    >>> fit_dwi.inputs.dti_flag = True
    >>> fit_dwi.inputs.rgbmap_file = 'rgb_map.nii.gz'
    >>> fit_dwi.cmdline  # doctest: +SKIP
    'fit_dwi -source im1.nii.gz -bval im1.val -bvec im1.bvec -dti -rgbmap \
rgb_map.nii.gz -syn dwifit_syn.nii.gz -res dwifit_mcmap.nii.gz\
-mdmap dwifit_mdmap.nii.gz -famap dwifit_famap.nii.gz -v1map \
dwifit_v1map.nii.gz -tenmap2 dwifit_tenmap2.nii.gz -bvallowthreshold \
20.00000 -rotsform 0 -error dwifit_error.nii.gz'

    """
    _cmd = get_custom_path('fit_dwi')
    input_spec = FitDwiInputSpec
    output_spec = FitDwiOutputSpec
    _suffix = '_fit_dwi'

    def _gen_filename(self, name):
        if name == 'mcmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'error_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_error', ext='.nii.gz')
        if name == 'res_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_resmap', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_mdmap', ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_famap', ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_v1map', ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_rgbmap', ext='.nii.gz')
        if name == 'tenmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_tenmap2', ext='.nii.gz')
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

        return outputs


class DwiToolInputSpec(CommandLineInputSpec):
    """ Input Spec for DwiTool. """
    desc = 'The source image containing the fitted model.'
    source_file = traits.File(exists=True,
                              desc=desc,
                              argstr='-source %s',
                              mandatory=True)
    desc = 'The file containing the bvalues of the source DWI.'
    bval_file = traits.File(exists=True,
                            desc=desc,
                            argstr='-bval %s',
                            mandatory=True)
    desc = 'The file containing the bvectors of the source DWI.'
    bvec_file = traits.File(exists=True,
                            desc=desc,
                            argstr='-bvec %s',
                            mandatory=True)
    mask_file = traits.File(exists=True,
                            desc='The image mask',
                            argstr='-mask %s',
                            mandatory=True)
    b0_file = traits.File(exists=True,
                          desc='The B0 image corresponding to the source DWI',
                          argstr='-b0 %s',
                          mandatory=True)

    op_basename = traits.String('dwitool',
                                desc='Output file basename',
                                usedefault=True)

    # Output options, with templated output names based on the source image
    desc = 'Filename of multi-compartment model parameter map \
(-ivim,-ball,-nod)'
    mcmap_file = traits.File(desc=desc,
                             argstr='-mcmap %s',
                             genfile=True)
    syn_file = traits.File(desc='Filename of synthetic image',
                           argstr='-syn %s',
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
    rgbmap_file = traits.File(desc='Filename of colour FA map',
                              argstr='-rgbmap %s',
                              requires=['dti_flag'],
                              genfile=True)
    logdti_file = traits.File(desc='Filename of output logdti map',
                              argstr='-logdti2 %s',
                              requires=['dti_flag'],
                              genfile=True)
    desc = 'B-value threshold used for detection of B0 and DWI images \
[default: 10]'
    bvallowthreshold = traits.Float(10,
                                    desc=desc,
                                    argstr='-bvallowthreshold %f',
                                    usedefault=True)

    # Methods options
    desc = 'Input is a single exponential to non-directional data \
[default with no b-vectors]'
    mono_flag = traits.Bool(desc=desc,
                            argstr='-mono',
                            xor=['ivim_flag', 'dti_flag', 'dti_flag2',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    desc = 'Inputs is an IVIM model to non-directional data.'
    ivim_flag = traits.Bool(desc=desc,
                            argstr='-ivim',
                            xor=['mono_flag', 'dti_flag', 'dti_flag2',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    dti_flag = traits.Bool(desc='Input is a tensor model diag/off-diag.',
                           argstr='-dti',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag2',
                                'ball_flag', 'ballv_flag', 'nod_flag',
                                'nodv_flag'])
    dti_flag2 = traits.Bool(desc='Input is a tensor model lower triangular',
                            argstr='-dti2',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'ball_flag', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    ball_flag = traits.Bool(desc='Input is a ball and stick model.',
                            argstr='-ball',
                            xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                 'dti_flag2', 'ballv_flag', 'nod_flag',
                                 'nodv_flag'])
    desc = 'Input is a ball and stick model with optimised PDD.'
    ballv_flag = traits.Bool(desc=desc,
                             argstr='-ballv',
                             xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                  'dti_flag2', 'ball_flag', 'nod_flag',
                                  'nodv_flag'])
    nod_flag = traits.Bool(desc='Input is a NODDI model',
                           argstr='-nod',
                           xor=['mono_flag', 'ivim_flag', 'dti_flag',
                                'dti_flag2', 'ball_flag', 'ballv_flag',
                                'nodv_flag'])
    nodv_flag = traits.Bool(desc='Input is a NODDI model with optimised PDD',
                            argstr='-nodv',
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
    desc = 'Threshold for perfusion/diffsuion effects [100].'
    perf_thr = traits.Float(desc=desc, argstr='-perfusionthreshold %f')


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
    """ Use DwiTool.

    Examples
    --------

    >>> from nipype.interfaces.niftyfit import DwiTool
    >>> dwi_tool = DwiTool()
    >>> dwi_tool.inputs.source_file = 'im1.nii.gz'  # doctest: +SKIP
    >>> dwi_tool.inputs.bvec_file = 'im1.bval'  # doctest: +SKIP
    >>> dwi_tool.inputs.bval_file = 'im1.bvec'  # doctest: +SKIP
    >>> dwi_tool.inputs.mask_file = 'im1.bvec'  # doctest: +SKIP
    >>> dwi_tool.inputs.b0_file = 'b0.nii.gz'  # doctest: +SKIP
    >>> dwi_tool.inputs.dti_flag = True
    >>> dwi_tool.inputs.rgbmap_file = 'rgb_map.nii.gz'
    >>> dwi_tool.cmdline  # doctest: +SKIP
    'fit_dwi -source im1.nii.gz -bval im1.val -bvec im1.bvec -dti -mask \
mask.nii.gz -b0 b0.nii.gz -rgbmap rgb_map.nii.gz -syn dwitool_syn.nii.gz \
-mdmap dwitool_mdmap.nii.gz -famap dwitool_famap.nii.gz -v1map \
dwitool_v1map.nii.gz -logdti2 dwitool_logdti2.nii.gz -bvallowthreshold \
10.00000'

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
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_mcmap', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'mdmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_mdmap', ext='.nii.gz')
        if name == 'famap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_famap', ext='.nii.gz')
        if name == 'v1map_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_v1map', ext='.nii.gz')
        if name == 'rgbmap_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_rgbmap', ext='.nii.gz')
        if name == 'logdti_file':
            return self._gen_fname(self.inputs.op_basename,
                                   suffix='_logdti2', ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.mcmap_file):
            outputs['mcmap_file'] = self.inputs.mcmap_file
        else:
            outputs['mcmap_file'] = self._gen_filename('mcmap_file')

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

        if isdefined(self.inputs.logdti_file):
            outputs['logdti_file'] = self.inputs.logdti_file
        else:
            outputs['logdti_file'] = self._gen_filename('logdti_file')

        return outputs
