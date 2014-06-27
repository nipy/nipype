# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fitutils module, which wraps the fitting methods in NiftyFit.
"""

import warnings

from nipype.interfaces.niftyfit.base import NIFTYFITCommandInputSpec, NIFTYFITCommand

from nipype.interfaces.base import (TraitedSpec, File, traits)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

#-----------------------------------------------------------
# reg_resample wrapper interface
#-----------------------------------------------------------

# Input spec
class FitDwiInputSpec(NIFTYFITCommandInputSpec):
    # Input options
    source_file = File(exists=True, desc='The source image containing the dwi data',
                   argstr='-source %s', mandatory=True)
    bval_file = File(exists=True, desc='The file containing the bvalues of the source DWI',
                   argstr='-bval %s', mandatory=True)
    bvec_file = File(exists=True, desc='The file containing the bvectors of the source DWI',
                   argstr='-bvec %s', mandatory=True)
    mask_file = File(exists=True, desc='The image mask',
                   argstr='-mask %s', mandatory=False)
    prior_file = File(exists=True, desc='Filename of parameter priors for -ball and -nod',
                   argstr='-prior %s', mandatory=False)

    # Output options, with templated output names based on the source image
    mcmap_file = File(desc='Filename of multi-compartment model parameter map (-ivim,-ball,-nod)',
                      argstr='-mcmap %s', name_source=['source_file'], name_template='%s_mcmap')     
    error_file = File(desc='Filename of parameter error maps', argstr='-error %s',
                      name_source=['source_file'], name_template='%s_error')
    res_file = File(desc='Filename of model residual map', argstr='-res %s',
                    name_source=['source_file'], name_template='%s_res')
    syn_file = File(desc='Filename of synthetic image', argstr='-syn %s', 
                    name_source=['source_file'], name_template='%s_syn')
    mdmap_file = File(desc='Filename of MD map/ADC', argstr='-mdmap %s',
                      name_source=['source_file'], name_template='%s_mdmap')
    famap_file = File(desc='Filename of FA map', argstr='-famap %s', 
                      name_source=['source_file'], name_template='%s_famap')
    v1map_file = File(desc='Filename of PDD map [x,y,z]', argstr='-v1map %s',
                      name_source=['source_file'], name_template='%s_v1map')
    rgbmap_file = File(desc='Filename of colour FA map', argstr='-rgbmap %s',
                       name_source=['source_file'], name_template='%s_rgbmap', requires=['dti_flag'])
    tenmap_file = File(desc='Filename of tensor map', argstr='-tenmap %s',
                        name_source=['source_file'], name_template='%s_tenmap', requires=['dti_flag'])
    
    
    # Methods options
    mono_flag = traits.Bool(desc='Fit single exponential to non-directional data [default with no b-vectors]',
                            argstr='-mono',xor=['method_type'])
    ivim_flag =traits.Bool(desc='Fit IVIM model to non-directional data.',
                           argstr='-ivim ',xor=['method_type'])
    dti_flag = traits.Bool(desc='Fit the tensor model [default with b-vectors].',
                           argstr='-dti ', xor=['method_type'])
    ball_flag = traits.Bool(desc='Fit the ball and stick model.', argstr='-ball ', xor=['method_type'])
    ballv_flag = traits.Bool(desc='Fit the ball and stick model with optimised PDD.',
                             argstr='-ballv ', xor=['method_type'])
    nod_flag = traits.Bool(desc='Fit the NODDI model', argstr='-nod ', xor=['method_type'])
    nodv_flag = traits.Bool(desc='Fit the NODDI model with optimised PDD', argstr='-nodv ', xor=['method_type'])
    
    
    # Experimental options
    maxit_val = traits.Int(desc='Maximum number of non-linear LSQR iterations [100x2 passes])', argstr='-maxit %i', requires=['gn_flag'])
    lm_vals = traits.Tuple(traits.Float, traits.Float,
                           desc='LM parameters (initial value, decrease rate) [100,1.2]', argstr='-lm %f $f', requires=['gn_flag'])
    gn_flag = traits.Bool(desc='Use Gauss-Newton algorithm [Levenberg-Marquardt].', argstr='-gn', xor=['opt_type'])
    wls_flag = traits.Bool(desc='Use variance-weighted least squares for DTI fitting', argstr='-wls', xor=['opt_type'])
    slice_no = traits.Int(desc='Fit to single slice number', argstr='-slice %i')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]', argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].', argstr='-dpr %f')
    perf_thr = traits.Float(desc='Threshold for perfusion/diffsuion effects [100].', argstr='-perfusionthreshold %f')

# Output spec
class FitDwiOutputSpec(TraitedSpec):
    mcmap_file = File(desc='Filename of multi-compartment model parameter map (-ivim,-ball,-nod)')       
    error_file = File(desc='Filename of parameter error maps')
    res_file = File(desc='Filename of model residual map')
    syn_file = File(desc='Filename of synthetic image')
    mdmap_file = File(desc='Filename of MD map/ADC')
    famap_file = File(desc='Filename of FA map')
    v1map_file = File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = File(desc='Filename of colour FA map')
    tenmap_file = File(desc='Filename of tensor map')

# FitDwi function
# TODO: Add functionality to selectivitly generate outputs images, as currently all possible
# images will be generated
class FitDwi(NIFTYFITCommand):
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
    _cmd = 'fit_dwi'
    input_spec = FitDwiInputSpec
    output_spec = FitDwiOutputSpec
    
    _suffix = '_fit_dwi'


# Input spec
class DwiToolInputSpec(NIFTYFITCommandInputSpec):
    # Input options
    source_file = File(exists=True, desc='The source image containing the dwi data',
                   argstr='-source %s', mandatory=True)
    bval_file = File(exists=True, desc='The file containing the bvalues of the source DWI',
                   argstr='-bval %s', mandatory=True)
    bvec_file = File(exists=True, desc='The file containing the bvectors of the source DWI',
                   argstr='-bvec %s', mandatory=True)
    mask_file = File(exists=True, desc='The image mask',
                   argstr='-mask %s', mandatory=False)

    # Output options, with templated output names based on the source image
    mcmap_file = File(desc='Filename of multi-compartment model parameter map (-ivim,-ball,-nod)',
                      argstr='-mcmap %s', name_source=['source_file'], name_template='%s_mcmap')     
    syn_file = File(desc='Filename of synthetic image', argstr='-syn %s', 
                    name_source=['source_file'], name_template='%s_syn')
    mdmap_file = File(desc='Filename of MD map/ADC', argstr='-mdmap %s',
                      name_source=['source_file'], name_template='%s_mdmap')
    famap_file = File(desc='Filename of FA map', argstr='-famap %s', 
                      name_source=['source_file'], name_template='%s_famap')
    v1map_file = File(desc='Filename of PDD map [x,y,z]', argstr='-v1map %s',
                      name_source=['source_file'], name_template='%s_v1map')
    rgbmap_file = File(desc='Filename of colour FA map', argstr='-rgbmap %s',
                       name_source=['source_file'], name_template='%s_rgbmap', requires=['dti_flag'])
    
    
    # Methods options
    mono_flag = traits.Bool(desc='Input is a single exponential to non-directional data [default with no b-vectors]',
                            argstr='-mono',xor=['method_type'])
    ivim_flag =traits.Bool(desc='Inputs is an IVIM model to non-directional data.',
                           argstr='-ivim ',xor=['method_type'])
    dti_flag = traits.Bool(desc='Input is a tensor model diag/off-diag.',
                           argstr='-dti ', xor=['method_type'])
    dti_flag2 = traits.Bool(desc='Input is a tensor model lower triangular',
                           argstr='-dti2 ', xor=['method_type'])
    ball_flag = traits.Bool(desc='Input is a ball and stick model.', argstr='-ball ', xor=['method_type'])
    ballv_flag = traits.Bool(desc='Input is a ball and stick model with optimised PDD.',
                             argstr='-ballv ', xor=['method_type'])
    nod_flag = traits.Bool(desc='Input is a NODDI model', argstr='-nod ', xor=['method_type'])
    nodv_flag = traits.Bool(desc='Input is a NODDI model with optimised PDD', argstr='-nodv ', xor=['method_type'])
    
    
    # Experimental options
    slice_no = traits.Int(desc='Fit to single slice number', argstr='-slice %i')
    diso_val = traits.Float(desc='Isotropic diffusivity for -nod [3e-3]', argstr='-diso %f')
    dpr_val = traits.Float(desc='Parallel diffusivity for -nod [1.7e-3].', argstr='-dpr %f')
    perf_thr = traits.Float(desc='Threshold for perfusion/diffsuion effects [100].', argstr='-perfusionthreshold %f')

# Output spec
class DwiToolOutputSpec(TraitedSpec):
    mcmap_file = File(desc='Filename of multi-compartment model parameter map (-ivim,-ball,-nod)')
    syn_file = File(desc='Filename of synthetic image')
    mdmap_file = File(desc='Filename of MD map/ADC')
    famap_file = File(desc='Filename of FA map')
    v1map_file = File(desc='Filename of PDD map [x,y,z]')
    rgbmap_file = File(desc='Filename of colour FA map')
 

# DwiTool command
class DwiTool(NIFTYFITCommand):
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
    _cmd = 'dwi_tool'
    input_spec = DwiToolInputSpec
    output_spec = DwiToolOutputSpec
    
    _suffix = '_dwi_tool'
