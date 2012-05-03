from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory, traits, isdefined, InputMultiPath, OutputMultiPath
import os
from nipype.interfaces.slicer.base import SlicerCommandLine


class gtractCostFastMarchingInputSpec(CommandLineInputSpec):
    inputTensorVolume = File(desc="Required: input tensor image file name", exists=True, argstr="--inputTensorVolume %s")
    inputAnisotropyVolume = File(desc="Required: input anisotropy image file name", exists=True, argstr="--inputAnisotropyVolume %s")
    inputStartingSeedsLabelMapVolume = File(desc="Required: input starting seeds LabelMap image file name", exists=True, argstr="--inputStartingSeedsLabelMapVolume %s")
    startingSeedsLabel = traits.Int(desc="Label value for Starting Seeds", argstr="--startingSeedsLabel %d")
    outputCostVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output vcl_cost image", argstr="--outputCostVolume %s")
    outputSpeedVolume = traits.Either(traits.Bool, File(), hash_files=False, desc="Output speed image", argstr="--outputSpeedVolume %s")
    anisotropyWeight = traits.Float(desc="Anisotropy weight used for vcl_cost function calculations", argstr="--anisotropyWeight %f")
    stoppingValue = traits.Float(desc="Terminiating value for vcl_cost function estimation", argstr="--stoppingValue %f")
    seedThreshold = traits.Float(desc="Anisotropy threshold used for seed selection", argstr="--seedThreshold %f")
    numberOfThreads = traits.Int(desc="Explicitly specify the maximum number of threads to use.", argstr="--numberOfThreads %d")


class gtractCostFastMarchingOutputSpec(TraitedSpec):
    outputCostVolume = File(desc="Output vcl_cost image", exists=True)
    outputSpeedVolume = File(desc="Output speed image", exists=True)


class gtractCostFastMarching(SlicerCommandLine):
    """title: Cost Fast Marching

category: Diffusion.GTRACT

description:  This program will use a fast marching fiber tracking algorithm to identify fiber tracts from a tensor image. This program is the first portion of the algorithm. The user must first run gtractFastMarchingTracking to generate the actual fiber tracts.  This algorithm is roughly based on the work by G. Parker et al. from IEEE Transactions On Medical Imaging, 21(5): 505-512, 2002. An additional feature of including anisotropy into the vcl_cost function calculation is included.  

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris. The original code here was developed by Daisy Espino.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

"""

    input_spec = gtractCostFastMarchingInputSpec
    output_spec = gtractCostFastMarchingOutputSpec
    _cmd = " gtractCostFastMarching "
    _outputs_filenames = {'outputCostVolume':'outputCostVolume.nrrd','outputSpeedVolume':'outputSpeedVolume.nrrd'}
