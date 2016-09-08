#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nipype.testing import (assert_equal, example_data)
from nipype.algorithms.confounds import FramewiseDisplacement
import numpy as np
from tempfile import mkdtemp
from shutil import rmtree

def test_fd():
    tempdir = mkdtemp()
    ground_truth = np.loadtxt(example_data('fsl_motion_outliers_fd.txt'))
    fd = FramewiseDisplacement(in_plots=example_data('fsl_mcflirt_movpar.txt'),
                               out_file=tempdir + '/fd.txt')
    res = fd.run()
    yield assert_equal, np.allclose(ground_truth, np.loadtxt(res.outputs.out_file)), True
    yield assert_equal, np.abs(ground_truth.mean() - res.outputs.fd_average) < 1e-4, True
    rmtree(tempdir)
