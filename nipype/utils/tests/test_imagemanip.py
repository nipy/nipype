# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import numpy as np
import nibabel as nb
import pytest
from ..imagemanip import copy_header


@pytest.mark.parametrize("keep_dtype", (True, False))
def test_copy_header(tmp_path, keep_dtype):
    """Cover copy_header."""
    fname1 = tmp_path / "reference.nii.gz"
    fname2 = tmp_path / "target.nii.gz"

    nii = nb.Nifti1Image(np.zeros((10, 10, 10), dtype="uint8"), None, None)
    nii.set_qform(np.diag((1.0, 2.0, 3.0, 1.0)), code=2)
    nii.set_sform(np.diag((1.0, 2.0, 3.0, 1.0)), code=1)
    nii.to_filename(str(fname1))

    nii.set_data_dtype("float32")
    nii.set_qform(np.eye(4), code=1)
    nii.to_filename(str(fname2))

    copied = nb.load(copy_header(fname1, fname2, keep_dtype=keep_dtype))
    ref = nb.load(str(fname1))
    assert np.all(copied.get_qform(coded=False) == ref.get_qform(coded=False))
    assert np.all(copied.get_sform(coded=False) == ref.get_sform(coded=False))
    assert copied.get_qform(coded=True)[1] == ref.get_qform(coded=True)[1]
    assert copied.get_sform(coded=True)[1] == ref.get_sform(coded=True)[1]
    assert (copied.header.get_data_dtype() == ref.header.get_data_dtype()) != keep_dtype
