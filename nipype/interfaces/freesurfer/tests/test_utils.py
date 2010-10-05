# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nipype.externals.pynifti as nif
from nipype.testing import (assert_equal, assert_not_equal,
                            assert_raises, parametric, skipif)

import nipype.interfaces.freesurfer as fs

def no_freesurfer():
    if fs.Info().version is None:
        return True
    else:
        return False
    
@skipif(no_freesurfer)
def test_sample2surf():

    pass

@skipif(no_freesurfer)
def test_surfshots():

    pass
