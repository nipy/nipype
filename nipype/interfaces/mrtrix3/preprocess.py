# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__ ))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os
import os.path as op

from nipype.interfaces.base import (
    CommandLineInputSpec, CommandLine, traits, TraitedSpec, File)

from nipype.utils.filemanip import split_filename
from nipype.interfaces.traits_extension import isdefined


class ResponseSDInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input diffusion weighted images')

    out_file = File(
        'response.txt', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file containing SH coefficients')

    # DW gradient table import options
    grad_file = File(exists=True, argstr='-grad %s',
                     desc='dw gradient scheme (MRTrix format')
    grad_fsl = traits.Tuple(
        File(exists=True), File(exists=True), argstr='-fslgrad %s %s',
        desc='(bvecs, bvals) dw gradient scheme (FSL format')
    bval_scale = traits.Enum(
        'yes', 'no', argstr='-bvalue_scaling %s',
        desc=('specifies whether the b - values should be scaled by the square'
              ' of the corresponding DW gradient norm, as often required for '
              'multishell or DSI DW acquisition schemes. The default action '
              'can also be set in the MRtrix config file, under the '
              'BValueScaling entry. Valid choices are yes / no, true / '
              'false, 0 / 1 (default: true).'))

    # DW Shell selection options

    shell = traits.List(traits.Float, sep=',', argstr='-shell %f',
                        desc='specify one or more dw gradient shells')
    in_mask = File(exists=True, argstr='-mask %s',
                   desc='provide initial mask image')
    max_sh = traits.Int(8, argstr='-lmax %d',
                        desc='maximum harmonic degree of response function')
    out_sf = File('sf_mask.nii.gz', argstr='-sf %s',
                  desc='write a mask containing single-fibre voxels')
    test_all = traits.Bool(False, argstr='-test_all',
                           desc='re-test all voxels at every iteration')

    # Optimization
    iterations = traits.Int(0, argstr='-max_iters %d',
                            desc='maximum number of iterations per pass')
    max_change = traits.Float(
        argstr='-max_change %f',
        desc=('maximum percentile change in any response function coefficient;'
              ' if no individual coefficient changes by more than this '
              'fraction, the algorithm is terminated.'))

    # Thresholds
    vol_ratio = traits.Float(
        .15, argstr='-volume_ratio %f',
        desc=('maximal volume ratio between the sum of all other positive'
              ' lobes in the voxel and the largest FOD lobe'))
    disp_mult = traits.Float(
        1., argstr='-dispersion_multiplier %f',
        desc=('dispersion of FOD lobe must not exceed some threshold as '
              'determined by this multiplier and the FOD dispersion in other '
              'single-fibre voxels. The threshold is: (mean + (multiplier * '
              '(mean - min))); default = 1.0. Criterion is only applied in '
              'second pass of RF estimation.'))
    int_mult = traits.Float(
        2., argstr='-integral_multiplier %f',
        desc=('integral of FOD lobe must not be outside some range as '
              'determined by this multiplier and FOD lobe integral in other'
              ' single-fibre voxels. The range is: (mean +- (multiplier * '
              'stdev)); default = 2.0. Criterion is only applied in second '
              'pass of RF estimation.'))


class ResponseSDOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')
    out_sf = File(desc=('mask containing single-fibre voxels'))


class ResponseSD(CommandLine):

    """
    Performs tractography after selecting the appropriate algorithm

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> resp = mrt.ResponseSD()
    >>> resp.inputs.in_file = 'dwi.mif'
    >>> resp.inputs.in_mask = 'mask.nii.gz'
    >>> resp.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> resp.cmdline                               # doctest: +ELLIPSIS
    'dwi2response -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif response.txt'
    >>> resp.run()                                 # doctest: +SKIP
    """

    _cmd = 'dwi2response'
    input_spec = ResponseSDInputSpec
    output_spec = ResponseSDOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)

        if isdefined(self.inputs.out_sf):
            outputs['out_sf'] = op.abspath(self.inputs.out_sf)
        return outputs


class ACTPrepareFSLInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input anatomical image')

    out_file = File(
        'act_5tt.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file after processing')


class ACTPrepareFSLOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class ACTPrepareFSL(CommandLine):

    """
    Performs tractography after selecting the appropriate algorithm

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ACTPrepareFSL()
    >>> prep.inputs.in_file = 'T1.nii.gz'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'act_anat_prepare_fsl T1.nii.gz act_5tt.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = 'act_anat_prepare_fsl'
    input_spec = ACTPrepareFSLInputSpec
    output_spec = ACTPrepareFSLOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs