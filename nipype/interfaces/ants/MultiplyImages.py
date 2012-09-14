#o emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# Standard library imports
import os
from glob import glob

# Local imports
from ..base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec

class MultiplyImagesInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='%d', usedefault=False, mandatory=True, position=0, desc='image dimension (2 or 3)')
    first_input = File(argstr='%s', exists=True, mandatory=True, position=1, desc='image 1')
    second_input = traits.Either(File(exists=True), traits.Float, argstr='%s', mandatory=True, position=2, desc='image 2 or multiplication weight')
    output_product_image = File(argstr='%s', mandatory=True, position=3, desc='Outputfname.nii.gz: the name of the resulting image.')

class MultiplyImagesOutputSpec(TraitedSpec):
    output_product_image = File(exists=True, desc='average image file')

class MultiplyImages(ANTSCommand):
    """
    Examples
    --------
    >>>
    """
    _cmd = 'MultiplyImages'
    input_spec = MultiplyImagesInputSpec
    output_spec = MultiplyImagesOutputSpec

    def _format_arg(self, opt, spec, val):
        return super(MultiplyImages, self)._format_arg(opt, spec, val)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_product_image'] = os.path.abspath(self.inputs.output_product_image)
        return outputs

"""
Usage:

MultiplyImages ImageDimension img1.nii img2.nii product.nii {smoothing}


"""
