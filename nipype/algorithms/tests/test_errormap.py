#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from nipype.testing import example_data
from nipype.algorithms.metrics import ErrorMap
import nibabel as nb
import numpy as np
import os


def test_errormap(tmpdir):

    tempdir = str(tmpdir)
    # Single-Spectual
    # Make two fake 2*2*2 voxel volumes
    volume1 = np.array([[[2.0, 8.0], [1.0, 2.0]], [[1.0, 9.0], [0.0, 3.0]]])  # John von Neumann's birthday
    volume2 = np.array([[[0.0, 7.0], [2.0, 3.0]], [[1.0, 9.0], [1.0, 2.0]]])  # Alan Turing's birthday
    mask = np.array([[[1, 0], [0, 1]], [[1, 0], [0, 1]]])

    img1 = nb.Nifti1Image(volume1, np.eye(4))
    img2 = nb.Nifti1Image(volume2, np.eye(4))
    maskimg = nb.Nifti1Image(mask, np.eye(4))

    nb.save(img1, os.path.join(tempdir, 'von.nii.gz'))
    nb.save(img2, os.path.join(tempdir, 'alan.nii.gz'))
    nb.save(maskimg, os.path.join(tempdir, 'mask.nii.gz'))

    # Default metric
    errmap = ErrorMap()
    errmap.inputs.in_tst = os.path.join(tempdir, 'von.nii.gz')
    errmap.inputs.in_ref = os.path.join(tempdir, 'alan.nii.gz')
    errmap.out_map = os.path.join(tempdir, 'out_map.nii.gz')
    result = errmap.run()
    assert result.outputs.distance == 1.125

    # Square metric
    errmap.inputs.metric = 'sqeuclidean'
    result = errmap.run()
    assert result.outputs.distance == 1.125

    # Linear metric
    errmap.inputs.metric = 'euclidean'
    result = errmap.run()
    assert result.outputs.distance == 0.875

    # Masked
    errmap.inputs.mask = os.path.join(tempdir, 'mask.nii.gz')
    result = errmap.run()
    assert result.outputs.distance == 1.0

    # Multi-Spectual
    volume3 = np.array([[[1.0, 6.0], [0.0, 3.0]], [[1.0, 9.0], [3.0, 6.0]]])  # Raymond Vahan Damadian's birthday

    msvolume1 = np.zeros(shape=(2, 2, 2, 2))
    msvolume1[:, :, :, 0] = volume1
    msvolume1[:, :, :, 1] = volume3
    msimg1 = nb.Nifti1Image(msvolume1, np.eye(4))

    msvolume2 = np.zeros(shape=(2, 2, 2, 2))
    msvolume2[:, :, :, 0] = volume3
    msvolume2[:, :, :, 1] = volume1
    msimg2 = nb.Nifti1Image(msvolume2, np.eye(4))

    nb.save(msimg1, os.path.join(tempdir, 'von-ray.nii.gz'))
    nb.save(msimg2, os.path.join(tempdir, 'alan-ray.nii.gz'))

    errmap.inputs.in_tst = os.path.join(tempdir, 'von-ray.nii.gz')
    errmap.inputs.in_ref = os.path.join(tempdir, 'alan-ray.nii.gz')
    errmap.inputs.metric = 'sqeuclidean'
    result = errmap.run()
    assert result.outputs.distance == 5.5

    errmap.inputs.metric = 'euclidean'
    result = errmap.run()
    assert result.outputs.distance == np.float32(1.25 * (2**0.5))
