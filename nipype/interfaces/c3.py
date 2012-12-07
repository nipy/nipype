"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)
"""
from nipype.interfaces.base import (CommandLineInputSpec, traits, TraitedSpec,
				    File, SEMLikeCommandLine)


class C3dAffineToolInputSpec(CommandLineInputSpec):
    reference_file = File(exists=True, argstr="-ref %s", position=1)
    source_file = File(exists=True, argstr='-src %s', position=2)
    transform_file = File(exists=True, argstr='%s', position=3)
    itk_transform = traits.Either(traits.Bool, File(), hash_files=False,
				  desc="Export ITK transform.",
				  argstr="-oitk %s", position=5)
    fsl2ras = traits.Bool(argstr='-fsl2ras', position=4)


class C3dAffineToolOutputSpec(TraitedSpec):
    itk_transform = File(exists=True)


class C3dAffineTool(SEMLikeCommandLine):
    """Converts fsl-style Affine registration into ANTS compatible itk format

    Example
    >>> from nipype.interfaces.c3 import C3dAffineTool
    >>> c3 = C3dAffineTool()
    >>> c3.inputs.source_file = 'cmatrix.mat'
    >>> c3.inputs.itk_transform = 'affine.txt'
    >>> c3.inputs.fsl2ras = True
    >>> c3.cmdline
    'c3d_affine_tool -src cmatrix.mat -fsl2ras -oitk affine.txt'
    """
    input_spec = C3dAffineToolInputSpec
    output_spec = C3dAffineToolOutputSpec

    _cmd = 'c3d_affine_tool'
    _outputs_filenames = {'itk_transform': 'affine.txt'}
