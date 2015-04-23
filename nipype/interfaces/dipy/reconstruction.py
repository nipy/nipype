# -*- coding: utf-8 -*-
import os
import os.path as op

import numpy as np
from dipy.core.gradients import GradientTable
import nibabel as nb

from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    isdefined, OutputMultiPath,
                                    CommandLineInputSpec, CommandLine,
                                    BaseInterface, BaseInterfaceInputSpec,
                                    traits)
from nipype.utils.filemanip import split_filename, fname_presuffix

from .base import DipyBaseInterface, DipyBaseInterfaceInputSpec

from nipype import logging
iflogger = logging.getLogger('interface')


class RESTOREInputSpec(DipyBaseInterfaceInputSpec):
    in_mask = File(exists=True, desc=('input mask in which compute tensors'))
    noise_mask = File(
        exists=True, desc=('input mask in which compute noise variance'))


class RESTOREOutputSpec(TraitedSpec):
    fa = File(desc=('output fractional anisotropy (FA) map computed from '
                    'the fitted DTI'))
    md = File(desc=('output mean diffusivity (MD) map computed from the '
                    'fitted DTI'))
    rd = File(desc=('output radial diffusivity (RD) map computed from '
                    'the fitted DTI'))
    mode = File(desc=('output mode (MO) map computed from the fitted DTI'))
    trace = File(desc=('output the tensor trace map computed from the '
                       'fitted DTI'))
    evals = File(desc=('output the eigenvalues of the fitted DTI'))
    evecs = File(desc=('output the eigenvectors of the fitted DTI'))


class RESTORE(DipyBaseInterface):

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
        hdr = img.get_header().copy()
        affine = img.get_affine()
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
            iflogger.info('Input data are masked.')
            noise_msk = msk.reshape(-1).astype(np.uint8)
        else:
            noise_msk = (1 - msk).reshape(-1).astype(np.uint8)

        nb0 = np.sum(gtab.b0s_mask)
        dsample = data.reshape(-1, data.shape[-1])

        if try_b0 and (nb0 > 1):
            noise_data = dsample.take(np.where(gtab.b0s_mask),
                                      axis=-1)[noise_msk == 0, ...]
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
            bias = (1. - np.sqrt(2. / (n - 1)) *
                    (gamma(n / 2.) / gamma((n - 1) / 2.)))
        except:
            bias = .0
            pass

        sigma = mean_std * (1 + bias)

        if sigma == 0:
            iflogger.warn(
                ('Noise std is 0.0, looks like data was masked and noise'
                 ' cannot be estimated correctly. Using default tensor '
                 'model instead of RESTORE.'))
            dti = TensorModel(gtab)
        else:
            iflogger.info(('Performing RESTORE with noise std=%.4f.') % sigma)
            dti = TensorModel(gtab, fit_method='RESTORE', sigma=sigma)

        try:
            fit_restore = dti.fit(data, msk)
        except TypeError as e:
            dti = TensorModel(gtab)
            fit_restore = dti.fit(data, msk)

        hdr.set_data_dtype(np.float32)
        hdr['data_type'] = 16

        for k in self._outputs().get():
            scalar = getattr(fit_restore, k)
            hdr.set_data_shape(np.shape(scalar))
            nb.Nifti1Image(scalar.astype(np.float32),
                           affine, hdr).to_filename(self._gen_filename(k))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for k in outputs.keys():
            outputs[k] = self._gen_filename(k)
        return outputs


class EstimateResponseSHInputSpec(DipyBaseInterfaceInputSpec):
    in_evals = File(
        exists=True, mandatory=True, desc=('input eigenvalues file'))
    in_mask = File(
        exists=True, desc=('input mask in which we find single fibers'))
    fa_thresh = traits.Float(
        0.7, usedefault=True, desc=('default FA threshold'))
    save_glyph = traits.Bool(False, usedefault=True,
                             desc=('save a png file of the response'))
    response = File(desc=('the output response file'))


class EstimateResponseSHOutputSpec(TraitedSpec):
    response = File(desc=('the response file'))
    glyph_file = File(desc='graphical representation of the response')


