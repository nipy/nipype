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
    verbosity_off_val = traits.Bool(argstr='-voff', desc='Turn off verbose output')

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
        # first do what should be done in general
        formated = super(RegResample, self)._format_arg(name, spec, value)
        if name == 'inter_val':
            formated = spec.argstr%{"NN":0, "LIN":1, "CUB":2}[value]

        return formated

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