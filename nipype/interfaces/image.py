# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import numpy as np
import nibabel as nb

from ..utils.filemanip import fname_presuffix
from .base import (SimpleInterface, TraitedSpec, BaseInterfaceInputSpec,
                   traits, File)

_axes = ('RL', 'AP', 'SI')
_orientations = tuple(
    ''.join((x[i], y[j], z[k]))
    for x in _axes for y in _axes for z in _axes
    if x != y != z != x
    for i in (0, 1) for j in (0, 1) for k in (0, 1))


class ReorientInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='Input image')
    orientation = traits.Enum(_orientations, usedefault=True,
                              desc='Target axis orientation')


class ReorientOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Reoriented image')
    transform = File(exists=True,
                     desc='Affine transform from input orientation to output')


class Reorient(SimpleInterface):
    """Reorient an image
    """
    input_spec = ReorientInputSpec
    output_spec = ReorientOutputSpec

    def _run_interface(self, runtime):
        from nibabel.orientations import (
            axcodes2ornt, ornt_transform, inv_ornt_aff)

        fname = self.inputs.in_file
        orig_img = nb.load(fname)

        # Find transform from current (approximate) orientation to
        # target, in nibabel orientation matrix and affine forms
        orig_ornt = nb.io_orientation(orig_img.affine)
        targ_ornt = axcodes2ornt(self.inputs.orientation)
        transform = ornt_transform(orig_ornt, targ_ornt)
        affine_xfm = inv_ornt_aff(transform, orig_img.shape)

        # Check can be eliminated when minimum nibabel version >= 2.2
        if hasattr(orig_img, 'as_reoriented'):
            reoriented = orig_img.as_reoriented(transform)
        else:
            reoriented = _as_reoriented_backport(orig_img, transform)

        # Image may be reoriented
        if reoriented is not orig_img:
            suffix = '_' + self.inputs.orientation.lower()
            out_name = fname_presuffix(fname, suffix=suffix,
                                       newpath=runtime.cwd)
            reoriented.to_filename(out_name)
        else:
            out_name = fname

        mat_name = fname_presuffix(fname, suffix='.mat',
                                   newpath=runtime.cwd, use_ext=False)
        np.savetxt(mat_name, affine_xfm, fmt='%.08f')

        self._results['out_file'] = out_name
        self._results['transform'] = mat_name

        return runtime


def _as_reoriented_backport(img, ornt):
    """Backport of img.as_reoriented as of nibabel 2.2.0"""
    from nibabel.orientations import inv_ornt_aff
    if np.array_equal(ornt, [[0, 1], [1, 1], [2, 1]]):
        return img

    t_arr = nb.apply_orientation(img.get_data(), ornt)
    new_aff = img.affine.dot(inv_ornt_aff(ornt, img.shape))
    reoriented = img.__class__(t_arr, new_aff, img.header)

    if isinstance(reoriented, nb.Nifti1Pair):
        # Also apply the transform to the dim_info fields
        new_dim = list(reoriented.header.get_dim_info())
        for idx, value in enumerate(new_dim):
            # For each value, leave as None if it was that way,
            # otherwise check where we have mapped it to
            if value is None:
                continue
            new_dim[idx] = np.where(ornt[:, 0] == idx)[0]

        reoriented.header.set_dim_info(*new_dim)

    return reoriented
