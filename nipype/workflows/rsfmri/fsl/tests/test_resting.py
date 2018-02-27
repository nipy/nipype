# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest
import os
import mock
import numpy as np

from .....testing import utils
from .....interfaces import IdentityInterface
from .....pipeline.engine import Node, Workflow

from ..resting import create_resting_preproc

ALL_FIELDS = [
    'func', 'in_file', 'slice_time_corrected_file', 'stddev_file', 'out_stat',
    'thresh', 'num_noise_components', 'detrended_file', 'design_file',
    'highpass_sigma', 'lowpass_sigma', 'out_file', 'noise_mask_file',
    'filtered_file'
]


def stub_node_factory(*args, **kwargs):
    if 'name' not in kwargs.keys():
        raise Exception()
    name = kwargs['name']
    if name == 'compcor':
        return Node(*args, **kwargs)
    else:  # replace with an IdentityInterface
        return Node(IdentityInterface(fields=ALL_FIELDS), name=name)


def stub_wf(*args, **kwargs):
    wflow = Workflow(name='realigner')
    inputnode = Node(IdentityInterface(fields=['func']), name='inputspec')
    outputnode = Node(
        interface=IdentityInterface(fields=['realigned_file']),
        name='outputspec')
    wflow.connect(inputnode, 'func', outputnode, 'realigned_file')
    return wflow


class TestResting():

    in_filenames = {
        'realigned_file': 'rsfmrifunc.nii',
        'mask_file': 'rsfmrimask.nii'
    }

    out_filenames = {
        'components_file': 'restpreproc/compcor/noise_components.txt'
    }

    num_noise_components = 6

    @pytest.fixture(autouse=True)
    def setup_class(self, tmpdir):
        # setup temp folder
        tmpdir.chdir()
        self.in_filenames = {
            key: os.path.abspath(value)
            for key, value in self.in_filenames.items()
        }

        # create&save input files
        utils.save_toy_nii(self.fake_data, self.in_filenames['realigned_file'])
        mask = np.zeros(self.fake_data.shape[:3])
        for i in range(mask.shape[0]):
            for j in range(mask.shape[1]):
                if i == j:
                    mask[i, j] = 1
        utils.save_toy_nii(mask, self.in_filenames['mask_file'])

    @mock.patch(
        'nipype.workflows.rsfmri.fsl.resting.create_realign_flow',
        side_effect=stub_wf)
    @mock.patch('nipype.pipeline.engine.Node', side_effect=stub_node_factory)
    def test_create_resting_preproc(self, mock_node, mock_realign_wf):
        wflow = create_resting_preproc(base_dir=os.getcwd())

        wflow.inputs.inputspec.num_noise_components = self.num_noise_components
        mask_in = wflow.get_node('threshold').inputs
        mask_in.out_file = self.in_filenames['mask_file']
        func_in = wflow.get_node('slicetimer').inputs
        func_in.slice_time_corrected_file = self.in_filenames['realigned_file']

        wflow.run()

        # assert
        expected_file = os.path.abspath(self.out_filenames['components_file'])
        with open(expected_file, 'r') as components_file:
            components_data = [line.split() for line in components_file]
            num_got_components = len(components_data)
            assert (num_got_components == self.num_noise_components
                    or num_got_components == self.fake_data.shape[3])
            first_two = [row[:2] for row in components_data[1:]]
            assert first_two == [['-0.5172356654', '-0.6973053243'], [
                '0.2574722644', '0.1645270737'
            ], ['-0.0806469590',
                '0.5156853779'], ['0.7187176051', '-0.3235820287'],
                                 ['-0.3783072450', '0.3406749013']]

    fake_data = np.array([[[[2, 4, 3, 9, 1], [3, 6, 4, 7, 4]],
                           [[8, 3, 4, 6, 2], [4, 0, 4, 4, 2]]],
                          [[[9, 7, 5, 5, 7], [7, 8, 4, 8, 4]],
                           [[0, 4, 7, 1, 7], [6, 8, 8, 8, 7]]]])
