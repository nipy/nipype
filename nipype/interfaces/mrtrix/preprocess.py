# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os.path as op

from ...utils.filemanip import split_filename
from ..base import (
    CommandLineInputSpec,
    CommandLine,
    traits,
    TraitedSpec,
    File,
    InputMultiPath,
    isdefined,
)


class MRConvertInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="voxel-order data filename",
    )
    out_filename = File(genfile=True, argstr="%s", position=-1, desc="Output filename")
    extract_at_axis = traits.Enum(
        1,
        2,
        3,
        argstr="-coord %s",
        position=1,
        desc='"Extract data only at the coordinates specified. This option specifies the Axis. Must be used in conjunction with extract_at_coordinate.',
    )
    extract_at_coordinate = traits.List(
        traits.Float,
        argstr="%s",
        sep=",",
        position=2,
        minlen=1,
        maxlen=3,
        desc='"Extract data only at the coordinates specified. This option specifies the coordinates. Must be used in conjunction with extract_at_axis. Three comma-separated numbers giving the size of each voxel in mm.',
    )
    voxel_dims = traits.List(
        traits.Float,
        argstr="-vox %s",
        sep=",",
        position=3,
        minlen=3,
        maxlen=3,
        desc="Three comma-separated numbers giving the size of each voxel in mm.",
    )
    output_datatype = traits.Enum(
        "nii",
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr="-output %s",
        position=2,
        desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"',
    )  # , usedefault=True)
    extension = traits.Enum(
        "mif",
        "nii",
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        position=2,
        desc='"i.e. Bfloat". Can be "char", "short", "int", "long", "float" or "double"',
        usedefault=True,
    )
    layout = traits.Enum(
        "nii",
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr="-output %s",
        position=2,
        desc="specify the layout of the data in memory. The actual layout produced will depend on whether the output image format can support it.",
    )
    resample = traits.Float(
        argstr="-scale %d",
        position=3,
        units="mm",
        desc="Apply scaling to the intensity values.",
    )
    offset_bias = traits.Float(
        argstr="-scale %d",
        position=3,
        units="mm",
        desc="Apply offset to the intensity values.",
    )
    replace_NaN_with_zero = traits.Bool(
        argstr="-zero", position=3, desc="Replace all NaN values with zero."
    )
    prs = traits.Bool(
        argstr="-prs",
        position=3,
        desc="Assume that the DW gradients are specified in the PRS frame (Siemens DICOM only).",
    )


class MRConvertOutputSpec(TraitedSpec):
    converted = File(exists=True, desc="path/name of 4D volume in voxel order")


