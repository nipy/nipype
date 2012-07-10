# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    The maths module provides higher-level interfaces to some of the operations
    that can be performed with the fslmaths command-line program.
"""
import os
import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, traits, InputMultiPath,
                                    isdefined)


class MathsInput(FSLCommandInputSpec):

    in_file = File(position=2, argstr="%s", exists=True, mandatory=True,
                desc="image to operate on")
    out_file = File(genfile=True, position=-2, argstr="%s", desc="image to write", hash_files=False)
    _dtypes = ["float", "char", "int", "short", "double", "input"]
    internal_datatype = traits.Enum(*_dtypes, position=1, argstr="-dt %s",
                                    desc="datatype to use for calculations (default is float)")
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s",
                                  desc="datatype to use for output (default uses input type)")


class MathsOutput(TraitedSpec):

    out_file = File(exists=True, desc="image written after calculations")


class MathsCommand(FSLCommand):

    _cmd = "fslmaths"
    input_spec = MathsInput
    output_spec = MathsOutput
    _suffix = "_maths"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        outputs["out_file"] = os.path.abspath(self.inputs.out_file)
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class ChangeDataTypeInput(MathsInput):

    _dtypes = ["float", "char", "int", "short", "double", "input"]
    output_datatype = traits.Enum(*_dtypes,
                                  position=-1, argstr="-odt %s", mandatory=True,
                                  desc="output data type")


class ChangeDataType(MathsCommand):
    """Use fslmaths to change the datatype of an image.

    """
    input_spec = ChangeDataTypeInput
    _suffix = "_chdt"


class ThresholdInputSpec(MathsInput):

    thresh = traits.Float(mandatory=True, position=3, argstr="%s",
                          desc="threshold value")
    direction = traits.Enum("below", "above", usedefault=True,
                            desc="zero-out either below or above thresh value")
    use_robust_range = traits.Bool(desc="inteperet thresh as percentage (0-100) of robust range")
    use_nonzero_voxels = traits.Bool(desc="use nonzero voxels to caluclate robust range",
                                     requires=["use_robust_range"])


class Threshold(MathsCommand):
    """Use fslmaths to apply a threshold to an image in a variety of ways.

    """
    input_spec = ThresholdInputSpec
    _suffix = "_thresh"

    def _format_arg(self, name, spec, value):
        if name == "thresh":
            arg = "-"
            _si = self.inputs
            if self.inputs.direction == "above":
                arg += "u"
            arg += "thr"
            if isdefined(_si.use_robust_range) and _si.use_robust_range:
                if isdefined(_si.use_nonzero_voxels) and _si.use_nonzero_voxels:
                    arg += "P"
                else:
                    arg += "p"
            arg += " %.10f" % value
            return arg
        return super(Threshold, self)._format_arg(name, spec, value)


class MeanImageInput(MathsInput):

    dimension = traits.Enum("T", "X", "Y", "Z", usedefault=True, argstr="-%smean", position=3,
                            desc="dimension to mean across")


class MeanImage(MathsCommand):
    """Use fslmaths to generate a mean image across a given dimension.

    """
    input_spec = MeanImageInput
    _suffix = "_mean"


class IsotropicSmoothInput(MathsInput):

    fwhm = traits.Float(mandatory=True, xor=["sigma"], position=3, argstr="-s %.5f",
                        desc="fwhm of smoothing kernel")
    sigma = traits.Float(mandatory=True, xor=["fwhm"], position=3, argstr="-s %.5f",
                         desc="sigma of smoothing kernel")


class IsotropicSmooth(MathsCommand):
    """Use fslmaths to spatially smooth an image with a gaussian kernel.

    """
    input_spec = IsotropicSmoothInput
    _suffix = "_smooth"

    def _format_arg(self, name, spec, value):
        if name == "fwhm":
            sigma = float(value) / np.sqrt(8 * np.log(2))
            return spec.argstr % sigma
        return super(IsotropicSmooth, self)._format_arg(name, spec, value)


class ApplyMaskInput(MathsInput):

    mask_file = File(exists=True, mandatory=True, argstr="-mas %s", position=3,
                      desc="binary image defining mask space")


class ApplyMask(MathsCommand):
    """Use fslmaths to apply a binary mask to another image.

    """
    input_spec = ApplyMaskInput
    _suffix = "_masked"


class KernelInput(MathsInput):

    kernel_shape = traits.Enum("3D", "2D", "box", "boxv", "gauss", "sphere", "file",
                               argstr="-kernel %s", position=3, desc="kernel shape to use")
    kernel_size = traits.Float(argstr="%.4f", position=4, xor=["kernel_file"],
                             desc="kernel size - voxels for box/boxv, mm for sphere, mm sigma for gauss")
    kernel_file = File(exists=True, argstr="%s", position=4, xor=["kernel_size"],
                       desc="use external file for kernel")


class DilateInput(KernelInput):

    operation = traits.Enum("mean", "modal", "max", argstr="-dil%s", position=5, mandatory=True,
                            desc="filtering operation to perfoem in dilation")


class DilateImage(MathsCommand):
    """Use fslmaths to perform a spatial dilation of an image.

    """
    input_spec = DilateInput
    _suffix = "_dil"

    def _format_arg(self, name, spec, value):
        if name == "operation":
            return spec.argstr % dict(mean="M", modal="D", max="F")[value]
        return super(DilateImage, self)._format_arg(name, spec, value)


class ErodeInput(KernelInput):

    minimum_filter = traits.Bool(argstr="%s", position=5, usedefault=True, default_value=False,
                                 desc="if true, minimum filter rather than erosion by zeroing-out")


class ErodeImage(MathsCommand):
    """Use fslmaths to perform a spatial erosion of an image.

    """
    input_spec = ErodeInput
    _suffix = "_ero"

    def _format_arg(self, name, spec, value):
        if name == "minimum_filter":
            if value:
                return "-eroF"
            return "-ero"
        return super(ErodeImage, self)._format_arg(name, spec, value)


class SpatialFilterInput(KernelInput):

    operation = traits.Enum("mean", "median", "meanu", argstr="-f%s", position=5, mandatory=True,
                            desc="operation to filter with")


class SpatialFilter(MathsCommand):
    """Use fslmaths to spatially filter an image.

    """
    input_spec = SpatialFilterInput
    _suffix = "_filt"


class UnaryMathsInput(MathsInput):

    operation = traits.Enum("exp", "log", "sin", "cos", "sqr", "sqrt", "recip", "abs", "bin", "index",
                            argstr="-%s", position=3, mandatory=True,
                            desc="operation to perform")


class UnaryMaths(MathsCommand):
    """Use fslmaths to perorm a variety of mathematical operations on an image.

    """
    input_spec = UnaryMathsInput

    def _list_outputs(self):
        self._suffix = "_" + self.inputs.operation
        return super(UnaryMaths, self)._list_outputs()


class BinaryMathsInput(MathsInput):

    operation = traits.Enum("add", "sub", "mul", "div", "rem", "max", "min",
                            mandatory=True, argstr="-%s", position=3,
                            desc="operation to perform")
    operand_file = File(exists=True, argstr="%s", mandatory=True, position=4, xor=["operand_value"],
                        desc="second image to perform operation with")
    operand_value = traits.Float(argstr="%.8f", mandatory=True, position=4, xor=["operand_file"],
                                 desc="value to perform operation with")


class BinaryMaths(MathsCommand):
    """Use fslmaths to perform mathematical operations using a second image or a numeric value.

    """
    input_spec = BinaryMathsInput


class MultiImageMathsInput(MathsInput):

    op_string = traits.String(position=3, argstr="%s", mandatory=True,
                              desc="python formatted string of operations to perform")
    operand_files = InputMultiPath(File(exists=True), mandatory=True,
                                 desc="list of file names to plug into op string")


class MultiImageMaths(MathsCommand):
    """Use fslmaths to perform a sequence of mathematical operations.

    Examples
    --------
    from nipype.interfaces.fsl import MultiImageMaths
    maths = MultiImageMaths()
    maths.inputs.in_file = "functional.nii"
    maths.inputs.op_string = "-add %s -mul -1 -div %s"
    maths.inputs.operand_files = ["functional2.nii", "functional3.nii"]
    maths.inputs.out_file = functional4.nii
    maths.cmdline
    fslmaths functional1.nii -add functional2.nii -mul -1 -div functional3.nii functional4.nii

    """
    input_spec = MultiImageMathsInput

    def _format_arg(self, name, spec, value):
        if name == "op_string":
            return value % tuple(self.inputs.operand_files)
        return super(MultiImageMaths, self)._format_arg(name, spec, value)


class TemporalFilterInput(MathsInput):

    lowpass_sigma = traits.Float(-1, argstr="%.6f", position=4, usedefault=True,
                                 desc="lowpass filter sigma (in volumes)")
    highpass_sigma = traits.Float(-1, argstr="-bptf %.6f", position=3, usedefault=True,
                                  desc="highpass filter sigma (in volumes)")


class TemporalFilter(MathsCommand):
    """Use fslmaths to apply a low, high, or bandpass temporal filter to a timeseries.

    """
    input_spec = TemporalFilterInput
    _suffix = "_filt"
