# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

from nipype.testing import (assert_equal, assert_true, assert_raises,
                            assert_not_equal, skipif)
from ... import fsl
from ..base import FSLCommandInputSpec
from nipype.interfaces.base import InterfaceResult
from nipype.interfaces.fsl import check_fsl, no_fsl


def test_fslversion():
    ver = fsl.Info.version()
    if check_fsl():
        # If ver is None, fsl is not installed
        ver = ver.split('.')
        yield assert_true, ver[0] in ['4', '5']
    else:
        yield assert_equal, None, ver


def test_fsloutputtype():
    types = list(fsl.Info.ftypes.keys())
    orig_out_type = fsl.Info.output_type()
    yield assert_true, orig_out_type in types
    yield assert_raises, KeyError, lambda: fsl.Info.ftypes['JUNK']


def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand(command='ls')
    res = cmd.run()
    yield assert_equal, type(res), InterfaceResult


def test_FSLCommandInputSpec():
    # Check default output type and environ
    fslspec = FSLCommandInputSpec()
    yield assert_equal, fslspec.output_type, lambda: os.getenv('FSLOUTPUTTYPE', 'NIFTI')

def test_FSLCommand2():
    cmd = fsl.FSLCommand(command='junk')
    yield assert_equal, cmd.inputs.environ['FSLOUTPUTTYPE'], cmd.inputs.output_type
    for out_type in fsl.Info.ftypes:
        cmd.inputs.output_type = out_type
        yield assert_equal, cmd.inputs.output_type_, fsl.Info.ftypes[out_type]
