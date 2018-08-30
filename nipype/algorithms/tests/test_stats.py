# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nb
from nipype.algorithms.stats import ActivationCount
import pytest


def test_ActivationCount(tmpdir):
    tmpdir.chdir()
    in_files = ['{:d}.nii'.format(i) for i in range(3)]
    for fname in in_files:
        nb.Nifti1Image(np.random.normal(size=(5, 5, 5)),
                       np.eye(4)).to_filename(fname)

    acm = ActivationCount(in_files=in_files, threshold=1.65)
    res = acm.run()
    diff = nb.load(res.outputs.out_file)
    pos = nb.load(res.outputs.acm_pos)
    neg = nb.load(res.outputs.acm_neg)
    assert np.allclose(diff.get_data(), pos.get_data() - neg.get_data())


@pytest.mark.parametrize("threshold, above_thresh", [
    (1, 15.865),  # above one standard deviation (one side)
    (2, 2.275),   # above two standard deviations (one side)
    (3, 0.135)    # above three standard deviations (one side)
])
def test_ActivationCount_normaldistr(tmpdir, threshold, above_thresh):
    tmpdir.chdir()
    in_files = ['{:d}.nii'.format(i) for i in range(3)]
    for fname in in_files:
        nb.Nifti1Image(np.random.normal(size=(100, 100, 100)),
                       np.eye(4)).to_filename(fname)

    acm = ActivationCount(in_files=in_files, threshold=threshold)
    res = acm.run()
    pos = nb.load(res.outputs.acm_pos)
    neg = nb.load(res.outputs.acm_neg)
    assert np.isclose(pos.get_data().mean(),
                      above_thresh * 1.e-2, rtol=0.1, atol=1.e-4)
    assert np.isclose(neg.get_data().mean(),
                      above_thresh * 1.e-2, rtol=0.1, atol=1.e-4)
