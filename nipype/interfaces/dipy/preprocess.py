#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)
"""
import os.path as op
import warnings

import nibabel as nb
import numpy as np

from ..base import (traits, TraitedSpec, BaseInterface, File, isdefined)
from ...utils.filemanip import split_filename
from ...utils.misc import package_check
from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception as e:
    have_dipy = False
else:
    from dipy.align.aniso2iso import resample
    from dipy.core.gradients import GradientTable


class ResampleInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    vox_size = traits.Tuple(traits.Float, traits.Float, traits.Float,
                            desc=('specify the new voxel zooms. If no vox_size'
                                  ' is set, then isotropic regridding will '
                                  'be performed, with spacing equal to the '
                                  'smallest current zoom.'))
    interp = traits.Int(1, mandatory=True, usedefault=True, desc=('order of '
                        'the interpolator (0 = nearest, 1 = linear, etc.'))


class ResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Resample(BaseInterface):
    """
    An interface to reslicing diffusion datasets.
    See
    http://nipy.org/dipy/examples_built/reslice_datasets.html#example-reslice-datasets.

    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> reslice = dipy.Resample()
    >>> reslice.inputs.in_file = 'diffusion.nii'
    >>> reslice.run() # doctest: +SKIP
    """
    input_spec = ResampleInputSpec
    output_spec = ResampleOutputSpec

    def _run_interface(self, runtime):
        order = self.inputs.interp
        vox_size = None

        if isdefined(self.inputs.vox_size):
            vox_size = self.inputs.vox_size

        out_file = op.abspath(self._gen_outfilename())
        resample_proxy(self.inputs.in_file, order=order,
                       new_zooms=vox_size, out_file=out_file)

        iflogger.info('Resliced image saved as {i}'.format(i=out_file))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        fname, fext = op.splitext(op.basename(self.inputs.in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        return op.abspath('%s_reslice%s' % (fname, fext))


class DenoiseInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    in_mask = File(exists=True, desc='brain mask')
    noise_model = traits.Enum('rician', 'gaussian', mandatory=True,
                              usedefault=True,
                              desc=('noise distribution model'))
    noise_mask = File(desc=('mask in which the standard deviation of noise '
                            'will be computed'), exists=True)
    patch_radius = traits.Int(1, desc='patch radius')
    block_radius = traits.Int(5, desc='block_radius')


class DenoiseOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Denoise(BaseInterface):
    """
    An interface to denoising diffusion datasets [Coupe2008]_.
    See
    http://nipy.org/dipy/examples_built/denoise_nlmeans.html#example-denoise-nlmeans.

    .. [Coupe2008] Coupe P et al., `An Optimized Blockwise Non Local Means
      Denoising Filter for 3D Magnetic Resonance Images
      <http://dx.doi.org/10.1109%2FTMI.2007.906087>`_,
      IEEE Transactions on Medical Imaging, 27(4):425-441, 2008.


    Example
    -------

    >>> import nipype.interfaces.dipy as dipy
    >>> denoise = dipy.Denoise()
    >>> denoise.inputs.in_file = 'diffusion.nii'
    >>> denoise.run() # doctest: +SKIP
    """
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec

    def _run_interface(self, runtime):
        out_file = op.abspath(self._gen_outfilename())

        settings = dict(mask=None,
                        rician=(self.inputs.noise_model == 'rician'))

        if isdefined(self.inputs.in_mask):
            settings['mask'] = nb.load(self.inputs.in_mask).get_data()

        if isdefined(self.inputs.patch_radius):
            settings['patch_radius'] = self.inputs.patch_radius

        if isdefined(self.inputs.block_radius):
            settings['block_radius'] = self.inputs.block_radius

        noise_mask = None
        if isdefined(self.inputs.in_mask):
            noise_mask = nb.load(self.inputs.noise_mask).get_data()

        _, s = nlmeans_proxy(self.inputs.in_file,
                             settings,
                             noise_mask=noise_mask,
                             out_file=out_file)
        iflogger.info(('Denoised image saved as {i}, estimated '
                      'sigma={s}').format(i=out_file, s=s))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        fname, fext = op.splitext(op.basename(self.inputs.in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        return op.abspath('%s_denoise%s' % (fname, fext))


def resample_proxy(in_file, order=3, new_zooms=None, out_file=None):
    """
    Performs regridding of an image to set isotropic voxel sizes using dipy.
    """

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        out_file = op.abspath('./%s_reslice%s' % (fname, fext))

    img = nb.load(in_file)
    hdr = img.header.copy()
    data = img.get_data().astype(np.float32)
    affine = img.affine
    im_zooms = hdr.get_zooms()[:3]

    if new_zooms is None:
        minzoom = np.array(im_zooms).min()
        new_zooms = tuple(np.ones((3,)) * minzoom)

    if np.all(im_zooms == new_zooms):
        return in_file

    data2, affine2 = resample(data, affine, im_zooms, new_zooms, order=order)
    tmp_zooms = np.array(hdr.get_zooms())
    tmp_zooms[:3] = new_zooms[0]
    hdr.set_zooms(tuple(tmp_zooms))
    hdr.set_data_shape(data2.shape)
    hdr.set_xyzt_units('mm')
    nb.Nifti1Image(data2.astype(hdr.get_data_dtype()),
                   affine2, hdr).to_filename(out_file)
    return out_file, new_zooms


def nlmeans_proxy(in_file, settings,
                  noise_mask=None, out_file=None):
    """
    Uses non-local means to denoise 4D datasets
    """
    package_check('dipy', version='0.8.0.dev')
    from dipy.denoise.nlmeans import nlmeans

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        out_file = op.abspath('./%s_denoise%s' % (fname, fext))

    img = nb.load(in_file)
    hdr = img.header
    data = img.get_data()
    aff = img.affine

    nmask = data[..., 0] > 80
    if noise_mask is not None:
        nmask = noise_mask > 0

    sigma = np.std(data[nmask == 1])
    den = nlmeans(data, sigma, **settings)

    nb.Nifti1Image(den.astype(hdr.get_data_dtype()), aff,
                   hdr).to_filename(out_file)
    return out_file, sigma
