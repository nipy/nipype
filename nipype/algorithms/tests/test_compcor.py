# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from ...testing import assert_equal, assert_true, assert_false, skipif, utils
from ..compcor import CompCor, TCompCor, ACompCor

import unittest
import mock
import nibabel as nb
import numpy as np
import os
import tempfile
import shutil

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
        mask[0,0,0] = 0
        mask[0,0,1] = 0
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

    @mock.patch('nipype.algorithms.compcor.CompCor._add_extras')
    def test_compcor_with_extra_regressors(self, mock_add_extras):
        regressors_file ='regress.txt'
        open(regressors_file, 'a').close() # make sure file exists
        CompCor(realigned_file=self.realigned_file, mask_file=self.mask_file,
                extra_regressors=regressors_file).run()
        assert_true(mock_add_extras.called)

    def test_tcompcor(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file)
        self.run_cc(ccinterface, [['-0.2846272268'], ['0.7115680670'],
                                  ['-0.6048328569'], ['0.2134704201'],
                                  ['-0.0355784033']])

    def test_tcompcor_with_percentile(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file, percentile_threshold=0.2)
        ccinterface.run()

        mask = nb.load('mask.nii').get_data()
        num_nonmasked_voxels = np.count_nonzero(mask)
        assert_equal(num_nonmasked_voxels, 2)

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
