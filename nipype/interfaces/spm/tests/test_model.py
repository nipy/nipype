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

def test_estimatemodel():
    yield assert_equal, spm.EstimateModel._jobtype, 'stats'
    yield assert_equal, spm.EstimateModel._jobname, 'fmri_est'

def test_estimatecontrast():
    yield assert_equal, spm.EstimateContrast._jobtype, 'stats'
    yield assert_equal, spm.EstimateContrast._jobname, 'con'

def test_threshold():
    yield assert_equal, spm.Threshold._jobtype, 'basetype'
    yield assert_equal, spm.Threshold._jobname, 'basename'

def test_factorialdesign():
    yield assert_equal, spm.FactorialDesign._jobtype, 'stats'
    yield assert_equal, spm.FactorialDesign._jobname, 'factorial_design'

def test_onesamplettestdesign():
    yield assert_equal, spm.OneSampleTTestDesign._jobtype, 'stats'
    yield assert_equal, spm.OneSampleTTestDesign._jobname, 'factorial_design'

def test_twosamplettestdesign():
    yield assert_equal, spm.TwoSampleTTestDesign._jobtype, 'stats'
    yield assert_equal, spm.TwoSampleTTestDesign._jobname, 'factorial_design'
