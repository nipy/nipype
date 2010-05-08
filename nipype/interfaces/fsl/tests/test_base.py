import os

from nipype.testing import (assert_equal, assert_true, assert_raises,
                            assert_not_equal, parametric)
import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import InterfaceResult

def test_fslversion():
    ver = fsl.Info.version()
    if ver:
        # If ver is None, fsl is not installed
        ver = ver.split('.')
        yield assert_equal, ver[0], '4'

def test_fsloutputtype():
    types = fsl.Info.ftypes
    orig_out_type, _ = fsl.Info.outputtype()
    yield assert_true, orig_out_type in types
    for ftype in types.keys():
        out_type, _ = fsl.Info.outputtype(ftype)
        yield assert_equal, out_type, fsl.Info.outputtype()[0]

    # Test for possible common mistake of passing in outputtype tuple
    out_type = fsl.Info.outputtype()
    yield assert_raises, KeyError, fsl.Info.outputtype, out_type

    # Restore original output type, otherwise the last one set in this
    # test will affect any tests that import fsl that follow this when
    # nose is run.
    _, _ = fsl.Info.outputtype(orig_out_type)

def test_outputtype_to_ext():
    for ftype, ext in fsl.Info.ftypes.items():
        res = fsl.Info.outputtype_to_ext(ftype)
        yield assert_equal, res, ext

    yield assert_raises, KeyError, fsl.Info.outputtype_to_ext, 'JUNK'

def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand()
    cmd.cmd = 'bet' # Set the cmd to something
    res = cmd.run()
    yield assert_equal, type(res), InterfaceResult

def test_FSLCommand():
    # Check default output type and environ
    cmd = fsl.FSLCommand(command='junk')
    yield assert_equal, cmd._outputtype, fsl.Info.outputtype()
    yield assert_equal, cmd.inputs.environ['FSLOUTPUTTYPE'], cmd._outputtype
    yield assert_true, cmd._outputtype in fsl.Info.ftypes

    cmd = fsl.FSLCommand
    cmdinst = fsl.FSLCommand(command='junk')
    for out_type in fsl.Info.ftypes:
        cmd.set_default_outputtype(out_type)
        yield assert_equal, cmd._outputtype, out_type
        if out_type != fsl.Info.outputtype():
            #  Setting class outputtype should not effect existing instances
            yield assert_not_equal, cmdinst.inputs.outputtype, out_type

@parametric
def test_gen_fname():
    # Test _gen_fname method of FSLCommand
    cmd = fsl.FSLCommand(command = 'junk')
    pth = os.getcwd()
    # just the filename
    fname = cmd._gen_fname('foo.nii.gz')
    desired = os.path.join(pth, 'foo_fsl.nii.gz')
    yield assert_equal(fname, desired)
    # filename with suffix
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain')
    desired = os.path.join(pth, 'foo_brain.nii.gz')
    yield assert_equal(fname, desired)
    # filename with suffix and working directory
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain', cwd = '/data')
    desired = os.path.join('/data', 'foo_brain.nii.gz')
    yield assert_equal(fname, desired)
    # filename with suffix and no file extension change
    fname = cmd._gen_fname('foo.nii.gz', suffix = '_brain.mat',
                           change_ext = False)
    desired = os.path.join(pth, 'foo_brain.mat')
    yield assert_equal(fname, desired)
