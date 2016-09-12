#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from nipype.testing import (assert_equal, example_data, skipif)
from nipype.algorithms.confounds import FramewiseDisplacement, ComputeDVARS
import numpy as np
from tempfile import mkdtemp
from shutil import rmtree

nonitime = True
try:
    import nitime
    nonitime = False
except ImportError:
    pass


def test_fd():
    tempdir = mkdtemp()
    ground_truth = np.loadtxt(example_data('fsl_motion_outliers_fd.txt'))
    fd = FramewiseDisplacement(in_plots=example_data('fsl_mcflirt_movpar.txt'),
                               out_file=tempdir + '/fd.txt')
    res = fd.run()
    yield assert_equal, np.allclose(ground_truth, np.loadtxt(res.outputs.out_file)), True
    yield assert_equal, np.abs(ground_truth.mean() - res.outputs.fd_average) < 1e-4, True
    rmtree(tempdir)

@skipif(nonitime)
def test_dvars():
    tempdir = mkdtemp()
    ground_truth = np.loadtxt(example_data('ds003_sub-01_mc.DVARS'))
    dvars = ComputeDVARS(in_file=example_data('ds003_sub-01_mc.nii.gz'),
                         in_mask=example_data('ds003_sub-01_mc_brainmask.nii.gz'),
                         save_all = True)
    os.chdir(tempdir)
    res = dvars.run()

    dv1 = np.loadtxt(res.outputs.out_std)
    yield assert_equal, (np.abs(dv1 - ground_truth).sum()/ len(dv1)) < 0.05, True