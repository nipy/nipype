# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os.path as op
import nibabel as nb
import numpy as np

from ...utils import NUMPY_MMAP

from ... import logging
from ..base import (traits, TraitedSpec, File, isdefined)
from .base import DipyBaseInterface

IFLOGGER = logging.getLogger('nipype.interface')


class ResampleInputSpec(TraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc='The input 4D diffusion-weighted image file')
    vox_size = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        desc=('specify the new voxel zooms. If no vox_size'
              ' is set, then isotropic regridding will '
              'be performed, with spacing equal to the '
              'smallest current zoom.'))
    interp = traits.Int(
        1,
        mandatory=True,
        usedefault=True,
        desc=('order of the interpolator (0 = nearest, 1 = linear, etc.'))


class ResampleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Resample(DipyBaseInterface):
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
        resample_proxy(
            self.inputs.in_file,
            order=order,
            new_zooms=vox_size,
            out_file=out_file)

        IFLOGGER.info('Resliced image saved as %s', out_file)
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
    in_file = File(
        exists=True,
        mandatory=True,
        desc='The input 4D diffusion-weighted image file')
    in_mask = File(exists=True, desc='brain mask')
    noise_model = traits.Enum(
        'rician',
        'gaussian',
        mandatory=True,
        usedefault=True,
        desc=('noise distribution model'))
    signal_mask = File(
        desc=('mask in which the mean signal '
              'will be computed'),
        exists=True)
    noise_mask = File(
        desc=('mask in which the standard deviation of noise '
              'will be computed'),
        exists=True)
    patch_radius = traits.Int(1, usedefault=True, desc='patch radius')
    block_radius = traits.Int(5, usedefault=True, desc='block_radius')
    snr = traits.Float(desc='manually set an SNR')


class DenoiseOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Denoise(DipyBaseInterface):
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

        settings = dict(
            mask=None, rician=(self.inputs.noise_model == 'rician'))

        if isdefined(self.inputs.in_mask):
            settings['mask'] = nb.load(self.inputs.in_mask).get_data()

        if isdefined(self.inputs.patch_radius):
            settings['patch_radius'] = self.inputs.patch_radius

        if isdefined(self.inputs.block_radius):
            settings['block_radius'] = self.inputs.block_radius

        snr = None
        if isdefined(self.inputs.snr):
            snr = self.inputs.snr

        signal_mask = None
        if isdefined(self.inputs.signal_mask):
            signal_mask = nb.load(self.inputs.signal_mask).get_data()
        noise_mask = None
        if isdefined(self.inputs.noise_mask):
            noise_mask = nb.load(self.inputs.noise_mask).get_data()

        _, s = nlmeans_proxy(
            self.inputs.in_file,
            settings,
            snr=snr,
            smask=signal_mask,
            nmask=noise_mask,
            out_file=out_file)
        IFLOGGER.info('Denoised image saved as %s, estimated SNR=%s', out_file,
                      str(s))
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
    from dipy.align.reslice import reslice

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        out_file = op.abspath('./%s_reslice%s' % (fname, fext))

    img = nb.load(in_file, mmap=NUMPY_MMAP)
    hdr = img.header.copy()
    data = img.get_data().astype(np.float32)
    affine = img.affine
    im_zooms = hdr.get_zooms()[:3]

    if new_zooms is None:
        minzoom = np.array(im_zooms).min()
        new_zooms = tuple(np.ones((3, )) * minzoom)

    if np.all(im_zooms == new_zooms):
        return in_file

    data2, affine2 = reslice(data, affine, im_zooms, new_zooms, order=order)
    tmp_zooms = np.array(hdr.get_zooms())
    tmp_zooms[:3] = new_zooms[0]
    hdr.set_zooms(tuple(tmp_zooms))
    hdr.set_data_shape(data2.shape)
    hdr.set_xyzt_units('mm')
    nb.Nifti1Image(data2.astype(hdr.get_data_dtype()), affine2,
                   hdr).to_filename(out_file)
    return out_file, new_zooms


def nlmeans_proxy(in_file,
                  settings,
                  snr=None,
                  smask=None,
                  nmask=None,
                  out_file=None):
    """
    Uses non-local means to denoise 4D datasets
    """
    from dipy.denoise.nlmeans import nlmeans
    from scipy.ndimage.morphology import binary_erosion
    from scipy import ndimage

    if out_file is None:
        fname, fext = op.splitext(op.basename(in_file))
        if fext == '.gz':
            fname, fext2 = op.splitext(fname)
            fext = fext2 + fext
        out_file = op.abspath('./%s_denoise%s' % (fname, fext))

    img = nb.load(in_file, mmap=NUMPY_MMAP)
    hdr = img.header
    data = img.get_data()
    aff = img.affine

    if data.ndim < 4:
        data = data[..., np.newaxis]

    data = np.nan_to_num(data)

    if data.max() < 1.0e-4:
        raise RuntimeError('There is no signal in the image')

    df = 1.0
    if data.max() < 1000.0:
        df = 1000. / data.max()
        data *= df

    b0 = data[..., 0]

    if smask is None:
        smask = np.zeros_like(b0)
        smask[b0 > np.percentile(b0, 85.)] = 1

    smask = binary_erosion(
        smask.astype(np.uint8), iterations=2).astype(np.uint8)

    if nmask is None:
        nmask = np.ones_like(b0, dtype=np.uint8)
        bmask = settings['mask']
        if bmask is None:
            bmask = np.zeros_like(b0)
            bmask[b0 > np.percentile(b0[b0 > 0], 10)] = 1
            label_im, nb_labels = ndimage.label(bmask)
            sizes = ndimage.sum(bmask, label_im, range(nb_labels + 1))
            maxidx = np.argmax(sizes)
            bmask = np.zeros_like(b0, dtype=np.uint8)
            bmask[label_im == maxidx] = 1
        nmask[bmask > 0] = 0
    else:
        nmask = np.squeeze(nmask)
        nmask[nmask > 0.0] = 1
        nmask[nmask < 1] = 0
        nmask = nmask.astype(bool)

    nmask = binary_erosion(nmask, iterations=1).astype(np.uint8)

    den = np.zeros_like(data)

    est_snr = True
    if snr is not None:
        snr = [snr] * data.shape[-1]
        est_snr = False
    else:
        snr = []

    for i in range(data.shape[-1]):
        d = data[..., i]
        if est_snr:
            s = np.mean(d[smask > 0])
            n = np.std(d[nmask > 0])
            snr.append(s / n)

        den[..., i] = nlmeans(d, snr[i], **settings)

    den = np.squeeze(den)
    den /= df

    nb.Nifti1Image(den.astype(hdr.get_data_dtype()), aff,
                   hdr).to_filename(out_file)
    return out_file, snr
