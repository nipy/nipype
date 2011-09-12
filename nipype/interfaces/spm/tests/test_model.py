# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

from nipype.testing import (assert_equal, assert_false, assert_true,
                            assert_raises, skipif)
import nibabel as nb
import nipype.interfaces.spm.model as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(outdir,f))
    return filelist, outdir, cwd

def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)

def test_level1design():
    yield assert_equal, spm.Level1Design._jobtype, 'stats'
    yield assert_equal, spm.Level1Design._jobname, 'fmri_spec'
    input_map = dict(bases = dict(field='bases',),
                     factor_info = dict(field='fact',),
                     global_intensity_normalization = dict(field='global',),
                     interscan_interval = dict(field='timing.RT',),
                     mask_image = dict(field='mask',),
                     mask_threshold = dict(),
                     microtime_onset = dict(field='timing.fmri_t0',),
                     microtime_resolution = dict(field='timing.fmri_t',),
                     model_serial_correlations = dict(field='cvi',),
                     session_info = dict(field='sess',),
                     spm_mat_dir = dict(field='dir',),
                     timing_units = dict(field='timing.units',),
                     volterra_expansion_order = dict(field='volt',),
                     )
    instance = spm.Level1Design()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_estimatemodel():
    yield assert_equal, spm.EstimateModel._jobtype, 'stats'
    yield assert_equal, spm.EstimateModel._jobname, 'fmri_est'
    input_map = dict(estimation_method = dict(field='method',),
                     spm_mat_file = dict(copyfile=True,field='spmmat',),
                     )
    instance = spm.EstimateModel()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_estimatecontrast():
    yield assert_equal, spm.EstimateContrast._jobtype, 'stats'
    yield assert_equal, spm.EstimateContrast._jobname, 'con'
    input_map = dict(beta_images = dict(copyfile=False,),
                     residual_image = dict(copyfile=False,),
                     spm_mat_file = dict(copyfile=True,field='spmmat',),
                     )
    instance = spm.EstimateContrast()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_threshold():
    yield assert_equal, spm.Threshold._jobtype, 'basetype'
    yield assert_equal, spm.Threshold._jobname, 'basename'
    input_map = dict(contrast_index = dict(mandatory=True,),
                     stat_image = dict(copyfile=False,mandatory=True,),
                     spm_mat_file = dict(copyfile=True,mandatory=True,),
                     use_fwe_correction = dict(usedefault=True),
                     height_threshold = dict(usedefault=True),
                     extent_fdr_p_threshold = dict(usedefault=True),
                     extent_threshold = dict(usedefault=True),
                     )
    instance = spm.Threshold()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_factorialdesign():
    yield assert_equal, spm.FactorialDesign._jobtype, 'stats'
    yield assert_equal, spm.FactorialDesign._jobname, 'factorial_design'
    input_map = dict(covariates = dict(field='cov',),
                     explicit_mask_file = dict(field='masking.em',),
                     global_calc_mean = dict(field='globalc.g_mean',),
                     global_calc_omit = dict(field='globalc.g_omit',),
                     global_calc_values = dict(field='globalc.g_user.global_uval',),
                     global_normalization = dict(field='globalm.glonorm',),
                     no_grand_mean_scaling = dict(field='globalm.gmsca.gmsca_no',),
                     spm_mat_dir = dict(field='dir',),
                     threshold_mask_absolute = dict(field='masking.tm.tma.athresh',),
                     threshold_mask_none = dict(field='masking.tm.tm_none',),
                     use_implicit_threshold = dict(field='masking.im',),
                     )
    instance = spm.FactorialDesign()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_onesamplettestdesign():
    yield assert_equal, spm.OneSampleTTestDesign._jobtype, 'stats'
    yield assert_equal, spm.OneSampleTTestDesign._jobname, 'factorial_design'
    input_map = dict(covariates = dict(field='cov',),
                     explicit_mask_file = dict(field='masking.em',),
                     global_calc_mean = dict(field='globalc.g_mean',),
                     global_calc_omit = dict(field='globalc.g_omit',),
                     global_calc_values = dict(field='globalc.g_user.global_uval',),
                     global_normalization = dict(field='globalm.glonorm',),
                     in_files = dict(field='des.t1.scans',mandatory=True,),
                     no_grand_mean_scaling = dict(field='globalm.gmsca.gmsca_no',),
                     spm_mat_dir = dict(field='dir',),
                     threshold_mask_absolute = dict(field='masking.tm.tma.athresh',),
                     threshold_mask_none = dict(field='masking.tm.tm_none',),
                     use_implicit_threshold = dict(field='masking.im',),
                     )
    instance = spm.OneSampleTTestDesign()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_twosamplettestdesign():
    yield assert_equal, spm.TwoSampleTTestDesign._jobtype, 'stats'
    yield assert_equal, spm.TwoSampleTTestDesign._jobname, 'factorial_design'
    input_map = dict(covariates = dict(field='cov',),
                     dependent = dict(field='des.t2.dept',),
                     explicit_mask_file = dict(field='masking.em',),
                     global_calc_mean = dict(field='globalc.g_mean',),
                     global_calc_omit = dict(field='globalc.g_omit',),
                     global_calc_values = dict(field='globalc.g_user.global_uval',),
                     global_normalization = dict(field='globalm.glonorm',),
                     group1_files = dict(field='des.t2.scans1',mandatory=True,),
                     group2_files = dict(field='des.t2.scans2',mandatory=True,),
                     no_grand_mean_scaling = dict(field='globalm.gmsca.gmsca_no',),
                     spm_mat_dir = dict(field='dir',),
                     threshold_mask_absolute = dict(field='masking.tm.tma.athresh',),
                     threshold_mask_none = dict(field='masking.tm.tm_none',),
                     unequal_variance = dict(field='des.t2.variance',),
                     use_implicit_threshold = dict(field='masking.im',),
                     )
    instance = spm.TwoSampleTTestDesign()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

#@skipif(no_spm, "SPM not found")
#def test_spm_realign_inputs():
#    pass
