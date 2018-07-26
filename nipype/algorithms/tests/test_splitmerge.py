#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nipype.testing import example_data
from nipype.utils import NUMPY_MMAP


def test_split_and_merge(tmpdir):
    import numpy as np
    import nibabel as nb
    import os.path as op
    import os

    from nipype.algorithms.misc import split_rois, merge_rois

    in_mask = example_data('tpms_msk.nii.gz')
    dwfile = tmpdir.join('dwi.nii.gz').strpath
    mskdata = nb.load(in_mask, mmap=NUMPY_MMAP).get_data()
    aff = nb.load(in_mask, mmap=NUMPY_MMAP).affine

    dwshape = (mskdata.shape[0], mskdata.shape[1], mskdata.shape[2], 6)
    dwdata = np.random.normal(size=dwshape)
    tmpdir.chdir()
    nb.Nifti1Image(dwdata.astype(np.float32), aff, None).to_filename(dwfile)

    resdw, resmsk, resid = split_rois(dwfile, in_mask, roishape=(20, 20, 2))
    merged = merge_rois(resdw, resid, in_mask)
    dwmerged = nb.load(merged, mmap=NUMPY_MMAP).get_data()

    dwmasked = dwdata * mskdata[:, :, :, np.newaxis]

    assert np.allclose(dwmasked, dwmerged)
