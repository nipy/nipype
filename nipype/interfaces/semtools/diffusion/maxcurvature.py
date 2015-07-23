# -*- coding: utf8 -*-
"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

from nipype.interfaces.base import CommandLine, CommandLineInputSpec, SEMLikeCommandLine, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os


class maxcurvatureInputSpec(CommandLineInputSpec):
    image = File(desc="FA Image", exists=True, argstr="--image %s")
    output = traits.Either(traits.Bool, File(), hash_files=False, desc="Output File", argstr="--output %s")
    sigma = traits.Float(desc="Scale of Gradients", argstr="--sigma %f")
    verbose = traits.Bool(desc="produce verbose output", argstr="--verbose ")


class maxcurvatureOutputSpec(TraitedSpec):
    output = File(desc="Output File", exists=True)


class maxcurvature(SEMLikeCommandLine):

    """title: MaxCurvature-Hessian (DTIProcess)

category: Diffusion

description: This program computes the Hessian of the FA image (--image). We use this scalar image as a registration input when doing DTI atlas building. For most adult FA we use a sigma of 2 whereas for neonate or primate images and sigma of 1 or 1.5 is more appropriate. For really noisy images, 2.5 - 4 can be considered. The final image (--output) shows the main feature of the input image.

version: 1.1.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); (1=University of Iowa Department of Psychiatry, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering) provided conversions to make DTIProcess compatible with Slicer execution, and simplified the stand-alone build requirements by removing the dependancies on boost and a fortran compiler.

"""

    input_spec = maxcurvatureInputSpec
    output_spec = maxcurvatureOutputSpec
    _cmd = " maxcurvature "
    _outputs_filenames = {'output': 'output.nii'}
    _redirect_x = False
