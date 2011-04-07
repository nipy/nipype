"""The ANTS module provides classes for interfacing with commands from the Advanced Normalization Tools module
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings
from nipype.utils.filemanip import fname_presuffix, split_filename
from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class MeasureImageSimilarityInputSpec(CommandLineInputSpec):
   image_dimension = traits.Enum('3', '2', argstr='%s', mandatory=True, position=1, usedefault=True
        desc='ImageDimension: 2 or 3 (for 2 or 3 Dimensional registration)')

   image_metric = traits.Enum('0', '1', '2', '3', argstr='%s', position=2, usedefault=True
        desc='Metric: 0 - MeanSquareDifference, 1 - Cross-Correlation, 2-Mutual Information , 3-SMI')

   image1 = File(exists=True, argstr='%s', mandatory=True, position=3,
        desc='The first of two images to compare')

   image2 = File(exists=True, argstr='%s', mandatory=True, position=4,
        desc='The second of two images to compare')

   log_file = File(exists=True, argstr='%s', position=5,
        desc='Optional logfile')

   output_image = File(exists=True, argstr='%s', position=6,
        desc='The output image filename (Not Implemented for Mutual Information yet)')

   target_value = traits.Float(argstr='%s', position=7,
        desc='target_value and epsilon_tolerance set goals for the metric value'\
        'If the metric value is within epsilon_tolerance of the target_value, then the test succeeds')

   epsilon_tolerance = traits.Float(argstr='%s', position=8,
        desc='target_value and epsilon_tolerance set goals for the metric value'\
        'If the metric value is within epsilon_tolerance of the target_value, then the test succeeds')

class MeasureImageSimilarityOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='The output file')

class MeasureImageSimilarity(CommandLine):
    """ MeasureImageSimilarity
    """

    _cmd = 'MeasureImageSimilarity'
    input_spec=MeasureImageSimilarityInputSpec
    output_spec=MeasureImageSimilarityOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["output_image"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'output_image':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_MeasureSimilarity"
