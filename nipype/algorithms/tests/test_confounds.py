#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from io import open

import pytest
from nipype.testing import example_data
from nipype.algorithms.confounds import FramewiseDisplacement, ComputeDVARS
import numpy as np


nonitime = True
try:
    import nitime
    nonitime = False
except ImportError:
    pass


def test_fd(tmpdir):
    tempdir = str(tmpdir)
    ground_truth = np.loadtxt(example_data('fsl_motion_outliers_fd.txt'))
    fdisplacement = FramewiseDisplacement(in_plots=example_data('fsl_mcflirt_movpar.txt'),
                                          out_file=tempdir + '/fd.txt')
    res = fdisplacement.run()

    with open(res.outputs.out_file) as all_lines:
        for line in all_lines:
            assert 'FramewiseDisplacement' in line
            break

    assert np.allclose(ground_truth, np.loadtxt(res.outputs.out_file, skiprows=1), atol=.16)
    assert np.abs(ground_truth.mean() - res.outputs.fd_average) < 1e-2


@pytest.mark.skipif(nonitime, reason="nitime is not installed")
def test_dvars(tmpdir):
    ground_truth = np.loadtxt(example_data('ds003_sub-01_mc.DVARS'))
    dvars = ComputeDVARS(in_file=example_data('ds003_sub-01_mc.nii.gz'),
                         in_mask=example_data('ds003_sub-01_mc_brainmask.nii.gz'),
                         save_all=True)
    os.chdir(str(tmpdir))
    res = dvars.run()

    dv1 = np.loadtxt(res.outputs.out_std)
    assert (np.abs(dv1 - ground_truth).sum()/ len(dv1)) < 0.05
