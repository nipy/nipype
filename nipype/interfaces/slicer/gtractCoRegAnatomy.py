from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractCoRegAnatomyInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input vector image file name. It is recommended that the input volume is the skull stripped baseline image of the DWI scan.", exists=True, argstr="--inputVolume %s")
    inputAnatomicalVolume = File(desc="Required: input anatomical image file name. It is recommended that that the input anatomical image has been skull stripped and has the same orientation as the DWI scan.", exists=True, argstr="--inputAnatomicalVolume %s")
    vectorIndex = traits.Int(desc="Vector image index in the moving image (within the DWI) to be used for registration.", argstr="--vectorIndex %d")
    inputRigidTransform = File(desc="Required (for B-Spline type co-registration): input rigid transform file name. Used as a starting point for the anatomical B-Spline registration.", exists=True, argstr="--inputRigidTransform %s")
    outputTransformName = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: filename for the  fit transform.", argstr="--outputTransformName %s")
    transformType = traits.Enum("Rigid", "Bspline", desc="Transform Type: Rigid|Bspline", argstr="--transformType %s")
    numberOfIterations = traits.Int(desc="Number of iterations in the selected 3D fit", argstr="--numberOfIterations %d")
    gridSize = InputMultiPath(traits.Int, desc="Number of grid subdivisions in all 3 directions", sep=",", argstr="--gridSize %s")
    borderSize = traits.Int(desc="Size of border", argstr="--borderSize %d")
    numberOfHistogramBins = traits.Int(desc="Number of histogram bins", argstr="--numberOfHistogramBins %d")
    spatialScale = traits.Int(desc="Scales the number of voxels in the image by this value to specify the number of voxels used in the registration", argstr="--spatialScale %d")
    convergence = traits.Float(desc="Convergence Factor", argstr="--convergence %f")
    gradientTolerance = traits.Float(desc="Gradient Tolerance", argstr="--gradientTolerance %f")
    maxBSplineDisplacement = traits.Float(desc=" Sets the maximum allowed displacements in image physical coordinates for BSpline control grid along each axis.  A value of 0.0 indicates that the problem should be unbounded.  NOTE:  This only constrains the BSpline portion, and does not limit the displacement from the associated bulk transform.  This can lead to a substantial reduction in computation time in the BSpline optimizer.,       ", argstr="--maxBSplineDisplacement %f")
    maximumStepSize = traits.Float(desc="Maximum permitted step size to move in the selected 3D fit", argstr="--maximumStepSize %f")
    minimumStepSize = traits.Float(desc="Minimum required step size to move in the selected 3D fit without converging -- decrease this to make the fit more exacting", argstr="--minimumStepSize %f")
    translationScale = traits.Float(desc="How much to scale up changes in position compared to unit rotational changes in radians -- decrease this to put more translation in the fit", argstr="--translationScale %f")
    relaxationFactor = traits.Float(desc="Fraction of gradient from Jacobian to attempt to move in the selected 3D fit", argstr="--relaxationFactor %f")
    numberOfSamples = traits.Int(desc="Number of voxels sampled for mutual information computation in the selected 3D fit", argstr="--numberOfSamples %d")
    useMomentsAlign = traits.Bool(desc="MomentsAlign assumes that the center of mass of the images represent similar structures.  Perform a MomentsAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either CenterOfHeadLAlign, GeometryAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useMomentsAlign ")
    useGeometryAlign = traits.Bool(desc="GeometryAlign on assumes that the center of the voxel lattice of the images represent similar structures. Perform a GeometryCenterAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either MomentsAlign, CenterOfHeadAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useGeometryAlign ")
    useCenterOfHeadAlign = traits.Bool(desc="CenterOfHeadAlign attempts to find a hemisphere full of foreground voxels from the superior direction as an estimate of where the center of a head shape would be to drive a center of mass estimate.  Perform a CenterOfHeadAlign registration as part of the sequential registration steps.   This option MUST come first, and CAN NOT be used with either MomentsAlign, GeometryAlign, or initialTransform file.  This family of options superceeds the use of transformType if any of them are set.", argstr="--useCenterOfHeadAlign ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCoRegAnatomyOutputSpec(TraitedSpec):
    outputTransformName = File(desc="Required: filename for the  fit transform.", exists=True)


class gtractCoRegAnatomy(SlicerCommandLine):
    """title: Coregister B0 to Anatomy B-Spline

category: Diffusion.GTRACT

description: This program will register a Nrrd diffusion weighted 4D vector image to a fixed anatomical image. Two registration methods are supported for alignment with anatomical images: Rigid and B-Spline. The rigid registration performs a rigid body registration with the anatomical images and should be done as well to initialize the B-Spline transform. The B-SPline transform is the deformable transform, where the user can control the amount of deformation based on the number of control points as well as the maximum distance that these points can move. The B-Spline registration places a low dimensional grid in the image, which is deformed. This allows for some susceptibility related distortions to be removed from the diffusion weighted images. In general the amount of motion in the slice selection and read-out directions direction should be kept low. The distortion is in the phase encoding direction in the images. It is recommended that skull stripped (i.e. image containing only brain with skull removed) images shoud be used for image co-registration with the B-Spline transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCoRegAnatomyInputSpec
    output_spec = gtractCoRegAnatomyOutputSpec
    _cmd = " gtractCoRegAnatomy "
    _outputs_filenames = {'outputTransformName':'outputTransformName.mat'}
