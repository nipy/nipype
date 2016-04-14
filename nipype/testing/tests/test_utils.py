# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Test testing utilities
"""

import os
import warnings
from nipype.testing.utils import TempFATFS
from nose.tools import assert_true


def test_tempfatfs():
    try:
        fatfs = TempFATFS()
    except IOError:
        warnings.warn("Cannot mount FAT filesystems with FUSE")
    else:
        with fatfs as tmpdir:
            yield assert_true, os.path.exists(tmpdir)
