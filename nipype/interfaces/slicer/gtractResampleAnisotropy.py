from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractResampleAnisotropyInputSpec(CommandLineInputSpec):
    inputAnisotropyVolume = File(desc="Required: input file containing the anisotropy image", exists=True, argstr="--inputAnisotropyVolume %s")
    inputAnatomicalVolume = File(desc="Required: input file containing the anatomical image whose characteristics will be cloned.", exists=True, argstr="--inputAnatomicalVolume %s")
    inputTransform = File(desc="Required: input Rigid OR Bspline transform file name", exists=True, argstr="--inputTransform %s")
    transformType = traits.Enum("Rigid", "B-Spline", desc="Transform type: Rigid, B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled transformed anisotropy image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleAnisotropyOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled transformed anisotropy image.", exists=True)


class gtractResampleAnisotropy(SlicerCommandLine):
    """title: Resample Anisotropy

category: Diffusion.GTRACT

description: This program will resample a floating point image using either the Rigid or B-Spline transform. You may want to save the aligned B0 image after each of the anisotropy map co-registration steps with the anatomical image to check the registration quality with another tool.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleAnisotropyInputSpec
    output_spec = gtractResampleAnisotropyOutputSpec
    _cmd = " gtractResampleAnisotropy "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
