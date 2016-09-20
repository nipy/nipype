# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil
import unittest

import nibabel as nb
import numpy as np

from ...testing import assert_equal, assert_true, utils
from ..confounds import CompCor, TCompCor, ACompCor

class TestCompCor(unittest.TestCase):
    ''' Note: Tests currently do a poor job of testing functionality '''

    filenames = {'functionalnii': 'compcorfunc.nii',
                 'masknii': 'compcormask.nii',
                 'components_file': None}

    def setUp(self):
        # setup
        self.orig_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        noise = np.fromfunction(self.fake_noise_fun, self.fake_data.shape)
        self.realigned_file = utils.save_toy_nii(self.fake_data + noise,
                                                 self.filenames['functionalnii'])
        mask = np.ones(self.fake_data.shape[:3])
        mask[0, 0, 0] = 0
        mask[0, 0, 1] = 0
        self.mask_file = utils.save_toy_nii(mask, self.filenames['masknii'])

    def test_compcor(self):
        expected_components = [['-0.1989607212', '-0.5753813646'],
                               ['0.5692369697', '0.5674945949'],
                               ['-0.6662573243', '0.4675843432'],
                               ['0.4206466244', '-0.3361270124'],
                               ['-0.1246655485', '-0.1235705610']]

        ccresult = self.run_cc(CompCor(realigned_file=self.realigned_file,
                                       mask_file=self.mask_file),
                               expected_components)

        accresult = self.run_cc(ACompCor(realigned_file=self.realigned_file,
                                         mask_file=self.mask_file,
                                         components_file='acc_components_file'),
                                expected_components)

        assert_equal(os.path.getsize(ccresult.outputs.components_file),
                     os.path.getsize(accresult.outputs.components_file))

    def test_tcompcor(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file, percentile_threshold=0.75)
        self.run_cc(ccinterface, [['-0.1114536190', '-0.4632908609'],
                                  ['0.4566907310', '0.6983205193'],
                                  ['-0.7132557407', '0.1340170559'],
                                  ['0.5022537643', '-0.5098322262'],
                                  ['-0.1342351356', '0.1407855119']])

    def test_tcompcor_no_percentile(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file)
        ccinterface.run()

        mask = nb.load('mask.nii').get_data()
        num_nonmasked_voxels = np.count_nonzero(mask)
        assert_equal(num_nonmasked_voxels, 1)

    def test_compcor_no_regress_poly(self):
        self.run_cc(CompCor(realigned_file=self.realigned_file, mask_file=self.mask_file,
                            use_regress_poly=False), [['0.4451946442', '-0.7683311482'],
                                                      ['-0.4285129505', '-0.0926034137'],
                                                      ['0.5721540256', '0.5608764842'],
                                                      ['-0.5367548139', '0.0059943226'],
                                                      ['-0.0520809054', '0.2940637551']])

    def run_cc(self, ccinterface, expected_components):
        # run
        ccresult = ccinterface.run()

        # assert
        expected_file = ccinterface._list_outputs()['components_file']
        assert_equal(ccresult.outputs.components_file, expected_file)
        assert_true(os.path.exists(expected_file))
        assert_true(os.path.getsize(expected_file) > 0)
        assert_equal(ccinterface.inputs.num_components, 6)

        with open(ccresult.outputs.components_file, 'r') as components_file:
            components_data = [line.split() for line in components_file]
            num_got_components = len(components_data)
            assert_true(num_got_components == ccinterface.inputs.num_components
                        or num_got_components == self.fake_data.shape[3])
            first_two = [row[:2] for row in components_data]
            assert_equal(first_two, expected_components)
        return ccresult

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)

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
