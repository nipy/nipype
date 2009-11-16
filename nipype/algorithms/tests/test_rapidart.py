from nipype.testing import (assert_equal, assert_false, assert_true, 
                            assert_raises, assert_almost_equal)
import nipype.algorithms.rapidart as ra
from nipype.interfaces.base import Bunch
from tempfile import mkdtemp
import os
from shutil import rmtree
import numpy as np

def test_ad_init():
    ad = ra.ArtifactDetect(use_differences=[True,False])
    yield assert_true, ad.inputs.use_differences[0]
    yield assert_false, ad.inputs.use_differences[1]

def test_ad_populate_inputs():
    ad = ra.ArtifactDetect()
    inputs = Bunch(realigned_files=None,
                   realignment_parameters=None,
                   parameter_source=None,
                   use_differences=[True,True],
                   use_norm=True,
                   norm_threshold=None,
                   rotation_threshold=None,
                   translation_threshold=None,
                   zintensity_threshold=None,
                   mask_type=None,
                   mask_file=None,
                   mask_threshold=None,
                   intersect_mask=True)
    yield assert_equal, ad.inputs.__dict__.keys(), inputs.__dict__.keys()

def test_ad_output_filenames():
    ad = ra.ArtifactDetect()
    outputdir = '/tmp'
    f = 'motion.nii'
    outlierfile,intensityfile,statsfile,normfile = ad._get_output_filenames(f,outputdir)
    yield assert_equal, outlierfile, '/tmp/art.motion_outliers.txt'
    yield assert_equal, intensityfile, '/tmp/global_intensity.motion.txt'
    yield assert_equal, statsfile, '/tmp/stats.motion.txt'
    yield assert_equal, normfile, '/tmp/norm.motion.txt'

def test_ad_outputs():
    ad = ra.ArtifactDetect()
    outputs = Bunch(outlier_files=None,
                    intensity_files=None,
                    statistic_files=None)
    yield assert_equal, ad.outputs().__dict__.keys(), outputs.__dict__.keys()

def test_ad_get_input_info():
    yield assert_equal, ra.ArtifactDetect().get_input_info(), []

def test_ad_get_affine_matrix():
    ad = ra.ArtifactDetect()
    matrix = ad._get_affine_matrix(np.array([0]))
    yield assert_equal, matrix, np.eye(4)
    # test translation
    params = [1,2,3]
    matrix = ad._get_affine_matrix(params)
    out = np.eye(4)
    out[0:3,3] = params
    yield assert_equal, matrix, out
    # test rotation
    params = np.array([0,0,0,np.pi/2,np.pi/2,np.pi/2])
    matrix = ad._get_affine_matrix(params)
    out = np.array([0,0,1,0,0,-1,0,0,1,0,0,0,0,0,0,1]).reshape((4,4))
    yield assert_almost_equal, matrix, out
    # test scaling
    params = np.array([0,0,0,0,0,0,1,2,3])
    matrix = ad._get_affine_matrix(params)
    out = np.array([1,0,0,0,0,2,0,0,0,0,3,0,0,0,0,1]).reshape((4,4))
    yield assert_equal, matrix, out
    # test shear
    params = np.array([0,0,0,0,0,0,1,1,1,1,2,3])
    matrix = ad._get_affine_matrix(params)
    out = np.array([1,1,2,0,0,1,3,0,0,0,1,0,0,0,0,1]).reshape((4,4))
    yield assert_equal, matrix, out

def test_ad_get_norm():
    ad = ra.ArtifactDetect()
    params = np.array([0,0,0,0,0,0,0,0,0,np.pi/4,np.pi/4,np.pi/4,0,0,0,-np.pi/4,-np.pi/4,-np.pi/4]).reshape((3,6))
    norm = ad._calc_norm(params,False)
    yield assert_almost_equal, norm, np.array([18.86436316, 37.74610158,  31.29780829])
    norm = ad._calc_norm(params,True)
    yield assert_almost_equal, norm, np.array([   0.        ,  143.72192614,  173.92527131])

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
    corrfile = sc._get_output_filenames(f,outputdir)
    yield assert_equal, corrfile, '/tmp/qa.motion_stimcorr.txt'
    
def test_sc_outputs():
    sc = ra.StimulusCorrelation()
    outputs = Bunch(stimcorr_files=None)
    yield assert_equal, sc.outputs().__dict__.keys(), outputs.__dict__.keys()

def test_sc_get_input_info():
    yield assert_equal, ra.StimulusCorrelation().get_input_info(), []
