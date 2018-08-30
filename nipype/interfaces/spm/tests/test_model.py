# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nipype.interfaces.spm.model as spm
import nipype.interfaces.matlab as mlab

mlab.MatlabCommand.set_default_matlab_cmd(os.getenv('MATLABCMD', 'matlab'))


def test_level1design():
    assert spm.Level1Design._jobtype == 'stats'
    assert spm.Level1Design._jobname == 'fmri_spec'


def test_estimatemodel():
    assert spm.EstimateModel._jobtype == 'stats'
    assert spm.EstimateModel._jobname == 'fmri_est'


def test_estimatecontrast():
    assert spm.EstimateContrast._jobtype == 'stats'
    assert spm.EstimateContrast._jobname == 'con'


def test_threshold():
    assert spm.Threshold._jobtype == 'basetype'
    assert spm.Threshold._jobname == 'basename'


def test_factorialdesign():
    assert spm.FactorialDesign._jobtype == 'stats'
    assert spm.FactorialDesign._jobname == 'factorial_design'


def test_onesamplettestdesign():
    assert spm.OneSampleTTestDesign._jobtype == 'stats'
    assert spm.OneSampleTTestDesign._jobname == 'factorial_design'


def test_twosamplettestdesign():
    assert spm.TwoSampleTTestDesign._jobtype == 'stats'
    assert spm.TwoSampleTTestDesign._jobname == 'factorial_design'
