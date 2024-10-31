# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import numpy as np
import nibabel as nb
import pytest

from looseversion import LooseVersion
from nibabel.orientations import axcodes2ornt, ornt_transform

from ..image import _as_reoriented_backport, _orientations

nibabel24 = LooseVersion(nb.__version__) >= LooseVersion("2.4.0")


@pytest.mark.skipif(not nibabel24, reason="Old nibabel - can't directly compare")
def test_reorientation_backport():
    pixdims = ((1, 1, 1), (2, 2, 3))
    data = np.random.normal(size=(17, 18, 19, 2))

    for pixdim in pixdims:
        # Generate a randomly rotated affine
        angles = np.random.uniform(-np.pi, np.pi, 3) * [1, 0.5, 1]
        rot = nb.eulerangles.euler2mat(*angles)
        scale = np.diag(pixdim)
        translation = np.array((17, 18, 19)) / 2
        affine = nb.affines.from_matvec(rot.dot(scale), translation)

        # Create image
        img = nb.Nifti1Image(data, affine)
        dim_info = {"freq": 0, "phase": 1, "slice": 2}
        img.header.set_dim_info(**dim_info)

        # Find a random, non-identity transform
        targ_ornt = orig_ornt = nb.io_orientation(affine)
        while np.array_equal(targ_ornt, orig_ornt):
            new_code = np.random.choice(_orientations)
            targ_ornt = axcodes2ornt(new_code)

        identity = ornt_transform(orig_ornt, orig_ornt)
        transform = ornt_transform(orig_ornt, targ_ornt)

        # Identity transform returns exact image
        assert img.as_reoriented(identity) is img
        assert _as_reoriented_backport(img, identity) is img

        reoriented_a = img.as_reoriented(transform)
        reoriented_b = _as_reoriented_backport(img, transform)

        flips_only = img.shape == reoriented_a.shape

        # Reorientation changes affine and data array
        assert not np.allclose(img.affine, reoriented_a.affine)
        assert not (
            flips_only and np.allclose(img.get_fdata(), reoriented_a.get_fdata())
        )
        # Dimension info changes iff axes are reordered
        assert flips_only == np.array_equal(
            img.header.get_dim_info(), reoriented_a.header.get_dim_info()
        )

        # Both approaches produce equivalent images
        assert np.allclose(reoriented_a.affine, reoriented_b.affine)
        assert np.array_equal(reoriented_a.get_fdata(), reoriented_b.get_fdata())
        assert np.array_equal(
            reoriented_a.header.get_dim_info(), reoriented_b.header.get_dim_info()
        )
