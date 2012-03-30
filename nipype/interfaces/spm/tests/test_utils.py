# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from nipype.testing import (assert_equal, assert_false,assert_raises, 
			    assert_true, skipif, example_data)
from nipype.interfaces.spm import no_spm
import nipype.interfaces.spm.utils as spmu
from nipype.interfaces.base import isdefined
from nipype.utils.filemanip import split_filename, fname_presuffix


def test_spm_util_coreg():
    moving = example_data(infile='functional.nii')
    target = example_data(infile='T1.nii')
    mat = example_data(infile='trans.mat')
    coreg = spmu.CalcCoregAffine(matlab_cmd = 'mymatlab')
    coreg.inputs.target = target
    yield assert_equal, coreg.inputs.matlab_cmd, 'mymatlab'
    coreg.inputs.moving = moving 
    yield assert_equal, isdefined(coreg.inputs.mat),False 
    pth, mov, _ = split_filename(moving)
    _, tgt, _ = split_filename(target)
    mat = os.path.join(pth, '%s_to_%s.mat'%(mov,tgt)) 
    invmat = fname_presuffix(mat, prefix='inverse_')
    scrpt = coreg._make_matlab_command(None)
    yield assert_equal, coreg.inputs.mat, mat
    yield assert_equal, coreg.inputs.invmat, invmat
