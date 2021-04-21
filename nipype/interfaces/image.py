# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ..utils.filemanip import fname_presuffix
from .base import SimpleInterface, TraitedSpec, BaseInterfaceInputSpec, traits, File
from .. import LooseVersion


class RescaleInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Skull-stripped image to rescale")
    ref_file = File(exists=True, mandatory=True, desc="Skull-stripped reference image")
    invert = traits.Bool(desc="Invert contrast of rescaled image")
    percentile = traits.Range(
        low=0.0,
        high=50.0,
        value=0.0,
        usedefault=True,
        desc="Percentile to use for reference to allow "
        "for outliers - 1 indicates the 1st and "
        "99th percentiles in the input file will "
        "be mapped to the 99th and 1st percentiles "
        "in the reference; 0 indicates minima and "
        "maxima will be mapped",
    )


class RescaleOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Rescaled image")


class Rescale(SimpleInterface):
    """Rescale an image

    Rescales the non-zero portion of ``in_file`` to match the bounds of the
    non-zero portion of ``ref_file``.
    Reference values in the input and reference images are defined by the
    ``percentile`` parameter, and the reference values in each image are
    identified and the remaining values are scaled accordingly.
    In the case of ``percentile == 0``, the reference values are the maxima
    and minima of each image.
    If the ``invert`` parameter is set, the input file is inverted prior to
    rescaling.

    Examples
    --------

    To use a high-resolution T1w image as a registration target for a T2\\*
    image, it may be useful to invert the T1w image and rescale to the T2\\*
    range.
    Using the 1st and 99th percentiles may reduce the impact of outlier
    voxels.

    >>> from nipype.interfaces.image import Rescale
    >>> invert_t1w = Rescale(invert=True)
    >>> invert_t1w.inputs.in_file = 'structural.nii'
    >>> invert_t1w.inputs.ref_file = 'functional.nii'
    >>> invert_t1w.inputs.percentile = 1.
    >>> res = invert_t1w.run()  # doctest: +SKIP

    """

    input_spec = RescaleInputSpec
    output_spec = RescaleOutputSpec

    def _run_interface(self, runtime):
        import numpy as np
        import nibabel as nb

        img = nb.load(self.inputs.in_file)
        data = img.get_fdata()
        ref_data = nb.load(self.inputs.ref_file).get_fdata()

        in_mask = data > 0
        ref_mask = ref_data > 0

        q = [self.inputs.percentile, 100.0 - self.inputs.percentile]
        in_low, in_high = np.percentile(data[in_mask], q)
        ref_low, ref_high = np.percentile(ref_data[ref_mask], q)
        scale_factor = (ref_high - ref_low) / (in_high - in_low)

        signal = in_high - data if self.inputs.invert else data - in_low
        out_data = in_mask * (signal * scale_factor + ref_low)

        suffix = "_inv" if self.inputs.invert else "_rescaled"
        out_file = fname_presuffix(
            self.inputs.in_file, suffix=suffix, newpath=runtime.cwd
        )
        img.__class__(out_data, img.affine, img.header).to_filename(out_file)

        self._results["out_file"] = out_file
        return runtime


_axes = ("RL", "AP", "SI")
_orientations = tuple(
    "".join((x[i], y[j], z[k]))
    for x in _axes
    for y in _axes
    for z in _axes
    if x != y != z != x
    for i in (0, 1)
    for j in (0, 1)
    for k in (0, 1)
)


class ReorientInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Input image")
    orientation = traits.Enum(
        _orientations, usedefault=True, desc="Target axis orientation"
    )


class ReorientOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Reoriented image")
    transform = File(
        exists=True, desc="Affine transform from input orientation to output"
    )


