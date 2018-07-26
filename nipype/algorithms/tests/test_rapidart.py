# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import division

import numpy as np

import numpy.testing as npt
from .. import rapidart as ra
from ...interfaces.base import Bunch


def test_ad_init():
    ad = ra.ArtifactDetect(use_differences=[True, False])
    assert ad.inputs.use_differences[0]
    assert not ad.inputs.use_differences[1]


def test_ad_output_filenames():
    ad = ra.ArtifactDetect()
    outputdir = '/tmp'
    f = 'motion.nii'
    (outlierfile, intensityfile, statsfile, normfile, plotfile,
     displacementfile, maskfile) = ad._get_output_filenames(f, outputdir)
    assert outlierfile == '/tmp/art.motion_outliers.txt'
    assert intensityfile == '/tmp/global_intensity.motion.txt'
    assert statsfile == '/tmp/stats.motion.txt'
    assert normfile == '/tmp/norm.motion.txt'
    assert plotfile == '/tmp/plot.motion.png'
    assert displacementfile == '/tmp/disp.motion.nii'
    assert maskfile == '/tmp/mask.motion.nii'


def test_ad_get_affine_matrix():
    matrix = ra._get_affine_matrix(np.array([0]), 'SPM')
    npt.assert_equal(matrix, np.eye(4))
    # test translation
    params = [1, 2, 3]
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.eye(4)
    out[0:3, 3] = params
    npt.assert_equal(matrix, out)
    # test rotation
    params = np.array([0, 0, 0, np.pi / 2, np.pi / 2, np.pi / 2])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]).reshape(
        (4, 4))
    npt.assert_almost_equal(matrix, out)
    # test scaling
    params = np.array([0, 0, 0, 0, 0, 0, 1, 2, 3])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1]).reshape(
        (4, 4))
    npt.assert_equal(matrix, out)
    # test shear
    params = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 3])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([1, 1, 2, 0, 0, 1, 3, 0, 0, 0, 1, 0, 0, 0, 0, 1]).reshape(
        (4, 4))
    npt.assert_equal(matrix, out)


def test_ad_get_norm():
    params = np.array([
        0, 0, 0, 0, 0, 0, 0, 0, 0, np.pi / 4, np.pi / 4, np.pi / 4, 0, 0, 0,
        -np.pi / 4, -np.pi / 4, -np.pi / 4
    ]).reshape((3, 6))
    norm, _ = ra._calc_norm(params, False, 'SPM')
    npt.assert_almost_equal(norm,
                            np.array([18.86436316, 37.74610158, 31.29780829]))
    norm, _ = ra._calc_norm(params, True, 'SPM')
    npt.assert_almost_equal(norm, np.array([0., 143.72192614, 173.92527131]))


def test_sc_init():
    sc = ra.StimulusCorrelation(concatenated_design=True)
    assert sc.inputs.concatenated_design


def test_sc_populate_inputs():
    sc = ra.StimulusCorrelation()
    inputs = Bunch(
        realignment_parameters=None,
        intensity_values=None,
        spm_mat_file=None,
        concatenated_design=None)
    assert set(sc.inputs.__dict__.keys()) == set(inputs.__dict__.keys())


def test_sc_output_filenames():
    sc = ra.StimulusCorrelation()
    outputdir = '/tmp'
    f = 'motion.nii'
    corrfile = sc._get_output_filenames(f, outputdir)
    assert corrfile == '/tmp/qa.motion_stimcorr.txt'
