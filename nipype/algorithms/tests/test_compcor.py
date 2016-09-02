# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function
from builtins import zip
from builtins import range
from builtins import open

import os
import glob
import shutil
import os.path as op
from tempfile import mkstemp, mkdtemp
from subprocess import Popen

from nose.tools import assert_raises
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
from nipype.algorithms.compcor import CompCore

def test_compcore():
    ccinterface = CompCore(realigned_file='../../testing/data/functional.nii', mask_file='../../testing/data/mask.nii')
    ccresult = ccinterface.run()
