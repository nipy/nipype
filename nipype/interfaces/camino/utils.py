# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
import os

from ..base import (traits, TraitedSpec, File, CommandLine,
                    CommandLineInputSpec, InputMultiPath)
from ...utils.filemanip import split_filename


class ImageStatsInputSpec(CommandLineInputSpec):
    in_files = InputMultiPath(
        File(exists=True),
        argstr='-images %s',
        mandatory=True,
        position=-1,
        desc=('List of images to process. They must '
              'be in the same space and have the same '
              'dimensions.'))
    stat = traits.Enum(
        "min",
        "max",
        "mean",
        "median",
        "sum",
        "std",
        "var",
        argstr='-stat %s',
        units='NA',
        mandatory=True,
        desc="The statistic to compute.")

    out_type = traits.Enum(
        "float",
        "char",
        "short",
        "int",
        "long",
        "double",
        argstr='-outputdatatype %s',
        usedefault=True,
        desc=('A Camino data type string, default is "float". '
              'Type must be signed.'))
    output_root = File(
        argstr='-outputroot %s',
        mandatory=True,
        desc=('Filename root prepended onto the names of the output '
              ' files. The extension will be determined from the input.'))


class ImageStatsOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc='Path of the file computed with the statistic chosen')


class ImageStats(CommandLine):
    """
    This program computes voxelwise statistics on a series of 3D images. The images
    must be in the same space; the operation is performed voxelwise and one output
    is produced per voxel.

    Examples
    --------

    >>> import nipype.interfaces.camino as cam
    >>> imstats = cam.ImageStats()
    >>> imstats.inputs.in_files = ['im1.nii','im2.nii','im3.nii']
    >>> imstats.inputs.stat = 'max'
    >>> imstats.run()                  # doctest: +SKIP
    """
    _cmd = 'imagestats'
    input_spec = ImageStatsInputSpec
    output_spec = ImageStatsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        output_root = self.inputs.output_root
        first_file = self.inputs.in_files[0]
        _, _, ext = split_filename(first_file)
        return output_root + ext
