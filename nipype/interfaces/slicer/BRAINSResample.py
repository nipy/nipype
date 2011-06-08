from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os

class BRAINSResampleInputSpec(CommandLineInputSpec):
    inputVolume = File( exists = True,argstr = "--inputVolume %s")
    referenceVolume = File( exists = True,argstr = "--referenceVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), argstr = "--outputVolume %s")
    pixelType = traits.Enum("float","short","ushort","int","uint","uchar","binary", argstr = "--pixelType %s")
    deformationVolume = File( exists = True,argstr = "--deformationVolume %s")
    warpTransform = File( exists = True,argstr = "--warpTransform %s")
    interpolationMode = traits.Enum("NearestNeighbor","Linear","BSpline","WindowedSinc", argstr = "--interpolationMode %s")
    defaultValue = traits.Float( argstr = "--defaultValue %f")
    gridSpacing = InputMultiPath(traits.Int, sep = ",",argstr = "--gridSpacing %s")


class BRAINSResampleOutputSpec(TraitedSpec):
    outputVolume = File( exists = True)


class BRAINSResample(CommandLine):

    input_spec = BRAINSResampleInputSpec
    output_spec = BRAINSResampleOutputSpec
    _cmd = "Slicer3 --launch BRAINSResample "
    _outputs_filenames = {'outputVolume':'outputVolume.nii'}

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
        return super(BRAINSResample, self)._format_arg(name, spec, value)

