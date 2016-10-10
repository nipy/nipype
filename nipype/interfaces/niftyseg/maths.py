# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The maths module provides higher-level interfaces to some of the operations
that can be performed with the niftysegmaths (seg_maths) command-line program.
"""
import os

from nipype.interfaces.niftyseg.base import NIFTYSEGCommand, \
                                    NIFTYSEGCommandInputSpec, getNiftySegPath
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined,
                                    InputMultiPath)


class MathsInput(NIFTYSEGCommandInputSpec):
    in_file = File(position=2, argstr='%s', exists=True, mandatory=True,
                   desc='image to operate on')
    out_file = File(genfile=True, position=-2, argstr='%s',
                    desc='image to write')
    _dtypes = ['float', 'char', 'int', 'short', 'double', 'input']
    output_datatype = traits.Enum(
                *_dtypes, position=-3, argstr='-odt %s',
                desc='datatype to use for output (default uses input type)')


class MathsOutput(TraitedSpec):
    out_file = File(exists=True, desc='image written after calculations')


class MathsCommand(NIFTYSEGCommand):
    _cmd = getNiftySegPath('seg_maths')
    input_spec = MathsInput
    output_spec = MathsOutput
    _suffix = '_maths'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            if isdefined(self.inputs.operation) and \
               self.inputs.operation == 'hdr_copy':
                outputs['out_file'] = self._gen_fname(self.inputs.operand_file,
                                                      suffix=self._suffix)
            else:
                outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                      suffix=self._suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class UnaryMathsInput(MathsInput):
    operation = traits.Enum('sqrt', 'exp', 'log', 'recip', 'abs', 'bin',
                            'otsu', 'lconcomp', 'concomp6', 'concomp26',
                            'fill', 'euc', 'tpmax', 'tmean', 'tmin', 'tmax',
                            'splitlab', 'removenan', 'isnan', 'subsamp2',
                            'scl', '4to5', 'range',
                            argstr='-%s', position=4, mandatory=True,
                            desc='operation to perform')


class UnaryMaths(MathsCommand):
    """
    Use seg_maths to perform a variety of mathematical unary operations.

    mandatory input specs is operation
    Examples
    --------
    from nipype.interfaces.niftyseg import UnaryMaths
    squarerooter = UnaryMaths()
    squarerooter.inputs.in_file = "T1.nii.gz"
    squarerooter.inputs.out_file = "T1-sqrt.nii.gz"
    squarerooter.inputs.operation = "sqrt"
    squarerooter.inputs.output_datatype = "float"
    squarerooter.cmdline
    seg_maths T1.nii.gz -sqrt -odt float T1-sqrt.nii.gz

    available operations:

    * * Operations on 3-D and 4-D images* *
    -sqrt 			Square root of the image.
    -exp 			Exponential root of the image.
    -log 			Log of the image.
    -recip 			Reciprocal (1/I) of the image.
    -abs 			Absolute value of the image.
    -bin 			Binarise the image.
    -otsu 			Otsu thresholding of the current image.

    * * Operations binary 3-D images * *
    -lconcomp      	Take the largest connected component
    -concomp6      	Label the different connected components with a 6NN kernel
    -concomp26     	Label the different connected components with a 26NN kernel
    -fill  			Fill holes in binary object (e.g. fill ventricle in brain mask).
    -euc   			Euclidean distance trasnform

    * * Dimensionality reduction operations: from 4-D to 3-D * *
    -tp <int>      	Extract time point <int>
    -tpmax 			Get the time point with the highest value
                    (binarise 4D probabilities)
    -tmean 			Mean value of all time points.
    -tmax  			Max value of all time points.
    -tmin  			Mean value of all time points.

    * * Dimensionality increase operations: from 3-D to 4-D * *
    -splitlab		Split the integer labels into multiple timepoints

    * * NaN handling * *
    -removenan     		Remove all NaNs and replace then with 0
    -isnan 			Binary image equal to 1 if the value is NaN and 0 otherwise

    * * Sampling * *
    -subsamp2		Subsample the image by 2 using NN sampling
                    (qform and sform scaled)

    * * Image header operations * *
    -scl   			Reset scale and slope info.
    -4to5  			Flip the 4th and 5th dimension.

    * * Output * *
    -range			Reset the image range to the min max
    """
    input_spec = UnaryMathsInput

    def _list_outputs(self):
        self._suffix = '_' + self.inputs.operation
        return super(UnaryMaths, self)._list_outputs()


class BinaryMathsInput(MathsInput):
    operation = traits.Enum('mul', 'div', 'add', 'sub', 'pow', 'thr', 'uthr',
                            'smo', 'edge', 'sobel3', 'sobel5', 'min',
                            'smol', 'geo', 'llsnorm', 'masknan', 'hdr_copy',
                            mandatory=True, argstr='-%s', position=4,
                            desc='operation to perform')
    operand_file = File(exists=True, argstr='%s', mandatory=True, position=5,
                        xor=['operand_value'],
                        desc='second image to perform operation with')
    operand_value = traits.Float(argstr='%.8f', mandatory=True, position=5,
                                 xor=['operand_file'],
                                 desc='float value to perform operation with')


class BinaryMaths(MathsCommand):
    """
    Use seg_maths to perform a variety of mathematical binary operations.

    mandatory input specs is operation and (operand_file or operand_value)
    Examples
    --------
    from nipype.interfaces.niftyseg import BinaryMaths
    substracter = BinaryMaths()
    substracter.inputs.in_file = "T1.nii.gz"
    substracter.inputs.out_file = "T1-T2.nii.gz"
    substracter.inputs.operand_file = "T1.nii.gz"
    substracter.inputs.operation = "sub"
    substracter.inputs.output_datatype = "float"
    substracter.cmdline
    seg_maths T1.nii.gz -odt float -sub T2.nii.gz T1-T2.nii

    available operations:

    * * Operations on 3-D and 4-D images* *
    -mul	<float/file>	Multiply image <float> value or by other image.
    -div	<float/file>	Divide image by <float> or by other image.
    -add	<float/file>	Add image by <float> or by other image.
    -sub	<float/file>	Subtract image by <float> or by other image.
    -pow	<float>		Image to the power of <float>.
    -thr	<float>		Threshold the image below <float>.
    -uthr	<float>		Threshold image above <float>.
    -smo	<float>		Gaussian smoothing by std <float> (in voxels and up to 4-D).

    * * Operations on 3-D images * *
    -smol  	<float>		Gaussian smoothing of a 3D label image.

    * * Operations binary 3-D images * *
    -geo <float/file>	Geodesic distance according to the speed function
                        <float/file>

    * * Normalisation * *
    -llsnorm  <file_norm>   Linear LS normalisation between current and
                            <file_norm>

    * * Image header operations * *
    -hdr_copy <file> 	Copy header from working image to <file> and save in
                        <output>.

    """
    input_spec = BinaryMathsInput
  
    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for niftkMTPDbc."""
        if opt == 'operand_value' and float(val) == 0.0:
            return '0'

        return super(BinaryMaths, self)._format_arg(opt, spec, val)