class Reorient(SimpleInterface):
    """Conform an image to a given orientation

    Flips and reorder the image data array so that the axes match the
    directions indicated in ``orientation``.
    The default ``RAS`` orientation corresponds to the first axis being ordered
    from left to right, the second axis from posterior to anterior, and the
    third axis from inferior to superior.

    For oblique images, the original orientation is considered to be the
    closest plumb orientation.

    No resampling is performed, and thus the output image is not de-obliqued
    or registered to any other image or template.

    The effective transform is calculated from the original affine matrix to
    the reoriented affine matrix.

    Examples
    --------

    If an image is not reoriented, the original file is not modified

    .. testsetup::

        >>> def print_affine(matrix):
        ...     print(str(matrix).replace(']', ' ').replace('[', ' '))

    >>> import numpy as np
    >>> from nipype.interfaces.image import Reorient
    >>> reorient = Reorient(orientation='LPS')
    >>> reorient.inputs.in_file = 'segmentation0.nii.gz'
    >>> res = reorient.run()
    >>> res.outputs.out_file
    'segmentation0.nii.gz'

    >>> print_affine(np.loadtxt(res.outputs.transform))
    1.  0.  0.  0.
    0.  1.  0.  0.
    0.  0.  1.  0.
    0.  0.  0.  1.

    >>> reorient.inputs.orientation = 'RAS'
    >>> res = reorient.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../segmentation0_ras.nii.gz'

    >>> print_affine(np.loadtxt(res.outputs.transform))
    -1.   0.   0.  60.
     0.  -1.   0.  72.
     0.   0.   1.   0.
     0.   0.   0.   1.

    .. testcleanup::

        >>> import os
        >>> os.unlink(res.outputs.out_file)
        >>> os.unlink(res.outputs.transform)
    """

    input_spec = ReorientInputSpec
    output_spec = ReorientOutputSpec

    def _run_interface(self, runtime):
        import numpy as np
        import nibabel as nb
        from nibabel.orientations import axcodes2ornt, ornt_transform, inv_ornt_aff

        fname = self.inputs.in_file
        orig_img = nb.load(fname)

        # Find transform from current (approximate) orientation to
        # target, in nibabel orientation matrix and affine forms
        orig_ornt = nb.io_orientation(orig_img.affine)
        targ_ornt = axcodes2ornt(self.inputs.orientation)
        transform = ornt_transform(orig_ornt, targ_ornt)
        affine_xfm = inv_ornt_aff(transform, orig_img.shape)

        # Check can be eliminated when minimum nibabel version >= 2.4
        if LooseVersion(nb.__version__) >= LooseVersion("2.4.0"):
            reoriented = orig_img.as_reoriented(transform)
        else:
            reoriented = _as_reoriented_backport(orig_img, transform)

        # Image may be reoriented
        if reoriented is not orig_img:
            suffix = "_" + self.inputs.orientation.lower()
            out_name = fname_presuffix(fname, suffix=suffix, newpath=runtime.cwd)
            reoriented.to_filename(out_name)
        else:
            out_name = fname

        mat_name = fname_presuffix(
            fname, suffix=".mat", newpath=runtime.cwd, use_ext=False
        )
        np.savetxt(mat_name, affine_xfm, fmt="%.08f")

        self._results["out_file"] = out_name
        self._results["transform"] = mat_name

        return runtime


def _as_reoriented_backport(img, ornt):
    """Backport of img.as_reoriented as of nibabel 2.4.0"""
    import numpy as np
    import nibabel as nb
    from nibabel.orientations import inv_ornt_aff

    if np.array_equal(ornt, [[0, 1], [1, 1], [2, 1]]):
        return img

    t_arr = nb.apply_orientation(img.dataobj, ornt)
    new_aff = img.affine.dot(inv_ornt_aff(ornt, img.shape))
    reoriented = img.__class__(t_arr, new_aff, img.header)

    if isinstance(reoriented, nb.Nifti1Pair):
        # Also apply the transform to the dim_info fields
        new_dim = [
            None if orig_dim is None else int(ornt[orig_dim, 0])
            for orig_dim in img.header.get_dim_info()
        ]

        reoriented.header.set_dim_info(*new_dim)

    return reoriented
