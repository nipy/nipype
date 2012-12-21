# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

from nipype.testing import (assert_equal, assert_true, assert_raises,
                            assert_not_equal, skipif)
import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import InterfaceResult
from nipype.interfaces.fsl import check_fsl, no_fsl


@skipif(no_fsl)#skip if fsl not installed)
def test_fslversion():
    ver = fsl.Info.version()
    if ver:
        # If ver is None, fsl is not installed
        ver = ver.split('.')
        yield assert_true, ver[0] in ['4', '5']

@skipif(no_fsl)#skip if fsl not installed)
def test_fsloutputtype():
    types = fsl.Info.ftypes.keys()
    orig_out_type = fsl.Info.output_type()
    yield assert_true, orig_out_type in types


def test_outputtype_to_ext():
    for ftype, ext in fsl.Info.ftypes.items():
        res = fsl.Info.output_type_to_ext(ftype)
        yield assert_equal, res, ext

    yield assert_raises, KeyError, fsl.Info.output_type_to_ext, 'JUNK'

@skipif(no_fsl)#skip if fsl not installed)
def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand(command='ls')
    res = cmd.run()
    yield assert_equal, type(res), InterfaceResult

@skipif(no_fsl)#skip if fsl not installed)
def test_FSLCommand2():
    # Check default output type and environ
    cmd = fsl.FSLCommand(command='junk')
    yield assert_equal, cmd._output_type, fsl.Info.output_type()
    yield assert_equal, cmd.inputs.environ['FSLOUTPUTTYPE'], cmd._output_type
    yield assert_true, cmd._output_type in fsl.Info.ftypes

    cmd = fsl.FSLCommand
    cmdinst = fsl.FSLCommand(command='junk')
    for out_type in fsl.Info.ftypes:
        cmd.set_default_output_type(out_type)
        yield assert_equal, cmd._output_type, out_type
        if out_type != fsl.Info.output_type():
            #  Setting class outputtype should not effect existing instances
            yield assert_not_equal, cmdinst.inputs.output_type, out_type

@skipif(no_fsl)#skip if fsl not installed)
def test_gen_fname():
    # Test _gen_fname method of FSLCommand
    cmd = fsl.FSLCommand(command = 'junk',output_type = 'NIFTI_GZ')
    pth = os.getcwd()
    # just the filename
    fname = cmd._gen_fname('foo.nii.gz',suffix='_fsl')
    desired = os.path.join(pth, 'foo_fsl.nii.gz')
    yield assert_equal, fname, desired
    # filename with suffix
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain')
    desired = os.path.join(pth, 'foo_brain.nii.gz')
    yield assert_equal, fname, desired
    # filename with suffix and working directory
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain', cwd = '/data')
    desired = os.path.join('/data', 'foo_brain.nii.gz')
    yield assert_equal, fname, desired
    # filename with suffix and no file extension change
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain.mat',
                           change_ext = False)
    desired = os.path.join(pth, 'foo_brain.mat')
    yield assert_equal, fname, desired
