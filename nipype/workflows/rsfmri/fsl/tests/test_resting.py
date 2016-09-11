# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from .....testing import (assert_equal, assert_true, assert_almost_equal,
                          skipif, utils)
from .....interfaces import fsl, IdentityInterface
from .....pipeline.engine import Node, Workflow

from ..resting import create_resting_preproc

import unittest
import mock
from mock import MagicMock
import nibabel as nb
import numpy as np
import os
import tempfile
import shutil

all_fields = ['func', 'in_file', 'slice_time_corrected_file', 'stddev_file',
              'out_stat', 'thresh', 'num_noise_components', 'detrended_file',
              'design_file', 'highpass_sigma', 'lowpass_sigma', 'out_file',
              'noise_mask_file', 'filtered_file']

def stub_node_factory(*args, **kwargs):
    if 'name' not in kwargs.keys():
        raise Exception()
    name = kwargs['name']
    if name == 'compcor':
        return Node(*args, **kwargs)
    else: # replace with an IdentityInterface
        return Node(IdentityInterface(fields=all_fields),
                    name=name)

def stub_wf(*args, **kwargs):
    wf = Workflow(name='realigner')
    inputnode = Node(IdentityInterface(fields=['func']), name='inputspec')
    outputnode = Node(interface=IdentityInterface(fields=['realigned_file']),
                      name='outputspec')
    wf.connect(inputnode, 'func', outputnode, 'realigned_file')
    return wf

class TestResting(unittest.TestCase):

    in_filenames = {}

    out_filenames = {
        'noise_mask_file': '',
        'filtered_file': ''
    }

    def setUp(self):
        # setup
        self.orig_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        self.in_filenames['realigned_file'] = utils.save_toy_nii(self.fake_data, os.path.abspath('rsfmrifunc.nii'))
        mask = np.zeros(self.fake_data.shape[:3])
        for i in range(mask.shape[0]):
            for j in range(mask.shape[1]):
                if i==j:
                    mask[i,j] = 1
        self.in_filenames['noise_mask_file'] = utils.save_toy_nii(mask, os.path.abspath('rsfmrimask.nii'))

    @mock.patch('nipype.workflows.rsfmri.fsl.resting.create_realign_flow',
                side_effect=stub_wf)
    @mock.patch('nipype.pipeline.engine.Node', side_effect=stub_node_factory)
    def test_create_resting_preproc(self, mock_Node, mock_realign_wf):
        wf = create_resting_preproc()

        wf.inputs.inputspec.num_noise_components = 6
        wf.get_node('slicetimer').inputs.slice_time_corrected_file = self.in_filenames['realigned_file']
        wf.get_node('threshold').inputs.out_file = self.in_filenames['noise_mask_file']

        wf.run()

        # assert

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.temp_dir)

    fake_data = np.array([[[[2, 4, 3, 9, 1],
                            [3, 6, 4, 7, 4]],

                           [[8, 3, 4, 6, 2],
                            [4, 0, 4, 4, 2]]],

                          [[[9, 7, 5, 5, 7],
                            [7, 8, 4, 8, 4]],

                           [[0, 4, 7, 1, 7],
                            [6, 8, 8, 8, 7]]]])
