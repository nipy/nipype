# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from ...testing import (assert_equal, assert_true, assert_false, skipif, utils,
                        assert_almost_equal)
from .. import stats

import unittest
import nibabel as nb
import numpy as np
import os
import tempfile
import shutil

class TestStatExtraction(unittest.TestCase):

    filenames = {
        'in_file': 'fmri.nii',
        'label_file': 'labels.nii',
        'out_file': 'stats.tsv'
    }

    def setUp(self):
        self.orig_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        utils.save_toy_nii(self.fake_fmri_data, self.filenames['in_file'])
        utils.save_toy_nii(self.fake_label_data, self.filenames['label_file'])

    @skipif(True)
    def test_stat_extraction(self):
        # setup
        wanted = [[]]
        num_timepoints_wanted = self.fake_fmri_data.shape[3]
        # run

        labels_wanted = ['csf', 'gray', 'white']
        stats.StatExtraction(in_file=self.filenames['in_file'],
                             label_file=self.filenames['label_file'],
                             class_labels=labels_wanted).run()
        # assert
        with open(self.filenames['out_file'], 'r') as output:
            got = [line.split() for line in output]
            labels_got = got.pop(0)
            assert_equal(labels_got, labels_wanted)
            assert_equal(len(got), num_timepoints_wanted)
            for time in range(len(got)):
                for segment in range(len(got[time])):
                    assert_almost_equal(got[time][segment],
                                        wanted[time][segment])

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)

    fake_fmri_data = np.array([[[[ 2, -1,  4, -2,  3],
                                 [ 4, -2, -5, -1,  0]],
                                
                                [[-2,  0,  1,  4,  4],
                                 [-5,  3, -3,  1, -5]]],
                               
                               
                               [[[ 2, -2, -1, -2, -5],
                                 [ 3,  0,  3, -5, -2]],
                                
                                [[-4, -2, -2,  1, -2],
                                 [ 3,  1,  4, -3, -2]]]])
    
    fake_label_data = np.array([[[1, 0],
                                 [3, 1]],

                                [[2, 0],
                                 [1, 3]]])
