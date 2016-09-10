# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .....testing import (assert_equal, assert_true, assert_almost_equal,
                          skipif, utils)
from .....interfaces import fsl, IdentityInterface
from .....pipeline.engine import Node

from ..resting import create_resting_preproc

import unittest
import mock
from mock import MagicMock
import nibabel as nb
import numpy as np
import os





def mock_node_factory(*args, **kwargs):
    ''' return mocks for all the nodes except compcor and compcor's neighbors'''
    mock = MagicMock()
    if 'interface' in kwargs.keys():
        mock = mock.create_autospec(kwargs['interface'], instance=True)
    if 'name' in kwargs.keys():
        name = kwargs['name']
        if name == 'compcor':
            return Node(*args, **kwargs)
        if name in ['threshold', 'inputspec']:
            # nodes that provide inputs for compcor
            # just give all of them all of the fields
            return Node(IdentityInterface(fields=['out_file', 'lowpass_sigma',
                                                  'num_noise_components',
                                                  'func', 'highpass_sigma']),
                        name=name)
        if name in ('remove_noise'):
            # node that takes output from compcor
            return Node(IdentityInterface(fields=['design_file', 'out_file']),
                        name=name)
        mock.name = kwargs['name']
    mock.iterables = None
    return mock

class TestResting(unittest.TestCase):

    in_filenames = {
        'in_file': 'rsfmrifunc.nii',
        'noise_mask_file': 'rsfmrimask.nii'
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
                return_value=Node(name='realigner', interface=IdentityInterface(
                    fields=['outputspec.realigned_file'])))
    @mock.patch('nipype.pipeline.engine.Node', side_effect=mock_node_factory)
    def test_create_resting_preproc(self, mock_Node, mock_realign_wf, nothing):
        # setup
        # run
        wf = create_resting_preproc()
        wf.inputs.inputspec.num_noise_components = 6
        wf.get_node('threshold').inputs.out_file = self.in_filenames['noise_mask_file']
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
