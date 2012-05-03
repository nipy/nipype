from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractImageConformityInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the signed short image to reorient without resampling.", exists=True, argstr="--inputVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing the standard image to clone the characteristics of.", exists=True, argstr="--inputReferenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output Nrrd or Nifti file containing the reoriented image in reference image space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractImageConformityOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output Nrrd or Nifti file containing the reoriented image in reference image space.", exists=True)


class gtractImageConformity(SlicerCommandLine):
    """title: Image Conformity

category: Diffusion.GTRACT

description: This program will straighten out the Direction and Origin to match the Reference Image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractImageConformityInputSpec
    output_spec = gtractImageConformityOutputSpec
    _cmd = " gtractImageConformity "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
