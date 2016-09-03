# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype
from nipype.testing import assert_equal, assert_true, assert_false, skipif
from nipype.algorithms.compcor import CompCore

import nibabel as nb
import numpy as np

# first 3 = spatial; last = temporal
dim = 2, 3, 4, 5

@skipif(True)
def test_compcore():
    ccinterface = CompCore(realigned_file=make_toy(np.random.rand(*dim), 'func.nii'),
                           mask_file=make_toy(np.random.randint(0, 2, dim[:2]),
                                              'mask.nii'))
    ccresult = ccinterface.run()

def make_toy(array, filename):
    toy = nb.Nifti1Image(array, np.eye(4))
    nb.nifti1.save(toy, filename)
    return filename
