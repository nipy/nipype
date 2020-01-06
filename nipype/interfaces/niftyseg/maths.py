# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype interface for seg_maths.

The maths module provides higher-level interfaces to some of the operations
that can be performed with the niftysegmaths (seg_maths) command-line program.

"""

import os

from ..base import (
    TraitedSpec,
    File,
    traits,
    isdefined,
    CommandLineInputSpec,
    NipypeInterfaceError,
)
from .base import NiftySegCommand
from ..niftyreg.base import get_custom_path
from ...utils.filemanip import split_filename


class MathsInput(CommandLineInputSpec):
    """Input Spec for seg_maths interfaces."""

    in_file = File(
        position=2, argstr="%s", exists=True, mandatory=True, desc="image to operate on"
    )

    out_file = File(
        name_source=["in_file"],
        name_template="%s",
        position=-2,
        argstr="%s",
        desc="image to write",
    )

    desc = "datatype to use for output (default uses input type)"
    output_datatype = traits.Enum(
        "float",
        "char",
        "int",
        "short",
        "double",
        "input",
        position=-3,
        argstr="-odt %s",
        desc=desc,
    )


class MathsOutput(TraitedSpec):
    """Output Spec for seg_maths interfaces."""

    out_file = File(desc="image written after calculations")


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

    _cmd = get_custom_path("seg_maths", env_dir="NIFTYSEGDIR")
    input_spec = MathsInput
    output_spec = MathsOutput
    _suffix = "_maths"

    def _overload_extension(self, value, name=None):
        path, base, _ = split_filename(value)
        _, _, ext = split_filename(self.inputs.in_file)

        suffix = self._suffix
        if suffix != "_merged" and isdefined(self.inputs.operation):
            suffix = "_" + self.inputs.operation

        return os.path.join(path, "{0}{1}{2}".format(base, suffix, ext))


class UnaryMathsInput(MathsInput):
    """Input Spec for seg_maths Unary operations."""

    operation = traits.Enum(
        "sqrt",
        "exp",
        "log",
        "recip",
        "abs",
        "bin",
        "otsu",
        "lconcomp",
        "concomp6",
        "concomp26",
        "fill",
        "euc",
        "tpmax",
        "tmean",
        "tmax",
        "tmin",
        "splitlab",
        "removenan",
        "isnan",
        "subsamp2",
        "scl",
        "4to5",
        "range",
        argstr="-%s",
        position=4,
        mandatory=True,
        desc="""\
Operation to perform:

    * sqrt - Square root of the image).
    * exp - Exponential root of the image.
    * log - Log of the image.
    * recip - Reciprocal (1/I) of the image.
    * abs - Absolute value of the image.
    * bin - Binarise the image.
    * otsu - Otsu thresholding of the current image.
    * lconcomp - Take the largest connected component
    * concomp6 - Label the different connected components with a 6NN kernel
    * concomp26 - Label the different connected components with a 26NN kernel
    * fill - Fill holes in binary object (e.g. fill ventricle in brain mask).
    * euc - Euclidean distance transform
    * tpmax - Get the time point with the highest value (binarise 4D probabilities)
    * tmean - Mean value of all time points.
    * tmax - Max value of all time points.
    * tmin - Mean value of all time points.
    * splitlab - Split the integer labels into multiple timepoints
    * removenan - Remove all NaNs and replace then with 0
    * isnan - Binary image equal to 1 if the value is NaN and 0 otherwise
    * subsamp2 - Subsample the image by 2 using NN sampling (qform and sform scaled)
    * scl  - Reset scale and slope info.
    * 4to5 - Flip the 4th and 5th dimension.
    * range - Reset the image range to the min max.

