# -*- coding: utf-8 -*-
"""Various utilities common to IPython release and maintenance tools.
"""

from builtins import map
# Library imports
import os
import sys

from subprocess import Popen, PIPE, CalledProcessError, check_call

from distutils.dir_util import remove_tree

# Useful shorthands
pjoin = os.path.join
cd = os.chdir

# Utility functions

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def sh(cmd):
    """Execute command in a subshell, return status code."""
    return check_call(cmd, shell=True)


def compile_tree():
    """Compile all Python files below current directory."""
    vstr = '.'.join(map(str, sys.version_info[:2]))
    stat = os.system('python %s/lib/python%s/compileall.py .' % (sys.prefix,
                                                                 vstr))
    if stat:
        msg = '*** ERROR: Some Python files in tree do NOT compile! ***\n'
        msg += 'See messages above for the actual file that produced it.\n'
        raise SystemExit(msg)
