# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Test testing utilities
"""

import os
import subprocess
from unittest.mock import patch, MagicMock
from unittest import SkipTest
from nipype.testing.utils import TempFATFS


def test_tempfatfs():
    try:
        fatfs = TempFATFS()
    except OSError:
        raise SkipTest("Cannot mount FAT filesystems with FUSE")
    with fatfs as tmp_dir:
        assert os.path.exists(tmp_dir)


@patch(
    "subprocess.check_call",
    MagicMock(side_effect=subprocess.CalledProcessError("", "")),
)
def test_tempfatfs_calledprocesserror():
    try:
        TempFATFS()
    except OSError as e:
        assert isinstance(e, IOError)
        assert isinstance(e.__cause__, subprocess.CalledProcessError)
    else:
        assert False


@patch("subprocess.check_call", MagicMock())
@patch("subprocess.Popen", MagicMock(side_effect=OSError()))
def test_tempfatfs_oserror():
    try:
        TempFATFS()
    except OSError as e:
        assert isinstance(e, IOError)
        assert isinstance(e.__cause__, OSError)
    else:
        assert False
