# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Test testing utilities
"""

from nipype.testing.utils import TempFATFS
from nose.tools import assert_true


def test_tempfatfs():
    with TempFATFS() as tmpdir:
        yield assert_true, tmpdir is not None
