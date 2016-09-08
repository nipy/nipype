# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Algorithms to compute confounds in :abbr:`fMRI (functional MRI)`

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str, zip, range, open

import os
import os.path as op

import nibabel as nb
import numpy as np

from ..external.due import due, Doi, BibTeX
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File)


class ComputeDVARSInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='functional data, after HMC')
    in_mask = File(exists=True, mandatory=True, desc='a brain mask')
    save_std = traits.Bool(True, usedefault=True,
                           desc='save standardized DVARS')
    save_nstd = traits.Bool(False, usedefault=True,
                            desc='save non-standardized DVARS')
    save_vxstd = traits.Bool(False, usedefault=True,
                             desc='save voxel-wise standardized DVARS')
    save_all = traits.Bool(False, usedefault=True, desc='output all DVARS')


class ComputeDVARSOutputSpec(TraitedSpec):
    out_std = File(exists=True, desc='output text file')
    out_nstd = File(exists=True, desc='output text file')
    out_vxstd = File(exists=True, desc='output text file')
    out_all = File(exists=True, desc='output text file')


class ComputeDVARS(BaseInterface):
    """
    Computes the DVARS.
    """
    input_spec = ComputeDVARSInputSpec
    output_spec = ComputeDVARSOutputSpec
    references_ = [{
        'entry': BibTex("""\
@techreport{nichols_notes_2013,
    address = {Coventry, UK},
    title = {Notes on {Creating} a {Standardized} {Version} of {DVARS}},
    url = {http://www2.warwick.ac.uk/fac/sci/statistics/staff/academic-\
research/nichols/scripts/fsl/standardizeddvars.pdf},
    urldate = {2016-08-16},
    institution = {University of Warwick},
    author = {Nichols, Thomas},
    year = {2013}
}"""),
        'tags': ['method']
    }, {
        'entry': BibTex("""\
@article{power_spurious_2012,
    title = {Spurious but systematic correlations in functional connectivity {MRI} networks \
arise from subject motion},
    volume = {59},
    doi = {10.1016/j.neuroimage.2011.10.018},
    number = {3},
    urldate = {2016-08-16},
    journal = {NeuroImage},
    author = {Power, Jonathan D. and Barnes, Kelly A. and Snyder, Abraham Z. and Schlaggar, \
Bradley L. and Petersen, Steven E.},
    year = {2012},
    pages = {2142--2154},
}
"""),
        'tags': ['method']
    }]

    def __init__(self, **inputs):
        self._results = {}
        super(ComputeDVARS, self).__init__(**inputs)

    def _gen_fname(self, suffix, ext=None):
        fname, in_ext = op.splitext(op.basename(
            self.inputs.in_file))

        if in_ext == '.gz':
            fname, in_ext2 = op.splitext(fname)
            in_ext = in_ext2 + in_ext

        if ext is None:
            ext = in_ext

        if ext.startswith('.'):
            ext = ext[1:]

        return op.abspath('{}_{},{}'.format(fname, suffix, ext))

    def _parse_inputs(self):
        if (self.inputs.save_std or self.inputs.save_nstd or
            self.inputs.save_vxstd or self.inputs.save_all):
            return super(ComputeDVARS, self)._parse_inputs()
        else:
            raise RuntimeError('At least one of the save_* options must be True')

    def _run_interface(self, runtime):
        dvars = compute_dvars(self.inputs.in_file, self.inputs.in_mask)

        if self.inputs.save_std:
            out_file = self._gen_fname('dvars_std', ext='tsv')
            np.savetxt(out_file, dvars[0], fmt=b'%.12f')
            self._results['out_std'] = out_file

        if self.inputs.save_nstd:
            out_file = self._gen_fname('dvars_nstd', ext='tsv')
            np.savetxt(out_file, dvars[1], fmt=b'%.12f')
            self._results['out_nstd'] = out_file

        if self.inputs.save_vxstd:
            out_file = self._gen_fname('dvars_vxstd', ext='tsv')
            np.savetxt(out_file, dvars[2], fmt=b'%.12f')
            self._results['out_vxstd'] = out_file

        if self.inputs.save_all:
            out_file = self._gen_fname('dvars', ext='tsv')
            np.savetxt(out_file, np.vstack(dvars), fmt=b'%.12f', delimiter=b'\t',
                       header='# std DVARS\tnon-std DVARS\tvx-wise std DVARS')
            self._results['out_all'] = out_file

        return runtime

    def _list_outputs(self):
        return self._results


