# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# Standard library imports
import os

# Local imports
from ..base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec

class AverageImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    output_average_image = File(argstr='%s', mandatory=True, position=1, desc='Outputfname.nii.gz: the name of the resulting image.')
    normalize = traits.Enum(0, 1, argstr="%s", mandatory=True, position=2, desc='Normalize: 0 (false) or 1 (true); if true, the 2nd image' +
                            'is divided by its mean. This will select the largest image to average into.')
    images = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, position=3, desc=('image to apply transformation to (generally a coregistered functional)') )

class AverageImagesOutputSpec(TraitedSpec):
    output_average_image = File(exists=True, desc='average image file')

class AverageImages(ANTSCommand):
    """
    Examples
    --------
    >>>
    """
    _cmd = 'AverageImages'
    input_spec = AverageImagesInputSpec
    output_spec = AverageImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(AverageImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_average_image'] = os.path.realpath(self.inputs.output_average_image)
        return outputs

"""
Usage:

AverageImages ImageDimension Outputfname.nii.gz Normalize <images>

=======================================================================

 Compulsory arguments:

     ImageDimension: 2 or 3 (for 2 or 3 dimensional input).

     Outputfname.nii.gz: the name of the resulting image.

     Normalize: 0 (false) or 1 (true); if true, the 2nd image is divided by
      its mean. This will select the largest image to average into.

     -h
          Print the help menu (short version).
          <VALUES>: 0

     --help
          Print the help menu.
          <VALUES>: 0

=======================================================================

How to run the test case:

cd {TEST_DATA}/EXPERIEMENTS/ANTS_NIPYPE_SMALL_TEST
{BINARIES_DIRECTORY}/bin/AverageImages  \
    3 \
    average.nii.gz \
    1  \
    *.nii.gz

=======================================================================

  Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
