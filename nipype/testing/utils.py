# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Additional handy utilities for testing
"""
import tempfile
import os
import shutil
__docformat__ = 'restructuredtext'

from nipype.utils.misc import package_check
from nose import SkipTest
from nipype.pipeline.engine import Node, Workflow
from nipype.interfaces.fsl.maths import BinaryMaths
from nipype.interfaces.fsl.utils import ImageStats
from nipype.interfaces.utility import IdentityInterface
from nipype.testing import assert_equal

def skip_if_no_package(*args, **kwargs):
    """Raise SkipTest if package_check fails

    Parameters
    ----------
    *args Positional parameters passed to `package_check`
    *kwargs Keyword parameters passed to `package_check`
    """
    package_check(exc_failed_import=SkipTest,
                  exc_failed_check=SkipTest,
                  *args, **kwargs)

def create_compare_pipeline(name="compare_and_test"):
    """ Creates a pipeline that takes two inputs - volume1 and volume2 
    calculates their difference and asserts the standard deviation of difference
    is zero."""
    
    inputnode = Node(interface=IdentityInterface(fields=["volume1", "volume2"]), name="inputnode")
    difference = Node(interface=BinaryMaths(operation="sub"), name="difference")
    
    mean = Node(interface=ImageStats(op_string="-s"), name="mean")
    
    test = Node(interface=IdentityInterface(fields=["mean"]), name="test")
    
    def assert_zero(val):
        assert val==0, "failed in " + name
    
    pipeline = Workflow(name=name)
    
    pipeline.connect([(inputnode, difference, [("volume1", "in_file")]),
                      (inputnode, difference, [("volume2", "operand_file")]),
                      (difference, mean, [("out_file", "in_file")]),
                      (mean, test, [(("out_stat", assert_zero), "mean")])
                      ])
    return pipeline

def setup_test_dir():
    # Setup function is called before each test.  Setup is called only
    # once for each generator function.
    global test_dir, cur_dir
    test_dir = tempfile.mkdtemp()
    cur_dir = os.getcwd()
    os.chdir(test_dir)

def remove_test_dir():
    # Teardown is called after each test to perform cleanup
    os.chdir(cur_dir)
    shutil.rmtree(test_dir)