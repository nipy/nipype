# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

import pytest
from nipype.testing import example_data

import numpy as np
import nibabel as nb
import nipype.testing as nit

from nipype.algorithms.misc import normalize_tpms


def test_normalize_tpms(tmpdir):

    in_mask = example_data("tpms_msk.nii.gz")
    mskdata = np.asanyarray(nb.load(in_mask).dataobj)
    mskdata[mskdata > 0.0] = 1.0

    mapdata = []
    in_files = []
    out_files = []

    for i in range(3):
        mapname = example_data("tpm_%02d.nii.gz" % i)
        filename = tmpdir.join("modtpm_%02d.nii.gz" % i).strpath
        out_files.append(tmpdir.join("normtpm_%02d.nii.gz" % i).strpath)

        im = nb.load(mapname)
        data = im.get_fdata()
        mapdata.append(data)

        nb.Nifti1Image(2.0 * (data * mskdata), im.affine, im.header).to_filename(
            filename
        )
        in_files.append(filename)

    normalize_tpms(in_files, in_mask, out_files=out_files)

    sumdata = np.zeros_like(mskdata)

    for i, tstfname in enumerate(out_files):
        normdata = nb.load(tstfname).get_fdata()
        sumdata += normdata
        assert np.all(normdata[mskdata == 0] == 0)
        assert np.allclose(normdata, mapdata[i])

    assert np.allclose(sumdata[sumdata > 0.0], 1.0)
