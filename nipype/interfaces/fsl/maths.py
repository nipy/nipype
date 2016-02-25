# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The maths module provides higher-level interfaces to some of the operations
    that can be performed with the fslmaths command-line program.

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

from __future__ import division
import numpy as np

from ..base import (TraitedSpec, File, GenFile, traits, InputMultiPath, isdefined)
from ..fsl.base import FSLCommand, FSLCommandInputSpec


class MathsInput(FSLCommandInputSpec):
    in_file = File(position=2, argstr="%s", exists=True, mandatory=True,
                   desc="image to operate on")
    out_file = GenFile(
        template='{in_file}_maths{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    _dtypes = ["float", "char", "int", "short", "double", "input"]
    internal_datatype = traits.Enum(*_dtypes, position=1, argstr="-dt %s",
                                    desc="datatype to use for calculations (default is float)")
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s",
                                  desc="datatype to use for output (default uses input type)")
    nan2zeros = traits.Bool(False, usedefault=True, position=3, argstr='-nan',
                            desc='change NaNs to zeros before doing anything')


class MathsOutput(TraitedSpec):
    out_file = File(exists=True, desc="image written after calculations")


class MathsCommand(FSLCommand):
    _cmd = "fslmaths"
    _input_spec = MathsInput
    _output_spec = MathsOutput


class ChangeDataTypeInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_chdt{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")

    _dtypes = ["float", "char", "int", "short", "double", "input"]
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s", mandatory=True,
                                  desc="output data type")


class ChangeDataType(MathsCommand):
    """Use fslmaths to change the datatype of an image."""
    _input_spec = ChangeDataTypeInput


class ThresholdInputSpec(MathsInput):
    out_file = GenFile(
        template='{in_file}_thresh{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    thresh = traits.Float(mandatory=True, position=4, argstr="%s",
                          desc="threshold value")
    direction = traits.Enum("below", "above", usedefault=True,
                            desc="zero-out either below or above thresh value")
    use_robust_range = traits.Bool(desc="interpret thresh as percentage (0-100) of robust range")
    use_nonzero_voxels = traits.Bool(desc="use nonzero voxels to calculate robust range",
                                     requires=["use_robust_range"])

    def _format_arg(self, name, spec, value):
        if name == "thresh":
            arg = "-"
            if self.direction == "above":
                arg += "u"
            arg += "thr"
            if isdefined(self.use_robust_range) and self.use_robust_range:
                if isdefined(self.use_nonzero_voxels) and self.use_nonzero_voxels:
                    arg += "P"
                else:
                    arg += "p"
            arg += " %.10f" % value
            return arg
        return super(ThresholdInputSpec, self)._format_arg(name, spec, value)

class Threshold(MathsCommand):
    """Use fslmaths to apply a threshold to an image in a variety of ways."""
    _input_spec = ThresholdInputSpec


class MeanImageInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_mean{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    dimension = traits.Enum("T", "X", "Y", "Z", usedefault=True, argstr="-%smean", position=4,
                            desc="dimension to mean across")


class MeanImage(MathsCommand):
    """Use fslmaths to generate a mean image across a given dimension."""
    _input_spec = MeanImageInput


class MaxImageInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_max{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    dimension = traits.Enum("T", "X", "Y", "Z", usedefault=True, argstr="-%smax", position=4,
                            desc="dimension to max across")


class MaxImage(MathsCommand):
    """
    Use fslmaths to generate a max image across a given dimension.

    Examples
    --------
    >>> from nipype.interfaces.fsl.maths import MaxImage
    >>> maxer = MaxImage()
    >>> maxer.inputs.in_file = "functional.nii"  # doctest: +SKIP
    >>> maxer.dimension = "T"
    >>> maxer.cmdline  # doctest: +SKIP
    'fslmaths functional.nii -Tmax functional_max.nii'

    """
    _input_spec = MaxImageInput


class IsotropicSmoothInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_smooth{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    fwhm = traits.Float(mandatory=True, xor=["sigma"], position=4, argstr="-s %.5f",
                        desc="fwhm of smoothing kernel [mm]")
    sigma = traits.Float(mandatory=True, xor=["fwhm"], position=4, argstr="-s %.5f",
                         desc="sigma of smoothing kernel [mm]")

    def _format_arg(self, name, spec, value):
        if name == "fwhm":
            sigma = float(value) / np.sqrt(8 * np.log(2))
            return spec.argstr % sigma
        return super(IsotropicSmoothInput, self)._format_arg(name, spec, value)

class IsotropicSmooth(MathsCommand):
    """Use fslmaths to spatially smooth an image with a gaussian kernel."""
    _input_spec = IsotropicSmoothInput


class ApplyMaskInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_masked{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    mask_file = File(exists=True, mandatory=True, argstr="-mas %s", position=4,
                     desc="binary image defining mask space")


class ApplyMask(MathsCommand):
    """Use fslmaths to apply a binary mask to another image."""
    _input_spec = ApplyMaskInput


class KernelInput(MathsInput):
    kernel_shape = traits.Enum("3D", "2D", "box", "boxv", "gauss", "sphere", "file",
                               argstr="-kernel %s", position=4, desc="kernel shape to use")
    kernel_size = traits.Float(argstr="%.4f", position=5, xor=["kernel_file"],
                               desc="kernel size - voxels for box/boxv, mm for sphere, mm sigma for gauss")
    kernel_file = File(exists=True, argstr="%s", position=5, xor=["kernel_size"],
                       desc="use external file for kernel")


class DilateInput(KernelInput):
    out_file = GenFile(
        template='{in_file}_dil{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    operation = traits.Enum("mean", "modal", "max", argstr="-dil%s", position=6, mandatory=True,
                            desc="filtering operation to perfoem in dilation")

