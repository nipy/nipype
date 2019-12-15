#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from nipype.testing import example_data
from nipype.algorithms.metrics import ErrorMap
import nibabel as nb
import numpy as np
import os


def test_errormap(tmpdir):

    # Single-Spectual
    # Make two fake 2*2*2 voxel volumes
    # John von Neumann's birthday
    volume1 = np.array([[[2.0, 8.0], [1.0, 2.0]], [[1.0, 9.0], [0.0, 3.0]]])
    # Alan Turing's birthday
    volume2 = np.array([[[0.0, 7.0], [2.0, 3.0]], [[1.0, 9.0], [1.0, 2.0]]])
    mask = np.array([[[1, 0], [0, 1]], [[1, 0], [0, 1]]])

    img1 = nb.Nifti1Image(volume1, np.eye(4))
    img2 = nb.Nifti1Image(volume2, np.eye(4))
    maskimg = nb.Nifti1Image(mask, np.eye(4))

    nb.save(img1, tmpdir.join("von.nii.gz").strpath)
    nb.save(img2, tmpdir.join("alan.nii.gz").strpath)
    nb.save(maskimg, tmpdir.join("mask.nii.gz").strpath)

    # Default metric
    errmap = ErrorMap()
    errmap.inputs.in_tst = tmpdir.join("von.nii.gz").strpath
    errmap.inputs.in_ref = tmpdir.join("alan.nii.gz").strpath
    errmap.out_map = tmpdir.join("out_map.nii.gz").strpath
    result = errmap.run()
    assert result.outputs.distance == 1.125

    # Square metric
    errmap.inputs.metric = "sqeuclidean"
    result = errmap.run()
    assert result.outputs.distance == 1.125

    # Linear metric
    errmap.inputs.metric = "euclidean"
    result = errmap.run()
    assert result.outputs.distance == 0.875

    # Masked
    errmap.inputs.mask = tmpdir.join("mask.nii.gz").strpath
    result = errmap.run()
    assert result.outputs.distance == 1.0

    # Multi-Spectual
    # Raymond Vahan Damadian's birthday
    volume3 = np.array([[[1.0, 6.0], [0.0, 3.0]], [[1.0, 9.0], [3.0, 6.0]]])

    msvolume1 = np.zeros(shape=(2, 2, 2, 2))
    msvolume1[:, :, :, 0] = volume1
    msvolume1[:, :, :, 1] = volume3
    msimg1 = nb.Nifti1Image(msvolume1, np.eye(4))

    msvolume2 = np.zeros(shape=(2, 2, 2, 2))
    msvolume2[:, :, :, 0] = volume3
    msvolume2[:, :, :, 1] = volume1
    msimg2 = nb.Nifti1Image(msvolume2, np.eye(4))

    nb.save(msimg1, tmpdir.join("von-ray.nii.gz").strpath)
    nb.save(msimg2, tmpdir.join("alan-ray.nii.gz").strpath)

    errmap.inputs.in_tst = tmpdir.join("von-ray.nii.gz").strpath
    errmap.inputs.in_ref = tmpdir.join("alan-ray.nii.gz").strpath
    errmap.inputs.metric = "sqeuclidean"
    result = errmap.run()
    assert result.outputs.distance == 5.5

    errmap.inputs.metric = "euclidean"
    result = errmap.run()
    assert result.outputs.distance == np.float32(1.25 * (2 ** 0.5))
