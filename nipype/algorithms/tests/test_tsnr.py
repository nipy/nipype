# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, skipif, utils
from nipype.algorithms.misc import TSNR

from hashlib import sha1
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

    in_filenames = {
        'in_file': 'tsnrinfile.nii',
    }

    out_filenames = {# default output file names
        'detrended_file': 'detrend.nii.gz',
        'mean_file':  'mean.nii.gz',
        'stddev_file': 'stdev.nii.gz',
        'tsnr_file': 'tsnr.nii.gz'
    }

    def setUp(self):
        # setup
        utils.save_toy_nii(self.fake_data, self.in_filenames['in_file'])

    def test_tsnr(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames['in_file']).run()

        # assert
        self.assert_expected_outputs(tsnrresult, {
            'mean_file':   '1a55bcdf49901f25a2a838c90769989b9e4f2f19',
            'stddev_file': '0ba52a51fae90a9db6090c735432df5b742d663a',
            'tsnr_file': 'a794fc55766c8ad725437d3ff8b1153bd5f6e9b0'
        })

    def test_tsnr_withpoly1(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames['in_file'],
                          regress_poly=1).run()

        # assert
        self.assert_expected_outputs_poly(tsnrresult, {
            'detrended_file': 'ee4f6c0b0e8c547617fc11aa50cf659436f9ccf0',
            'mean_file': '1a55bcdf49901f25a2a838c90769989b9e4f2f19',
            'stddev_file': 'e61d94e3cfea20b0c86c81bfdf80d82c55e9203b',
            'tsnr_file': 'a49f1cbd88f2aa71183dcd7aa4b86b17df622f0c'
        })

    def test_tsnr_withpoly2(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames['in_file'],
                          regress_poly=2).run()

        # assert
        self.assert_expected_outputs_poly(tsnrresult, {
            'detrended_file': '22cb7f058d61cc090eb1a9dd7d31550bd4362a61',
            'mean_file': '4cee6776461f6bc238d11a55c0a8d1947a5732df',
            'stddev_file': '7267de4d9b63fcc553115c0198f1fa3bbb6a5a13',
            'tsnr_file': '1c6ed05f94806838f7b563df65900f37e60f8a6d'
        })

    def test_tsnr_withpoly3(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames['in_file'],
                          regress_poly=3).run()

        # assert
        self.assert_expected_outputs_poly(tsnrresult, {
            'detrended_file': '3f2c1c7da233f128a7020b6fed79d6be2ec59fca',
            'mean_file': '4cee6776461f6bc238d11a55c0a8d1947a5732df',
            'stddev_file': '82bb793b76fab503d1d6b3e2d1b20a1bdebd7a2a',
            'tsnr_file': 'e004bd6096a0077b15058aabd4b0339bf6e21f64'
        })

    def assert_expected_outputs_poly(self, tsnrresult, hash_dict):
        assert_equal(os.path.basename(tsnrresult.outputs.detrended_file),
                     self.out_filenames['detrended_file'])
        self.assert_expected_outputs(tsnrresult, hash_dict)

    def assert_expected_outputs(self, tsnrresult, hash_dict):
        self.assert_default_outputs(tsnrresult.outputs)
        self.assert_unchanged(hash_dict)

    def assert_default_outputs(self, outputs):
        assert_equal(os.path.basename(outputs.mean_file),
                     self.out_filenames['mean_file'])
        assert_equal(os.path.basename(outputs.stddev_file),
                     self.out_filenames['stddev_file'])
        assert_equal(os.path.basename(outputs.tsnr_file),
                     self.out_filenames['tsnr_file'])

    def assert_unchanged(self, expected_hashes):
        for key, hexhash in expected_hashes.iteritems():
            data = np.asanyarray(nb.load(self.out_filenames[key])._data)
            assert_equal(sha1(str(data)).hexdigest(), hexhash)

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
