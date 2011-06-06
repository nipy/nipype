from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined
import os

class BRAINSFitInputSpec(CommandLineInputSpec):
    fixedVolume = File( exists = "True",argstr = "--fixedVolume %s")
    movingVolume = File( exists = "True",argstr = "--movingVolume %s")
    initialTransform = File( exists = "True",argstr = "--initialTransform %s")
    initializeTransformMode = traits.Enum("Off","useMomentsAlign","useCenterOfHeadAlign","useGeometryAlign", argstr = "--initializeTransformMode %s")
    useRigid = traits.Bool( argstr = "--useRigid ")
    useScaleVersor3D = traits.Bool( argstr = "--useScaleVersor3D ")
    useScaleSkewVersor3D = traits.Bool( argstr = "--useScaleSkewVersor3D ")
    useAffine = traits.Bool( argstr = "--useAffine ")
    useBSpline = traits.Bool( argstr = "--useBSpline ")
    bsplineTransform = traits.Either(traits.Bool, File, argstr = "--bsplineTransform %s")
    linearTransform = traits.Either(traits.Bool, File, argstr = "--linearTransform %s")
    outputTransform = traits.Either(traits.Bool, File, argstr = "--outputTransform %s")
    outputVolume = traits.Either(traits.Bool, File, argstr = "--outputVolume %s")
    outputVolumePixelType = traits.Enum("float","short","ushort","int","uint","uchar", argstr = "--outputVolumePixelType %s")
    transformType = traits.List(traits.Str, sep = ",",argstr = "--transformType %s")
    numberOfIterations = traits.List(traits.Int, sep = ",",argstr = "--numberOfIterations %d")
    numberOfSamples = traits.Int( argstr = "--numberOfSamples %d")
    minimumStepLength = traits.List(traits.Float, sep = ",",argstr = "--minimumStepLength %f")
    translationScale = traits.Float( argstr = "--translationScale %f")
    reproportionScale = traits.Float( argstr = "--reproportionScale %f")
    skewScale = traits.Float( argstr = "--skewScale %f")
    splineGridSize = traits.List(traits.Int, sep = ",",argstr = "--splineGridSize %d")
    maxBSplineDisplacement = traits.Float( argstr = "--maxBSplineDisplacement %f")
    strippedOutputTransform = traits.Either(traits.Bool, File, argstr = "--strippedOutputTransform %s")
    backgroundFillValue = traits.Float( argstr = "--backgroundFillValue %f")
    maskInferiorCutOffFromCenter = traits.Float( argstr = "--maskInferiorCutOffFromCenter %f")
    scaleOutputValues = traits.Bool( argstr = "--scaleOutputValues ")
    interpolationMode = traits.Enum("NearestNeighbor","Linear","ResampleInPlace","BSpline","WindowedSinc", argstr = "--interpolationMode %s")
    maskProcessingMode = traits.Enum("NOMASK","ROIAUTO","ROI", argstr = "--maskProcessingMode %s")
    outputFixedVolumeROI = traits.Either(traits.Bool, File, argstr = "--outputFixedVolumeROI %s")
    outputMovingVolumeROI = traits.Either(traits.Bool, File, argstr = "--outputMovingVolumeROI %s")
    fixedBinaryVolume = File( exists = "True",argstr = "--fixedBinaryVolume %s")
    movingBinaryVolume = File( exists = "True",argstr = "--movingBinaryVolume %s")
    fixedVolumeTimeIndex = traits.Int( argstr = "--fixedVolumeTimeIndex %d")
    movingVolumeTimeIndex = traits.Int( argstr = "--movingVolumeTimeIndex %d")
    medianFilterSize = traits.List(traits.Int, sep = ",",argstr = "--medianFilterSize %d")
    removeIntensityOutliers = traits.Float( argstr = "--removeIntensityOutliers %f")
    histogramMatch = traits.Bool( argstr = "--histogramMatch ")
    numberOfHistogramBins = traits.Int( argstr = "--numberOfHistogramBins %d")
    numberOfMatchPoints = traits.Int( argstr = "--numberOfMatchPoints %d")
    useCachingOfBSplineWeightsMode = traits.Enum("ON","OFF", argstr = "--useCachingOfBSplineWeightsMode %s")
    useExplicitPDFDerivativesMode = traits.Enum("AUTO","ON","OFF", argstr = "--useExplicitPDFDerivativesMode %s")
    ROIAutoDilateSize = traits.Float( argstr = "--ROIAutoDilateSize %f")
    ROIAutoClosingSize = traits.Float( argstr = "--ROIAutoClosingSize %f")
    relaxationFactor = traits.Float( argstr = "--relaxationFactor %f")
    maximumStepLength = traits.Float( argstr = "--maximumStepLength %f")
    failureExitCode = traits.Int( argstr = "--failureExitCode %d")
    writeTransformOnFailure = traits.Bool( argstr = "--writeTransformOnFailure ")
    debugNumberOfThreads = traits.Int( argstr = "--debugNumberOfThreads %d")
    debugLevel = traits.Int( argstr = "--debugLevel %d")
    costFunctionConvergenceFactor = traits.Float( argstr = "--costFunctionConvergenceFactor %f")
    projectedGradientTolerance = traits.Float( argstr = "--projectedGradientTolerance %f")
    UseDebugImageViewer = traits.Bool( argstr = "--gui ")
    PromptAfterImageSend = traits.Bool( argstr = "--promptUser ")
    useMomentsAlign = traits.Bool( argstr = "--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_00 ")
    useGeometryAlign = traits.Bool( argstr = "--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_01 ")
    useCenterOfHeadAlign = traits.Bool( argstr = "--NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_02 ")
    permitParameterVariation = traits.List(traits.Int, sep = ",",argstr = "--permitParameterVariation %d")
    costMetric = traits.Enum("MMI","MSE","NC","MC", argstr = "--costMetric %s")


class BRAINSFitOutputSpec(TraitedSpec):
    bsplineTransform = File(exists=True, argstr = "--bsplineTransform %s")
    linearTransform = File(exists=True, argstr = "--linearTransform %s")
    outputTransform = File(exists=True, argstr = "--outputTransform %s")
    outputVolume = File(exists=True, argstr = "--outputVolume %s")
    strippedOutputTransform = File(exists=True, argstr = "--strippedOutputTransform %s")
    outputFixedVolumeROI = File(exists=True, argstr = "--outputFixedVolumeROI %s")
    outputMovingVolumeROI = File(exists=True, argstr = "--outputMovingVolumeROI %s")


class BRAINSFit(CommandLine):

    input_spec = BRAINSFitInputSpec
    output_spec = BRAINSFitOutputSpec
    _cmd = " BRAINSFit "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','bsplineTransform':'bsplineTransform.mat','outputTransform':'outputTransform.mat','outputFixedVolumeROI':'outputFixedVolumeROI.nii','strippedOutputTransform':'strippedOutputTransform.mat','outputMovingVolumeROI':'outputMovingVolumeROI.nii','linearTransform':'linearTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    outputs[name] = coresponding_input
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    fname = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
            else:
                fname = value
            return spec.argstr % fname
        return super(BRAINSFit, self)._format_arg(name, spec, value)

