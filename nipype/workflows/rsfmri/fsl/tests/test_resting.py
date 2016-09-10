# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .....testing import (assert_equal, assert_true, assert_almost_equal,
                          skipif, utils)
from .....interfaces import fsl

from ..resting import create_resting_preproc

import unittest
import mock
from mock import MagicMock
import nibabel as nb
import numpy as np
import os

def mock_node_factory(*args, **kwargs):
    mock = MagicMock()
    mock.name = kwargs['name'] if 'name' in kwargs.keys() else ''
    if 'interface' in kwargs.keys():
        mock = mock.create_autospec(kwargs['interface'], instance=True)
    mock.iterables = None
    return mock

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
    @mock.patch('nipype.pipeline.engine.Workflow._write_report_info')
    @mock.patch('nipype.workflows.rsfmri.fsl.resting.create_realign_flow',
                side_effect=mock_node_factory)
    @mock.patch('nipype.pipeline.engine.Node', side_effect=mock_node_factory)
    def test_create_resting_preproc(self, mock_Node, mock_realign_wf, nothing):
        # setup
        print(np.random.randint(0, 10, (2, 2, 2, 5)))
        # run
        wf = create_resting_preproc()
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
