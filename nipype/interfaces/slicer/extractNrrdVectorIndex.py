from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class extractNrrdVectorIndexInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input file containing the vector that will be extracted", exists=True, argstr="--inputVolume %s")
    vectorIndex = traits.Int(desc="Index in the vector image to extract", argstr="--vectorIndex %d")
    setImageOrientation = traits.Enum("AsAcquired", "Axial", "Coronal", "Sagittal", desc="Sets the image orientation of the extracted vector (Axial, Coronal, Sagittal)", argstr="--setImageOrientation %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing the vector image at the given index", argstr="--outputVolume %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class extractNrrdVectorIndexOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing the vector image at the given index", exists=True)


class extractNrrdVectorIndex(SlicerCommandLine):
    """title: Extract Nrrd Index

category: Diffusion.GTRACT

description: This program will extract a 3D image (single vector) from a vector 3D image at a given vector index.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = extractNrrdVectorIndexInputSpec
    output_spec = extractNrrdVectorIndexOutputSpec
    _cmd = " extractNrrdVectorIndex "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}
