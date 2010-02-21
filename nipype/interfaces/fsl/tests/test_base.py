import os

from nipype.testing import assert_equal, assert_true

import nipype.interfaces.fsl as fsl
from nipype.interfaces.base import InterfaceResult

def test_fslversion():
    ver = fsl.FSLInfo.version()
    if ver:
        # If ver is None, fsl is not installed
        ver = ver.split('.')
        yield assert_equal, ver[0], '4'


def test_fsloutputtype():
    types = ['ANALYZE_GZ', 'NIFTI_PAIR_GZ', 'NIFTI', 'NIFTI_PAIR',
             'NIFTI_GZ', 'ANALYZE']
    out_type, _ = fsl.FSLInfo.outputtype()
    if out_type is None:
        # Environment variable is not set.  FSL may not be installed.
        return
    yield assert_true, out_type in types
    env_type = os.environ.get('FSLOUTPUTTYPE')
    if env_type:
        # Set to same value for test.
        out_type, _ = fsl.FSLInfo.outputtype(env_type)
        yield assert_equal, out_type, env_type


def test_FSLCommand():
    # Most methods in FSLCommand are tested in the subclasses.  Only
    # testing the one item that is not.
    cmd = fsl.FSLCommand()
    cmd.cmd = 'bet' # Set the cmd to something
    res = cmd.run()
    yield assert_equal, type(res), InterfaceResult
