from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractResampleCodeImageInputSpec(CommandLineInputSpec):
    inputCodeVolume = File(desc="Required: input file containing the code image", exists=True, argstr="--inputCodeVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing the standard image to clone the characteristics of.", exists=True, argstr="--inputReferenceVolume %s")
    inputTransform = File(desc="Required: input Rigid or Inverse-B-Spline transform file name", exists=True, argstr="--inputTransform %s")
    transformType = traits.Enum("Rigid", "Affine", "B-Spline", "Inverse-B-Spline", "None", desc="Transform type: Rigid or Inverse-B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled code image in acquisition space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleCodeImageOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled code image in acquisition space.", exists=True)


class gtractResampleCodeImage(SlicerCommandLine):
    """title: Resample Code Image

category: Diffusion.GTRACT

description: This program will resample a short integer code image using either the Rigid or Inverse-B-Spline transform.  The reference image is the DTI tensor anisotropy image space, and the input code image is in anatomical space.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleCodeImageInputSpec
    output_spec = gtractResampleCodeImageOutputSpec
    _cmd = " gtractResampleCodeImage "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
