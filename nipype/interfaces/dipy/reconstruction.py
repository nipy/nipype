# -*- coding: utf-8 -*-
"""
Interfaces to the reconstruction algorithms in dipy

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from future import standard_library
standard_library.install_aliases()
from builtins import str, open

import os.path as op

import numpy as np
import nibabel as nb

from ... import logging
from ..base import TraitedSpec, File, traits, isdefined
from .base import DipyDiffusionInterface, DipyBaseInterfaceInputSpec

IFLOGGER = logging.getLogger('nipype.interface')


class RESTOREInputSpec(DipyBaseInterfaceInputSpec):
    in_mask = File(exists=True, desc=('input mask in which compute tensors'))
    noise_mask = File(
        exists=True, desc=('input mask in which compute noise variance'))


class RESTOREOutputSpec(TraitedSpec):
    fa = File(desc='output fractional anisotropy (FA) map computed from '
              'the fitted DTI')
    md = File(desc='output mean diffusivity (MD) map computed from the '
              'fitted DTI')
    rd = File(desc='output radial diffusivity (RD) map computed from '
              'the fitted DTI')
    mode = File(desc=('output mode (MO) map computed from the fitted DTI'))
    trace = File(
        desc=('output the tensor trace map computed from the '
              'fitted DTI'))
    evals = File(desc=('output the eigenvalues of the fitted DTI'))
    evecs = File(desc=('output the eigenvectors of the fitted DTI'))


class RESTORE(DipyDiffusionInterface):
    """
    Uses RESTORE [Chang2005]_ to perform DTI fitting with outlier detection.
    The interface uses :py:mod:`dipy`, as explained in `dipy's documentation`_.

    .. [Chang2005] Chang, LC, Jones, DK and Pierpaoli, C. RESTORE: robust \
    estimation of tensors by outlier rejection. MRM, 53:1088-95, (2005).

    .. _dipy's documentation: \
    http://nipy.org/dipy/examples_built/restore_dti.html


    Example
    -------

    >>> from nipype.interfaces import dipy as ndp
    >>> dti = ndp.RESTORE()
    >>> dti.inputs.in_file = '4d_dwi.nii'
    >>> dti.inputs.in_bval = 'bvals'
    >>> dti.inputs.in_bvec = 'bvecs'
    >>> res = dti.run() # doctest: +SKIP


    """
    input_spec = RESTOREInputSpec
    output_spec = RESTOREOutputSpec

    def _run_interface(self, runtime):
        from scipy.special import gamma
        from dipy.reconst.dti import TensorModel
        import gc

        img = nb.load(self.inputs.in_file)
        hdr = img.header.copy()
        affine = img.affine
        data = img.get_data()
        gtab = self._get_gradient_table()

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data().astype(np.uint8)
        else:
            msk = np.ones(data.shape[:3], dtype=np.uint8)

        try_b0 = True
        if isdefined(self.inputs.noise_mask):
            noise_msk = nb.load(self.inputs.noise_mask).get_data().reshape(-1)
            noise_msk[noise_msk > 0.5] = 1
            noise_msk[noise_msk < 1.0] = 0
            noise_msk = noise_msk.astype(np.uint8)
            try_b0 = False
        elif np.all(data[msk == 0, 0] == 0):
            IFLOGGER.info('Input data are masked.')
            noise_msk = msk.reshape(-1).astype(np.uint8)
        else:
            noise_msk = (1 - msk).reshape(-1).astype(np.uint8)

        nb0 = np.sum(gtab.b0s_mask)
        dsample = data.reshape(-1, data.shape[-1])

        if try_b0 and (nb0 > 1):
            noise_data = dsample.take(
                np.where(gtab.b0s_mask), axis=-1)[noise_msk == 0, ...]
            n = nb0
        else:
            nodiff = np.where(~gtab.b0s_mask)
            nodiffidx = nodiff[0].tolist()
            n = 20 if len(nodiffidx) >= 20 else len(nodiffidx)
            idxs = np.random.choice(nodiffidx, size=n, replace=False)
            noise_data = dsample.take(idxs, axis=-1)[noise_msk == 1, ...]

        # Estimate sigma required by RESTORE
        mean_std = np.median(noise_data.std(-1))
        try:
            bias = (1. - np.sqrt(2. / (n - 1)) * (gamma(n / 2.) / gamma(
                (n - 1) / 2.)))
        except:
            bias = .0
            pass

        sigma = mean_std * (1 + bias)

        if sigma == 0:
            IFLOGGER.warn('Noise std is 0.0, looks like data was masked and '
                          'noise cannot be estimated correctly. Using default '
                          'tensor model instead of RESTORE.')
            dti = TensorModel(gtab)
        else:
            IFLOGGER.info('Performing RESTORE with noise std=%.4f.', sigma)
            dti = TensorModel(gtab, fit_method='RESTORE', sigma=sigma)

        try:
            fit_restore = dti.fit(data, msk)
        except TypeError:
            dti = TensorModel(gtab)
            fit_restore = dti.fit(data, msk)

        hdr.set_data_dtype(np.float32)
        hdr['data_type'] = 16

        for k in self._outputs().get():
            scalar = getattr(fit_restore, k)
            hdr.set_data_shape(np.shape(scalar))
            nb.Nifti1Image(scalar.astype(np.float32), affine, hdr).to_filename(
                self._gen_filename(k))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for k in list(outputs.keys()):
            outputs[k] = self._gen_filename(k)
        return outputs


class EstimateResponseSHInputSpec(DipyBaseInterfaceInputSpec):
    in_evals = File(
        exists=True, mandatory=True, desc=('input eigenvalues file'))
    in_mask = File(
        exists=True, desc=('input mask in which we find single fibers'))
    fa_thresh = traits.Float(0.7, usedefault=True, desc=('FA threshold'))
    roi_radius = traits.Int(
        10, usedefault=True, desc=('ROI radius to be used in auto_response'))
    auto = traits.Bool(
        xor=['recursive'], desc='use the auto_response estimator from dipy')
    recursive = traits.Bool(
        xor=['auto'], desc='use the recursive response estimator from dipy')
    response = File(
        'response.txt', usedefault=True, desc=('the output response file'))
    out_mask = File('wm_mask.nii.gz', usedefault=True, desc='computed wm mask')


class EstimateResponseSHOutputSpec(TraitedSpec):
    response = File(exists=True, desc=('the response file'))
    out_mask = File(exists=True, desc=('output wm mask'))


class EstimateResponseSH(DipyDiffusionInterface):
    """
    Uses dipy to compute the single fiber response to be used in spherical
    deconvolution methods, in a similar way to MRTrix's command
    ``estimate_response``.


    Example
    -------

    >>> from nipype.interfaces import dipy as ndp
    >>> dti = ndp.EstimateResponseSH()
    >>> dti.inputs.in_file = '4d_dwi.nii'
    >>> dti.inputs.in_bval = 'bvals'
    >>> dti.inputs.in_bvec = 'bvecs'
    >>> dti.inputs.in_evals = 'dwi_evals.nii'
    >>> res = dti.run() # doctest: +SKIP


    """
    input_spec = EstimateResponseSHInputSpec
    output_spec = EstimateResponseSHOutputSpec

    def _run_interface(self, runtime):
        from dipy.core.gradients import GradientTable
        from dipy.reconst.dti import fractional_anisotropy, mean_diffusivity
        from dipy.reconst.csdeconv import recursive_response, auto_response

        img = nb.load(self.inputs.in_file)
        imref = nb.four_to_three(img)[0]
        affine = img.affine

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data()
            msk[msk > 0] = 1
            msk[msk < 0] = 0
        else:
            msk = np.ones(imref.shape)

        data = img.get_data().astype(np.float32)
        gtab = self._get_gradient_table()

        evals = np.nan_to_num(nb.load(self.inputs.in_evals).get_data())
        FA = np.nan_to_num(fractional_anisotropy(evals)) * msk
        indices = np.where(FA > self.inputs.fa_thresh)
        S0s = data[indices][:, np.nonzero(gtab.b0s_mask)[0]]
        S0 = np.mean(S0s)

        if self.inputs.auto:
            response, ratio = auto_response(
                gtab,
                data,
                roi_radius=self.inputs.roi_radius,
                fa_thr=self.inputs.fa_thresh)
            response = response[0].tolist() + [S0]
        elif self.inputs.recursive:
            MD = np.nan_to_num(mean_diffusivity(evals)) * msk
            indices = np.logical_or(FA >= 0.4,
                                    (np.logical_and(FA >= 0.15, MD >= 0.0011)))
            data = nb.load(self.inputs.in_file).get_data()
            response = recursive_response(
                gtab,
                data,
                mask=indices,
                sh_order=8,
                peak_thr=0.01,
                init_fa=0.08,
                init_trace=0.0021,
                iter=8,
                convergence=0.001,
                parallel=True)
            ratio = abs(response[1] / response[0])
        else:
            lambdas = evals[indices]
            l01 = np.sort(np.mean(lambdas, axis=0))

            response = np.array([l01[-1], l01[-2], l01[-2], S0])
            ratio = abs(response[1] / response[0])

        if ratio > 0.25:
            IFLOGGER.warn('Estimated response is not prolate enough. '
                          'Ratio=%0.3f.', ratio)
        elif ratio < 1.e-5 or np.any(np.isnan(response)):
            response = np.array([1.8e-3, 3.6e-4, 3.6e-4, S0])
            IFLOGGER.warn(
                'Estimated response is not valid, using a default one')
        else:
            IFLOGGER.info('Estimated response: %s', str(response[:3]))

        np.savetxt(op.abspath(self.inputs.response), response)

        wm_mask = np.zeros_like(FA)
        wm_mask[indices] = 1
        nb.Nifti1Image(wm_mask.astype(np.uint8), affine, None).to_filename(
            op.abspath(self.inputs.out_mask))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['response'] = op.abspath(self.inputs.response)
        outputs['out_mask'] = op.abspath(self.inputs.out_mask)
        return outputs


class CSDInputSpec(DipyBaseInterfaceInputSpec):
    in_mask = File(exists=True, desc=('input mask in which compute tensors'))
    response = File(exists=True, desc=('single fiber estimated response'))
    sh_order = traits.Int(
        8, usedefault=True, desc=('maximal shperical harmonics order'))
    save_fods = traits.Bool(True, usedefault=True, desc=('save fODFs in file'))
    out_fods = File(desc=('fODFs output file name'))


class CSDOutputSpec(TraitedSpec):
    model = File(desc='Python pickled object of the CSD model fitted.')
    out_fods = File(desc=('fODFs output file name'))


class CSD(DipyDiffusionInterface):
    """
    Uses CSD [Tournier2007]_ to generate the fODF of DWIs. The interface uses
    :py:mod:`dipy`, as explained in `dipy's CSD example
    <http://nipy.org/dipy/examples_built/reconst_csd.html>`_.

    .. [Tournier2007] Tournier, J.D., et al. NeuroImage 2007.
      Robust determination of the fibre orientation distribution in diffusion
      MRI: Non-negativity constrained super-resolved spherical deconvolution


    Example
    -------

    >>> from nipype.interfaces import dipy as ndp
    >>> csd = ndp.CSD()
    >>> csd.inputs.in_file = '4d_dwi.nii'
    >>> csd.inputs.in_bval = 'bvals'
    >>> csd.inputs.in_bvec = 'bvecs'
    >>> res = csd.run() # doctest: +SKIP
    """
    input_spec = CSDInputSpec
    output_spec = CSDOutputSpec

    def _run_interface(self, runtime):
        from dipy.reconst.csdeconv import ConstrainedSphericalDeconvModel
        from dipy.data import get_sphere
        # import marshal as pickle
        import pickle as pickle
        import gzip

        img = nb.load(self.inputs.in_file)
        imref = nb.four_to_three(img)[0]

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data()
        else:
            msk = np.ones(imref.shape)

        data = img.get_data().astype(np.float32)

        gtab = self._get_gradient_table()
        resp_file = np.loadtxt(self.inputs.response)

        response = (np.array(resp_file[0:3]), resp_file[-1])
        ratio = response[0][1] / response[0][0]

        if abs(ratio - 0.2) > 0.1:
            IFLOGGER.warn('Estimated response is not prolate enough. '
                          'Ratio=%0.3f.', ratio)

        csd_model = ConstrainedSphericalDeconvModel(
            gtab, response, sh_order=self.inputs.sh_order)

        IFLOGGER.info('Fitting CSD model')
        csd_fit = csd_model.fit(data, msk)

        f = gzip.open(self._gen_filename('csdmodel', ext='.pklz'), 'wb')
        pickle.dump(csd_model, f, -1)
        f.close()

        if self.inputs.save_fods:
            sphere = get_sphere('symmetric724')
            fods = csd_fit.odf(sphere)
            nb.Nifti1Image(fods.astype(np.float32), img.affine,
                           None).to_filename(self._gen_filename('fods'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['model'] = self._gen_filename('csdmodel', ext='.pklz')
        if self.inputs.save_fods:
            outputs['out_fods'] = self._gen_filename('fods')
        return outputs
