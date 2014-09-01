#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: oesteban
# @Date:   2014-09-01 10:33:35
# @Last Modified by:   oesteban
# @Last Modified time: 2014-09-01 11:27:55
from nipype.interfaces.base import (traits, TraitedSpec, BaseInterface,
                                    File, isdefined)
from nipype.utils.filemanip import split_filename
import os.path as op
import nibabel as nb
import numpy as np
from nipype.utils.misc import package_check
import warnings
from ... import logging
iflogger = logging.getLogger('interface')

have_dipy = True
try:
    package_check('dipy', version='0.6.0')
except Exception, e:
    have_dipy = False
else:
    from dipy.align.aniso2iso import resample
    from dipy.core.gradients import GradientTable
    from dipy.denoise.nlmeans import nlmeans


class ResampleInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True,
                   desc='The input 4D diffusion-weighted image file')
    vox_size = traits.Tuple(traits.Float, traits.Float, traits.Float, desc=('specify the new '
                            'voxel zooms. If no vox_size is set, then isotropic regridding will '
                            'be performed, with spacing equal to the smallest current zoom.'))
    interp = traits.Int(1, mandatory=True, usedefault=True, desc=('order of the interpolator'
                        '(0 = nearest, 1 = linear, etc.'))


class ResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Resample(BaseInterface):
    """
    An interface to reslicing diffusion datasets.
    See http://nipy.org/dipy/examples_built/reslice_datasets.html#example-reslice-datasets.

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
    noise_model = traits.Enum('rician', 'gaussian', mandatory=True, usedefault=True,
                              desc=('noise distribution model'))


class DenoiseOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Denoise(BaseInterface):
    """
    An interface to denoising diffusion datasets [Coupe2008]_.
    See http://nipy.org/dipy/examples_built/denoise_nlmeans.html#example-denoise-nlmeans.

    .. [Coupe2008] P. Coupe, P. Yger, S. Prima, P. Hellier, C. Kervrann, C. Barillot,
      `An Optimized Blockwise Non Local Means Denoising Filter for 3D Magnetic Resonance Images
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

        mask = None
        if isdefined(self.inputs.in_mask):
            mask = nb.load(self.inputs.in_mask).get_data()

        nlmeans_proxy(self.inputs.in_file, in_mask=mask,
                      rician=(self.inputs.noise_model=='rician'),
                      out_file=out_file)
        iflogger.info('Denoised image saved as {i}'.format(i=out_file))
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
    hdr = img.get_header().copy()
    data = img.get_data().astype(np.float32)
    affine = img.get_affine()
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


def nlmeans_proxy(in_file, in_mask=None, rician=True, out_file=None):
    """
    Uses non-local means to denoise 4D datasets
    """

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        out_file = op.abspath('./%s_denoise%s' % (fname, fext))

    img = nb.load(in_file)
    hdr = img.get_header()
    data = img.get_data()
    aff = img.get_affine()

    if in_mask is None:
        mask = data[..., 0] > 80
    else:
        mask = in_mask > 0

    sigma = np.std(data[~mask])
    den = nlmeans(data, sigma=sigma, mask=mask)

    nb.Nifti1Image(den.astype(hdr.get_data_dtype()), aff,
                   hdr).to_filename(out_file)
    return out_file

