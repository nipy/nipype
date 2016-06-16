# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Test testing utilities
"""

import os
import warnings
import subprocess
from mock import patch, MagicMock
from nipype.testing.utils import TempFATFS
from nose.tools import assert_true, assert_raises


def test_tempfatfs():
    try:
        fatfs = TempFATFS()
    except (IOError, OSError):
        warnings.warn("Cannot mount FAT filesystems with FUSE")
    else:
        with fatfs as tmpdir:
            yield assert_true, os.path.exists(tmpdir)

def test_tempfatfs_calledprocesserror():
    with patch('subprocess.check_call', MagicMock(side_effect=subprocess.CalledProcessError('',''))):
        yield assert_raises, IOError, TempFATFS

def test_tempfatfs_oserror():
    with patch('subprocess.Popen', MagicMock()):
        subprocess.Popen.return_value.side_effect = OSError()
        yield assert_raises, IOError, TempFATFS
