from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractClipAnisotropyInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image file name", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the clipped anisotropy image", argstr="--outputVolume %s")
    clipFirstSlice = traits.Bool(desc="Clip the first slice of the anisotropy image", argstr="--clipFirstSlice ")
    clipLastSlice = traits.Bool(desc="Clip the last slice of the anisotropy image", argstr="--clipLastSlice ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractClipAnisotropyOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the clipped anisotropy image", exists=True)


class gtractClipAnisotropy(SlicerCommandLine):
    """title: Clip Anisotropy

category: Diffusion.GTRACT

description: This program will zero the first and/or last slice of an anisotropy image, creating a clipped anisotropy image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractClipAnisotropyInputSpec
    output_spec = gtractClipAnisotropyOutputSpec
    _cmd = " gtractClipAnisotropy "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