""",
    )


class UnaryMaths(MathsCommand):
    """Unary mathematical operations.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces import niftyseg
    >>> unary = niftyseg.UnaryMaths()
    >>> unary.inputs.output_datatype = 'float'
    >>> unary.inputs.in_file = 'im1.nii'

    >>> # Test sqrt operation
    >>> unary_sqrt = copy.deepcopy(unary)
    >>> unary_sqrt.inputs.operation = 'sqrt'
    >>> unary_sqrt.cmdline
    'seg_maths im1.nii -sqrt -odt float im1_sqrt.nii'
    >>> unary_sqrt.run()  # doctest: +SKIP

    >>> # Test sqrt operation
    >>> unary_abs = copy.deepcopy(unary)
    >>> unary_abs.inputs.operation = 'abs'
    >>> unary_abs.cmdline
    'seg_maths im1.nii -abs -odt float im1_abs.nii'
    >>> unary_abs.run()  # doctest: +SKIP

    >>> # Test bin operation
    >>> unary_bin = copy.deepcopy(unary)
    >>> unary_bin.inputs.operation = 'bin'
    >>> unary_bin.cmdline
    'seg_maths im1.nii -bin -odt float im1_bin.nii'
    >>> unary_bin.run()  # doctest: +SKIP

    >>> # Test otsu operation
    >>> unary_otsu = copy.deepcopy(unary)
    >>> unary_otsu.inputs.operation = 'otsu'
    >>> unary_otsu.cmdline
    'seg_maths im1.nii -otsu -odt float im1_otsu.nii'
    >>> unary_otsu.run()  # doctest: +SKIP

    >>> # Test isnan operation
    >>> unary_isnan = copy.deepcopy(unary)
    >>> unary_isnan.inputs.operation = 'isnan'
    >>> unary_isnan.cmdline
    'seg_maths im1.nii -isnan -odt float im1_isnan.nii'
    >>> unary_isnan.run()  # doctest: +SKIP

    """

    input_spec = UnaryMathsInput


class BinaryMathsInput(MathsInput):
    """Input Spec for seg_maths Binary operations."""

    operation = traits.Enum(
        "mul",
        "div",
        "add",
        "sub",
        "pow",
        "thr",
        "uthr",
        "smo",
        "edge",
        "sobel3",
        "sobel5",
        "min",
        "smol",
        "geo",
        "llsnorm",
        "masknan",
        "hdr_copy",
        "splitinter",
        mandatory=True,
        argstr="-%s",
        position=4,
        desc="""\
Operation to perform:

    * mul - <float/file> - Multiply image <float> value or by other image.
    * div - <float/file> - Divide image by <float> or by other image.
    * add - <float/file> - Add image by <float> or by other image.
    * sub - <float/file> - Subtract image by <float> or by other image.
    * pow - <float> - Image to the power of <float>.
    * thr - <float> - Threshold the image below <float>.
    * uthr - <float> - Threshold image above <float>.
    * smo - <float> - Gaussian smoothing by std <float> (in voxels and up to 4-D).
    * edge - <float> - Calculate the edges of the image using a threshold <float>.
    * sobel3 - <float> - Calculate the edges of all timepoints using a Sobel filter
      with a 3x3x3 kernel and applying <float> gaussian smoothing.
    * sobel5 - <float> - Calculate the edges of all timepoints using a Sobel filter
      with a 5x5x5 kernel and applying <float> gaussian smoothing.
    * min - <file> - Get the min per voxel between <current> and <file>.
    * smol - <float> - Gaussian smoothing of a 3D label image.
    * geo - <float/file> - Geodesic distance according to the speed function <float/file>
    * llsnorm  <file_norm> - Linear LS normalisation between current and <file_norm>
    * masknan <file_norm> - Assign everything outside the mask (mask==0) with NaNs
    * hdr_copy <file> - Copy header from working image to <file> and save in <output>.
    * splitinter <x/y/z> - Split interleaved slices in direction <x/y/z>
      into separate time points

