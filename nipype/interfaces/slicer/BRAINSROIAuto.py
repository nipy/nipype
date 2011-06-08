from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os

class BRAINSROIAutoInputSpec(CommandLineInputSpec):
    inputVolume = File( exists = True,argstr = "--inputVolume %s")
    outputROIMaskVolume = traits.Either(traits.Bool, File(), argstr = "--outputROIMaskVolume %s")
    outputClippedVolumeROI = traits.Either(traits.Bool, File(), argstr = "--outputClippedVolumeROI %s")
    otsuPercentileThreshold = traits.Float( argstr = "--otsuPercentileThreshold %f")
    thresholdCorrectionFactor = traits.Float( argstr = "--thresholdCorrectionFactor %f")
    closingSize = traits.Float( argstr = "--closingSize %f")
    ROIAutoDilateSize = traits.Float( argstr = "--ROIAutoDilateSize %f")
    outputVolumePixelType = traits.Enum("float","short","ushort","int","uint","uchar", argstr = "--outputVolumePixelType %s")


class BRAINSROIAutoOutputSpec(TraitedSpec):
    outputROIMaskVolume = File( exists = True)
    outputClippedVolumeROI = File( exists = True)


class BRAINSROIAuto(CommandLine):

    input_spec = BRAINSROIAutoInputSpec
    output_spec = BRAINSROIAutoOutputSpec
    _cmd = "Slicer3 --launch BRAINSROIAuto "
    _outputs_filenames = {'outputROIMaskVolume':'outputROIMaskVolume.nii','outputClippedVolumeROI':'outputClippedVolumeROI.nii'}

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
        return super(BRAINSROIAuto, self)._format_arg(name, spec, value)

