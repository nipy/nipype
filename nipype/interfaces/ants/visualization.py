"""The ants visualisation module provides basic functions based on ITK.
"""

import os

from ..base import TraitedSpec, File, traits
from .base import ANTSCommand, ANTSCommandInputSpec


class ConvertScalarImageToRGBInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr="%d",
        usedefault=True,
        desc="image dimension (2 or 3)",
        mandatory=True,
        position=0,
    )
    input_image = File(
        argstr="%s",
        exists=True,
        desc="Main input is a 3-D grayscale image.",
        mandatory=True,
        position=1,
    )
    output_image = traits.Str(
        "rgb.nii.gz", argstr="%s", usedefault=True, desc="rgb output image", position=2
    )
    mask_image = traits.Either(
        "none",
        traits.File(exists=True),
        argstr="%s",
        desc="mask image",
        position=3,
        default="none",
        usedefault=True,
    )
    colormap = traits.Enum(
        "grey",
        "red",
        "green",
        "blue",
        "copper",
        "jet",
        "hsv",
        "spring",
        "summer",
        "autumn",
        "winter",
        "hot",
        "cool",
        "overunder",
        "custom",
        argstr="%s",
        desc="Select a colormap",
        mandatory=True,
        position=4,
    )
    custom_color_map_file = traits.Str(
        "none", argstr="%s", usedefault=True, desc="custom color map file", position=5
    )
    minimum_input = traits.Int(
        argstr="%d", desc="minimum input", mandatory=True, position=6
    )
    maximum_input = traits.Int(
        argstr="%d", desc="maximum input", mandatory=True, position=7
    )
    minimum_RGB_output = traits.Int(0, usedefault=True, argstr="%d", position=8)
    maximum_RGB_output = traits.Int(255, usedefault=True, argstr="%d", position=9)


class ConvertScalarImageToRGBOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="converted RGB image")


class ConvertScalarImageToRGB(ANTSCommand):
    """
    Convert scalar images to RGB.

    Examples
    --------
    >>> from nipype.interfaces.ants.visualization import ConvertScalarImageToRGB
    >>> converter = ConvertScalarImageToRGB()
    >>> converter.inputs.dimension = 3
    >>> converter.inputs.input_image = 'T1.nii.gz'
    >>> converter.inputs.colormap = 'jet'
    >>> converter.inputs.minimum_input = 0
    >>> converter.inputs.maximum_input = 6
    >>> converter.cmdline
    'ConvertScalarImageToRGB 3 T1.nii.gz rgb.nii.gz none jet none 0 6 0 255'

    """

    _cmd = "ConvertScalarImageToRGB"
    input_spec = ConvertScalarImageToRGBInputSpec
    output_spec = ConvertScalarImageToRGBOutputSpec

    def _format_arg(self, opt, spec, val):
        return super()._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_image"] = os.path.join(os.getcwd(), self.inputs.output_image)
        return outputs


class CreateTiledMosaicInputSpec(ANTSCommandInputSpec):
    input_image = File(
        argstr="-i %s",
        exists=True,
        desc="Main input is a 3-D grayscale image.",
        mandatory=True,
    )
    rgb_image = File(
        argstr="-r %s",
        exists=True,
        desc=(
            "An optional Rgb image can be added as an overlay."
            "It must have the same image"
            "geometry as the input grayscale image."
        ),
        mandatory=True,
    )
    mask_image = File(
        argstr="-x %s", exists=True, desc="Specifies the ROI of the RGB voxels used."
    )
    alpha_value = traits.Float(
        argstr="-a %.2f",
        desc=(
            "If an Rgb image is provided, render the overlay "
            "using the specified alpha parameter."
        ),
    )
    output_image = traits.Str(
        "output.png",
        argstr="-o %s",
        desc="The output consists of the tiled mosaic image.",
        usedefault=True,
    )
    tile_geometry = traits.Str(
        argstr="-t %s",
        desc=(
            "The tile geometry specifies the number of rows and columns"
            'in the output image. For example, if the user specifies "5x10", '
            "then 5 rows by 10 columns of slices are rendered. If R < 0 and C > "
            "0 (or vice versa), the negative value is selected"
            "based on direction."
        ),
    )
    direction = traits.Int(
        argstr="-d %d",
        desc=(
            "Specifies the direction of "
            "the slices. If no direction is specified, the "
            "direction with the coarsest spacing is chosen."
        ),
    )
    pad_or_crop = traits.Str(
        argstr="-p %s",
        desc="argument passed to -p flag:"
        "[padVoxelWidth,<constantValue=0>]"
        "[lowerPadding[0]xlowerPadding[1],upperPadding[0]xupperPadding[1],"
        "constantValue]"
        "The user can specify whether to pad or crop a specified "
        "voxel-width boundary of each individual slice. For this "
        "program, cropping is simply padding with negative voxel-widths."
        "If one pads (+), the user can also specify a constant pad "
        "value (default = 0). If a mask is specified, the user can use "
        'the mask to define the region, by using the keyword "mask"'
        ' plus an offset, e.g. "-p mask+3".',
    )
    slices = traits.Str(
        argstr="-s %s",
        desc=(
            "Number of slices to increment Slice1xSlice2xSlice3"
            "[numberOfSlicesToIncrement,<minSlice=0>,<maxSlice=lastSlice>]"
        ),
    )
    flip_slice = traits.Str(argstr="-f %s", desc="flipXxflipY")
    permute_axes = traits.Bool(argstr="-g", desc="doPermute")


class CreateTiledMosaicOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc="image file")


class CreateTiledMosaic(ANTSCommand):
    """The program CreateTiledMosaic in conjunction with ConvertScalarImageToRGB
    provides useful functionality for common image analysis tasks. The basic
    usage of CreateTiledMosaic is to tile a 3-D image volume slice-wise into
    a 2-D image.

    Examples
    --------

    >>> from nipype.interfaces.ants.visualization import CreateTiledMosaic
    >>> mosaic_slicer = CreateTiledMosaic()
    >>> mosaic_slicer.inputs.input_image = 'T1.nii.gz'
    >>> mosaic_slicer.inputs.rgb_image = 'rgb.nii.gz'
    >>> mosaic_slicer.inputs.mask_image = 'mask.nii.gz'
    >>> mosaic_slicer.inputs.output_image = 'output.png'
    >>> mosaic_slicer.inputs.alpha_value = 0.5
    >>> mosaic_slicer.inputs.direction = 2
    >>> mosaic_slicer.inputs.pad_or_crop = '[ -15x -50 , -15x -30 ,0]'
    >>> mosaic_slicer.inputs.slices = '[2 ,100 ,160]'
    >>> mosaic_slicer.cmdline
    'CreateTiledMosaic -a 0.50 -d 2 -i T1.nii.gz -x mask.nii.gz -o output.png -p [ -15x -50 , -15x -30 ,0] \
-r rgb.nii.gz -s [2 ,100 ,160]'
    """

    _cmd = "CreateTiledMosaic"
    input_spec = CreateTiledMosaicInputSpec
    output_spec = CreateTiledMosaicOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["output_image"] = os.path.join(os.getcwd(), self.inputs.output_image)
        return outputs
