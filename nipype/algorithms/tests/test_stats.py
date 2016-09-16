# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import unittest
import os
import tempfile
import shutil

import numpy as np

from ...testing import (assert_equal, utils, assert_almost_equal, raises,
                        skipif)
from .. import stats

no_nilearn = True
try:
    import nilearn
    no_nilearn = False
except ImportError:
    pass

class TestSignalExtraction(unittest.TestCase):

    filenames = {
        'in_file': 'fmri.nii',
        'label_file': 'labels.nii',
        'out_file': 'signals.tsv'
    }

    def setUp(self):
        self.orig_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        utils.save_toy_nii(self.fake_fmri_data, self.filenames['in_file'])
        utils.save_toy_nii(self.fake_label_data, self.filenames['label_file'])

    @skipif(no_nilearn)
    def test_signal_extraction(self):
        # setup
        wanted = [[-2.33333, 2, .5],
                  [0, -2, .5],
                  [-.3333333, -1, 2.5],
                  [0, -2, .5],
                  [-1.3333333, -5, 1]]
        num_timepoints_wanted = self.fake_fmri_data.shape[3]
        # run

        labels_wanted = ['csf', 'gray', 'white']
        stats.SignalExtraction(in_file=self.filenames['in_file'],
                               label_file=self.filenames['label_file'],
                               class_labels=labels_wanted).run()
        # assert
        with open(self.filenames['out_file'], 'r') as output:
            got = [line.split() for line in output]
            labels_got = got.pop(0) # remove header
            assert_equal(labels_got, labels_wanted)
            assert_equal(len(got), num_timepoints_wanted)
            # convert from string to float
            got = [[float(num) for num in row] for row in got]
            for i, time in enumerate(got):
                assert_equal(len(labels_wanted), len(time))
                for j, segment in enumerate(time):
                    assert_almost_equal(segment, wanted[i][j], decimal=1)

    @skipif(no_nilearn)
    @raises(ValueError)
    def test_signal_extraction_bad_class_labels(self):
        # run
        stats.SignalExtraction(in_file=self.filenames['in_file'],
                               label_file=self.filenames['label_file'],
                               class_labels=['bad']).run()

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)

    fake_fmri_data = np.array([[[[2, -1, 4, -2, 3],
                                 [4, -2, -5, -1, 0]],

                                [[-2, 0, 1, 4, 4],
                                 [-5, 3, -3, 1, -5]]],


                               [[[2, -2, -1, -2, -5],
                                 [3, 0, 3, -5, -2]],

                                [[-4, -2, -2, 1, -2],
                                 [3, 1, 4, -3, -2]]]])

    fake_label_data = np.array([[[1, 0],
                                 [3, 1]],

                                [[2, 0],
                                 [1, 3]]])