def compute_dvars(in_file, in_mask):
    """
    Compute the :abbr:`DVARS (D referring to temporal
    derivative of timecourses, VARS referring to RMS variance over voxels)`
    [Power2012]_.

    Particularly, the *standardized* :abbr:`DVARS (D referring to temporal
    derivative of timecourses, VARS referring to RMS variance over voxels)`
    [Nichols2013]_ are computed.

    .. [Nichols2013] Nichols T, `Notes on creating a standardized version of
         DVARS <http://www2.warwick.ac.uk/fac/sci/statistics/staff/academic-\
research/nichols/scripts/fsl/standardizeddvars.pdf>`_, 2013.

    .. note:: Implementation details

      Uses the implementation of the `Yule-Walker equations
      from nitime
      <http://nipy.org/nitime/api/generated/nitime.algorithms.autoregressive.html\
#nitime.algorithms.autoregressive.AR_est_YW>`_
      for the :abbr:`AR (auto-regressive)` filtering of the fMRI signal.

    :param numpy.ndarray func: functional data, after head-motion-correction.
    :param numpy.ndarray mask: a 3D mask of the brain
    :param bool output_all: write out all dvars
    :param str out_file: a path to which the standardized dvars should be saved.
    :return: the standardized DVARS

    """
    import os.path as op
    import numpy as np
    import nibabel as nb
    from nitime.algorithms import AR_est_YW

    func = nb.load(in_file).get_data().astype(np.float32)
    mask = nb.load(in_mask).get_data().astype(np.uint8)

    if len(func.shape) != 4:
        raise RuntimeError(
            "Input fMRI dataset should be 4-dimensional")

    # Remove zero-variance voxels across time axis
    zv_mask = zero_variance(func, mask)
    idx = np.where(zv_mask > 0)
    mfunc = func[idx[0], idx[1], idx[2], :]

    # Robust standard deviation
    func_sd = (np.percentile(mfunc, 75) -
               np.percentile(mfunc, 25)) / 1.349

    # Demean
    mfunc -= mfunc.mean(axis=1).astype(np.float32)[..., np.newaxis]

    # AR1
    ak_coeffs = np.apply_along_axis(AR_est_YW, 1, mfunc, 1)

    # Predicted standard deviation of temporal derivative
    func_sd_pd = np.squeeze(np.sqrt((2. * (1. - ak_coeffs[:, 0])).tolist()) * func_sd)
    diff_sd_mean = func_sd_pd[func_sd_pd > 0].mean()

    # Compute temporal difference time series
    func_diff = np.diff(mfunc, axis=1)

    # DVARS (no standardization)
    dvars_nstd = func_diff.std(axis=0)

    # standardization
    dvars_stdz = dvars_nstd / diff_sd_mean

    # voxelwise standardization
    diff_vx_stdz = func_diff / np.array([func_sd_pd] * func_diff.shape[-1]).T
    dvars_vx_stdz = diff_vx_stdz.std(1, ddof=1)

    return (dvars_stdz, dvars_nstd, dvars_vx_stdz)

def zero_variance(func, mask):
    """
    Mask out voxels with zero variance across t-axis

    :param numpy.ndarray func: input fMRI dataset, after motion correction
    :param numpy.ndarray mask: 3D brain mask
    :return: the 3D mask of voxels with nonzero variance across :math:`t`.
    :rtype: numpy.ndarray

    """
    idx = np.where(mask > 0)
    func = func[idx[0], idx[1], idx[2], :]
    tvariance = func.var(axis=1)
    tv_mask = np.zeros_like(tvariance, dtype=np.uint8)
    tv_mask[tvariance > 0] = 1

    newmask = np.zeros_like(mask, dtype=np.uint8)
    newmask[idx] = tv_mask
    return newmask
