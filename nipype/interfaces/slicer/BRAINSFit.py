from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os

class BRAINSFitInputSpec(CommandLineInputSpec):
    fixedVolume = File( exists = True,argstr = "--fixedVolume %s")
    movingVolume = File( exists = True,argstr = "--movingVolume %s")
    initialTransform = File( exists = True,argstr = "--initialTransform %s")
    useMomentsAlign = traits.Bool( argstr = "--useMomentsAlign ")
    useGeometryAlign = traits.Bool( argstr = "--useGeometryAlign ")
    useCenterOfHeadAlign = traits.Bool( argstr = "--useCenterOfHeadAlign ")
    useRigid = traits.Bool( argstr = "--useRigid ")
    useScaleVersor3D = traits.Bool( argstr = "--useScaleVersor3D ")
    useScaleSkewVersor3D = traits.Bool( argstr = "--useScaleSkewVersor3D ")
    useAffine = traits.Bool( argstr = "--useAffine ")
    useBSpline = traits.Bool( argstr = "--useBSpline ")
    bsplineTransform = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--bsplineTransform %s")
    linearTransform = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--linearTransform %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--outputTransform %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--outputVolume %s")
    outputVolumePixelType = traits.Enum("float","short","ushort","int","uint","uchar", argstr = "--outputVolumePixelType %s")
    transformType = InputMultiPath(traits.Str, sep = ",",argstr = "--transformType %s")
    numberOfIterations = InputMultiPath(traits.Int, sep = ",",argstr = "--numberOfIterations %s")
    numberOfSamples = traits.Int( argstr = "--numberOfSamples %d")
    minimumStepSize = InputMultiPath(traits.Float, sep = ",",argstr = "--minimumStepSize %s")
    translationScale = traits.Float( argstr = "--translationScale %f")
    reproportionScale = traits.Float( argstr = "--reproportionScale %f")
    skewScale = traits.Float( argstr = "--skewScale %f")
    splineGridSize = InputMultiPath(traits.Int, sep = ",",argstr = "--splineGridSize %s")
    maxBSplineDisplacement = traits.Float( argstr = "--maxBSplineDisplacement %f")
    strippedOutputTransform = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--strippedOutputTransform %s")
    backgroundFillValue = traits.Float( argstr = "--backgroundFillValue %f")
    maskInferiorCutOffFromCenter = traits.Float( argstr = "--maskInferiorCutOffFromCenter %f")
    scaleOutputValues = traits.Bool( argstr = "--scaleOutputValues ")
    interpolationMode = traits.Enum("NearestNeighbor","Linear","BSpline","WindowedSinc", argstr = "--interpolationMode %s")
    maskProcessingMode = traits.Enum("NOMASK","ROIAUTO","ROI", argstr = "--maskProcessingMode %s")
    outputFixedVolumeROI = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--outputFixedVolumeROI %s")
    outputMovingVolumeROI = traits.Either(traits.Bool, File(), hash_files = False,argstr = "--outputMovingVolumeROI %s")
    fixedBinaryVolume = File( exists = True,argstr = "--fixedBinaryVolume %s")
    movingBinaryVolume = File( exists = True,argstr = "--movingBinaryVolume %s")
    fixedVolumeTimeIndex = traits.Int( argstr = "--fixedVolumeTimeIndex %d")
    movingVolumeTimeIndex = traits.Int( argstr = "--movingVolumeTimeIndex %d")
    medianFilterSize = InputMultiPath(traits.Int, sep = ",",argstr = "--medianFilterSize %s")
    histogramMatch = traits.Bool( argstr = "--histogramMatch ")
    numberOfHistogramBins = traits.Int( argstr = "--numberOfHistogramBins %d")
    numberOfMatchPoints = traits.Int( argstr = "--numberOfMatchPoints %d")
    useCachingOfBSplineWeightsMode = traits.Enum("ON","OFF", argstr = "--useCachingOfBSplineWeightsMode %s")
    useExplicitPDFDerivativesMode = traits.Enum("AUTO","ON","OFF", argstr = "--useExplicitPDFDerivativesMode %s")
    ROIAutoDilateSize = traits.Float( argstr = "--ROIAutoDilateSize %f")
    relaxationFactor = traits.Float( argstr = "--relaxationFactor %f")
    maximumStepSize = traits.Float( argstr = "--maximumStepSize %f")
    failureExitCode = traits.Int( argstr = "--failureExitCode %d")
    writeTransformOnFailure = traits.Bool( argstr = "--writeTransformOnFailure ")
    debugNumberOfThreads = traits.Int( argstr = "--debugNumberOfThreads %d")
    debugLevel = traits.Int( argstr = "--debugLevel %d")
    costFunctionConvergenceFactor = traits.Float( argstr = "--costFunctionConvergenceFactor %f")
    projectedGradientTolerance = traits.Float( argstr = "--projectedGradientTolerance %f")
    UseDebugImageViewer = traits.Bool( argstr = "--gui ")
    PromptAfterImageSend = traits.Bool( argstr = "--promptUser ")
    permitParameterVariation = InputMultiPath(traits.Int, sep = ",",argstr = "--permitParameterVariation %s")


class BRAINSFitOutputSpec(TraitedSpec):
    bsplineTransform = File( exists = True)
    linearTransform = File( exists = True)
    outputTransform = File( exists = True)
    outputVolume = File( exists = True)
    strippedOutputTransform = File( exists = True)
    outputFixedVolumeROI = File( exists = True)
    outputMovingVolumeROI = File( exists = True)


class BRAINSFit(CommandLine):

    input_spec = BRAINSFitInputSpec
    output_spec = BRAINSFitOutputSpec
    _cmd = "Slicer3 --launch BRAINSFit "
    _outputs_filenames = {'outputVolume':'outputVolume.nii','bsplineTransform':'bsplineTransform.mat','outputTransform':'outputTransform.mat','outputFixedVolumeROI':'outputFixedVolumeROI.nii','strippedOutputTransform':'strippedOutputTransform.mat','outputMovingVolumeROI':'outputMovingVolumeROI.nii','linearTransform':'linearTransform.mat'}

    def _list_outputs(self):
        outputs = self.output_spec().get()
        for name in outputs.keys():
            coresponding_input = getattr(self.inputs, name)
            if isdefined(coresponding_input):
                if isinstance(coresponding_input, bool) and coresponding_input == True:
                    outputs[name] = os.path.abspath(self._outputs_filenames[name])
                else:
                    if isinstance(coresponding_input, list):
                        outputs[name] = [os.path.abspath(inp) for inp in coresponding_input]
                    else:
                        outputs[name] = os.path.abspath(coresponding_input)
        return outputs

    def _format_arg(self, name, spec, value):
        if name in self._outputs_filenames.keys():
            if isinstance(value, bool):
                if value == True:
                    value = os.path.abspath(self._outputs_filenames[name])
                else:
                    return ""
        return super(BRAINSFit, self)._format_arg(name, spec, value)

