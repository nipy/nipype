# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
from nipype.algorithms.compcor import CompCore

@skipif(True)
def test_compcore():
    ccinterface = CompCore(realigned_file='../../testing/data/functional.nii', mask_file='../../testing/data/mask.nii')
    ccresult = ccinterface.run()
