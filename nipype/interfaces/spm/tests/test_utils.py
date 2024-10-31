# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import pytest
from nipype.testing import example_data
import nipype.interfaces.spm.utils as spmu
from nipype.interfaces.base import isdefined
from nipype.utils.filemanip import split_filename, fname_presuffix
from nipype.interfaces.base import TraitError


def test_coreg():
    moving = example_data(infile="functional.nii")
    target = example_data(infile="T1.nii")
    mat = example_data(infile="trans.mat")
    coreg = spmu.CalcCoregAffine(matlab_cmd="mymatlab")
    coreg.inputs.target = target
    assert coreg.inputs.matlab_cmd == "mymatlab"
    coreg.inputs.moving = moving
    assert not isdefined(coreg.inputs.mat)
    pth, mov, _ = split_filename(moving)
    _, tgt, _ = split_filename(target)
    mat = os.path.join(pth, f"{mov}_to_{tgt}.mat")
    invmat = fname_presuffix(mat, prefix="inverse_")
    script = coreg._make_matlab_command(None)
    assert coreg.inputs.mat == mat
    assert coreg.inputs.invmat == invmat


def test_apply_transform():
    moving = example_data(infile="functional.nii")
    mat = example_data(infile="trans.mat")
    applymat = spmu.ApplyTransform(matlab_cmd="mymatlab")
    assert applymat.inputs.matlab_cmd == "mymatlab"
    applymat.inputs.in_file = moving
    applymat.inputs.mat = mat
    script = applymat._make_matlab_command(None)
    expected = "[p n e v] = spm_fileparts(V.fname);"
    assert expected in script
    expected = "V.mat = transform.M * V.mat;"
    assert expected in script


def test_reslice():
    moving = example_data(infile="functional.nii")
    space_defining = example_data(infile="T1.nii")
    reslice = spmu.Reslice(matlab_cmd="mymatlab_version")
    assert reslice.inputs.matlab_cmd == "mymatlab_version"
    reslice.inputs.in_file = moving
    reslice.inputs.space_defining = space_defining
    assert reslice.inputs.interp == 0
    with pytest.raises(TraitError):
        reslice.inputs.trait_set(interp="nearest")
    with pytest.raises(TraitError):
        reslice.inputs.trait_set(interp=10)
    reslice.inputs.interp = 1
    script = reslice._make_matlab_command(None)
    outfile = fname_presuffix(moving, prefix="r")
    assert reslice.inputs.out_file == outfile
    expected = "\nflags.mean=0;\nflags.which=1;\nflags.mask=0;"
    assert expected in script.replace(" ", "")
    expected_interp = "flags.interp = 1;\n"
    assert expected_interp in script
    assert "spm_reslice(invols, flags);" in script


def test_dicom_import():
    dicom = example_data(infile="dicomdir/123456-1-1.dcm")
    di = spmu.DicomImport(matlab_cmd="mymatlab")
    assert di.inputs.matlab_cmd == "mymatlab"
    assert di.inputs.output_dir_struct == "flat"
    assert di.inputs.output_dir == "./converted_dicom"
    assert di.inputs.format == "nii"
    assert not di.inputs.icedims
    with pytest.raises(TraitError):
        di.inputs.trait_set(output_dir_struct="wrong")
    with pytest.raises(TraitError):
        di.inputs.trait_set(format="FAT")
    with pytest.raises(TraitError):
        di.inputs.trait_set(in_files=["does_sfd_not_32fn_exist.dcm"])
    di.inputs.in_files = [dicom]
    assert di.inputs.in_files == [dicom]
