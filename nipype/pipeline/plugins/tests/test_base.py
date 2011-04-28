# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""
import numpy as np
import scipy.sparse as ssp

from nipype.testing import (assert_raises, assert_equal, assert_true,
                            assert_false, skipif)
import nipype.pipeline.plugins.base as pb

def test_scipy_sparse():
    foo = ssp.lil_matrix(np.eye(3, k=1))
    goo = foo.getrowview(0)
    goo[goo.nonzero()] = 0
    yield assert_equal, foo[0,1], 0
