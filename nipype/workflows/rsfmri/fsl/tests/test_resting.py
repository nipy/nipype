# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.testing import (assert_equal, assert_true, assert_almost_equal,
                            skipif, utils)
from nipype.workflows.rsfmri.fsl import resting

import unittest
import mock
import nibabel as nb
import numpy as np
import os

class TestResting(unittest.TestCase):

    in_filenames = {
        'in_file': 'rsfmrifunc.nii',
    }

    out_filenames = {
        'noise_mask_file': '',
        'filtered_file': ''
    }

    def setUp(self):
        # setup
        utils.save_toy_nii(self.fake_data, self.in_filenames['in_file'])

    @skipif(True)
    def test_create_resting_preproc(self):
        # setup
        print(np.random.randint(0, 10, (2, 2, 2, 5)))
        # run
        wf = resting.create_resting_preproc()
        wf.run()

        # assert

    def tearDown(self):
        utils.remove_nii(self.in_filenames.values())
        utils.remove_nii(self.out_filenames.values())

    fake_data = np.array([[[[2, 4, 3, 9, 1],
                            [3, 6, 4, 7, 4]],

                           [[8, 3, 4, 6, 2],
                            [4, 0, 4, 4, 2]]],

                          [[[9, 7, 5, 5, 7],
                            [7, 8, 4, 8, 4]],

                           [[0, 4, 7, 1, 7],
                            [6, 8, 8, 8, 7]]]])
