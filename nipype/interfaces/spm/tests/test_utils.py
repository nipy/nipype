# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from nipype.testing import (assert_equal, assert_false,assert_raises,
			    assert_true, skipif, example_data)
from nipype.interfaces.spm import no_spm
import nipype.interfaces.spm.utils as spmu
from nipype.interfaces.base import isdefined
from nipype.utils.filemanip import split_filename, fname_presuffix
from nipype.interfaces.base import TraitError

def test_coreg():
    moving = example_data(infile = 'functional.nii')
    target = example_data(infile = 'T1.nii')
    mat = example_data(infile = 'trans.mat')
    coreg = spmu.CalcCoregAffine(matlab_cmd = 'mymatlab')
    coreg.inputs.target = target
    assert_equal(coreg.inputs.matlab_cmd, 'mymatlab')
    coreg.inputs.moving = moving
    assert_equal( isdefined(coreg.inputs.mat),False)
    pth, mov, _ = split_filename(moving)
    _, tgt, _ = split_filename(target)
    mat = os.path.join(pth, '%s_to_%s.mat'%(mov,tgt))
    invmat = fname_presuffix(mat, prefix = 'inverse_')
    scrpt = coreg._make_matlab_command(None)
    assert_equal(coreg.inputs.mat, mat)
    assert_equal( coreg.inputs.invmat, invmat)


def test_apply_transform():
    moving = example_data(infile = 'functional.nii')
    mat = example_data(infile = 'trans.mat')
    applymat = spmu.ApplyTransform(matlab_cmd = 'mymatlab')
    assert_equal( applymat.inputs.matlab_cmd, 'mymatlab' )
    applymat.inputs.in_file = moving
    applymat.inputs.mat = mat
    scrpt = applymat._make_matlab_command(None)
    expected = 'img_space = spm_get_space(infile);'
    assert_equal( expected in scrpt, True)
    expected = 'spm_get_space(infile, transform.M * img_space);'
    assert_equal(expected in scrpt, True)

def test_reslice():
    moving = example_data(infile = 'functional.nii')
    space_defining = example_data(infile = 'T1.nii')
    reslice = spmu.Reslice(matlab_cmd = 'mymatlab_version')
    assert_equal( reslice.inputs.matlab_cmd, 'mymatlab_version')
    reslice.inputs.in_file = moving
    reslice.inputs.space_defining = space_defining
    assert_equal( reslice.inputs.interp, 0)
    assert_raises(TraitError,reslice.inputs.trait_set,interp = 'nearest')
    assert_raises(TraitError, reslice.inputs.trait_set, interp = 10)
    reslice.inputs.interp = 1
    script = reslice._make_matlab_command(None)
    outfile = fname_presuffix(moving, prefix='r')
    assert_equal(reslice.inputs.out_file, outfile)
    expected = '\nflags.mean=0;\nflags.which=1;\nflags.mask=0;'
    assert_equal(expected in script.replace(' ',''), True)
    expected_interp = 'flags.interp = 1;\n'
    assert_equal(expected_interp in script, True)
    assert_equal('spm_reslice(invols, flags);' in script, True)
