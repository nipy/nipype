# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nb
from nipype.testing import example_data
from ..metrics import FuzzyOverlap


def test_fuzzy_overlap(tmpdir):
    tmpdir.chdir()

    # Tests with tissue probability maps
    in_mask = example_data("tpms_msk.nii.gz")
    tpms = [example_data("tpm_%02d.nii.gz" % i) for i in range(3)]
    out = FuzzyOverlap(in_ref=tpms[0], in_tst=tpms[0]).run().outputs
    assert out.dice == 1

    out = FuzzyOverlap(in_mask=in_mask, in_ref=tpms[0], in_tst=tpms[0]).run().outputs
    assert out.dice == 1

    out = FuzzyOverlap(in_mask=in_mask, in_ref=tpms[0], in_tst=tpms[1]).run().outputs
    assert 0 < out.dice < 1

    out = FuzzyOverlap(in_ref=tpms, in_tst=tpms).run().outputs
    assert out.dice == 1.0

    out = FuzzyOverlap(in_mask=in_mask, in_ref=tpms, in_tst=tpms).run().outputs
    assert out.dice == 1.0

    # Tests with synthetic 3x3x3 images
    data = np.zeros((3, 3, 3), dtype=float)
    data[0, 0, 0] = 0.5
    data[2, 2, 2] = 0.25
    data[1, 1, 1] = 0.3
    nb.Nifti1Image(data, np.eye(4)).to_filename("test1.nii.gz")

    data = np.zeros((3, 3, 3), dtype=float)
    data[0, 0, 0] = 0.6
    data[1, 1, 1] = 0.3
    nb.Nifti1Image(data, np.eye(4)).to_filename("test2.nii.gz")

    out = FuzzyOverlap(in_ref="test1.nii.gz", in_tst="test2.nii.gz").run().outputs
    assert np.allclose(out.dice, 0.82051)

    # Just considering the mask, the central pixel
    # that raised the index now is left aside.
    data = np.zeros((3, 3, 3), dtype=np.uint8)
    data[0, 0, 0] = 1
    data[2, 2, 2] = 1
    nb.Nifti1Image(data, np.eye(4)).to_filename("mask.nii.gz")

    out = (
        FuzzyOverlap(
            in_ref="test1.nii.gz", in_tst="test2.nii.gz", in_mask="mask.nii.gz"
        )
        .run()
        .outputs
    )
    assert np.allclose(out.dice, 0.74074)
