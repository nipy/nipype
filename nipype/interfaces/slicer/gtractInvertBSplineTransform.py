from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractInvertBSplineTransformInputSpec(CommandLineInputSpec):
    inputReferenceVolume = File(desc="Required: input image file name to exemplify the anatomical space to interpolate over.", exists=True, argstr="--inputReferenceVolume %s")
    inputTransform = File(desc="Required: input B-Spline transform file name", exists=True, argstr="--inputTransform %s")
    outputTransform = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: output transform file name", argstr="--outputTransform %s")
    landmarkDensity = InputMultiPath(traits.Int, desc="Number of landmark subdivisions in all 3 directions", sep=",", argstr="--landmarkDensity %s")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractInvertBSplineTransformOutputSpec(TraitedSpec):
    outputTransform = File(desc="Required: output transform file name", exists=True)


class gtractInvertBSplineTransform(SlicerCommandLine):
    """title: B-Spline Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a B-Spline transform using a thin-plate spline approximation.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractInvertBSplineTransformInputSpec
    output_spec = gtractInvertBSplineTransformOutputSpec
    _cmd = " gtractInvertBSplineTransform "
    _outputs_filenames = {'outputTransform':'outputTransform.mat'}
