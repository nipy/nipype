#!/usr/bin/env python

import pytest
from nipype.testing import example_data
from nipype.algorithms.confounds import FramewiseDisplacement, ComputeDVARS, is_outlier
import numpy as np

nonitime = True
try:
    import nitime

    nonitime = False
except ImportError:
    pass


def test_fd(tmpdir):
    tempdir = tmpdir.strpath
    ground_truth = np.loadtxt(example_data("fsl_motion_outliers_fd.txt"))
    fdisplacement = FramewiseDisplacement(
        in_file=example_data("fsl_mcflirt_movpar.txt"),
        out_file=tempdir + "/fd.txt",
        parameter_source="FSL",
    )
    res = fdisplacement.run()

    with open(res.outputs.out_file) as all_lines:
        for line in all_lines:
            assert "FramewiseDisplacement" in line
            break

    assert np.allclose(
        ground_truth, np.loadtxt(res.outputs.out_file, skiprows=1), atol=0.16
    )
    assert np.abs(ground_truth.mean() - res.outputs.fd_average) < 1e-2


@pytest.mark.skipif(nonitime, reason="nitime is not installed")
def test_dvars(tmpdir):
    ground_truth = np.loadtxt(example_data("ds003_sub-01_mc.DVARS"))
    dvars = ComputeDVARS(
        in_file=example_data("ds003_sub-01_mc.nii.gz"),
        in_mask=example_data("ds003_sub-01_mc_brainmask.nii.gz"),
        save_all=True,
        intensity_normalization=0,
    )
    tmpdir.chdir()
    res = dvars.run()

    dv1 = np.loadtxt(res.outputs.out_all, skiprows=1)
    assert (np.abs(dv1[:, 0] - ground_truth[:, 0]).sum() / len(dv1)) < 0.05

    assert (np.abs(dv1[:, 1] - ground_truth[:, 1]).sum() / len(dv1)) < 0.05

    assert (np.abs(dv1[:, 2] - ground_truth[:, 2]).sum() / len(dv1)) < 0.05

    dvars = ComputeDVARS(
        in_file=example_data("ds003_sub-01_mc.nii.gz"),
        in_mask=example_data("ds003_sub-01_mc_brainmask.nii.gz"),
        save_all=True,
    )
    res = dvars.run()

    dv1 = np.loadtxt(res.outputs.out_all, skiprows=1)
    assert (np.abs(dv1[:, 0] - ground_truth[:, 0]).sum() / len(dv1)) < 0.05

    assert (np.abs(dv1[:, 1] - ground_truth[:, 1]).sum() / len(dv1)) > 0.05

    assert (np.abs(dv1[:, 2] - ground_truth[:, 2]).sum() / len(dv1)) < 0.05


def test_outliers():
    np.random.seed(0)
    in_data = np.random.randn(100)
    in_data[0] += 10

    assert is_outlier(in_data) == 1
