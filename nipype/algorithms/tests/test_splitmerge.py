#!/usr/bin/env python
# -*- coding: utf-8 -*-

from shutil import rmtree
from tempfile import mkdtemp
from nipype.testing import (assert_equal, example_data)


def test_split_and_merge():
    import numpy as np
    import nibabel as nb
    import os.path as op
    import os
    cwd = os.getcwd()

    from nipype.algorithms.misc import split_rois, merge_rois
    tmpdir = mkdtemp()

    in_mask = example_data('tpms_msk.nii.gz')
    dwfile = op.join(tmpdir, 'dwi.nii.gz')
    mskdata = nb.load(in_mask).get_data()
    aff = nb.load(in_mask).affine

    dwshape = (mskdata.shape[0], mskdata.shape[1], mskdata.shape[2], 6)
    dwdata = np.random.normal(size=dwshape)
    os.chdir(tmpdir)
    nb.Nifti1Image(dwdata.astype(np.float32),
                   aff, None).to_filename(dwfile)

    resdw, resmsk, resid = split_rois(dwfile, in_mask, roishape=(20, 20, 2))
    merged = merge_rois(resdw, resid, in_mask)
    dwmerged = nb.load(merged).get_data()

    dwmasked = dwdata * mskdata[:, :, :, np.newaxis]
    os.chdir(cwd)
    rmtree(tmpdir)

    yield assert_equal, np.allclose(dwmasked, dwmerged), True
