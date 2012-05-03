from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractResampleDWIInPlaceInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image is a 4D NRRD image.", exists=True, argstr="--inputVolume %s")
    inputTransform = File(desc="Required: transform file derived from rigid registration of b0 image to reference structural image.", exists=True, argstr="--inputTransform %s")
    debugLevel = traits.Int(desc="Display debug messages, and produce debug intermediate results.  0=OFF, 1=Minimal, 10=Maximum debugging.", argstr="--debugLevel %d")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output image (NRRD file) that has been transformed into the space of the structural image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleDWIInPlaceOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: output image (NRRD file) that has been transformed into the space of the structural image.", exists=True)


class gtractResampleDWIInPlace(SlicerCommandLine):
    """title: Resample DWI In Place

category: Diffusion.GTRACT

description: Resamples DWI image to structural image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleDWIInPlaceInputSpec
    output_spec = gtractResampleDWIInPlaceOutputSpec
    _cmd = " gtractResampleDWIInPlace "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}