    def _format_arg(self, name, spec, value):
        if name == "operation":
            return spec.argstr % dict(mean="M", modal="D", max="F")[value]
        return super(DilateInput, self)._format_arg(name, spec, value)


class DilateImage(MathsCommand):
    """Use fslmaths to perform a spatial dilation of an image."""
    _input_spec = DilateInput


class ErodeInput(KernelInput):
    out_file = GenFile(
        template='{in_file}_ero{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    minimum_filter = traits.Bool(
        False, argstr="-eroF", position=6, usedefault=True,
        desc="if true, minimum filter rather than erosion by zeroing-out")

    def _format_arg(self, name, spec, value):
        if name == "minimum_filter":
            if not value:
                return "-ero"
        return super(ErodeInput, self)._format_arg(name, spec, value)

class ErodeImage(MathsCommand):
    """Use fslmaths to perform a spatial erosion of an image."""
    _input_spec = ErodeInput


class SpatialFilterInput(KernelInput):
    out_file = GenFile(
        template='{in_file}_{operation}{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    operation = traits.Enum("mean", "median", "meanu", argstr="-f%s", position=6, mandatory=True,
                            desc="operation to filter with")


class SpatialFilter(MathsCommand):
    """Use fslmaths to spatially filter an image."""
    _input_spec = SpatialFilterInput


class UnaryMathsInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_{operation}{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    operation = traits.Enum("exp", "log", "sin", "cos", "tan", "asin", "acos", "atan", "sqr", "sqrt",
                            "recip", "abs", "bin", "binv", "fillh", "fillh26", "index", "edge", "nan",
                            "nanm", "rand", "randn", "range",
                            argstr="-%s", position=4, mandatory=True,
                            desc="operation to perform")


class UnaryMaths(MathsCommand):
    """Use fslmaths to perorm a variety of mathematical operations on an image."""
    _input_spec = UnaryMathsInput


class BinaryMathsInput(MathsInput):
    operation = traits.Enum("add", "sub", "mul", "div", "rem", "max", "min",
                            mandatory=True, argstr="-%s", position=4,
                            desc="operation to perform")
    operand_file = File(exists=True, argstr="%s", mandatory=True, position=5, xor=["operand_value"],
                        desc="second image to perform operation with")
    operand_value = traits.Float(argstr="%.8f", mandatory=True, position=5, xor=["operand_file"],
                                 desc="value to perform operation with")


class BinaryMaths(MathsCommand):
    """
    Use fslmaths to perform mathematical operations using a second
    image or a numeric value.
    """
    _input_spec = BinaryMathsInput


class MultiImageMathsInput(MathsInput):
    op_string = traits.String(position=4, argstr="%s", mandatory=True,
                              desc="python formatted string of operations to perform")
    operand_files = InputMultiPath(File(exists=True), mandatory=True,
                                   desc="list of file names to plug into op string")

    def _format_arg(self, name, spec, value):
        if name == "op_string":
            return value % tuple(self.operand_files)
        return super(MultiImageMathsInput, self)._format_arg(name, spec, value)

class MultiImageMaths(MathsCommand):
    """Use fslmaths to perform a sequence of mathematical operations.

    Examples
    --------
    >>> from nipype.interfaces.fsl import MultiImageMaths
    >>> maths = MultiImageMaths()
    >>> maths.inputs.in_file = "functional.nii"
    >>> maths.inputs.op_string = "-add %s -mul -1 -div %s"
    >>> maths.inputs.operand_files = ["functional2.nii", "functional3.nii"]
    >>> maths.cmdline
    'fslmaths functional.nii -add functional2.nii -mul -1 -div functional3.nii functional_maths.nii.gz'

    """
    _input_spec = MultiImageMathsInput


class TemporalFilterInput(MathsInput):
    out_file = GenFile(
        template='{in_file}_filt{output_type_}', position=-2, argstr="%s", hash_files=False,
        desc="image to write")
    lowpass_sigma = traits.Float(-1, argstr="%.6f", position=5, usedefault=True,
                                 desc="lowpass filter sigma (in volumes)")
    highpass_sigma = traits.Float(-1, argstr="-bptf %.6f", position=4, usedefault=True,
                                  desc="highpass filter sigma (in volumes)")


class TemporalFilter(MathsCommand):
    """Use fslmaths to apply a low, high, or bandpass temporal filter to a timeseries. """
    _input_spec = TemporalFilterInput
