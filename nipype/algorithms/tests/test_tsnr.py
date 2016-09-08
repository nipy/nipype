# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, skipif, utils
from nipype.algorithms.misc import TSNR

import unittest
import mock
import nibabel as nb
import numpy as np
import os

class TestTSNR(unittest.TestCase):
    ''' Note: Tests currently do a poor job of testing functionality '''
    '''
    in_file = InputMultiPath(File(exists=True), mandatory=True,
    regress_poly = traits.Range(low=1, desc='Remove polynomials')
    '''
    in_file_name = 'tsnrinfile.nii'

    def setUp(self):
        # setup
        utils.save_toy_nii(self.fake_data, self.in_file_name)

    def test_tsnr(self):
        # setup
        # run
        tsnrresult = TSNR(in_file=self.in_file_name, regress_poly=1)
        # assert
        # cleanup

    def tearDown(self):
        # remove temporary nifti files
        try:
            os.remove(self.in_file_name)
        except (OSError, TypeError) as e:
            print(e)

    fake_data = np.array([[[[2, 4, 3, 9, 1],
                            [3, 6, 4, 7, 4]],

                           [[8, 3, 4, 6, 2],
                            [4, 0, 4, 4, 2]]],

                          [[[9, 7, 5, 5, 7],
                            [7, 8, 4, 8, 4]],

                           [[0, 4, 7, 1, 7],
                            [6, 8, 8, 8, 7]]]])
