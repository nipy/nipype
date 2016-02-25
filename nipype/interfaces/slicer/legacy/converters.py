# -*- coding: utf8 -*-
"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

from nipype.interfaces.base import CommandLine, CommandLineInputSpec, SEMLikeCommandLine, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os


class BSplineToDeformationFieldInputSpec(CommandLineInputSpec):
    tfm = File(exists=True, argstr="--tfm %s")
    refImage = File(exists=True, argstr="--refImage %s")
    defImage = traits.Either(traits.Bool, File(), hash_files=False, argstr="--defImage %s")


class BSplineToDeformationFieldOutputSpec(TraitedSpec):
    defImage = File(exists=True)


class BSplineToDeformationField(SEMLikeCommandLine):
    """title: BSpline to deformation field

category: Legacy.Converters

description: Create a dense deformation field from a bspline+bulk transform.

version: 0.1.0.$Revision: 2104 $(alpha)

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BSplineToDeformationField

contributor: Andrey Fedorov (SPL, BWH)

acknowledgements: This work is funded by NIH grants R01 CA111288 and U01 CA151261.

"""

    _input_spec = BSplineToDeformationFieldInputSpec
    _output_spec = BSplineToDeformationFieldOutputSpec
    _cmd = "BSplineToDeformationField "
    _outputs_filenames = {'defImage': 'defImage.nii'}
