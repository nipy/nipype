from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
from nipype.utils.misc import isdefined
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec, Directory, InputMultiPath, OutputMultiPath
import os, os.path as op
import numpy as np
import nibabel as nb

class DWI2SphericalHarmonicsImageInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2, desc='Diffusion-weighted images')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1, 
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')	
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    normalise = traits.Bool(argstr='-normalise', position=3, desc="normalise the DW signal to the b=0 image")
	
class DWI2SphericalHarmonicsImageOutputSpec(TraitedSpec):
    spherical_harmonics_image = File(exists=True, desc='Spherical harmonics image')

class DWI2SphericalHarmonicsImage(CommandLine):
    """
    Convert base diffusion-weighted images to their spherical harmonic representation.

    This program outputs the spherical harmonic decomposition for the set measured signal attenuations.
    The signal attenuations are calculated by identifying the b-zero images from the diffusion encoding supplied
    (i.e. those with zero as the b-value), and dividing the remaining signals by the mean b-zero signal intensity. 
    The spherical harmonic decomposition is then calculated by least-squares linear fitting.
    Note that this program makes use of implied symmetries in the diffusion profile. 

    First, the fact the signal attenuation profile is real implies that it has conjugate symmetry, 
    i.e. Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the diffusion profile should be 
    antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l components should be zero. Therefore, 
    this program only computes the even elements.

    Note that the spherical harmonics equations used here differ slightly from those conventionally used, 
    in that the (-1)^m factor has been omitted. This should be taken into account in all subsequent calculations.

    Each volume in the output image corresponds to a different spherical harmonic component, according to the following convention:

    [0] Y(0,0)
    [1] Im {Y(2,2)}
    [2] Im {Y(2,1)}
    [3] Y(2,0)
    [4] Re {Y(2,1)}
    [5] Re {Y(2,2)}
    [6] Im {Y(4,4)}
    [7] Im {Y(4,3)}

    """
    _cmd = 'dwi2SH'
    input_spec=DWI2SphericalHarmonicsImageInputSpec
    output_spec=DWI2SphericalHarmonicsImageOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['spherical_harmonics_image'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_SH.mif'
        
class ConstrainedSphericalDeconvolutionInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3, desc='diffusion-weighted image')
    response_file = File(exists=True, argstr='%s', mandatory=True, position=-2, 
    desc='the diffusion-weighted signal response function for a single fibre population (see EstimateResponse)')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    mask_image = File(exists=True, argstr='-mask %s', position=2, desc='only perform computation within the specified binary brain mask image')
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1, 
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')
    filter_file = File(exists=True, argstr='-filter %s', position=-2,
    desc='a text file containing the filtering coefficients for each even harmonic order.' \
    'the linear frequency filtering parameters used for the initial linear spherical deconvolution step (default = [ 1 1 1 0 0 ]).')
    
    lambda_value = traits.Float(argstr='-lambda %s', desc='the regularisation parameter lambda that controls the strength of the constraint (default = 1.0).')
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    threshold_value = traits.Float(argstr='-threshold %s', desc='the threshold below which the amplitude of the FOD is assumed to be zero, expressed as a fraction of the mean value of the initial FOD (default = 0.1)')
    iterations = traits.Int(argstr='-niter %s', desc='the maximum number of iterations to perform for each voxel (default = 50)')
    
    directions_file = File(exists=True, argstr='-directions %s', position=-2,
    desc='a text file containing the [ el az ] pairs for the directions: Specify the directions over which to apply the non-negativity constraint (by default, the built-in 300 direction set is used)')
	
    normalise = traits.Bool(argstr='-normalise', position=3, desc="normalise the DW signal to the b=0 image")
	
class ConstrainedSphericalDeconvolutionOutputSpec(TraitedSpec):
    spherical_harmonics_image = File(exists=True, desc='Spherical harmonics image')

