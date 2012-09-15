# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
# Standard library imports
import os

# Local imports
from ..base import TraitedSpec, File, traits, InputMultiPath
from .base import ANTSCommand, ANTSCommandInputSpec

class AverageImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    output_average_image = File(argstr='%s', mandatory=True, position=1, desc='Outputfname.nii.gz: the name of the resulting image.')
    normalize = traits.Bool(argstr="%d", mandatory=True, position=2, desc='Normalize: if true, the 2nd image' +
                            'is divided by its mean. This will select the largest image to average into.')
    images = InputMultiPath(File(exists=True), argstr='%s', mandatory=True, position=3, desc=('image to apply transformation to (generally a coregistered functional)') )

class AverageImagesOutputSpec(TraitedSpec):
    output_average_image = File(exists=True, desc='average image file')

class AverageImages(ANTSCommand):
    """
    Examples
    --------
    >>> avg = AverageImages()
    >>> avg.inputs.dimension = 3
    >>> avg.inputs.output_average_image = "average.nii.gz"
    >>> avg.inputs.normalize = True
    >>> avg.inputs.images = ['rc1s1.nii', 'rc1s1.nii']
    >>> avg.cmdline
    'AverageImages 3 average.nii.gz 1 rc1s1.nii rc1s1.nii'
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