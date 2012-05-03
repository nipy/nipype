from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractResampleB0InputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the 4D image", exists=True, argstr="--inputVolume %s")
    inputAnatomicalVolume = File(desc="Required: input file containing the anatomical image defining the origin, spacing and size of the resampled image (template)", exists=True, argstr="--inputAnatomicalVolume %s")
    inputTransform = File(desc="Required: input Rigid OR Bspline transform file name", exists=True, argstr="--inputTransform %s")
    vectorIndex = traits.Int(desc="Index in the diffusion weighted image set for the B0 image", argstr="--vectorIndex %d")
    transformType = traits.Enum("Rigid", "B-Spline", desc="Transform type: Rigid, B-Spline", argstr="--transformType %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the resampled input image.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractResampleB0OutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the resampled input image.", exists=True)


class gtractResampleB0(SlicerCommandLine):
    """title: Resample B0

category: Diffusion.GTRACT

description: This program will resample a signed short image using either a Rigid or B-Spline transform. The user must specify a template image that will be used to define the origin, orientation, spacing, and size of the resampled image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractResampleB0InputSpec
    output_spec = gtractResampleB0OutputSpec
    _cmd = " gtractResampleB0 "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
