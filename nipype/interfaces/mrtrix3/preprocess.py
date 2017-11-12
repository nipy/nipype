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
from __future__ import print_function, division, unicode_literals, absolute_import

import os.path as op

from ..traits_extension import isdefined
from ..base import (CommandLineInputSpec, CommandLine, traits, TraitedSpec,
                    File)
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class ResponseSDInputSpec(MRTrix3BaseInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input diffusion weighted images')

    out_file = File(
        'response.txt', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file containing SH coefficients')

    # DW Shell selection options
    shell = traits.List(traits.Float, sep=',', argstr='-shell %s',
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


class ResponseSD(MRTrix3Base):

    """
    Generate an appropriate response function from the image data for
    spherical deconvolution.

    .. [1] Tax, C. M.; Jeurissen, B.; Vos, S. B.; Viergever, M. A. and
      Leemans, A., Recursive calibration of the fiber response function
      for spherical deconvolution of diffusion MRI data. NeuroImage,
      2014, 86, 67-80


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
    Generate anatomical information necessary for Anatomically
    Constrained Tractography (ACT).

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


class ReplaceFSwithFIRSTInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-4,
                   desc='input anatomical image')
    in_t1w = File(exists=True, argstr='%s', mandatory=True, position=-3,
                  desc='input T1 image')
    in_config = File(exists=True, argstr='%s', position=-2,
                     desc='connectome configuration file')

    out_file = File(
        'aparc+first.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file after processing')


class ReplaceFSwithFIRSTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class ReplaceFSwithFIRST(CommandLine):

    """
    Replace deep gray matter structures segmented with FSL FIRST in a
    FreeSurfer parcellation.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ReplaceFSwithFIRST()
    >>> prep.inputs.in_file = 'aparc+aseg.nii'
    >>> prep.inputs.in_t1w = 'T1.nii.gz'
    >>> prep.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'fs_parc_replace_sgm_first aparc+aseg.nii T1.nii.gz \
mrtrix3_labelconfig.txt aparc+first.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = 'fs_parc_replace_sgm_first'
    input_spec = ReplaceFSwithFIRSTInputSpec
    output_spec = ReplaceFSwithFIRSTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
