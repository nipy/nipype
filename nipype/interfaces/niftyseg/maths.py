# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
Nipype interface for seg_maths.

The maths module provides higher-level interfaces to some of the operations
that can be performed with the niftysegmaths (seg_maths) command-line program.

Examples
--------
See the docstrings of the individual classes for examples.

Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
import os

from ..base import (TraitedSpec, File, traits, isdefined, CommandLineInputSpec,
                    NipypeInterfaceError)
from .base import NiftySegCommand, get_custom_path


class MathsInput(CommandLineInputSpec):
    """Input Spec for seg_maths interfaces."""
    in_file = File(position=2,
                   argstr='%s',
                   exists=True,
                   mandatory=True,
                   desc='image to operate on')

    out_file = File(genfile=True,
                    position=-2,
                    argstr='%s',
                    desc='image to write')

    _dtypes = ['float', 'char', 'int', 'short', 'double', 'input']

    desc = 'datatype to use for output (default uses input type)'
    output_datatype = traits.Enum(*_dtypes,
                                  position=-3,
                                  argstr='-odt %s',
                                  desc=desc)


class MathsOutput(TraitedSpec):
    """Output Spec for seg_maths interfaces."""
    out_file = File(exists=True, desc='image written after calculations')


class MathsCommand(NiftySegCommand):
    """
    Base Command Interface for seg_maths interfaces.

    The executable seg_maths enables the sequential execution of arithmetic
    operations, like multiplication (-mul), division (-div) or addition
    (-add), binarisation (-bin) or thresholding (-thr) operations and
    convolution by a Gaussian kernel (-smo). It also alows mathematical
    morphology based operations like dilation (-dil), erosion (-ero),
    connected components (-lconcomp) and hole filling (-fill), Euclidean
    (- euc) and geodesic (-geo) distance transforms, local image similarity
    metric calculation (-lncc and -lssd). Finally, it allows multiple
    operations over the dimensionality of the image, from merging 3D images
    together as a 4D image (-merge) or splitting (-split or -tp) 4D images
    into several 3D images, to estimating the maximum, minimum and average
    over all time-points, etc.
    """
    _cmd = get_custom_path('seg_maths')
    input_spec = MathsInput
    output_spec = MathsOutput

    def _list_outputs(self):
        outputs = self.output_spec().get()

        suffix = self._suffix
        if suffix != '_merged' and isdefined(self.inputs.operation):
            suffix = '_' + self.inputs.operation

        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                  suffix=suffix)
        outputs['out_file'] = os.path.abspath(outputs['out_file'])
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['out_file']
        return None


class UnaryMathsInput(MathsInput):
    """Input Spec for seg_maths Unary operations."""
    operation = traits.Enum('sqrt', 'exp', 'log', 'recip', 'abs', 'bin',
                            'otsu', 'lconcomp', 'concomp6', 'concomp26',
                            'fill', 'euc', 'tpmax', 'tmean', 'tmax', 'tmin',
                            'splitlab', 'removenan', 'isnan', 'subsamp2',
                            'scl', '4to5', 'range',
                            argstr='-%s', position=4, mandatory=True,
                            desc='operation to perform')


class UnaryMaths(MathsCommand):
    """Interface for executable seg_maths from NiftySeg platform.

    Interface to use any unary mathematical operations that can be performed
    with the seg_maths command-line program. See below for those operations:
        -sqrt           Square root of the image.
        -exp            Exponential root of the image.
        -log            Log of the image.
        -recip          Reciprocal (1/I) of the image.
        -abs            Absolute value of the image.
        -bin            Binarise the image.
        -otsu           Otsu thresholding of the current image.
        -lconcomp       Take the largest connected component
        -concomp6       Label the different connected components with a 6NN
                        kernel
        -concomp26      Label the different connected components with a 26NN
                        kernel
        -fill           Fill holes in binary object (e.g. fill ventricle in
                        brain mask).
        -euc            Euclidean distance trasnform
        -tpmax          Get the time point with the highest value (binarise 4D
                        probabilities)
        -tmean          Mean value of all time points.
        -tmax           Max value of all time points.
        -tmin           Mean value of all time points.
        -splitlab       Split the integer labels into multiple timepoints
        -removenan      Remove all NaNs and replace then with 0
        -isnan          Binary image equal to 1 if the value is NaN and 0
                        otherwise
        -subsamp2       Subsample the image by 2 using NN sampling (qform and
                        sform scaled)
        -scl            Reset scale and slope info.
        -4to5           Flip the 4th and 5th dimension.
        -range          Reset the image range to the min max

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.UnaryMaths()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.operation = 'sqrt'
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_maths im1.nii -sqrt -odt float .../im1_sqrt.nii'

    """
    input_spec = UnaryMathsInput


class BinaryMathsInput(MathsInput):
    """Input Spec for seg_maths Binary operations."""
    operation = traits.Enum('mul', 'div', 'add', 'sub', 'pow', 'thr', 'uthr',
                            'smo', 'edge', 'sobel3', 'sobel5', 'min', 'smol',
                            'geo', 'llsnorm', 'masknan', 'hdr_copy',
                            'splitinter',
                            mandatory=True,
                            argstr='-%s',
                            position=4,
                            desc='operation to perform')

    operand_file = File(exists=True,
                        argstr='%s',
                        mandatory=True,
                        position=5,
                        xor=['operand_value', 'operand_str'],
                        desc='second image to perform operation with')

    operand_value = traits.Float(argstr='%.8f',
                                 mandatory=True,
                                 position=5,
                                 xor=['operand_file', 'operand_str'],
                                 desc='float value to perform operation with')

    desc = 'string value to perform operation splitinter'
    operand_str = traits.Enum('x', 'y', 'z',
                              argstr='%s',
                              mandatory=True,
                              position=5,
                              xor=['operand_value', 'operand_file'],
                              desc=desc)


class BinaryMaths(MathsCommand):
    """Interface for executable seg_maths from NiftySeg platform.

    Interface to use any binary mathematical operations that can be performed
    with the seg_maths command-line program. See below for those operations:
        -mul    <float/file>    Multiply image <float> value or by other image.
        -div    <float/file>    Divide image by <float> or by other image.
        -add    <float/file>    Add image by <float> or by other image.
        -sub    <float/file>    Subtract image by <float> or by other image.
        -pow    <float>         Image to the power of <float>.
        -thr    <float>         Threshold the image below <float>.
        -uthr   <float>         Threshold image above <float>.
        -smo    <float>         Gaussian smoothing by std <float> (in voxels
                                and up to 4-D).
        -edge   <float>         Calculate the edges of the image using a
                                threshold <float>.
        -sobel3 <float>         Calculate the edges of all timepoints using a
                                Sobel filter with a 3x3x3 kernel and applying
                                <float> gaussian smoothing.
        -sobel5 <float>         Calculate the edges of all timepoints using a
                                Sobel filter with a 5x5x5 kernel and applying
                                <float> gaussian smoothing.
        -min    <file>          Get the min per voxel between <current> and
                                <file>.
        -smol   <float>         Gaussian smoothing of a 3D label image.
        -geo    <float/file>    Geodesic distance according to the speed
                                function <float/file>
        -llsnorm  <file_norm>   Linear LS normalisation between current and
                                <file_norm>
        -masknan <file_norm>    Assign everything outside the mask (mask==0)
                                with NaNs
        -hdr_copy <file>        Copy header from working image to <file> and
                                save in <output>.
        -splitinter <x/y/z>     Split interleaved slices in direction <x/y/z>
                                into separate time points

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.BinaryMaths()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.operation = 'sub'
    >>> node.inputs.operand_file = 'im2.nii'
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_maths im1.nii -sub im2.nii -odt float .../im1_sub.nii'

    """
    input_spec = BinaryMathsInput

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_maths."""
        if opt == 'operand_value' and float(val) == 0.0:
            return '0'

        if opt == 'operand_str' and self.inputs.operation != 'splitinter':
            err = 'operand_str set but with an operation different than \
"splitinter"'
            raise NipypeInterfaceError(err)

        return super(BinaryMaths, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        self._suffix = '_' + self.inputs.operation

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


class BinaryMathsInputInteger(MathsInput):
    """Input Spec for seg_maths Binary operations that require integer."""
    operation = traits.Enum('dil', 'ero', 'tp', 'equal', 'pad', 'crop',
                            mandatory=True,
                            argstr='-%s',
                            position=4,
                            desc='operation to perform')

    operand_value = traits.Int(argstr='%d',
                               mandatory=True,
                               position=5,
                               desc='int value to perform operation with')


class BinaryMathsInteger(MathsCommand):
    """Interface for executable seg_maths from NiftySeg platform.

    Interface to use any integer mathematical operations that can be performed
    with the seg_maths command-line program. See below for those operations:
    (requiring integer values)
        -equal  <int>       Get voxels equal to <int>
        -dil    <int>       Dilate the image <int> times (in voxels).
        -ero    <int>       Erode the image <int> times (in voxels).
        -tp     <int>       Extract time point <int>
        -crop   <int>       Crop <int> voxels around each 3D volume.
        -pad    <int>       Pad <int> voxels with NaN value around each 3D
                            volume.

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces.niftyseg import BinaryMathsInteger
    >>> node = BinaryMathsInteger()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.operation = 'dil'
    >>> node.inputs.operand_value = 2
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_maths im1.nii -dil 2 -odt float .../im1_dil.nii'

    """
    input_spec = BinaryMathsInputInteger


class TupleMathsInput(MathsInput):
    """Input Spec for seg_maths Tuple operations."""
    operation = traits.Enum('lncc', 'lssd', 'lltsnorm', 'qlsnorm',
                            mandatory=True,
                            argstr='-%s',
                            position=4,
                            desc='operation to perform')

    operand_file1 = File(exists=True,
                         argstr='%s',
                         mandatory=True,
                         position=5,
                         xor=['operand_value1'],
                         desc='image to perform operation 1 with')

    desc = 'float value to perform operation 1 with'
    operand_value1 = traits.Float(argstr='%.8f',
                                  mandatory=True,
                                  position=5,
                                  xor=['operand_file1'],
                                  desc=desc)

    operand_file2 = File(exists=True,
                         argstr='%s',
                         mandatory=True,
                         position=6,
                         xor=['operand_value2'],
                         desc='image to perform operation 2 with')

    desc = 'float value to perform operation 2 with'
    operand_value2 = traits.Float(argstr='%.8f',
                                  mandatory=True,
                                  position=6,
                                  xor=['operand_file2'],
                                  desc=desc)


class TupleMaths(MathsCommand):
    """Interface for executable seg_maths from NiftySeg platform.

    Interface to use any tuple mathematical operations that can be performed
    with the seg_maths command-line program. See below for those operations:
        -lncc      <file> <std>    Local CC between current img and <file>
                                on a kernel with <std>
        -lssd      <file> <std>    Local SSD between current img and <file>
                                on a kernel with <std>
        -lltsnorm  <file_norm> <float>   Linear LTS normalisation assuming
                                         <float> percent outliers
        -qlsnorm   <order> <file_norm>   LS normalisation of <order>
                                         between current and <file_norm>

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.TupleMaths()
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.operation = 'lncc'
    >>> node.inputs.operand_file1 = 'im2.nii'
    >>> node.inputs.operand_value2 = 2.0
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_maths im1.nii -lncc im2.nii 2.00000000 -odt float .../im1_lncc.nii'

    """
    input_spec = TupleMathsInput


class MergeInput(MathsInput):
    """Input Spec for seg_maths merge operation."""
    dimension = traits.Int(mandatory=True,
                           desc='Dimension to merge the images.')

    desc = 'List of images to merge to the working image <input>.'
    merge_files = traits.List(File(exists=True),
                              argstr='%s',
                              mandatory=True,
                              position=4,
                              desc=desc)


class Merge(MathsCommand):
    """Interface for executable seg_maths from NiftySeg platform.

    Interface to use the merge operation that can be performed
    with the seg_maths command-line program. See below for this option:
        -merge  <i> <d> <files>   Merge <i> images and the working image in the
                                  <d> dimension

    For source code, see http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg
    For Documentation, see:
        http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.Merge()
    >>> node.inputs.in_file = 'im1.nii'
    >>> files = ['im2.nii', 'im3.nii']
    >>> node.inputs.merge_files = files
    >>> node.inputs.dimension = 2
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline  # doctest: +ELLIPSIS +ALLOW_UNICODE
    'seg_maths im1.nii -merge 2 2 im2.nii im3.nii -odt float \
.../im1_merged.nii'

    """
    input_spec = MergeInput
    _suffix = '_merged'

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_maths."""
        if opt == 'merge_files':
            return "-merge %d %d %s" % (len(val), self.inputs.dimension,
                                        ' '.join(val))

        return super(Merge, self)._format_arg(opt, spec, val)
