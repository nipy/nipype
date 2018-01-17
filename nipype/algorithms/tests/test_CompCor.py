# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nibabel as nb
import numpy as np

import pytest
from ...testing import utils
from ..confounds import CompCor, TCompCor, ACompCor


class TestCompCor():
    ''' Note: Tests currently do a poor job of testing functionality '''

    filenames = {
        'functionalnii': 'compcorfunc.nii',
        'masknii': 'compcormask.nii',
        'masknii2': 'compcormask2.nii',
        'components_file': None
    }

    @pytest.fixture(autouse=True)
    def setup_class(self, tmpdir):
        # setup
        tmpdir.chdir()
        noise = np.fromfunction(self.fake_noise_fun, self.fake_data.shape)
        self.realigned_file = utils.save_toy_nii(
            self.fake_data + noise, self.filenames['functionalnii'])
        mask = np.ones(self.fake_data.shape[:3])
        mask[0, 0, 0] = 0
        mask[0, 0, 1] = 0
        mask1 = utils.save_toy_nii(mask, self.filenames['masknii'])

        other_mask = np.ones(self.fake_data.shape[:3])
        other_mask[0, 1, 0] = 0
        other_mask[1, 1, 0] = 0
        mask2 = utils.save_toy_nii(other_mask, self.filenames['masknii2'])

        self.mask_files = [mask1, mask2]

    def test_compcor(self):
        expected_components = [['-0.1989607212', '-0.5753813646'], [
            '0.5692369697', '0.5674945949'
        ], ['-0.6662573243',
            '0.4675843432'], ['0.4206466244', '-0.3361270124'],
                               ['-0.1246655485', '-0.1235705610']]

        self.run_cc(
            CompCor(
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0), expected_components)

        self.run_cc(
            ACompCor(
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0,
                components_file='acc_components_file'), expected_components,
            'aCompCor')

    def test_tcompcor(self):
        ccinterface = TCompCor(
            realigned_file=self.realigned_file, percentile_threshold=0.75)
        self.run_cc(ccinterface, [['-0.1114536190', '-0.4632908609'], [
            '0.4566907310', '0.6983205193'
        ], ['-0.7132557407', '0.1340170559'], [
            '0.5022537643', '-0.5098322262'
        ], ['-0.1342351356', '0.1407855119']], 'tCompCor')

    def test_tcompcor_no_percentile(self):
        ccinterface = TCompCor(realigned_file=self.realigned_file)
        ccinterface.run()

        mask = nb.load('mask_000.nii.gz').get_data()
        num_nonmasked_voxels = np.count_nonzero(mask)
        assert num_nonmasked_voxels == 1

    def test_compcor_no_regress_poly(self):
        self.run_cc(
            CompCor(
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0,
                pre_filter=False), [['0.4451946442', '-0.7683311482'], [
                    '-0.4285129505', '-0.0926034137'
                ], ['0.5721540256', '0.5608764842'], [
                    '-0.5367548139', '0.0059943226'
                ], ['-0.0520809054', '0.2940637551']])

    def test_tcompcor_asymmetric_dim(self):
        asymmetric_shape = (2, 3, 4, 5)
        asymmetric_data = utils.save_toy_nii(
            np.zeros(asymmetric_shape), 'asymmetric.nii')

        TCompCor(realigned_file=asymmetric_data).run()
        assert nb.load(
            'mask_000.nii.gz').get_data().shape == asymmetric_shape[:3]

    def test_compcor_bad_input_shapes(self):
        # dim 0 is < dim 0 of self.mask_files (2)
        shape_less_than = (1, 2, 2, 5)
        # dim 0 is > dim 0 of self.mask_files (2)
        shape_more_than = (3, 3, 3, 5)

        for data_shape in (shape_less_than, shape_more_than):
            data_file = utils.save_toy_nii(np.zeros(data_shape), 'temp.nii')
            interface = CompCor(
                realigned_file=data_file, mask_files=self.mask_files[0])
            with pytest.raises(ValueError, message="Dimension mismatch"):
                interface.run()

    def test_tcompcor_bad_input_dim(self):
        bad_dims = (2, 2, 2)
        data_file = utils.save_toy_nii(np.zeros(bad_dims), 'temp.nii')
        interface = TCompCor(realigned_file=data_file)
        with pytest.raises(ValueError, message='Not a 4D file'):
            interface.run()

    def test_tcompcor_merge_intersect_masks(self):
        for method in ['union', 'intersect']:
            TCompCor(
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                merge_method=method).run()
            if method == 'union':
                assert np.array_equal(
                    nb.load('mask_000.nii.gz').get_data(),
                    ([[[0, 0], [0, 0]], [[0, 0], [1, 0]]]))
            if method == 'intersect':
                assert np.array_equal(
                    nb.load('mask_000.nii.gz').get_data(),
                    ([[[0, 0], [0, 0]], [[0, 1], [0, 0]]]))

    def test_tcompcor_index_mask(self):
        TCompCor(
            realigned_file=self.realigned_file,
            mask_files=self.mask_files,
            mask_index=1).run()
        assert np.array_equal(
            nb.load('mask_000.nii.gz').get_data(),
            ([[[0, 0], [0, 0]], [[0, 1], [0, 0]]]))

    def test_tcompcor_multi_mask_no_index(self):
        interface = TCompCor(
            realigned_file=self.realigned_file, mask_files=self.mask_files)
        with pytest.raises(ValueError, message='more than one mask file'):
            interface.run()

    def run_cc(self,
               ccinterface,
               expected_components,
               expected_header='CompCor'):
        # run
        ccresult = ccinterface.run()

        # assert
        expected_file = ccinterface._list_outputs()['components_file']
        assert ccresult.outputs.components_file == expected_file
        assert os.path.exists(expected_file)
        assert os.path.getsize(expected_file) > 0
        assert ccinterface.inputs.num_components == 6

        with open(ccresult.outputs.components_file, 'r') as components_file:
            expected_n_components = min(ccinterface.inputs.num_components,
                                        self.fake_data.shape[3])

            components_data = [line.split('\t') for line in components_file]

            # the first item will be '#', we can throw it out
            header = components_data.pop(0)
            expected_header = [
                expected_header + '{:02d}'.format(i)
                for i in range(expected_n_components)
            ]
            for i, heading in enumerate(header):
                assert expected_header[i] in heading

            num_got_timepoints = len(components_data)
            assert num_got_timepoints == self.fake_data.shape[3]
            for index, timepoint in enumerate(components_data):
                assert (len(timepoint) == ccinterface.inputs.num_components
                        or len(timepoint) == self.fake_data.shape[3])
                assert timepoint[:2] == expected_components[index]
        return ccresult

    @staticmethod
    def fake_noise_fun(i, j, l, m):
        return m * i + l - j

    fake_data = np.array([[[[8, 5, 3, 8, 0], [6, 7, 4, 7, 1]],
                           [[7, 9, 1, 6, 5], [0, 7, 4, 7, 7]]],
                          [[[2, 4, 5, 7, 0], [1, 7, 0, 5, 4]],
                           [[7, 3, 9, 0, 4], [9, 4, 1, 5, 0]]]])
