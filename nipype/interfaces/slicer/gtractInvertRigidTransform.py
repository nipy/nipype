from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractInvertRigidTransformInputSpec(CommandLineInputSpec):
    inputTransform = File(desc="Required: input rigid transform file name", exists=True, argstr="--inputTransform %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output transform file name", argstr="--outputTransform %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractInvertRigidTransformOutputSpec(TraitedSpec):
    outputTransform = File(desc="Required: output transform file name", exists=True)


class gtractInvertRigidTransform(SlicerCommandLine):
    """title: Rigid Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a Rigid transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractInvertRigidTransformInputSpec
    output_spec = gtractInvertRigidTransformOutputSpec
    _cmd = " gtractInvertRigidTransform "
    _outputs_filenames = {'outputTransform':'outputTransform.mat'}
