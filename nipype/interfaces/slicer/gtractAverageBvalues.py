from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractAverageBvaluesInputSpec(CommandLineInputSpec):
    inputVolume = File(desc="Required: input image file name containing multiple baseline gradients to average", exists=True, argstr="--inputVolume %s")
    outputVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Required: name of output NRRD file containing directly averaged baseline images", argstr="--outputVolume %s")
    directionsTolerance = traits.Float(desc="Tolerance for matching identical gradient direction pairs", argstr="--directionsTolerance %f")
    averageB0only = traits.Bool(desc="Average only baseline gradients. All other gradient directions are not averaged, but retained in the outputVolume", argstr="--averageB0only ")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractAverageBvaluesOutputSpec(TraitedSpec):
    outputVolume = File(desc="Required: name of output NRRD file containing directly averaged baseline images", exists=True)


class gtractAverageBvalues(SlicerCommandLine):
    """title: Average B-Values

category: Diffusion.GTRACT

description: This program will directly average together the baseline gradients (b value equals 0) within a DWI scan. This is usually used after gtractCoregBvalues.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractAverageBvaluesInputSpec
    output_spec = gtractAverageBvaluesOutputSpec
    _cmd = " gtractAverageBvalues "
    _outputs_filenames = {'outputVolume':'outputVolume.nrrd'}
