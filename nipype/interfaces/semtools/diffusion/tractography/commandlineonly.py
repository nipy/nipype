# -*- coding: utf8 -*-
"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

import os

from ....base import (CommandLine, CommandLineInputSpec, SEMLikeCommandLine,
                      TraitedSpec, File, Directory, traits, isdefined,
                      InputMultiPath, OutputMultiPath)


class fiberstatsInputSpec(CommandLineInputSpec):
    fiber_file = File(desc="DTI Fiber File", exists=True, argstr="--fiber_file %s")
    verbose = traits.Bool(desc="produce verbose output", argstr="--verbose ")


class fiberstatsOutputSpec(TraitedSpec):
    pass


class fiberstats(SEMLikeCommandLine):

    """title: FiberStats (DTIProcess)

category: Diffusion.Tractography.CommandLineOnly

description: Obsolete tool - Not used anymore

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

    _input_spec = fiberstatsInputSpec
    _output_spec = fiberstatsOutputSpec
    _cmd = " fiberstats "
    _outputs_filenames = {}
    _redirect_x = False
