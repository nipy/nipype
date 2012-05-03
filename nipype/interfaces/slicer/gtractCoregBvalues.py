from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractCoregBvaluesInputSpec(CommandLineInputSpec):
    movingVolume = File(desc="Required: input moving image file name. In order to register gradients within a scan to its first gradient, set the movingVolume and fixedVolume as the same image.", exists=True, argstr="--movingVolume %s")
    fixedVolume = File(desc="Required: input fixed image file name. It is recommended that this image should either contain or be a b0 image.", exists=True, argstr="--fixedVolume %s")
    fixedVolumeIndex = traits.Int(desc="Index in the fixed image for registration. It is recommended that this image should be a b0 image.", argstr="--fixedVolumeIndex %d")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing moving images individually resampled and fit to the specified fixed image index.", argstr="--outputVolume %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Registration 3D transforms concatenated in a single output file.  There are no tools that can use this, but can be used for debugging purposes.", argstr="--outputTransform %s")
    eddyCurrentCorrection = traits.Bool(desc="Flag to perform eddy current corection in addition to motion correction (recommended)", argstr="--eddyCurrentCorrection ")
    numberOfIterations = traits.Int(desc="Number of iterations in each 3D fit", argstr="--numberOfIterations %d")
    numberOfSpatialSamples = traits.Int(desc="Number of voxels sampled for mutual information computation in each 3D fit step", argstr="--numberOfSpatialSamples %d")
    relaxationFactor = traits.Float(desc="Fraction of gradient from Jacobian to attempt to move in each 3D fit step (adjust when eddyCurrentCorrection is enabled; suggested value = 0.25)", argstr="--relaxationFactor %f")
    maximumStepSize = traits.Float(desc="Maximum permitted step size to move in each 3D fit step (adjust when eddyCurrentCorrection is enabled; suggested value = 0.1)", argstr="--maximumStepSize %f")
    minimumStepSize = traits.Float(desc="Minimum required step size to move in each 3D fit step without converging -- decrease this to make the fit more exacting", argstr="--minimumStepSize %f")
    spatialScale = traits.Float(desc="How much to scale up changes in position compared to unit rotational changes in radians -- decrease this to put more rotation in the fit", argstr="--spatialScale %f")
    registerB0Only = traits.Bool(desc="Register the B0 images only", argstr="--registerB0Only ")
    debugLevel = traits.Int(desc="Display debug messages, and produce debug intermediate results.  0=OFF, 1=Minimal, 10=Maximum debugging.", argstr="--debugLevel %d")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCoregBvaluesOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing moving images individually resampled and fit to the specified fixed image index.", exists=True)
    outputTransform = File(desc="Registration 3D transforms concatenated in a single output file.  There are no tools that can use this, but can be used for debugging purposes.", exists=True)


class gtractCoregBvalues(SlicerCommandLine):
    """title: Coregister B-Values

category: Diffusion.GTRACT

description: This step should be performed after converting DWI scans from DICOM to NRRD format. This program will register all gradients in a NRRD diffusion weighted 4D vector image (moving image) to a specified index in a fixed image. It also supports co-registration with a T2 weighted image or field map in the same plane as the DWI data. The fixed image for the registration should be a b0 image. A mutual information metric cost function is used for the registration because of the differences in signal intensity as a result of the diffusion gradients. The full affine allows the registration procedure to correct for eddy current distortions that may exist in the data. If the eddyCurrentCorrection is enabled, relaxationFactor (0.25) and maximumStepSize (0.1) should be adjusted.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCoregBvaluesInputSpec
    output_spec = gtractCoregBvaluesOutputSpec
    _cmd = " gtractCoregBvalues "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd','outputTransform':'outputTransform.mat'}