class EstimateResponseSH(DipyBaseInterface):

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
        from dipy.reconst.csdeconv import fractional_anisotropy

        img = nb.load(self.inputs.in_file)
        affine = img.get_affine()

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data()
            msk[msk > 0] = 1
            msk[msk < 0] = 0
        else:
            msk = np.ones(imref.get_shape())

        data = img.get_data().astype(np.float32)
        gtab = self._get_gradient_table()

        evals = nb.load(self.inputs.in_evals).get_data()
        FA = fractional_anisotropy(evals)
        FA[np.isnan(FA)] = 0
        FA[msk != 1] = 0

        indices = np.where(FA > self.inputs.fa_thresh)

        lambdas = evals[indices][:, :2]
        S0s = data[indices][:, np.nonzero(gtab.b0s_mask)[0]]
        S0 = np.mean(S0s)
        l01 = np.mean(lambdas, axis=0)
        respev = np.array([l01[0], l01[1], l01[1]])
        response = (respev, S0)
        ratio = respev[1] / respev[0]

        if abs(ratio - 0.2) > 0.1:
            iflogger.warn(('Estimated response is not prolate enough. '
                           'Ratio=%0.3f.') % ratio)

        np.savetxt(self._gen_outname(),
                   np.array(respev.tolist() + [S0]).reshape(-1))

        if self.inputs.save_glyph:
            from dipy.viz import fvtk
            from dipy.data import get_sphere
            from dipy.sims.voxel import single_tensor_odf

            ren = fvtk.ren()
            evecs = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]).T
            sphere = get_sphere('symmetric724')
            response_odf = single_tensor_odf(sphere.vertices, respev, evecs)
            response_actor = fvtk.sphere_funcs(response_odf, sphere)
            fvtk.add(ren, response_actor)
            fvtk.record(ren, out_path=self._gen_outname() + '.png',
                        size=(200, 200))
            fvtk.rm(ren, response_actor)
        return runtime

    def _gen_outname(self):
        if isdefined(self.inputs.response):
            return self.inputs.response
        else:
            fname, fext = op.splitext(op.basename(self.inputs.in_file))
            if fext == '.gz':
                fname, fext2 = op.splitext(fname)
                fext = fext2 + fext
            return op.abspath(fname) + '_response.txt'
        return out_file

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['response'] = self._gen_outname()

        if isdefined(self.inputs.save_glyph) and self.inputs.save_glyph:
            outputs['glyph_file'] = self._gen_outname() + '.png'

        return outputs


class CSDInputSpec(DipyBaseInterfaceInputSpec):
    in_mask = File(exists=True, desc=('input mask in which compute tensors'))
    response = File(exists=True, desc=('single fiber estimated response'))
    sh_order = traits.Int(8, exists=True, usedefault=True,
                          desc=('maximal shperical harmonics order'))
    save_fods = traits.Bool(True, exists=True, usedefault=True,
                            desc=('save fODFs in file'))
    out_fods = File(desc=('fODFs output file name'))


class CSDOutputSpec(TraitedSpec):
    model = File(desc='Python pickled object of the CSD model fitted.')
    out_fods = File(desc=('fODFs output file name'))


class CSD(DipyBaseInterface):

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
        import marshal as pickle
        # import cPickle as pickle
        import gzip

        img = nb.load(self.inputs.in_file)
        imref = nb.four_to_three(img)[0]
        affine = img.get_affine()

        if isdefined(self.inputs.in_mask):
            msk = nb.load(self.inputs.in_mask).get_data()
        else:
            msk = np.ones(imref.get_shape())

        data = img.get_data().astype(np.float32)
        hdr = imref.get_header().copy()

        gtab = self._get_gradient_table()
        resp_file = np.loadtxt(self.inputs.response)

        response = (np.array(resp_file[0:3]), resp_file[-1])
        ratio = response[0][1] / response[0][0]

        if abs(ratio - 0.2) > 0.1:
            iflogger.warn(('Estimated response is not prolate enough. '
                           'Ratio=%0.3f.') % ratio)

        csd_model = ConstrainedSphericalDeconvModel(
            gtab, response, sh_order=self.inputs.sh_order)

        iflogger.info('Fitting CSD model')
        csd_fit = csd_model.fit(data, msk)

        f = gzip.open(self._gen_filename('csdmodel', ext='.pklz'), 'wb')
        pickle.dump(csd_model, f, -1)
        f.close()

        if self.inputs.save_fods:
            sphere = get_sphere('symmetric724')
            fods = csd_fit.odf(sphere)
            nb.Nifti1Image(fods.astype(np.float32), img.get_affine(),
                           None).to_filename(self._gen_filename('fods'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['model'] = self._gen_filename('csdmodel', ext='.pklz')
        if self.inputs.save_fods:
            outputs['out_fods'] = self._gen_filename('fods')
        return outputs
