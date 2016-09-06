# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
from nipype.algorithms.compcor import (CompCor, CompCorWorkflow, ACompCor,
                                       TCompCor)

import mock
import nibabel as nb
import numpy as np
import os

functionalnii = 'func.nii'
masknii = 'mask.nii'

def test_compcor():
    # setup
    noise = np.fromfunction(fake_noise_fun, fake_data.shape)
    realigned_file = make_toy(fake_data + noise, functionalnii)

    mask = np.ones(fake_data.shape[:3])
    mask[0,0,0] = 0
    mask[0,0,1] = 0
    mask_file = make_toy(mask, masknii)

    # run
    ccinterface = CompCor(realigned_file=realigned_file, mask_file=mask_file)
    ccresult = ccinterface.run()

    # asserts
    components = ccinterface._list_outputs()['components_file']
    assert_true(os.path.exists(components))
    assert_true(os.path.getsize(components) > 0)
    assert_equal(ccinterface.inputs.num_components, 6)

    #  apply components_file to realigned_file, is it better? the same as before adding noise?

    # remove temporary nifti files
    os.remove(functionalnii)
    os.remove(masknii)
    os.remove(components)

def make_toy(ndarray, filename):
    toy = nb.Nifti1Image(ndarray, np.eye(4))
    nb.nifti1.save(toy, filename)
    return filename

fake_data = np.array([[[[8, 5, 3, 8, 0],
                        [6, 7, 4, 7, 1]],

                       [[7, 9, 1, 6, 5],
                        [0, 7, 4, 7, 7]]],


                      [[[2, 4, 5, 7, 0],
                        [1, 7, 0, 5, 4]],

                       [[7, 3, 9, 0, 4],
                        [9, 4, 1, 5, 0]]]])

def fake_noise_fun(i, j, l, m):
    return m*i + l - j
