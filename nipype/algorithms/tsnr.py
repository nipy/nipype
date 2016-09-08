# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Miscellaneous algorithms

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from nipype.interfaces.base import (BaseInterface, traits, TraitedSpec, File,
                                    InputMultiPath, BaseInterfaceInputSpec,
                                    isdefined)

import nibabel as nb
import numpy as np
import os.path as op
from scipy.special import legendre

class TSNRInputSpec(BaseInterfaceInputSpec):
    in_file = InputMultiPath(File(exists=True), mandatory=True,
                             desc='realigned 4D file or a list of 3D files')
    regress_poly = traits.Range(low=1, desc='Remove polynomials')
    tsnr_file = File('tsnr.nii.gz', usedefault=True, hash_files=False,
                     desc='output tSNR file')
    mean_file = File('mean.nii.gz', usedefault=True, hash_files=False,
                     desc='output mean file')
    stddev_file = File('stdev.nii.gz', usedefault=True, hash_files=False,
                       desc='output tSNR file')
    detrended_file = File('detrend.nii.gz', usedefault=True, hash_files=False,
                          desc='input file after detrending')


class TSNROutputSpec(TraitedSpec):
    tsnr_file = File(exists=True, desc='tsnr image file')
    mean_file = File(exists=True, desc='mean image file')
    stddev_file = File(exists=True, desc='std dev image file')
    detrended_file = File(desc='detrended input file')


class TSNR(BaseInterface):
    """Computes the time-course SNR for a time series

    Typically you want to run this on a realigned time-series.

    Example
    -------

    >>> tsnr = TSNR()
    >>> tsnr.inputs.in_file = 'functional.nii'
    >>> res = tsnr.run() # doctest: +SKIP

    """
    input_spec = TSNRInputSpec
    output_spec = TSNROutputSpec

    def _run_interface(self, runtime):
        img = nb.load(self.inputs.in_file[0])
        header = img.header.copy()
        vollist = [nb.load(filename) for filename in self.inputs.in_file]
        data = np.concatenate([vol.get_data().reshape(
            vol.get_shape()[:3] + (-1,)) for vol in vollist], axis=3)
        data = np.nan_to_num(data)

        if data.dtype.kind == 'i':
            header.set_data_dtype(np.float32)
            data = data.astype(np.float32)

        if isdefined(self.inputs.regress_poly):
            timepoints = img.shape[-1]
            X = np.ones((timepoints, 1))
            for i in range(self.inputs.regress_poly):
                X = np.hstack((X, legendre(
                    i + 1)(np.linspace(-1, 1, timepoints))[:, None]))
            betas = np.dot(np.linalg.pinv(X), np.rollaxis(data, 3, 2))
            datahat = np.rollaxis(np.dot(X[:, 1:],
                                         np.rollaxis(
                                             betas[1:, :, :, :], 0, 3)),
                                  0, 4)
            data = data - datahat
            img = nb.Nifti1Image(data, img.get_affine(), header)
            nb.save(img, op.abspath(self.inputs.detrended_file))

        meanimg = np.mean(data, axis=3)
        stddevimg = np.std(data, axis=3)
        tsnr = np.zeros_like(meanimg)
        tsnr[stddevimg > 1.e-3] = meanimg[stddevimg > 1.e-3] / stddevimg[stddevimg > 1.e-3]
        img = nb.Nifti1Image(tsnr, img.get_affine(), header)
        nb.save(img, op.abspath(self.inputs.tsnr_file))
        img = nb.Nifti1Image(meanimg, img.get_affine(), header)
        nb.save(img, op.abspath(self.inputs.mean_file))
        img = nb.Nifti1Image(stddevimg, img.get_affine(), header)
        nb.save(img, op.abspath(self.inputs.stddev_file))
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        for k in ['tsnr_file', 'mean_file', 'stddev_file']:
            outputs[k] = op.abspath(getattr(self.inputs, k))

        if isdefined(self.inputs.regress_poly):
            outputs['detrended_file'] = op.abspath(self.inputs.detrended_file)
        return outputs