""",
    )

    operand_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=5,
        xor=["operand_value", "operand_str"],
        desc="second image to perform operation with",
    )

    operand_value = traits.Float(
        argstr="%.8f",
        mandatory=True,
        position=5,
        xor=["operand_file", "operand_str"],
        desc="float value to perform operation with",
    )

    desc = "string value to perform operation splitinter"
    operand_str = traits.Enum(
        "x",
        "y",
        "z",
        argstr="%s",
        mandatory=True,
        position=5,
        xor=["operand_value", "operand_file"],
        desc=desc,
    )


class BinaryMaths(MathsCommand):
    """Binary mathematical operations.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces import niftyseg
    >>> binary = niftyseg.BinaryMaths()
    >>> binary.inputs.in_file = 'im1.nii'
    >>> binary.inputs.output_datatype = 'float'

    >>> # Test sub operation
    >>> binary_sub = copy.deepcopy(binary)
    >>> binary_sub.inputs.operation = 'sub'
    >>> binary_sub.inputs.operand_file = 'im2.nii'
    >>> binary_sub.cmdline
    'seg_maths im1.nii -sub im2.nii -odt float im1_sub.nii'
    >>> binary_sub.run()  # doctest: +SKIP

    >>> # Test mul operation
    >>> binary_mul = copy.deepcopy(binary)
    >>> binary_mul.inputs.operation = 'mul'
    >>> binary_mul.inputs.operand_value = 2.0
    >>> binary_mul.cmdline
    'seg_maths im1.nii -mul 2.00000000 -odt float im1_mul.nii'
    >>> binary_mul.run()  # doctest: +SKIP

    >>> # Test llsnorm operation
    >>> binary_llsnorm = copy.deepcopy(binary)
    >>> binary_llsnorm.inputs.operation = 'llsnorm'
    >>> binary_llsnorm.inputs.operand_file = 'im2.nii'
    >>> binary_llsnorm.cmdline
    'seg_maths im1.nii -llsnorm im2.nii -odt float im1_llsnorm.nii'
    >>> binary_llsnorm.run()  # doctest: +SKIP

    >>> # Test splitinter operation
    >>> binary_splitinter = copy.deepcopy(binary)
    >>> binary_splitinter.inputs.operation = 'splitinter'
    >>> binary_splitinter.inputs.operand_str = 'z'
    >>> binary_splitinter.cmdline
    'seg_maths im1.nii -splitinter z -odt float im1_splitinter.nii'
    >>> binary_splitinter.run()  # doctest: +SKIP

    """

    input_spec = BinaryMathsInput

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_maths."""
        if opt == "operand_str" and self.inputs.operation != "splitinter":
            err = 'operand_str set but with an operation different than \
"splitinter"'

            raise NipypeInterfaceError(err)

        if opt == "operation":
            # Only float
            if val in ["pow", "thr", "uthr", "smo", "edge", "sobel3", "sobel5", "smol"]:
                if not isdefined(self.inputs.operand_value):
                    err = "operand_value not set for {0}.".format(val)
                    raise NipypeInterfaceError(err)
            # only files
            elif val in ["min", "llsnorm", "masknan", "hdr_copy"]:
                if not isdefined(self.inputs.operand_file):
                    err = "operand_file not set for {0}.".format(val)
                    raise NipypeInterfaceError(err)
            # splitinter:
            elif val == "splitinter":
                if not isdefined(self.inputs.operand_str):
                    err = "operand_str not set for splitinter."
                    raise NipypeInterfaceError(err)

        if opt == "operand_value" and float(val) == 0.0:
            return "0"

        return super(BinaryMaths, self)._format_arg(opt, spec, val)

    def _overload_extension(self, value, name=None):
        if self.inputs.operation == "hdr_copy":
            path, base, _ = split_filename(value)
            _, base, ext = split_filename(self.inputs.operand_file)
            suffix = self.inputs.operation
            return os.path.join(path, "{0}{1}{2}".format(base, suffix, ext))
        else:
            return super(BinaryMaths, self)._overload_extension(value, name)


class BinaryMathsInputInteger(MathsInput):
    """Input Spec for seg_maths Binary operations that require integer."""

    operation = traits.Enum(
        "dil",
        "ero",
        "tp",
        "equal",
        "pad",
        "crop",
        mandatory=True,
        argstr="-%s",
        position=4,
        desc="""\
Operation to perform:

    * equal - <int> - Get voxels equal to <int>
    * dil - <int>  - Dilate the image <int> times (in voxels).
    * ero - <int> - Erode the image <int> times (in voxels).
    * tp - <int> - Extract time point <int>
    * crop - <int> - Crop <int> voxels around each 3D volume.
    * pad - <int> -  Pad <int> voxels with NaN value around each 3D volume.

""",
    )

    operand_value = traits.Int(
        argstr="%d",
        mandatory=True,
        position=5,
        desc="int value to perform operation with",
    )


class BinaryMathsInteger(MathsCommand):
    """Integer mathematical operations.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces.niftyseg import BinaryMathsInteger
    >>> binaryi = BinaryMathsInteger()
    >>> binaryi.inputs.in_file = 'im1.nii'
    >>> binaryi.inputs.output_datatype = 'float'
    >>> # Test dil operation
    >>> binaryi_dil = copy.deepcopy(binaryi)
    >>> binaryi_dil.inputs.operation = 'dil'
    >>> binaryi_dil.inputs.operand_value = 2
    >>> binaryi_dil.cmdline
    'seg_maths im1.nii -dil 2 -odt float im1_dil.nii'
    >>> binaryi_dil.run()  # doctest: +SKIP
    >>> # Test dil operation
    >>> binaryi_ero = copy.deepcopy(binaryi)
    >>> binaryi_ero.inputs.operation = 'ero'
    >>> binaryi_ero.inputs.operand_value = 1
    >>> binaryi_ero.cmdline
    'seg_maths im1.nii -ero 1 -odt float im1_ero.nii'
    >>> binaryi_ero.run()  # doctest: +SKIP
    >>> # Test pad operation
    >>> binaryi_pad = copy.deepcopy(binaryi)
    >>> binaryi_pad.inputs.operation = 'pad'
    >>> binaryi_pad.inputs.operand_value = 4
    >>> binaryi_pad.cmdline
    'seg_maths im1.nii -pad 4 -odt float im1_pad.nii'
    >>> binaryi_pad.run()  # doctest: +SKIP

    """

    input_spec = BinaryMathsInputInteger


