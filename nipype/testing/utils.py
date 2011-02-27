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