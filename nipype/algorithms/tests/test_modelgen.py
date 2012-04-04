# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from copy import deepcopy
import os
from shutil import rmtree
from tempfile import mkdtemp

from nibabel import Nifti1Image
import numpy as np

from nipype.testing import (assert_equal,
                            assert_raises, assert_almost_equal)
from nipype.interfaces.base import Bunch, TraitError
from nipype.algorithms.modelgen import (SpecifyModel, SpecifySparseModel,
                                        SpecifySPMModel)


def test_modelgen1():
    tempdir = mkdtemp()
    filename1 = os.path.join(tempdir, 'test1.nii')
    filename2 = os.path.join(tempdir, 'test2.nii')
    Nifti1Image(np.random.rand(10, 10, 10, 200), np.eye(4)).to_filename(filename1)
    Nifti1Image(np.random.rand(10, 10, 10, 200), np.eye(4)).to_filename(filename2)
    s = SpecifyModel()
    s.inputs.input_units = 'scans'
    set_output_units = lambda: setattr(s.inputs, 'output_units', 'scans')
    yield assert_raises, TraitError, set_output_units
    s.inputs.functional_runs = [filename1, filename2]
    s.inputs.time_repetition = 6
    s.inputs.high_pass_filter_cutoff = 128.
    info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]], amplitudes=None,
                  pmod=None, regressors=None, regressor_names=None, tmod=None),
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]], amplitudes=None,
                  pmod=None, regressors=None, regressor_names=None, tmod=None)]
    s.inputs.subject_info = info
    res = s.run()
    yield assert_equal, len(res.outputs.session_info), 2
    yield assert_equal, len(res.outputs.session_info[0]['regress']), 0
    yield assert_equal, len(res.outputs.session_info[0]['cond']), 1
    yield assert_almost_equal, np.array(res.outputs.session_info[0]['cond'][0]['onset']), np.array([12, 300, 600, 1080])
    rmtree(tempdir)


def test_modelgen_spm_concat():
    tempdir = mkdtemp()
    filename1 = os.path.join(tempdir, 'test1.nii')
    filename2 = os.path.join(tempdir, 'test2.nii')
    Nifti1Image(np.random.rand(10, 10, 10, 30), np.eye(4)).to_filename(filename1)
    Nifti1Image(np.random.rand(10, 10, 10, 30), np.eye(4)).to_filename(filename2)
    s = SpecifySPMModel()
    s.inputs.input_units = 'secs'
    s.inputs.concatenate_runs = True
    setattr(s.inputs, 'output_units', 'secs')
    yield assert_equal, s.inputs.output_units, 'secs'
    s.inputs.functional_runs = [filename1, filename2]
    s.inputs.time_repetition = 6
    s.inputs.high_pass_filter_cutoff = 128.
    info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 170]], durations=[[1]]),
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
    s.inputs.subject_info = deepcopy(info)
    res = s.run()
    yield assert_equal, len(res.outputs.session_info), 1
    yield assert_equal, len(res.outputs.session_info[0]['regress']), 1
    yield assert_equal, np.sum(res.outputs.session_info[0]['regress'][0]['val']), 30
    yield assert_equal, len(res.outputs.session_info[0]['cond']), 1
    yield assert_almost_equal, np.array(res.outputs.session_info[0]['cond'][0]['onset']), np.array([2.0, 50.0, 100.0, 170.0, 210.0, 220.0, 280.0, 330.0])
    setattr(s.inputs, 'output_units', 'scans')
    yield assert_equal, s.inputs.output_units, 'scans'
    s.inputs.subject_info = deepcopy(info)
    res = s.run()
    yield assert_almost_equal, np.array(res.outputs.session_info[0]['cond'][0]['onset']), np.array([2.0, 50.0, 100.0, 170.0, 210.0, 220.0, 280.0, 330.0])/6
    s.inputs.concatenate_runs = False
    s.inputs.subject_info = deepcopy(info)
    s.inputs.output_units = 'secs'
    res = s.run()
    yield assert_almost_equal, np.array(res.outputs.session_info[0]['cond'][0]['onset']), np.array([2.0, 50.0, 100.0, 170.0])
    rmtree(tempdir)


def test_modelgen_sparse():
    tempdir = mkdtemp()
    filename1 = os.path.join(tempdir, 'test1.nii')
    filename2 = os.path.join(tempdir, 'test2.nii')
    Nifti1Image(np.random.rand(10, 10, 10, 50), np.eye(4)).to_filename(filename1)
    Nifti1Image(np.random.rand(10, 10, 10, 50), np.eye(4)).to_filename(filename2)
    s = SpecifySparseModel()
    s.inputs.input_units = 'secs'
    s.inputs.functional_runs = [filename1, filename2]
    s.inputs.time_repetition = 6
    info = [Bunch(conditions=['cond1'], onsets=[[0, 50, 100, 180]], durations=[[2]]),
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
    s.inputs.subject_info = info
    s.inputs.volumes_in_cluster = 1
    s.inputs.time_acquisition = 2
    s.inputs.high_pass_filter_cutoff = np.inf
    res = s.run()
    yield assert_equal, len(res.outputs.session_info), 2
    yield assert_equal, len(res.outputs.session_info[0]['regress']), 1
    yield assert_equal, len(res.outputs.session_info[0]['cond']), 0
    s.inputs.stimuli_as_impulses = False
    res = s.run()
    yield assert_equal, res.outputs.session_info[0]['regress'][0]['val'][0], 1.0
    s.inputs.model_hrf = True
    res = s.run()
    yield assert_almost_equal, res.outputs.session_info[0]['regress'][0]['val'][0], 0.016675298129743384
    yield assert_equal, len(res.outputs.session_info[0]['regress']), 1
    s.inputs.use_temporal_deriv = True
    res = s.run()
    yield assert_equal, len(res.outputs.session_info[0]['regress']), 2
    yield assert_almost_equal, res.outputs.session_info[0]['regress'][0]['val'][0], 0.016675298129743384
    yield assert_almost_equal, res.outputs.session_info[1]['regress'][1]['val'][5], 0.007671459162258378
    rmtree(tempdir)
