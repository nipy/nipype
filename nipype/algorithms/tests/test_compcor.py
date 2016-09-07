# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
from nipype.algorithms.compcor import CompCor, TCompCor, ACompCor

import unittest
import mock
import nibabel as nb
import numpy as np
import os

class TestCompCor(unittest.TestCase):
    ''' Note: Tests currently do a poor job of testing functionality '''

    functionalnii = 'func.nii'
    masknii = 'amask.nii'
    components_file = None

    def setUp(self):
        # setup
        noise = np.fromfunction(self.fake_noise_fun, self.fake_data.shape)
        self.realigned_file = self.make_toy(self.fake_data + noise,
                                            self.functionalnii)

    def test_compcor(self):
        mask = np.ones(self.fake_data.shape[:3])
        mask[0,0,0] = 0
        mask[0,0,1] = 0
        mask_file = self.make_toy(mask, self.masknii)

        ccresult = self.run_cc(CompCor(realigned_file=self.realigned_file,
                               mask_file=mask_file))

        accresult = self.run_cc(ACompCor(realigned_file=self.realigned_file,
                             mask_file=mask_file,
                             components_file='acc_components_file'))

        assert_equal(os.path.getsize(ccresult.outputs.components_file),
                     os.path.getsize(accresult.outputs.components_file))

    def test_tcompcor(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file)
        self.run_cc(ccinterface)

    def run_cc(self, ccinterface):
        # run
        ccresult = ccinterface.run()

        # assert
        expected_file = ccinterface._list_outputs()['components_file']
        assert_equal(ccresult.outputs.components_file, expected_file)
        assert_true(os.path.exists(expected_file))
        assert_true(os.path.getsize(expected_file) > 0)
        assert_equal(ccinterface.inputs.num_components, 6)

        return ccresult

    def tearDown(self):
        # remove temporary nifti files
        try:
            os.remove(self.functionalnii)
            os.remove(self.components_file)
            os.remove(self.masknii)
        except (OSError, TypeError) as e:
            print(e)

    def make_toy(self, ndarray, filename):
        toy = nb.Nifti1Image(ndarray, np.eye(4))
        nb.nifti1.save(toy, filename)
        return filename

    def fake_noise_fun(self, i, j, l, m):
        return m*i + l - j

    fake_data = np.array([[[[8, 5, 3, 8, 0],
                            [6, 7, 4, 7, 1]],

                           [[7, 9, 1, 6, 5],
                            [0, 7, 4, 7, 7]]],

                          [[[2, 4, 5, 7, 0],
                            [1, 7, 0, 5, 4]],

                           [[7, 3, 9, 0, 4],
                            [9, 4, 1, 5, 0]]]])
