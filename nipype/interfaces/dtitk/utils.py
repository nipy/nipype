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
    target_file = traits.File(desc='target volume to match',
                              position=2, argstr="-target %s")
    vsize = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                         desc='xyz voxel size (superseded by target)',
                         position=3, argstr="-vsize %f %f %f")
    origin = traits.Tuple((0, 0, 0),
                          desc='xyz origin (superseded by target)', position=4,
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


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   mandatory=True, position=0, argstr="-in %s")
    out_file = traits.Str(desc='output path', position=1,
                          name_source="in_file", name_template="%s_resampled",
                          keep_extension=True, argstr="-out %s")
    target_file = File(desc='specs read from the target volume', position=2,
                       argstr="-target %s")
    align = traits.Str('center', position=3, argstr="-align %s")
    interp = traits.Enum('LEI', 'EI', position=4)
    arraysz = traits.Tuple((128, 128, 64),
                           desc='resampled array size', position=5,
                           argstr="-size %f %f %f")
    voxsz = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                         desc='resampled voxel size (superseded by target)',
                         exists=True, position=6, argstr="-vsize %f %f %f")
    origin = traits.Tuple((0, 0, 0),
                          desc='xyz origin (superseded by target)', position=4,
                          argstr='-origin %f %f %f')


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

    '''Note: there are a lot more options here; not putting all of them in'''
    in_flag = traits.Enum('fa', 'tr', 'ad', 'rd', 'pd', 'rgb', exists=True,
                          position=2, argstr="-%s", desc='')
    out_file = traits.Str(exists=True,  position=1,
                          argstr="-out %s", name_source=["in_file", "in_flag"],
                          name_template="%s_tvt_%s.nii.gz")



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
