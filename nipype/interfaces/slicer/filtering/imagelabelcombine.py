# -*- coding: utf-8 -*-
# -*- coding: utf8 -*-
"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

from nipype.interfaces.base import CommandLine, CommandLineInputSpec, SEMLikeCommandLine, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os


class ImageLabelCombineInputSpec(CommandLineInputSpec):
    InputLabelMap_A = File(position=-3, desc="Label map image", exists=True, argstr="%s")
    InputLabelMap_B = File(position=-2, desc="Label map image", exists=True, argstr="%s")
    OutputLabelMap = traits.Either(traits.Bool, File(), position=-1, hash_files=False, desc="Resulting Label map image", argstr="%s")
    first_overwrites = traits.Bool(desc="Use first or second label when both are present", argstr="--first_overwrites ")


class ImageLabelCombineOutputSpec(TraitedSpec):
    OutputLabelMap = File(position=-1, desc="Resulting Label map image", exists=True)


class ImageLabelCombine(SEMLikeCommandLine):
    """title: Image Label Combine

category: Filtering

description: Combine two label maps into one

version: 0.1.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/ImageLabelCombine

contributor: Alex Yarmarkovich (SPL, BWH)

"""

    input_spec = ImageLabelCombineInputSpec
    output_spec = ImageLabelCombineOutputSpec
    _cmd = "ImageLabelCombine "
    _outputs_filenames = {'OutputLabelMap': 'OutputLabelMap.nii'}
