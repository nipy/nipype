from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractConcatDwiInputSpec(CommandLineInputSpec):
    inputVolume = InputMultiPath(File(exists=True), desc="Required: input file containing the first diffusion weighted image", argstr="--inputVolume %s...")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the combined diffusion weighted images.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractConcatDwiOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the combined diffusion weighted images.", exists=True)


class gtractConcatDwi(SlicerCommandLine):
    """title: Concat DWI Images

category: Diffusion.GTRACT

description: This program will concatenate two DTI runs together.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractConcatDwiInputSpec
    output_spec = gtractConcatDwiOutputSpec
    _cmd = " gtractConcatDwi "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
