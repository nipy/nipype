from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractCopyImageOrientationInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the signed short image to reorient without resampling.", exists=True, argstr="--inputVolume %s")
    inputReferenceVolume = File(desc="Required: input file containing orietation that will be cloned.", exists=True, argstr="--inputReferenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD or Nifti file containing the reoriented image in reference image space.", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCopyImageOrientationOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD or Nifti file containing the reoriented image in reference image space.", exists=True)


class gtractCopyImageOrientation(SlicerCommandLine):
    """title: Copy Image Orientation

category: Diffusion.GTRACT

description: This program will copy the orientation from the reference image into the moving image. Currently, the registration process requires that the diffusion weighted images and the anatomical images have the same image orientation (i.e. Axial, Coronal, Sagittal). It is suggested that you copy the image orientation from the diffusion weighted images and apply this to the anatomical image. This image can be subsequently removed after the registration step is complete. We anticipate that this limitation will be removed in future versions of the registration programs.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCopyImageOrientationInputSpec
    output_spec = gtractCopyImageOrientationOutputSpec
    _cmd = " gtractCopyImageOrientation "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
