from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File, InputMultiPath
from nipype.utils.filemanip import split_filename
import os

class MRConvertInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='voxel-order data filename')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    extract_at_axis = traits.Enum("LR","TB","FB", argstr='-coord %s', position=1,
                           desc='"Extract data only at the coordinates specified. This option specifies the Axis. Must be used in conjunction with extract_at_coordinate.')
    extract_at_coordinate = traits.List(traits.Float, argstr='%s', sep=',', position=2, minlen=3, maxlen=3,
        desc='"Extract data only at the coordinates specified. This option specifies the coordinates. Must be used in conjunction with extract_at_axis. Three comma-separated numbers giving the size of each voxel in mm.')
    voxel_dims = traits.List(traits.Float, argstr='-vox %s', sep=',',
        position=3, minlen=3, maxlen=3,
        desc='Three comma-separated numbers giving the size of each voxel in mm.')
    output_datatype = traits.Enum("nii", "float", "char", "short", "int", "long", "double", argstr='-output %s', position=2,
                           desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"') #, usedefault=True)
    layout = traits.Enum("nii", "float", "char", "short", "int", "long", "double", argstr='-output %s', position=2,
                           desc='specify the layout of the data in memory. The actual layout produced will depend on whether the output image format can support it.')
    resample = traits.Float(argstr='-scale %d', position=3,
        units='mm', desc='Apply scaling to the intensity values.')
    offset_bias = traits.Float(argstr='-scale %d', position=3,
        units='mm', desc='Apply offset to the intensity values.')
    zero = traits.Bool(argstr='-zero', position=3, desc="Replace all NaN values with zero.")
    prs = traits.Bool(argstr='-prs', position=3, desc="Assume that the DW gradients are specified in the PRS frame (Siemens DICOM only).")

class MRConvertOutputSpec(TraitedSpec):
    converted = File(exists=True, desc='path/name of 4D volume in voxel order')

class MRConvert(CommandLine):
    """
    Perform conversion between different file types and optionally extract a subset of the input image.
    If used correctly, this program can be a very useful workhorse.
    In addition to converting images between different formats, it can be used to extract specific studies from a data set,
    extract a specific region of interest, flip the images, or to scale the intensity of the images.
    """
    _cmd = 'mrconvert'
    input_spec=MRConvertInputSpec
    output_spec=MRConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_mrconvert.' + self.inputs.output_datatype
        
class DWI2TensorInputSpec(CommandLineInputSpec):
    in_file = InputMultiPath(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Diffusion-weighted images')
    out_filename = File(argstr='%s', genfile=True, position=-1, desc='Output tensor filename')
    encoding_file = File(argstr='-grad %s', position= 2, desc='Encoding file, , supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix()')
    ignore_slice_by_volume = traits.List(traits.Int, argstr='-ignoreslices %s', sep=' ', position=2, minlen=2, maxlen=2,
        desc='Requires two values (i.e. [34 1] for [Slice Volume] Ignores the image slices specified when computing the tensor. Slice here means the z coordinate of the slice to be ignored.')
    ignore_volumes = traits.List(traits.Int, argstr='-ignorevolumes %s', sep=' ', position=2, minlen=1,
        desc='Requires two values (i.e. [2 5 6] for [Volumes] Ignores the image volumes specified when computing the tensor.')
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")
    
class DWI2TensorOutputSpec(TraitedSpec):
    tensor = File(exists=True, desc='path/name of output diffusion tensor image')

class DWI2Tensor(CommandLine):
    """
    convert diffusion-weighted images to tensor images.
    """
    _cmd = 'dwi2tensor'
    input_spec=DWI2TensorInputSpec
    output_spec=DWI2TensorOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['tensor'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file[0])
        return name + '_tensor.mif'

class Tensor2VectorInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Diffusion tensor image')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output vector filename')    
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")

class Tensor2VectorOutputSpec(TraitedSpec):
    vector = File(exists=True, desc='the output image of the major eigenvectors of the diffusion tensor image.')

class Tensor2Vector(CommandLine):
    """
    Generates a map of the major eigenvectors of the tensors in each voxel.

    """
    _cmd = 'tensor2vector'
    input_spec=Tensor2VectorInputSpec
    output_spec=Tensor2VectorOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['vector'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_vector.mif'

class Tensor2FractionalAnisotropyInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Diffusion tensor image')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output Fractional Anisotropy filename')    
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")

class Tensor2FractionalAnisotropyOutputSpec(TraitedSpec):
    FA = File(exists=True, desc='the output image of the major eigenvectors of the diffusion tensor image.')

class Tensor2FractionalAnisotropy(CommandLine):
    """
    Generates a map of the fractional anisotropy in each voxel.

    """
    _cmd = 'tensor2FA'
    input_spec=Tensor2FractionalAnisotropyInputSpec
    output_spec=Tensor2FractionalAnisotropyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['FA'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_FA.mif'

class Tensor2ApparentDiffusionInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Diffusion tensor image')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output Fractional Anisotropy filename')    
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")

class Tensor2ApparentDiffusionOutputSpec(TraitedSpec):
    ADC = File(exists=True, desc='the output image of the major eigenvectors of the diffusion tensor image.')

class Tensor2ApparentDiffusion(CommandLine):
    """
    Generates a map of the apparent diffusion coefficient (ADC) in each voxel

    """
    _cmd = 'tensor2ADC'
    input_spec=Tensor2ApparentDiffusionInputSpec
    output_spec=Tensor2ApparentDiffusionOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['ADC'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_ADC.mif'

class MRMultiplyInputSpec(CommandLineInputSpec):
    in_file = InputMultiPath(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Input images to be multiplied')
    out_filename = File(argstr='%s', position=-1, desc='Output vector filename')    
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")

class MRMultiplyOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output image of the multiplication')

class MRMultiply(CommandLine):
    """
    Multiplies two images.

    """
    _cmd = 'mrmult'
    input_spec=MRMultiplyInputSpec
    output_spec=MRMultiplyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file[0])
        return name + '_MRMult.mif'

class MRTrixViewerInputSpec(CommandLineInputSpec):
    in_files = InputMultiPath(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Input images to be viewed')
    quiet = traits.Bool(argstr='-quiet', position=1, desc="Do not display information messages or progress status.")
    debug = traits.Bool(argstr='-debug', position=1, desc="Display debugging messages.")

class MRTrixViewerOutputSpec(TraitedSpec):
    pass
    #out_file = File(exists=True, desc='the output image of the multiplication')

class MRTrixViewer(CommandLine):
    """
    Loads the input images in the MRTrix Viewer.
    """
    _cmd = 'mrview'
    input_spec=MRTrixViewerInputSpec
    output_spec=MRTrixViewerOutputSpec

    def _list_outputs(self):
        return 
        
class MRTrixInfoInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
        desc='Input images to be read')

class MRTrixInfoOutputSpec(TraitedSpec):
    pass

class MRTrixInfo(CommandLine):
    """
    Prints out relevant header information found in the image specified.
    """
    _cmd = 'mrinfo'
    input_spec=MRTrixInfoInputSpec
    output_spec=MRTrixInfoOutputSpec

    def _list_outputs(self):
        return 

class GenerateWhiteMatterMaskInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3, desc='Diffusion-weighted images')
    binary_mask = File(exists=True, argstr='%s', mandatory=True, position = -2, desc='Binary brain mask')
    out_WMProb_filename = File(genfile=True, argstr='%s', position = -1, desc='Output WM probability image filename')
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1, 
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')	
    noise_level_margin = traits.Float(argstr='-margin %s', desc='Specify the width of the margin on either side of the image to be used to estimate the noise level (default = 10)')
    
class GenerateWhiteMatterMaskOutputSpec(TraitedSpec):
    WMprobabilitymap = File(exists=True, desc='WMprobabilitymap')

class GenerateWhiteMatterMask(CommandLine):
    """
    Estimate the fibre response function for use in spherical deconvolution.
    
    """
    _cmd = 'gen_WM_mask'
    input_spec=GenerateWhiteMatterMaskInputSpec
    output_spec=GenerateWhiteMatterMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['WMprobabilitymap'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_WMProb_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_WMProb.mif'
