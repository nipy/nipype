# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import InterfaceResult
from nipype.interfaces.fsl import no_fsl

import pytest


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_fslversion():
    ver = fsl.Info.version()
    assert ver.split(".", 1)[0].isdigit()


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_fsloutputtype():
    types = list(fsl.Info.ftypes.keys())
    orig_out_type = fsl.Info.output_type()
    assert orig_out_type in types


def test_outputtype_to_ext():
    for ftype, ext in fsl.Info.ftypes.items():
        res = fsl.Info.output_type_to_ext(ftype)
        assert res == ext

    with pytest.raises(KeyError):
        fsl.Info.output_type_to_ext("JUNK")


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand(command="ls")
    res = cmd.run()
    assert type(res) is InterfaceResult


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_FSLCommand2():
    # Check default output type and environ
    cmd = fsl.FSLCommand(command="junk")
    assert cmd._output_type == fsl.Info.output_type()
    assert cmd.inputs.environ["FSLOUTPUTTYPE"] == cmd._output_type
    assert cmd._output_type in fsl.Info.ftypes

    cmd = fsl.FSLCommand
    cmdinst = fsl.FSLCommand(command="junk")
    for out_type in fsl.Info.ftypes:
        cmd.set_default_output_type(out_type)
        assert cmd._output_type == out_type
        if out_type != fsl.Info.output_type():
            #  Setting class outputtype should not effect existing instances
            assert cmdinst.inputs.output_type != out_type


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
@pytest.mark.parametrize(
    "args, desired_name",
    [
        ({}, {"file": "foo.nii.gz"}),  # just the filename
        # filename with suffix
        ({"suffix": "_brain"}, {"file": "foo_brain.nii.gz"}),
        (
            {"suffix": "_brain", "cwd": "/data"},
            # filename with suffix and working directory
            {"dir": "/data", "file": "foo_brain.nii.gz"},
        ),
        # filename with suffix and no file extension change
        ({"suffix": "_brain.mat", "change_ext": False}, {"file": "foo_brain.mat"}),
    ],
)
def test_gen_fname(args, desired_name):
    # Test _gen_fname method of FSLCommand
    cmd = fsl.FSLCommand(command="junk", output_type="NIFTI_GZ")
    pth = os.getcwd()
    fname = cmd._gen_fname("foo.nii.gz", **args)
    if "dir" in desired_name:
        desired = os.path.join(desired_name["dir"], desired_name["file"])
    else:
        desired = os.path.join(pth, desired_name["file"])
    assert fname == desired
