# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""DTITK utility interfaces

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
__author__ = 'kjordan'

from ..base import TraitedSpec, CommandLineInputSpec, File, \
    traits, isdefined
import os
from .base import CommandLineDtitk


class TVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="tensor to resample", exists=True, mandatory=True,
                   position=0, argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path', position=1,
                          argstr="-out %s", name_source='in_file',
                          name_template='%s_avs', keep_extension=True)
    target = traits.File(desc='target volume',
                         position=2, argstr="-target %s")
    vsize = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                         desc='resampled voxel size',
                         position=3, argstr="-vsize %f %f %f")
    origin = traits.Tuple((0, 0, 0),
                          desc='xyz voxel size', position=4,
                          argstr='-origin %f %f %f', usedefault=True)


class TVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TVAdjustVoxSpTask(CommandLineDtitk):
    """
     Adjusts the voxel space of a tensor volume

    Example
    -------

    >>> import nipype.interfaces.dtitk as dtitk
    >>> node = dtitk.TVAdjustVoxSpTask()
    >>> node.inputs.in_file = 'diffusion.nii'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = 'TVAdjustVoxelspace'


# TODO not using these yet... need to be tested

class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   mandatory=True, position=0, argstr="-in %s")
    in_target = File(desc='target volume', mandatory=True,
                     position=2, argstr="-target %s")
    in_voxsz = traits.Str(desc='resampled voxel size', mandatory=True,
                          position=3, argstr="-vsize %s")
    out_file = traits.Str(desc='output path', position=1, argstr="-out %s",
                          name_source="in_file", name_template='%s_reslice',
                          keep_extension=True)
    origin = traits.Str(desc='xyz voxel size', mandatory=True,
                        position=4, argstr='-origin %s')


class SVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SVAdjustVoxSpTask(CommandLineDtitk):
    """
     Adjusts the voxel space of a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVAdjustVoxSpTask()
        >>> node.inputs.in_file = 'diffusion.nii.gz'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVAdjustVoxSpInputSpec
    output_spec = SVAdjustVoxSpOutputSpec
    _cmd = 'SVAdjustVoxelspace'


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   mandatory=True, position=0, argstr="-in %s")
    in_arraysz = traits.Str(desc='resampled array size', exists=True,
                            position=1, argstr="-size %s")
    in_voxsz = traits.Str(desc='resampled voxel size', exists=True,
                          position=2, argstr="-vsize %s")
    out_file = traits.Str(desc='output path', position=3, argstr="-out %s",
                          name_source="in_file", name_template="%s_resampled",
                          keep_extension=True)


class TVResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TVResampleTask(CommandLineDtitk):
    """
    Resamples a tensor volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.TVResampleTask()
        >>> node.inputs.in_file = 'diffusion.nii.gz'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = 'TVResample'


class SVResampleInputSpec(TVResampleInputSpec):
    pass


class SVResampleOutputSpec(TVResampleOutputSpec):
    pass


class SVResampleTask(CommandLineDtitk):
    """
    Resamples a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVResampleTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVResampleInputSpec
    output_spec = SVResampleOutputSpec
    _cmd = 'SVResample'


class TVtoolInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   position=0, argstr="-in %s")
    in_flag = traits.Enum('fa', 'tr', 'ad', 'rd', 'pd', 'rgb', exists=True,
                          position=1, argstr="-%s", desc='')


class TVtoolOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class TVtoolTask(CommandLineDtitk):
    """
    Calculates a tensor metric volume from a tensor volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.TVtoolTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_flag = 'fa'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVtoolInputSpec
    output_spec = TVtoolOutputSpec
    _cmd = 'TVtool'

    def _list_outputs(self):
        _suffix = self.inputs.in_flag
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(self.inputs.out_file):
            outputs["out_file"] = self._gen_fname(self.inputs.in_file,
                                                  suffix=_suffix,
                                                  ext='.' + '.'.join(
                                                      self.inputs.in_file.
                                                      split(".")[1:]))
        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None


class BinThreshInputSpec(CommandLineInputSpec):
    in_file = File(desc='', exists=True,  position=0,
                   argstr="%s")
    out_file = traits.Str(desc='',  position=1, argstr="%s",
                          keep_extension=True, name_source='in_file',
                          name_template='%s_bin')
    in_numbers = traits.List(traits.Float, minlen=4, maxlen=4,
                             desc='LB UB inside_value outside_value',
                             position=2, argstr="%s")


class BinThreshOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class BinThreshTask(CommandLineDtitk):
    """
    Binarizes an image based on parameters

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.BinThreshTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_numbers = [0, 100, 1, 0]
        >>> node.cmdline
        'BinaryThresholdImageFilter diffusion.nii diffusion_bin.nii 0.0 100.0 1.0 0.0'
        >>> node.run() # doctest: +SKIP
        """

    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd = 'BinaryThresholdImageFilter'
