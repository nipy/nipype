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
    >>> c3.inputs.source_file = cmatrix.mat
    >>> c3.inputs.itk_transform = True
    >>> c3.inouts.fsl2ras = True
    >>> c3.run() #doctest: +SKIP
    """
    input_spec = C3dAffineToolInputSpec
    output_spec = C3dAffineToolOutputSpec

    _cmd = 'c3d_affine_tool'
    _outputs_filenames = {'itk_transform': 'affine.txt'}
