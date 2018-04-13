# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nb
from nipype.algorithms.stats import ActivationCount


def test_ActivationCount(tmpdir):
    tmpdir.chdir()
    in_files = ['{:d}.nii'.format(i) for i in range(3)]
    for fname in in_files:
        nb.Nifti1Image(np.random.normal(size=(5, 5, 5)),
                       np.eye(4)).to_filename(fname)

    acm = ActivationCount(in_files=in_files)
    res = acm.run()
    diff = nb.load(res.outputs.out_file)
    pos = nb.load(res.outputs.acm_pos)
    neg = nb.load(res.outputs.acm_neg)
    assert np.allclose(diff.get_data(), pos.get_data() - neg.get_data())
