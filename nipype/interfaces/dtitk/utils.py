# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""DTITK utility interfaces

DTI-TK developed by Gary Hui Zhang, gary.zhang@ucl.ac.uk
For additional help, visit http://dti-tk.sf.net

The high-dimensional tensor-based DTI registration algorithm

Zhang, H., Avants, B.B, Yushkevich, P.A., Woo, J.H., Wang, S., McCluskey, L.H., Elman, L.B., Melhem, E.R., Gee, J.C., High-dimensional spatial normalization of diffusion tensor images improves the detection of white matter differences in amyotrophic lateral sclerosis, IEEE Transactions on Medical Imaging, 26(11):1585-1597, November 2007. PMID: 18041273.

The original piecewise-affine tensor-based DTI registration algorithm at the core of DTI-TK

Zhang, H., Yushkevich, P.A., Alexander, D.C., Gee, J.C., Deformable registration of diffusion tensor MR images with explicit orientation optimization, Medical Image Analysis, 10(5):764-785, October 2006. PMID: 16899392.

"""
__author__ = 'kjordan'

from ..base import TraitedSpec, CommandLineInputSpec, File, \
    traits, isdefined
import os
from .base import CommandLineDtitk

__docformat__ = 'restructuredtext'

class TVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="tensor volume to modify", exists=True,
                   mandatory=True, argstr="-in %s")
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
                          argstr='-origin %g %g %g',
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
    >>> node.inputs.in_file = 'im1.nii'
    >>> node.inputs.target_file = 'im2.nii'
    >>> node.cmdline
    'TVAdjustVoxelspace -in im1.nii -out im1_avs.nii -target im2.nii'
    >>> node.run() # doctest: +SKIP
    """
    input_spec = TVAdjustVoxSpInputSpec
    output_spec = TVAdjustVoxSpOutputSpec
    _cmd = 'TVAdjustVoxelspace'


class SVAdjustVoxSpInputSpec(CommandLineInputSpec):
    in_file = File(desc="scalar volume to modify", exists=True,
                   mandatory=True, argstr="-in %s")
    out_file = traits.Str(desc='output path', argstr="-out %s",
                          name_source="in_file", name_template='%s_avs',
                          keep_extension=True)
    target_file = File(desc='target volume to match',
                       argstr="-target %s", xor=['voxel_size', 'origin'])
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='xyz voxel size (superseded by target)',
                              argstr="-vsize %g %g %g", xor=['target_file'])
    origin = traits.Tuple((0, 0, 0),
                          desc='xyz origin (superseded by target)',
                          argstr='-origin %g %g %g',
                          xor=['target_file'])


class SVAdjustVoxSpOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SVAdjustVoxSpTask(CommandLineDtitk):
    """
     Adjusts the voxel space of a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVAdjustVoxSpTask()
        >>> node.inputs.in_file = 'im1.nii'
        >>> node.inputs.target_file = 'im2.nii'
        >>> node.cmdline
        'SVAdjustVoxelspace -in im1.nii -out im1_avs.nii -target im2.nii'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVAdjustVoxSpInputSpec
    output_spec = SVAdjustVoxSpOutputSpec
    _cmd = 'SVAdjustVoxelspace'


class TVResampleInputSpec(CommandLineInputSpec):
    in_file = File(desc="tensor volume to resample", exists=True,
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
        >>> node.inputs.in_file = 'im1.nii'
        >>> node.inputs.target_file = 'im2.nii'
        >>> node.cmdline
        'TVResample -in im1.nii -out im1_resampled.nii -target im2.nii'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = TVResampleInputSpec
    output_spec = TVResampleOutputSpec
    _cmd = 'TVResample'


class SVResampleInputSpec(CommandLineInputSpec):
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
    array_size = traits.Tuple((traits.Int(), traits.Int(), traits.Int()),
                              desc='resampled array size', xor=['target_file'],
                              argstr="-size %d %d %d")
    voxel_size = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                              desc='resampled voxel size', xor=['target_file'],
                              argstr="-vsize %g %g %g")
    origin = traits.Tuple((traits.Float(), traits.Float(), traits.Float()),
                          desc='xyz origin', xor=['target_file'],
                          argstr='-origin %g %g %g')


class SVResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)



class SVResampleTask(CommandLineDtitk):
    """
    Resamples a scalar volume

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.SVResampleTask()
        >>> node.inputs.in_file = 'im1.nii'
        >>> node.inputs.target_file = 'im2.nii'
        >>> node.cmdline
        'SVResample -in im1.nii -out im1_resampled.nii -target im2.nii'
        >>> node.run() # doctest: +SKIP
        """
    input_spec = SVResampleInputSpec
    output_spec = SVResampleOutputSpec
    _cmd = 'SVResample'


class TVtoolInputSpec(CommandLineInputSpec):
    in_file = File(desc="scalar volume to resample", exists=True,
                   argstr="-in %s", mandatory=True)
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
        >>> node.inputs.in_file = 'im1.nii'
        >>> node.inputs.in_flag = 'fa'
        >>> node.cmdline
        'TVtool -in im1.nii -fa -out im1_fa.nii'
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
        splitlist = os.path.basename(self.inputs.in_file).split('.')
        basename = splitlist[0]
        termination = '.' + '.'.join(splitlist[1:])
        return basename + '_'+self.inputs.in_flag + termination


'''Note: SVTool not implemented at this time'''


class BinThreshInputSpec(CommandLineInputSpec):
    in_file = File(desc='Image to threshold/binarize', exists=True,
                   position=0, argstr="%s", mandatory=True)
    out_file = traits.Str(desc='',  position=1, argstr="%s",
                          keep_extension=True, name_source='in_file',
                          name_template='%s_thrbin')
    lower_bound = traits.Float(0.01, position=2, argstr="%g", mandatory=True)
    upper_bound = traits.Float(100, position=3, argstr="%g", mandatory=True)
    inside_value = traits.Float(1, position=4, argstr="%g", usedefault=True,
                                mandatory=True)
    outside_value = traits.Float(0, position=5, argstr="%g", usedefault=True,
                                 mandatory=True)


class BinThreshOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class BinThreshTask(CommandLineDtitk):
    """
    Binarizes an image

        Example
        -------

        >>> import nipype.interfaces.dtitk as dtitk
        >>> node = dtitk.BinThreshTask()
        >>> node.inputs.in_file = 'im1.nii'
        >>> node.inputs.lower_bound = 0
        >>> node.inputs.upper_bound = 100
        >>> node.inputs.inside_value = 1
        >>> node.inputs.outside_value = 0
        >>> node.cmdline
        'BinaryThresholdImageFilter im1.nii im1_thrbin.nii 0 100 1 0'
        >>> node.run() # doctest: +SKIP
        """

    input_spec = BinThreshInputSpec
    output_spec = BinThreshOutputSpec
    _cmd = 'BinaryThresholdImageFilter'
