# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from nipype.testing import (assert_equal, assert_false, assert_true,
                            assert_almost_equal)
import nipype.algorithms.rapidart as ra
from nipype.interfaces.base import Bunch
import numpy as np


def test_artifactdetect():
    input_map = dict(intersect_mask=dict(),
                     mask_file=dict(),
                     mask_threshold=dict(),
                     mask_type=dict(),
                     norm_threshold=dict(),
                     parameter_source=dict(mandatory=True,),
                     realigned_files=dict(mandatory=True,),
                     realignment_parameters=dict(),
                     rotation_threshold=dict(),
                     translation_threshold=dict(),
                     use_differences=dict(usedefault=True,),
                     use_norm=dict(usedefault=True,),
                     zintensity_threshold=dict(),
                     )
    instance = ra.ArtifactDetect()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_stimuluscorrelation():
    input_map = dict(concatenated_design=dict(mandatory=True,),
                     intensity_values=dict(mandatory=True,),
                     realignment_parameters=dict(mandatory=True,),
                     spm_mat_file=dict(mandatory=True,),
                     )
    instance = ra.StimulusCorrelation()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def test_ad_init():
    ad = ra.ArtifactDetect(use_differences=[True, False])
    yield assert_true, ad.inputs.use_differences[0]
    yield assert_false, ad.inputs.use_differences[1]


def test_ad_output_filenames():
    ad = ra.ArtifactDetect()
    outputdir = '/tmp'
    f = 'motion.nii'
    (outlierfile, intensityfile, statsfile, normfile, plotfile,
     displacementfile, maskfile) = ad._get_output_filenames(f, outputdir)
    yield assert_equal, outlierfile, '/tmp/art.motion_outliers.txt'
    yield assert_equal, intensityfile, '/tmp/global_intensity.motion.txt'
    yield assert_equal, statsfile, '/tmp/stats.motion.txt'
    yield assert_equal, normfile, '/tmp/norm.motion.txt'
    yield assert_equal, plotfile, '/tmp/plot.motion.png'
    yield assert_equal, displacementfile, '/tmp/disp.motion.nii'
    yield assert_equal, maskfile, '/tmp/mask.motion.nii'


def test_ad_get_affine_matrix():
    matrix = ra._get_affine_matrix(np.array([0]), 'SPM')
    yield assert_equal, matrix, np.eye(4)
    # test translation
    params = [1, 2, 3]
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.eye(4)
    out[0:3, 3] = params
    yield assert_equal, matrix, out
    # test rotation
    params = np.array([0, 0, 0, np.pi / 2, np.pi / 2, np.pi / 2])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]).reshape((4, 4))
    yield assert_almost_equal, matrix, out
    # test scaling
    params = np.array([0, 0, 0, 0, 0, 0, 1, 2, 3])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1]).reshape((4, 4))
    yield assert_equal, matrix, out
    # test shear
    params = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 3])
    matrix = ra._get_affine_matrix(params, 'SPM')
    out = np.array([1, 1, 2, 0, 0, 1, 3, 0, 0, 0, 1, 0, 0, 0, 0, 1]).reshape((4, 4))
    yield assert_equal, matrix, out


def test_ad_get_norm():
    params = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, np.pi / 4, np.pi / 4,
                       np.pi / 4, 0, 0, 0, -np.pi / 4,
                       -np.pi / 4, -np.pi / 4]).reshape((3, 6))
    norm, _ = ra._calc_norm(params, False, 'SPM')
    yield assert_almost_equal, norm, np.array([18.86436316, 37.74610158, 31.29780829])
    norm, _ = ra._calc_norm(params, True, 'SPM')
    yield assert_almost_equal, norm, np.array([0., 143.72192614, 173.92527131])


def test_sc_init():
    sc = ra.StimulusCorrelation(concatenated_design=True)
    yield assert_true, sc.inputs.concatenated_design


def test_sc_populate_inputs():
    sc = ra.StimulusCorrelation()
    inputs = Bunch(realignment_parameters=None,
                   intensity_values=None,
                   spm_mat_file=None,
                   concatenated_design=None)
    yield assert_equal, sc.inputs.__dict__.keys(), inputs.__dict__.keys()


def test_sc_output_filenames():
    sc = ra.StimulusCorrelation()
    outputdir = '/tmp'
    f = 'motion.nii'
    corrfile = sc._get_output_filenames(f, outputdir)
    yield assert_equal, corrfile, '/tmp/qa.motion_stimcorr.txt'
