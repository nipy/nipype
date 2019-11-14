#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

from nipype.testing import example_data

import numpy as np


def test_overlap(tmpdir):
    from nipype.algorithms.metrics import Overlap

    def check_close(val1, val2):
        import numpy.testing as npt

        return npt.assert_almost_equal(val1, val2, decimal=3)

    in1 = example_data("segmentation0.nii.gz")
    in2 = example_data("segmentation1.nii.gz")

    tmpdir.chdir()
    overlap = Overlap()
    overlap.inputs.volume1 = in1
    overlap.inputs.volume2 = in1
    res = overlap.run()
    check_close(res.outputs.jaccard, 1.0)

    overlap = Overlap()
    overlap.inputs.volume1 = in1
    overlap.inputs.volume2 = in2
    res = overlap.run()
    check_close(res.outputs.jaccard, 0.99705)

    overlap = Overlap()
    overlap.inputs.volume1 = in1
    overlap.inputs.volume2 = in2
    overlap.inputs.vol_units = "mm"
    res = overlap.run()
    check_close(res.outputs.jaccard, 0.99705)
    check_close(res.outputs.roi_voldiff, np.array([0.0063086, -0.0025506, 0.0]))
