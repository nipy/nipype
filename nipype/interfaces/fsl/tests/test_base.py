import os

from nose import with_setup

from nipype.testing import assert_equal, assert_true, assert_raises
import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import InterfaceResult

def test_fslversion():
    ver = fsl.FSLInfo.version()
    if ver:
        # If ver is None, fsl is not installed
        ver = ver.split('.')
        yield assert_equal, ver[0], '4'

def test_fsloutputtype():
    types = fsl.FSLInfo.ftypes
    orig_out_type, _ = fsl.FSLInfo.outputtype()
    yield assert_true, orig_out_type in types
    for ftype in types.keys():
        out_type, _ = fsl.FSLInfo.outputtype(ftype)
        yield assert_equal, out_type, fsl.FSLInfo.outputtype()[0]

    # Test for possible common mistake of passing in outputtype tuple
    out_type = fsl.FSLInfo.outputtype()
    yield assert_raises, KeyError, fsl.FSLInfo.outputtype, out_type

    # Restore original output type, otherwise the last one set in this
    # test will affect any tests that import fsl that follow this when
    # nose is run.
    _, _ = fsl.FSLInfo.outputtype(orig_out_type)

def test_outputtype_to_ext():
    for ftype, ext in fsl.FSLInfo.ftypes.items():
        res = fsl.FSLInfo.outputtype_to_ext(ftype)
        yield assert_equal, res, ext

    yield assert_raises, KeyError, fsl.FSLInfo.outputtype_to_ext, 'JUNK'

def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand()
    cmd.cmd = 'bet' # Set the cmd to something
    res = cmd.run()
    yield assert_equal, type(res), InterfaceResult
