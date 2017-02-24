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

from ..base import traits, TraitedSpec, File
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class FitTensorInputSpec(MRTrix3BaseInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input diffusion weighted images')
    out_file = File(
        'dti.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='the output diffusion tensor image')

    # General options
    in_mask = File(exists=True, argstr='-mask %s',
                   desc=('only perform computation within the specified '
                         'binary brain mask image'))
    method = traits.Enum(
        'nonlinear', 'loglinear', 'sech', 'rician', argstr='-method %s',
        desc=('select method used to perform the fitting'))
    reg_term = traits.Float(
        5.e3, argstr='-regularisation %f',
        desc=('specify the strength of the regularisation term on the '
              'magnitude of the tensor elements (default = 5000). This '
              'only applies to the non-linear methods'))


class FitTensorOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output DTI file')


class FitTensor(MRTrix3Base):

    """
    Convert diffusion-weighted images to tensor images


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> tsr = mrt.FitTensor()
    >>> tsr.inputs.in_file = 'dwi.mif'
    >>> tsr.inputs.in_mask = 'mask.nii.gz'
    >>> tsr.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> tsr.cmdline                               # doctest: +ELLIPSIS +ALLOW_UNICODE
    'dwi2tensor -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif dti.mif'
    >>> tsr.run()                                 # doctest: +SKIP
    """

    _cmd = 'dwi2tensor'
    input_spec = FitTensorInputSpec
    output_spec = FitTensorOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class EstimateFODInputSpec(MRTrix3BaseInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3,
                   desc='input diffusion weighted images')
    response = File(
        exists=True, argstr='%s', mandatory=True, position=-2,
        desc=('a text file containing the diffusion-weighted signal response '
              'function coefficients for a single fibre population'))
    out_file = File(
        'fods.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc=('the output spherical harmonics coefficients'
                               ' image'))

    # DW Shell selection options
    shell = traits.List(traits.Float, sep=',', argstr='-shell %s',
                        desc='specify one or more dw gradient shells')

    # Spherical deconvolution options
    max_sh = traits.Int(8, argstr='-lmax %d',
                        desc='maximum harmonic degree of response function')
    in_mask = File(exists=True, argstr='-mask %s',
                   desc='provide initial mask image')
    in_dirs = File(
        exists=True, argstr='-directions %s',
        desc=('specify the directions over which to apply the non-negativity '
              'constraint (by default, the built-in 300 direction set is '
              'used). These should be supplied as a text file containing the '
              '[ az el ] pairs for the directions.'))
    sh_filter = File(
        exists=True, argstr='-filter %s',
        desc=('the linear frequency filtering parameters used for the initial '
              'linear spherical deconvolution step (default = [ 1 1 1 0 0 ]). '
              'These should be supplied as a text file containing the '
              'filtering coefficients for each even harmonic order.'))

    neg_lambda = traits.Float(
        1.0, argstr='-neg_lambda %f',
        desc=('the regularisation parameter lambda that controls the strength'
              ' of the non-negativity constraint'))
    thres = traits.Float(
        0.0, argstr='-threshold %f',
        desc=('the threshold below which the amplitude of the FOD is assumed '
              'to be zero, expressed as an absolute amplitude'))

    n_iter = traits.Int(
        50, argstr='-niter %d', desc=('the maximum number of iterations '
                                      'to perform for each voxel'))


class EstimateFODOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class EstimateFOD(MRTrix3Base):

    """
    Convert diffusion-weighted images to tensor images

    Note that this program makes use of implied symmetries in the diffusion
    profile. First, the fact the signal attenuation profile is real implies
    that it has conjugate symmetry, i.e. Y(l,-m) = Y(l,m)* (where * denotes
    the complex conjugate). Second, the diffusion profile should be
    antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l
    components should be zero. Therefore, this program only computes the even
    elements.

    Note that the spherical harmonics equations used here differ slightly from
    those conventionally used, in that the (-1)^m factor has been omitted.
    This should be taken into account in all subsequent calculations.
    The spherical harmonic coefficients are stored as follows. First, since
    the signal attenuation profile is real, it has conjugate symmetry, i.e.
    Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the
    diffusion profile should be antipodally symmetric (i.e. S(x) = S(-x)),
    implying that all odd l components should be zero. Therefore, only the
    even elements are computed.

    Note that the spherical harmonics equations used here differ slightly from
    those conventionally used, in that the (-1)^m factor has been omitted.
    This should be taken into account in all subsequent calculations.
    Each volume in the output image corresponds to a different spherical
    harmonic component. Each volume will correspond to the following:

    volume 0: l = 0, m = 0
    volume 1: l = 2, m = -2 (imaginary part of m=2 SH)
    volume 2: l = 2, m = -1 (imaginary part of m=1 SH)
    volume 3: l = 2, m = 0
    volume 4: l = 2, m = 1 (real part of m=1 SH)
    volume 5: l = 2, m = 2 (real part of m=2 SH)
    etc...



    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> fod = mrt.EstimateFOD()
    >>> fod.inputs.in_file = 'dwi.mif'
    >>> fod.inputs.response = 'response.txt'
    >>> fod.inputs.in_mask = 'mask.nii.gz'
    >>> fod.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> fod.cmdline                               # doctest: +ELLIPSIS +ALLOW_UNICODE
    'dwi2fod -fslgrad bvecs bvals -mask mask.nii.gz dwi.mif response.txt\
 fods.mif'
    >>> fod.run()                                 # doctest: +SKIP
    """

    _cmd = 'dwi2fod'
    input_spec = EstimateFODInputSpec
    output_spec = EstimateFODOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