class BinaryMathsInputInteger(MathsInput):
    operation = traits.Enum('dil', 'ero', 'tp',
                            mandatory=True, argstr='-%s', position=4,
                            desc='operation to perform')
    operand_file = File(exists=True, argstr='%s', mandatory=True, position=5,
                        xor=['operand_value'],
                        desc='second image to perform operation with')
    operand_value = traits.Int(argstr='%s', mandatory=True, position=5,
                               xor=['operand_file'],
                               desc='float value to perform operation with')


class BinaryMathsInteger(MathsCommand):
    """
    Use seg_maths to perform a variety of INT mathematical binary operations.

    mandatory input specs is operation and (operand_file or operand_value)

    available operations:
    * * Operations on 3-D and 4-D images* *
    -equal 	<int>  		Get voxels equal to <int>

    * * Operations on 3-D images * *
    -dil   	<int>  		Dilate the image <int> times (in voxels).
    -ero   	<int>  		Erode the image <int> times (in voxels).

    * * Dimensionality reduction operations: from 4-D to 3-D * *
    -tp <int>      		Extract time point <int>

    """
    input_spec = BinaryMathsInputInteger


class TupleMathsInput(MathsInput):
    operation = traits.Enum('lncc', 'lssd', 'lltsnorm', 'qlsnorm',
                            mandatory=True, argstr='-%s', position=4,
                            desc='operation to perform')
    operand_file1 = File(
        exists=True, argstr='%s', mandatory=True, position=5,
        xor=['operand_value1'], desc='image to perform operation 1 with')
    operand_value1 = traits.Float(
        argstr='%.8f', mandatory=True, position=5, xor=['operand_file1'],
        desc='float value to perform operation 1 with')
    operand_file2 = File(
        exists=True, argstr='%s', mandatory=True, position=6,
        xor=['operand_value2'], desc='image to perform operation 2 with')
    operand_value2 = traits.Float(
        argstr='%.8f', mandatory=True, position=6, xor=['operand_file2'],
        desc='float value to perform operation 2 with')


class TupleMaths(MathsCommand):
    """
    Use seg_maths to perform a variety of mathematical binary operations.

    mandatory input specs is operation and (operand_file or operand_value)

    available operations:

    * * Image similarity: Local metrics * *
    -lncc  	<file> <std>   	Local CC between current img and <file>
                            on a kernel with <std>
    -lssd  	<file> <std>   	Local SSD between current img and <file>
                            on a kernel with <std>

    * * Normalisation * *
    -lltsnorm      	<file_norm> <float>   Linear LTS normalisation assuming
                                          <float> percent outliers
    -qlsnorm       	<order> <file_norm>   LS normalisation of <order> between
                                          current and <file_norm>
    """
    input_spec = BinaryMathsInput


class MergeInput(MathsInput):
    nb_images = traits.Int(mandatory=True, argstr='-merge %d', position=4,
                           desc='Number of images to merge.')
    dimension = traits.Int(exists=True, argstr='%d', mandatory=True,
                           position=5, desc='Dimension to merge the images.')
    merge_files = InputMultiPath(argstr='%s', mandatory=True, position=6,
                                 desc='List of images to merge to the working \
image <input>.')


class Merge(MathsCommand):
    """
    Use seg_maths to merge all the files to the working image.

    operations:
    * * Dimensionality increase operations: from 3-D to 4-D * *
    -merge 	<i> <d> <files>	Merge <i> images and the working image in the
            <d> dimension

    """
    input_spec = BinaryMathsInputInteger