class ConstrainedSphericalDeconvolution(CommandLine):
    """
    Perform non-negativity constrained spherical deconvolution.

	Note that this program makes use of implied symmetries in the diffusion profile.
	First, the fact the signal attenuation profile is real implies that it has conjugate symmetry, 
	i.e. Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the diffusion profile should be 
	antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l components should be zero. 
	Therefore, this program only computes the even elements. 	Note that the spherical harmonics equations used here
	differ slightly from those conventionally used, in that the (-1)^m factor has been omitted. This should be taken 
	into account in all subsequent calculations. Each volume in the output image corresponds to a different spherical 
	harmonic component, according to the following convention:

	[0] Y(0,0)
	[1] Im {Y(2,2)}
	[2] Im {Y(2,1)}
	[3] Y(2,0)
	[4] Re {Y(2,1)}
	[5] Re {Y(2,2)}
	[6] Im {Y(4,4)}
	[7] Im {Y(4,3)} 
	
	Examples
	--------

    >>> import nipype.interfaces.mrtrix as mrt                  # doctest: +SKIP
    >>> csdeconv = mrt.ConstrainedSphericalDeconvolution()                  # doctest: +SKIP
    >>> csdeconv.inputs.in_file = 'tract_data.Bfloat'                  # doctest: +SKIP
    >>> csdeconv.inputs.gradient_encoding_file = 'encoding.txt'                  # doctest: +SKIP
    >>> csdeconv.inputs.offset = 0                  # doctest: +SKIP
    >>> csdeconv.run()                  # doctest: +SKIP
    """
    _cmd = 'csdeconv'
    input_spec=ConstrainedSphericalDeconvolutionInputSpec
    output_spec=ConstrainedSphericalDeconvolutionOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['spherical_harmonics_image'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_CSD.mif'
        
class EstimateResponseForSHInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3, desc='Diffusion-weighted images')
    mask_image = File(exists=True, mandatory=True, argstr='%s', position=-2, desc='only perform computation within the specified binary brain mask image')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')    
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1, 
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')	
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    normalise = traits.Bool(argstr='-normalise', desc='normalise the DW signal to the b=0 image')
    quiet = traits.Bool(argstr='-quiet', desc='Do not display information messages or progress status.')
    debug = traits.Bool(argstr='-debug', desc='Display debugging messages.')
	
class EstimateResponseForSHOutputSpec(TraitedSpec):
    response = File(exists=True, desc='Spherical harmonics image')

class EstimateResponseForSH(CommandLine):
    """
    Estimate the fibre response function for use in spherical deconvolution.
    
    """
    _cmd = 'estimate_response'
    input_spec=EstimateResponseForSHInputSpec
    output_spec=EstimateResponseForSHOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['response'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_ER.mif'

def concat_files(bvec_file, bval_file):
    bvecs = np.loadtxt(bvec_file)
    bvals = np.loadtxt(bval_file)
    encoding = np.transpose(np.vstack((bvecs,bvals)))
    _, bvec , _ = split_filename(bvec_file)
    _, bval , _ = split_filename(bval_file)
    out_encoding_file = bvec + '_' + bval + '.txt'
    np.savetxt(out_encoding_file, encoding)
    return out_encoding_file

class FSL2MRTrixInputSpec(TraitedSpec):
    bvec_file = File(exists=True, mandatory=True, desc='FSL b-vectors file (3xN text file)')
    bval_file = File(exists=True, mandatory=True, desc='FSL b-values file (1xN text file)')
    out_encoding_file = File(genfile=True, desc='Output encoding filename')

class FSL2MRTrixOutputSpec(TraitedSpec):
    encoding_file = File(desc='The gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient' \
        'and b gives the b-value in units (1000 s/mm^2).')

class FSL2MRTrix(BaseInterface):
    """
    Converts separate b-values and b-vectors from text files (FSL style) into a 4xN text file in which each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient',
        'and b gives the b-value in units (1000 s/mm^2).
    """
    input_spec = FSL2MRTrixInputSpec
    output_spec = FSL2MRTrixOutputSpec

    def _run_interface(self, runtime):
        encoding = concat_files(self.inputs.bvec_file, self.inputs.bval_file)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['encoding_file'] = os.path.abspath(self._gen_filename())
        return outputs
        
    def _gen_filename(self, name):
        if name is 'out_encoding_file':
            return self._gen_outfilename()
        else:
            return None
            
    def _gen_outfilename(self):
        _, bvec , _ = split_filename(self.inputs.bvec_file)
        _, bval , _ = split_filename(self.inputs.bval_file)
        return bvec + '_' + bval + '.txt'
