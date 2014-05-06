# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The regutils module provides classes for interfacing with the `niftyreg
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ utility command line tools. The 
interfaces were written to work with niftyreg version 1.4
"""

import os
import os.path as op
import warnings

from nipype.interfaces.niftyreg.base import NiftyRegCommandInputSpec

from nipype.interfaces.base import (CommandLine, TraitedSpec, File, 
                                    InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    isdefined, OutputMultiPath)
                                    
from nipype.utils.filemanip import split_filename

from nibabel import load

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

# A custom trait class for positive integers
class PositiveInt (traits.BaseInt):

    # Define the default value
    default_value = 1
    # Describe the trait type
    info_text = 'A positive integer'

    def validate ( self, object, name, value ):
        value = super(OddInt, self).validate(object, name, value)
        if (value >= 0) == 1:
            return value
        self.error( object, name, value )


#-----------------------------------------------------------
# reg_resample wrapper interface
#-----------------------------------------------------------

# Input spec
class RegResampleInputSpec(NiftyRegCommandInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                   argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                   argstr='-flo %s', mandatory=True)
    # Input affine transformation
    aff_file = File(exists=True, desc='The input affine transformation',
                   argstr='-aff %s', mandatory=False)
    # Input deformation field
    trans_file = File(exists=True, desc='The input CPP transformation file',
                   argstr='-trans %s', mandatory=False)
    # Output file name
    res_file = File(desc='The output filename of the transformed image',
                   argstr='-res %s', mandatory=False)
    # Deformaed grid file name
    blank_file = File(desc='The output filename of resampled blank grid',
                   argstr='-blank %s', mandatory=False)
    # Interpolation type
    inter_val = traits.Enum("NN", "LIN", "CUB", desc = 'Interpolation type',
                             argstr="-inter %d")
    # Padding value
    pad_val = traits.Int(desc = 'Padding value', argstr="-pad %d")
    # Verbosity off?
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')

# Output spec
class RegResampleOutputSpec(TraitedSpec):
    res_file = File(desc='The output filename of the transformed image')
    blank_file = File(desc='The output filename of resampled blank grid (if generated)')

# Resampler class
class RegResample(CommandLine):
    _cmd = 'reg_resample'
    input_spec = RegResampleInputSpec
    output_spec = RegResampleOutputSpec

    # Need this overload to properly constraint the interpolation type input
    def _format_arg(self, name, spec, value):
        if name == 'inter_val':
            return spec.argstr%{"NN":0, "LIN":1, "CUB":2}[value]
        else:
            return super(RegResample, self)._format_arg(name, spec, value)

    # Returns a dictionary containing names of generated files that are expected 
    # after package completes execution
    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        if isdefined(self.inputs.res_file) and self.inputs.res_file:
            outputs['res_file'] = os.path.abspath(self.inputs.res_file)

        if isdefined(self.inputs.blank_file) and self.inputs.blank_file:
            outputs['blank_file'] = os.path.abspath(self.inputs.blank_file)

        return outputs

#-----------------------------------------------------------
# reg_jacobian wrapper interface
#-----------------------------------------------------------
# Input spec
class RegJacobianInputSpec(NiftyRegCommandInputSpec):
    # Input transformation file
    trans_file = File(exists=True, desc='The input non-rigid transformation',
                   argstr='-trans %s', mandatory=True)
    # Input jacobian determinat file path
    jac_det_file = File(desc='The output jacobian determinant file name',
                   argstr='-jac %s')
    # Input jacobian matrix file name
    jac_mat_file = File(desc='The output jacobian matrix file name',
                   argstr='-jacM %s')
    # Input log of jacobian determinant file name
    jac_log_file = File(desc='The output log of jacobian determinant file name',
                   argstr='-jacL %s')
    # Reference file name
    ref_file_name = File(exists=True, desc='Reference/target file (required if specifying CPP transformations',
                    argstr='-ref %s')


# Output spec
class RegJacobianOutputSpec(TraitedSpec):
    jac_det_file = File(desc='The output jacobian determinant file')
    jac_mat_file = File(desc='The output filename of jacobian matrix')
    jac_log_file = File(desc='The output filename of the log of jacobian determinant')
                   
# Main interface class
class RegJacobian(CommandLine):
    _cmd = 'reg_jacobian'
    input_spec = RegJacobianInputSpec
    output_spec = RegJacobianOutputSpec

    # Returns a dictionary containing names of generated files that are expected 
    # after package completes execution
    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        if isdefined(self.inputs.jac_det_file) and self.inputs.jac_det_file:
            outputs['jac_det_file'] = os.path.abspath(self.inputs.jac_det_file)

        if isdefined(self.inputs.jac_mat_file) and self.inputs.jac_mat_file:
            outputs['jac_mat_file'] = os.path.abspath(self.inputs.jac_mat_file)

        if isdefined(self.inputs.jac_log_file) and self.inputs.jac_log_file:
            outputs['jac_log_file'] = os.path.abspath(self.inputs.jac_log_file)        

        return outputs

#-----------------------------------------------------------
# reg_tools wrapper interface
#-----------------------------------------------------------
# Input spec
class RegToolsInputSpec(NiftyRegCommandInputSpec):
    # Input image file
    in_file = File(exists=True, desc='The input image file path',
                   argstr='-in %s', mandatory=True)
    # Output file path
    out_file = File(desc='The output file name', argstr='-out %s')
    # Make the output image isotropic
    iso_flag = traits.Bool(argstr='-iso', desc='Make output image isotropic')
    # Set scale, slope to 0 and 1.
    noscl_flag = traits.Bool(argstr='-noscl', desc='Set scale, slope to 0 and 1')
    # Values outside the mask are set to NaN
    mask_file = File(exists=True, desc='Values outside the mask are set to NaN',
                   argstr='-nan %s')
    # Threshold the input image
    thr_val = traits.Float(desc='Binarise the input image with the given threshold', 
                argstr='-thr %f')
    # Binarise the input image
    bin_flag = traits.Bool(argstr='-bin', desc='Binarise the input image')
    # Compute the mean RMS between the two images
    rms_val = File(exists=True, desc='Compute the mean RMS between the images',
                argstr='-rms %s')
    # Perform division by image or value
    div_val = traits.Either(traits.Float, File(exists=True), 
                desc='Divide the input by image or value', argstr='-div %s')
    # Perform multiplication by image or value
    mul_val = traits.Either(traits.Float, File(exists=True), 
                desc='Multiply the input by image or value', argstr='-mul %s')
    # Perform addition by image or value
    add_val = traits.Either(traits.Float, File(exists=True), 
                desc='Add to the input image or value', argstr='-add %s')
    # Perform subtraction by image or value
    sub_val = traits.Either(traits.Float, File(exists=True), 
                desc='Add to the input image or value', argstr='-sub %s')
    # Downsample the image by a factor of 2.
    down_flag = traits.Bool(desc='Downsample the image by a factor of 2', argstr='-down')
    # Smoothing using spline kernel
    smo_s_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                    desc = 'Smooth the input image using a cubic spline kernel',
                    argstr='-smoS %f %f %f')
    # Smoothing using Gaussian kernel
    smo_g_val = traits.Tuple(traits.Float, traits.Float, traits.Float,
                    desc = 'Smooth the input image using a Gaussian kernel',
                    argstr='-smoG %f %f %f')



# Output spec    
class RegToolsOutputSpec(TraitedSpec):
    out_file = File(desc='The output file')

# Main interface class
class RegTools(CommandLine):
    _cmd = 'reg_tools'
    input_spec = RegToolsInputSpec
    output_spec = RegToolsOutputSpec

    # Returns a dictionary containing names of generated files that are expected 
    # after package completes execution
    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.out_file) and self.inputs.out_file:
                outputs['out_file'] = os.path.abspath(self.inputs.out_file)

#-----------------------------------------------------------
# reg_aladin wrapper interface
#-----------------------------------------------------------
# Input spec
class RegAladinInputSpec(NiftyRegCommandInputSpec):
    # Input reference file
    ref_file = File(exists=True, desc='The input reference/target image',
                   argstr='-ref %s', mandatory=True)
    # Input floating file
    flo_file = File(exists=True, desc='The input floating/source image',
                   argstr='-flo %s', mandatory=True)
    # Affine output matrix file
    aff_file = File(desc='The output affine matrix file', argstr='-aff %s')
    # No symmetric flag
    nosym_flag = traits.Bool(argstr='-noSym', desc='Turn off symmetric registration')
    # Rigid only registration
    rig_only_flag = traits.Bool(argstr='-rigOnly', desc='Do only a rigid registration')
    # Directly optimise affine flag
    aff_direct_flag = traits.Bool(argstr='-affDirect', desc='Directly optimise the affine parameters')
    # Input affine
    in_aff_file = File(exists=True, desc='The input affine transformation',
                   argstr='-inaff %s')
    # Input reference mask
    rmask_file = File(exists=True, desc='The input reference mask',
                   argstr='-rmask %s')
    # Input floating mask
    fmask_file = File(exists=True, desc='The input floating mask',
                   argstr='-fmask %s')
    # Result image path
    result_file = File(desc='The affine transformed floating image',
                   argstr='-res %s')
    # Maximum number of iterations
    maxit_val = PositiveInt(desc='Maximum number of iterations', argstr='-maxit %d')
    # Multiresolution levels
    ln_val = PositiveInt(desc='Number of resolution levels to create', argstr='-ln %d')
    # Number of resolution levels to process
    lp_val = PositiveInt(desc='Number of resolution levels to perform', argstr='-lp %d')
    # Smoothing to apply on reference image
    smoo_r_val = traits.Float(desc='Amount of smoothing to apply to reference image',
                    argstr='-smooR %f')
    # Smoothing to apply on floating image
    smoo_f_val = traits.Float(desc='Amount of smoothing to apply to floating image',
                    argstr='-smooF %f')
    # Use nifti header to initialise transformation
    nac_flag = traits.Bool(desc='Use nifti header to initialise transformaiton',
                argstr='-nac')
    # Percent of blocks that are considered active.
    v_val = PositiveInt(desc='Percent of blocks that are active', argstr='-%v %d')
    # Percent of inlier blocks
    i_val = PositiveInt(desc='Percent of inlier blocks', argstr='-%i %d')
    # Verbosity off?
    verbosity_off_flag = traits.Bool(argstr='-voff', desc='Turn off verbose output')
    # Lower threshold on reference image
    ref_low_val = traits.Float(desc='Lower threshold value on reference image',
                    argstr='-refLowThr %f')
    # Upper threshold on reference image
    ref_up_val = traits.Float(desc='Upper threshold value on reference image',
                    argstr='-refUpThr %f')
    # Lower threshold on floating image
    flo_low_val = traits.Float(desc='Lower threshold value on floating image',
                    argstr='-floLowThr %f')
    # Upper threshold on floating image
    flo_up_val = traits.Float(desc='Upper threshold value on floating image',
                    argstr='-floUpThr %f')


# Output spec
class RegAladinOutputSpec(TraitedSpec):
    aff_file = File(desc='The output affine file')
    result_file = File(desc='The output transformed image')

# Main interface class
class RegAladin(CommandLine):
    _cmd = 'reg_aladin'
    input_spec = RegAladinInputSpec
    output_spec = RegAladinOutputSpec

    # Returns a dictionary containing names of generated files that are expected 
    # after package completes execution
    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.aff_file) and self.inputs.aff_file:
            outputs['aff_file'] = os.path.abspath(self.inputs.aff_file)

        if isdefined(self.inputs.result_file) and self.inputs.result_file:
            outputs['result_file'] = os.path.abspath(self.inputs.result_file)