class TupleMathsInput(MathsInput):
    """Input Spec for seg_maths Tuple operations."""

    operation = traits.Enum(
        "lncc",
        "lssd",
        "lltsnorm",
        mandatory=True,
        argstr="-%s",
        position=4,
        desc="""\
Operation to perform:

    * lncc <file> <std> Local CC between current img and <file> on a kernel with <std>
    * lssd <file> <std> Local SSD between current img and <file> on a kernel with <std>
    * lltsnorm <file_norm> <float>  Linear LTS normalisation assuming <float> percent outliers

""",
    )

    operand_file1 = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=5,
        xor=["operand_value1"],
        desc="image to perform operation 1 with",
    )

    desc = "float value to perform operation 1 with"
    operand_value1 = traits.Float(
        argstr="%.8f", mandatory=True, position=5, xor=["operand_file1"], desc=desc
    )

    operand_file2 = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=6,
        xor=["operand_value2"],
        desc="image to perform operation 2 with",
    )

    desc = "float value to perform operation 2 with"
    operand_value2 = traits.Float(
        argstr="%.8f", mandatory=True, position=6, xor=["operand_file2"], desc=desc
    )


class TupleMaths(MathsCommand):
    """Mathematical operations on tuples.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces import niftyseg
    >>> tuple = niftyseg.TupleMaths()
    >>> tuple.inputs.in_file = 'im1.nii'
    >>> tuple.inputs.output_datatype = 'float'

    >>> # Test lncc operation
    >>> tuple_lncc = copy.deepcopy(tuple)
    >>> tuple_lncc.inputs.operation = 'lncc'
    >>> tuple_lncc.inputs.operand_file1 = 'im2.nii'
    >>> tuple_lncc.inputs.operand_value2 = 2.0
    >>> tuple_lncc.cmdline
    'seg_maths im1.nii -lncc im2.nii 2.00000000 -odt float im1_lncc.nii'
    >>> tuple_lncc.run()  # doctest: +SKIP

    >>> # Test lssd operation
    >>> tuple_lssd = copy.deepcopy(tuple)
    >>> tuple_lssd.inputs.operation = 'lssd'
    >>> tuple_lssd.inputs.operand_file1 = 'im2.nii'
    >>> tuple_lssd.inputs.operand_value2 = 1.0
    >>> tuple_lssd.cmdline
    'seg_maths im1.nii -lssd im2.nii 1.00000000 -odt float im1_lssd.nii'
    >>> tuple_lssd.run()  # doctest: +SKIP

    >>> # Test lltsnorm operation
    >>> tuple_lltsnorm = copy.deepcopy(tuple)
    >>> tuple_lltsnorm.inputs.operation = 'lltsnorm'
    >>> tuple_lltsnorm.inputs.operand_file1 = 'im2.nii'
    >>> tuple_lltsnorm.inputs.operand_value2 = 0.01
    >>> tuple_lltsnorm.cmdline
    'seg_maths im1.nii -lltsnorm im2.nii 0.01000000 -odt float im1_lltsnorm.nii'
    >>> tuple_lltsnorm.run()  # doctest: +SKIP

    """

    input_spec = TupleMathsInput


class MergeInput(MathsInput):
    """Input Spec for seg_maths merge operation."""

    dimension = traits.Int(mandatory=True, desc="Dimension to merge the images.")
    merge_files = traits.List(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=4,
        desc="List of images to merge to the working image <input>.",
    )


class Merge(MathsCommand):
    """Merge image files.

    See Also
    --------
    `Source code <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg>`__ --
    `Documentation <http://cmictig.cs.ucl.ac.uk/wiki/index.php/NiftySeg_documentation>`__

    Examples
    --------
    >>> from nipype.interfaces import niftyseg
    >>> node = niftyseg.Merge()
    >>> node.inputs.in_file = 'im1.nii'
    >>> files = ['im2.nii', 'im3.nii']
    >>> node.inputs.merge_files = files
    >>> node.inputs.dimension = 2
    >>> node.inputs.output_datatype = 'float'
    >>> node.cmdline
    'seg_maths im1.nii -merge 2 2 im2.nii im3.nii -odt float im1_merged.nii'

    """

    input_spec = MergeInput
    _suffix = "_merged"

    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for seg_maths."""
        if opt == "merge_files":
            return "-merge %d %d %s" % (len(val), self.inputs.dimension, " ".join(val))

        return super(Merge, self)._format_arg(opt, spec, val)