class MRConvert(CommandLine):
    """
    Perform conversion between different file types and optionally extract a subset of the input image.

    If used correctly, this program can be a very useful workhorse.
    In addition to converting images between different formats, it can
    be used to extract specific studies from a data set, extract a specific
    region of interest, flip the images, or to scale the intensity of the images.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> mrconvert = mrt.MRConvert()
    >>> mrconvert.inputs.in_file = 'dwi_FA.mif'
    >>> mrconvert.inputs.out_filename = 'dwi_FA.nii'
    >>> mrconvert.run()                                 # doctest: +SKIP
    """

    _cmd = "mrconvert"
    input_spec = MRConvertInputSpec
    output_spec = MRConvertOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["converted"] = self.inputs.out_filename
        if not isdefined(outputs["converted"]):
            outputs["converted"] = op.abspath(self._gen_outfilename())
        else:
            outputs["converted"] = op.abspath(outputs["converted"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        if isdefined(self.inputs.out_filename):
            outname = self.inputs.out_filename
        else:
            outname = name + "_mrconvert." + self.inputs.extension
        return outname


class DWI2TensorInputSpec(CommandLineInputSpec):
    in_file = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Diffusion-weighted images",
    )
    out_filename = File(
        name_template="%s_tensor.mif",
        name_source="in_file",
        output_name="tensor",
        argstr="%s",
        desc="Output tensor filename",
        position=-1,
    )
    encoding_file = File(
        argstr="-grad %s",
        position=2,
        desc=(
            "Encoding file supplied as a 4xN text file with "
            "each line is in the format [ X Y Z b ], where "
            "[ X Y Z ] describe the direction of the applied "
            "gradient, and b gives the b-value in units "
            "(1000 s/mm^2). See FSL2MRTrix()"
        ),
    )
    ignore_slice_by_volume = traits.List(
        traits.Int,
        argstr="-ignoreslices %s",
        sep=" ",
        position=2,
        minlen=2,
        maxlen=2,
        desc=(
            "Requires two values (i.e. [34 "
            "1] for [Slice Volume] Ignores "
            "the image slices specified "
            "when computing the tensor. "
            "Slice here means the z "
            "coordinate of the slice to be "
            "ignored."
        ),
    )
    ignore_volumes = traits.List(
        traits.Int,
        argstr="-ignorevolumes %s",
        sep=" ",
        position=2,
        minlen=1,
        desc=(
            "Requires two values (i.e. [2 5 6] for "
            "[Volumes] Ignores the image volumes "
            "specified when computing the tensor."
        ),
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc=("Do not display information messages or progress " "status."),
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class DWI2TensorOutputSpec(TraitedSpec):
    tensor = File(exists=True, desc="path/name of output diffusion tensor image")


class DWI2Tensor(CommandLine):
    """
    Converts diffusion-weighted images to tensor images.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> dwi2tensor = mrt.DWI2Tensor()
    >>> dwi2tensor.inputs.in_file = 'dwi.mif'
    >>> dwi2tensor.inputs.encoding_file = 'encoding.txt'
    >>> dwi2tensor.cmdline
    'dwi2tensor -grad encoding.txt dwi.mif dwi_tensor.mif'
    >>> dwi2tensor.run()                                   # doctest: +SKIP
    """

    _cmd = "dwi2tensor"
    input_spec = DWI2TensorInputSpec
    output_spec = DWI2TensorOutputSpec


class Tensor2VectorInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Diffusion tensor image",
    )
    out_filename = File(
        genfile=True, argstr="%s", position=-1, desc="Output vector filename"
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class Tensor2VectorOutputSpec(TraitedSpec):
    vector = File(
        exists=True,
        desc="the output image of the major eigenvectors of the diffusion tensor image.",
    )


class Tensor2Vector(CommandLine):
    """
    Generates a map of the major eigenvectors of the tensors in each voxel.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> tensor2vector = mrt.Tensor2Vector()
    >>> tensor2vector.inputs.in_file = 'dwi_tensor.mif'
    >>> tensor2vector.run()                             # doctest: +SKIP
    """

    _cmd = "tensor2vector"
    input_spec = Tensor2VectorInputSpec
    output_spec = Tensor2VectorOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["vector"] = self.inputs.out_filename
        if not isdefined(outputs["vector"]):
            outputs["vector"] = op.abspath(self._gen_outfilename())
        else:
            outputs["vector"] = op.abspath(outputs["vector"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_vector.mif"


class Tensor2FractionalAnisotropyInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Diffusion tensor image",
    )
    out_filename = File(
        genfile=True,
        argstr="%s",
        position=-1,
        desc="Output Fractional Anisotropy filename",
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class Tensor2FractionalAnisotropyOutputSpec(TraitedSpec):
    FA = File(
        exists=True,
        desc="the output image of the major eigenvectors of the diffusion tensor image.",
    )


class Tensor2FractionalAnisotropy(CommandLine):
    """
    Generates a map of the fractional anisotropy in each voxel.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> tensor2FA = mrt.Tensor2FractionalAnisotropy()
    >>> tensor2FA.inputs.in_file = 'dwi_tensor.mif'
    >>> tensor2FA.run()                                 # doctest: +SKIP
    """

    _cmd = "tensor2FA"
    input_spec = Tensor2FractionalAnisotropyInputSpec
    output_spec = Tensor2FractionalAnisotropyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["FA"] = self.inputs.out_filename
        if not isdefined(outputs["FA"]):
            outputs["FA"] = op.abspath(self._gen_outfilename())
        else:
            outputs["FA"] = op.abspath(outputs["FA"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_FA.mif"


class Tensor2ApparentDiffusionInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Diffusion tensor image",
    )
    out_filename = File(
        genfile=True,
        argstr="%s",
        position=-1,
        desc="Output Fractional Anisotropy filename",
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class Tensor2ApparentDiffusionOutputSpec(TraitedSpec):
    ADC = File(
        exists=True,
        desc="the output image of the major eigenvectors of the diffusion tensor image.",
    )


class Tensor2ApparentDiffusion(CommandLine):
    """
    Generates a map of the apparent diffusion coefficient (ADC) in each voxel

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> tensor2ADC = mrt.Tensor2ApparentDiffusion()
    >>> tensor2ADC.inputs.in_file = 'dwi_tensor.mif'
    >>> tensor2ADC.run()                                # doctest: +SKIP
    """

    _cmd = "tensor2ADC"
    input_spec = Tensor2ApparentDiffusionInputSpec
    output_spec = Tensor2ApparentDiffusionOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["ADC"] = self.inputs.out_filename
        if not isdefined(outputs["ADC"]):
            outputs["ADC"] = op.abspath(self._gen_outfilename())
        else:
            outputs["ADC"] = op.abspath(outputs["ADC"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_ADC.mif"


class MRMultiplyInputSpec(CommandLineInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be multiplied",
    )
    out_filename = File(
        genfile=True, argstr="%s", position=-1, desc="Output image filename"
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class MRMultiplyOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output image of the multiplication")


class MRMultiply(CommandLine):
    """
    Multiplies two images.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> MRmult = mrt.MRMultiply()
    >>> MRmult.inputs.in_files = ['dwi.mif', 'dwi_WMProb.mif']
    >>> MRmult.run()                                             # doctest: +SKIP
    """

    _cmd = "mrmult"
    input_spec = MRMultiplyInputSpec
    output_spec = MRMultiplyOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_filename
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_files[0])
        return name + "_MRMult.mif"


class MRTrixViewerInputSpec(CommandLineInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be viewed",
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class MRTrixViewerOutputSpec(TraitedSpec):
    pass


class MRTrixViewer(CommandLine):
    """
    Loads the input images in the MRTrix Viewer.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> MRview = mrt.MRTrixViewer()
    >>> MRview.inputs.in_files = 'dwi.mif'
    >>> MRview.run()                                    # doctest: +SKIP
    """

    _cmd = "mrview"
    input_spec = MRTrixViewerInputSpec
    output_spec = MRTrixViewerOutputSpec

    def _list_outputs(self):
        return


class MRTrixInfoInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be read",
    )


class MRTrixInfoOutputSpec(TraitedSpec):
    pass


class MRTrixInfo(CommandLine):
    """
    Prints out relevant header information found in the image specified.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> MRinfo = mrt.MRTrixInfo()
    >>> MRinfo.inputs.in_file = 'dwi.mif'
    >>> MRinfo.run()                                    # doctest: +SKIP
    """

    _cmd = "mrinfo"
    input_spec = MRTrixInfoInputSpec
    output_spec = MRTrixInfoOutputSpec

    def _list_outputs(self):
        return


class GenerateWhiteMatterMaskInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-3,
        desc="Diffusion-weighted images",
    )
    binary_mask = File(
        exists=True, argstr="%s", mandatory=True, position=-2, desc="Binary brain mask"
    )
    out_WMProb_filename = File(
        genfile=True,
        argstr="%s",
        position=-1,
        desc="Output WM probability image filename",
    )
    encoding_file = File(
        exists=True,
        argstr="-grad %s",
        mandatory=True,
        position=1,
        desc="Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix",
    )
    noise_level_margin = traits.Float(
        argstr="-margin %s",
        desc="Specify the width of the margin on either side of the image to be used to estimate the noise level (default = 10)",
    )


class GenerateWhiteMatterMaskOutputSpec(TraitedSpec):
    WMprobabilitymap = File(exists=True, desc="WMprobabilitymap")


class GenerateWhiteMatterMask(CommandLine):
    """
    Generates a white matter probability mask from the DW images.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> genWM = mrt.GenerateWhiteMatterMask()
    >>> genWM.inputs.in_file = 'dwi.mif'
    >>> genWM.inputs.encoding_file = 'encoding.txt'
    >>> genWM.run()                                     # doctest: +SKIP
    """

    _cmd = "gen_WM_mask"
    input_spec = GenerateWhiteMatterMaskInputSpec
    output_spec = GenerateWhiteMatterMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["WMprobabilitymap"] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name == "out_WMProb_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_WMProb.mif"


class ErodeInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input mask image to be eroded",
    )
    out_filename = File(
        genfile=True, argstr="%s", position=-1, desc="Output image filename"
    )
    number_of_passes = traits.Int(
        argstr="-npass %s", desc="the number of passes (default: 1)"
    )
    dilate = traits.Bool(
        argstr="-dilate", position=1, desc="Perform dilation rather than erosion"
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class ErodeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output image")


class Erode(CommandLine):
    """
    Erode (or dilates) a mask (i.e. binary) image

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> erode = mrt.Erode()
    >>> erode.inputs.in_file = 'mask.mif'
    >>> erode.run()                                     # doctest: +SKIP
    """

    _cmd = "erode"
    input_spec = ErodeInputSpec
    output_spec = ErodeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_filename
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_erode.mif"


class ThresholdInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="The input image to be thresholded",
    )
    out_filename = File(
        genfile=True, argstr="%s", position=-1, desc="The output binary image mask."
    )
    absolute_threshold_value = traits.Float(
        argstr="-abs %s", desc="Specify threshold value as absolute intensity."
    )
    percentage_threshold_value = traits.Float(
        argstr="-percent %s",
        desc="Specify threshold value as a percentage of the peak intensity in the input image.",
    )
    invert = traits.Bool(argstr="-invert", position=1, desc="Invert output binary mask")
    replace_zeros_with_NaN = traits.Bool(
        argstr="-nan", position=1, desc="Replace all zero values with NaN"
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class ThresholdOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="The output binary image mask.")


class Threshold(CommandLine):
    """
    Create bitwise image by thresholding image intensity.

    By default, the threshold level is determined using a histogram analysis
    to cut out the background. Otherwise, the threshold intensity can be
    specified using command line options.
    Note that only the first study is used for thresholding.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> thresh = mrt.Threshold()
    >>> thresh.inputs.in_file = 'wm_mask.mif'
    >>> thresh.run()                                             # doctest: +SKIP
    """

    _cmd = "threshold"
    input_spec = ThresholdInputSpec
    output_spec = ThresholdOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_filename
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_thresh.mif"


class MedianFilter3DInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be smoothed",
    )
    out_filename = File(
        genfile=True, argstr="%s", position=-1, desc="Output image filename"
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class MedianFilter3DOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output image")


class MedianFilter3D(CommandLine):
    """
    Smooth images using a 3x3x3 median filter.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> median3d = mrt.MedianFilter3D()
    >>> median3d.inputs.in_file = 'mask.mif'
    >>> median3d.run()                                  # doctest: +SKIP
    """

    _cmd = "median3D"
    input_spec = MedianFilter3DInputSpec
    output_spec = MedianFilter3DOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_filename
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_file)
        return name + "_median3D.mif"


class MRTransformInputSpec(CommandLineInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        mandatory=True,
        position=-2,
        desc="Input images to be transformed",
    )
    out_filename = File(genfile=True, argstr="%s", position=-1, desc="Output image")
    invert = traits.Bool(
        argstr="-inverse",
        position=1,
        desc="Invert the specified transform before using it",
    )
    replace_transform = traits.Bool(
        argstr="-replace",
        position=1,
        desc="replace the current transform by that specified, rather than applying it to the current transform",
    )
    transformation_file = File(
        exists=True,
        argstr="-transform %s",
        position=1,
        desc="The transform to apply, in the form of a 4x4 ascii file.",
    )
    template_image = File(
        exists=True,
        argstr="-template %s",
        position=1,
        desc="Reslice the input image to match the specified template image.",
    )
    reference_image = File(
        exists=True,
        argstr="-reference %s",
        position=1,
        desc="in case the transform supplied maps from the input image onto a reference image, use this option to specify the reference. Note that this implicitly sets the -replace option.",
    )
    flip_x = traits.Bool(
        argstr="-flipx",
        position=1,
        desc="assume the transform is supplied assuming a coordinate system with the x-axis reversed relative to the MRtrix convention (i.e. x increases from right to left). This is required to handle transform matrices produced by FSL's FLIRT command. This is only used in conjunction with the -reference option.",
    )
    quiet = traits.Bool(
        argstr="-quiet",
        position=1,
        desc="Do not display information messages or progress status.",
    )
    debug = traits.Bool(argstr="-debug", position=1, desc="Display debugging messages.")


class MRTransformOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="the output image of the transformation")


class MRTransform(CommandLine):
    """
    Apply spatial transformations or reslice images

    Example
    -------

    >>> MRxform = MRTransform()
    >>> MRxform.inputs.in_files = 'anat_coreg.mif'
    >>> MRxform.run()                                   # doctest: +SKIP
    """

    _cmd = "mrtransform"
    input_spec = MRTransformInputSpec
    output_spec = MRTransformOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_filename
        if not isdefined(outputs["out_file"]):
            outputs["out_file"] = op.abspath(self._gen_outfilename())
        else:
            outputs["out_file"] = op.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_filename":
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, name, _ = split_filename(self.inputs.in_files[0])
        return name + "_MRTransform.mif"
