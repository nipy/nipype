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
                   argstr="-in %s")
    out_file = traits.Str(genfile=True, desc='output path',
                          argstr="-out %s", name_source='in_file',
                          name_template='%s_avs', keep_extension=True)
    target_file = traits.File(desc='target volume to match',
                              argstr="-target %s",
                              xor=['voxel_size', 'origin'])
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='xyz voxel size (superseded by target)',
                              argstr="-vsize %g %g %g", xor=['target_file'])
    origin = traits.Tuple((0, 0, 0),
                          desc='xyz origin (superseded by target)',
                          argstr='-origin %g %g %g', usedefault=True,
                          xor=['target_file'])


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
    >>> node.inputs.target_file = 'diffusion2.nii'
    >>> node.cmdline # doctest: +ELLIPSIS
    'TVAdjustVoxelspace -in diffusion.nii -out diffusion_avs.nii -target 'diffusion2.nii''
    >>> node.run() # doctest: +SKIP
    """
    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = 'TVAdjustVoxelspace'


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   mandatory=True, argstr="-in %s")
    out_file = traits.Str(desc='output path',
                          name_source="in_file", name_template="%s_resampled",
                          keep_extension=True, argstr="-out %s")
    target_file = File(desc='specs read from the target volume',
                       argstr="-target %s",
                       xor=['array_size', 'voxel_size', 'origin'])
    align = traits.Enum('center', 'origin', argstr="-align %s",
                        desc='how to align output volume to input volume')
    interpolation = traits.Enum('LEI', 'EI', argstr="-interp %s",
                                desc='Log Euclidean Euclidean Interpolation')
    array_size = traits.Tuple((traits.Int(), traits.Int(), traits.Int()),
                              desc='resampled array size', xor=['target_file'],
                              argstr="-size %d %d %d")
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='resampled voxel size', xor=['target_file'],
                              argstr="-vsize %g %g %g")
    origin = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                          desc='xyz origin', xor=['target_file'],
                          argstr='-origin %g %g %g')


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
        >>> node.inputs.target_file = 'diffusion.nii.gz'
        >>> node.cmdline # doctest: +ELLIPSIS
        'TVResample -in diffusion.nii -out diffusion_resampled.nii -target 'diffusion2.nii''
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = 'TVResample'


class TVtoolInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True, argstr="-in %s",
                   mandatory=True)
    '''NOTE: there are a lot more options here; not putting all of them in'''
    in_flag = traits.Enum('fa', 'tr', 'ad', 'rd', 'pd', 'rgb', exists=True,
                          argstr="-%s", desc='')
    out_file = traits.Str(exists=True,
                          argstr="-out %s", genfile=True)


class TVtoolOutputSpec(TraitedSpec):
    out_file = File()


class TVtoolTask(CommandLineDtitk):
    """
    Calculates a tensor metric volume from a tensor volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.TVtoolTask()
        >>> node.inputs.in_file = 'diffusion.nii'
        >>> node.inputs.in_flag = 'fa'
        >>> node.cmdline # doctest: +ELLIPSIS
        'TVtool -in diffusion.nii -fa -out diffusion_fa.nii.gz'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVtoolInputSpec
    output_spec = TVtoolOutputSpec
    _cmd = 'TVtool'

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not isdefined(self.inputs.out_file):
            outputs['out_file'] = self._gen_filename('out_file')
        else:
            outputs['out_file'] = self.inputs.out_file
        return outputs

    def _gen_filename(self, name):
        basename = os.path.basename(self.inputs.in_file).split('.')[0]
        return basename + '_'+self.inputs.in_flag+'.nii.gz'


class BinThreshInputSpec(CommandLineInputSpec):
    in_file = File(desc='Image to threshold/binarize', exists=True,
                   position=0, argstr="%s")
    out_file = traits.Str(desc='',  position=1, argstr="%s",
                          keep_extension=True, name_source='in_file',
                          name_template='%s_thrbin')
    lower_bound = traits.Float(0.01, position=2, argstr="%g")
    upper_bound = traits.Float(100, position=3, argstr="%g")
    inside_value = traits.Float(1, position=4, argstr="%g", usedefault=True)
    outside_value = traits.Float(0, position=5, argstr="%g", usedefault=True)


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
        >>> node.inputs.lower_bound = 0
        >>> node.inputs.upper_bound = 100
        >>> node.inputs.inside_value = 1
        >>> node.inputs.outside_value = 0
        >>> node.cmdline
        'BinaryThresholdImageFilter diffusion.nii diffusion_bin.nii 0.0 100.0 1.0 0.0'
        >>> node.run() # doctest: +SKIP
        """

    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd = 'BinaryThresholdImageFilter'

# TODO not using these yet... need to be tested


class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="image to resample", exists=True,
                   mandatory=True, position=0, argstr="-in %s")
    target_file = File(desc='target volume', mandatory=True,
                     position=2, argstr="-target %s")
    voxel_size = traits.Str(desc='resampled voxel size', mandatory=True,
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
