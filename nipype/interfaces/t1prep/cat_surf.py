# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype interfaces for the ``cat_surf`` volume denoising and registration API.

These wrap the small subset of the CAT-Surface (``cat-surf``) Python API needed
to stand in for FreeSurfer / FSL (``bbregister``) / ANTs affine registration in
an fMRIPrep-style workflow:

**Volume operations**

* :class:`CatSurfVolSanlm`  – ``cat_surf.cli.vol_sanlm`` (SANLM denoising)

**Registration**

* :class:`CatSurfBbreg`                 – ``cat_surf.bbreg``
  (boundary-based registration, replaces FSL ``bbregister`` / ``flirt -bbr``)
* :class:`CatSurfBbregDetectContrast`   – ``cat_surf.bbreg_detect_contrast``
* :class:`CatSurfVolumeRegisterNmi`     – ``cat_surf.volume_register_nmi``
  (cross-modal affine, replaces ANTs NMI registration)
* :class:`CatSurfVolumeRegisterRobust`  – ``cat_surf.volume_register_robust``
  (same-modality robust affine)

Each interface is file-based: it reads its inputs from disk, calls the
``cat_surf`` wrapper, and writes its outputs (denoised volume / affine matrix)
to disk, so nodes pass file paths rather than pickled numpy arrays.

The full set of per-function ``cat_surf`` interfaces (surface I/O, geometry,
smoothing, resampling, DARTEL / Spherical Demons registration) is kept as an
archived reference in the CAT-Surface repository under
``cat_surface_cython/examples/nipype/cat_surf_interfaces_full.py``.

References
----------
https://github.com/ChristianGaser/CAT-Surface
https://github.com/ChristianGaser/T1Prep
"""

import os

import numpy as np

from ..base import (
    SimpleInterface,
    TraitedSpec,
    File,
    traits,
    isdefined,
)
from ...utils.filemanip import fname_presuffix
from .base import import_cat_surf as _import_cat_surf

__docformat__ = "restructuredtext"


def _cat_surf_cli():
    """Return the file-based ``cat_surf.cli`` mirror of the ``CAT_*`` binaries.

    File-based interfaces wrap ``cat_surf.cli.*`` (read files → call the
    in-memory wrapper → write files) rather than the low-level array API, so
    each node stays self-contained and passes file paths — not pickled numpy
    arrays — between workflow nodes.
    """
    cs = _import_cat_surf()
    cli = getattr(cs, "cli", None)
    if cli is None:  # plain cat_surf without the sub-module pre-imported
        import cat_surf.cli as cli  # noqa: F401
    return cli


# ===========================================================================
# Volume operations
# ===========================================================================


class CatSurfVolSanlmInputSpec(TraitedSpec):
    in_file = File(
        exists=True, mandatory=True, desc="Input NIfTI volume to denoise."
    )
    out_file = File(desc="Output denoised NIfTI path.")
    is_rician = traits.Bool(
        False, usedefault=True, desc="Assume Rician (rather than Gaussian) noise."
    )
    strength = traits.Float(
        1.0, usedefault=True, desc="Denoising strength (default 1.0)."
    )


class CatSurfVolSanlmOutputSpec(TraitedSpec):
    out_file = File(desc="Denoised NIfTI volume.")


class CatSurfVolSanlm(SimpleInterface):
    """Apply SANLM (Spatially Adaptive Non-Local Means) denoising to a volume.

    Wraps the file-based ``cat_surf.cli.vol_sanlm(in_file, out_file,
    is_rician=…, strength=…)`` (``CAT_VolSanlm``).  T1Prep applies SANLM
    denoising as the first preprocessing step on the raw T1w data.

    Examples
    --------
    >>> node = CatSurfVolSanlm()
    >>> node.inputs.in_file = 'sub-01_T1w.nii.gz'  # doctest: +SKIP
    >>> res = node.run()                # doctest: +SKIP
    >>> res.outputs.out_file            # denoised volume  # doctest: +SKIP
    """

    input_spec = CatSurfVolSanlmInputSpec
    output_spec = CatSurfVolSanlmOutputSpec

    def _run_interface(self, runtime):
        cli = _cat_surf_cli()
        if isdefined(self.inputs.out_file):
            out_file = os.path.abspath(self.inputs.out_file)
        else:
            out_file = fname_presuffix(
                self.inputs.in_file, prefix="sanlm_", newpath=runtime.cwd
            )
        cli.vol_sanlm(
            self.inputs.in_file,
            out_file,
            is_rician=self.inputs.is_rician,
            strength=self.inputs.strength,
        )
        self._results["out_file"] = out_file
        return runtime


# ===========================================================================
# Registration
# ===========================================================================


class CatSurfBbregInputSpec(TraitedSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        desc="Moving/functional NIfTI image to register (e.g. BOLD reference).",
    )
    lh_surface = File(
        exists=True, desc="Left white-matter surface used for the BBR cost."
    )
    rh_surface = File(
        exists=True, desc="Right white-matter surface used for the BBR cost."
    )
    ref_file = File(
        exists=True,
        desc="Reference T1w NIfTI used for NMI initialisation before BBR.",
    )
    out_matrix_file = File(
        desc="Output affine transform path (moving RAS → fixed RAS)."
    )
    invert_contrast = traits.Int(
        -1,
        usedefault=True,
        desc="Contrast: 0 = T1/FLAIR, 1 = T2/BOLD, -1 = auto-detect.",
    )
    fwhm = traits.Float(
        0.0, usedefault=True, desc="Pre-smoothing FWHM applied for BBR (mm)."
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfBbregOutputSpec(TraitedSpec):
    out_matrix_file = File(desc="4×4 affine transform (moving RAS → fixed RAS).")
    cost = traits.Float(desc="Final BBR cost (lower is better).")


class CatSurfBbreg(SimpleInterface):
    """Boundary-based registration of a volume to an anatomical reference.

    Wraps ``cat_surf.bbreg(in_file, lh_surface=…, rh_surface=…, ref_file=…,
    invert_contrast=…, fwhm=…, verbose=…) → (matrix, cost)`` and writes the 4×4
    affine to ``out_matrix_file``.  This replaces FSL ``bbregister`` /
    ``flirt -bbr`` in an fMRIPrep-style pipeline.

    The white-matter surfaces are read from disk and passed as ``(vertices,
    faces)`` arrays to ``cat_surf.bbreg``.

    Examples
    --------
    >>> node = CatSurfBbreg()
    >>> node.inputs.in_file = 'bold_ref.nii.gz'          # doctest: +SKIP
    >>> node.inputs.ref_file = 'sub-01_T1w.nii.gz'       # doctest: +SKIP
    >>> node.inputs.lh_surface = 'lh.white.sub-01.gii'   # doctest: +SKIP
    >>> node.inputs.rh_surface = 'rh.white.sub-01.gii'   # doctest: +SKIP
    >>> res = node.run()                                 # doctest: +SKIP
    """

    input_spec = CatSurfBbregInputSpec
    output_spec = CatSurfBbregOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = dict(
            invert_contrast=self.inputs.invert_contrast,
            fwhm=self.inputs.fwhm,
            verbose=self.inputs.verbose,
        )
        if isdefined(self.inputs.lh_surface):
            kwargs["lh_surface"] = cs.read_surface(self.inputs.lh_surface)
        if isdefined(self.inputs.rh_surface):
            kwargs["rh_surface"] = cs.read_surface(self.inputs.rh_surface)
        if isdefined(self.inputs.ref_file):
            kwargs["ref_file"] = self.inputs.ref_file

        matrix, cost = cs.bbreg(self.inputs.in_file, **kwargs)

        if isdefined(self.inputs.out_matrix_file):
            out_matrix_file = os.path.abspath(self.inputs.out_matrix_file)
        else:
            out_matrix_file = fname_presuffix(
                self.inputs.in_file,
                suffix="_bbreg.mat",
                newpath=runtime.cwd,
                use_ext=False,
            )
        np.savetxt(out_matrix_file, np.asarray(matrix, dtype=float))
        self._results["out_matrix_file"] = out_matrix_file
        self._results["cost"] = float(cost)
        return runtime


class CatSurfBbregDetectContrastInputSpec(TraitedSpec):
    in_file = File(
        exists=True, mandatory=True, desc="NIfTI volume whose contrast to detect."
    )
    lh_surface = File(
        exists=True, desc="Optional left white-matter surface for sampling."
    )
    rh_surface = File(
        exists=True, desc="Optional right white-matter surface for sampling."
    )


class CatSurfBbregDetectContrastOutputSpec(TraitedSpec):
    contrast = traits.Int(
        desc="0 = T1/FLAIR (WM brighter), 1 = T2/BOLD (WM darker), "
        "-1 = undetermined."
    )


class CatSurfBbregDetectContrast(SimpleInterface):
    """Detect the image contrast (WM vs GM polarity) for BBR.

    Wraps ``cat_surf.bbreg_detect_contrast(in_file, lh_surface=…,
    rh_surface=…) → int``.  The integer feeds :attr:`CatSurfBbreg.invert_contrast`.

    Examples
    --------
    >>> node = CatSurfBbregDetectContrast()
    >>> node.inputs.in_file = 'bold_ref.nii.gz'  # doctest: +SKIP
    >>> res = node.run()                         # doctest: +SKIP
    >>> res.outputs.contrast                     # 0, 1, or -1  # doctest: +SKIP
    """

    input_spec = CatSurfBbregDetectContrastInputSpec
    output_spec = CatSurfBbregDetectContrastOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        kwargs = {}
        if isdefined(self.inputs.lh_surface):
            kwargs["lh_surface"] = cs.read_surface(self.inputs.lh_surface)
        if isdefined(self.inputs.rh_surface):
            kwargs["rh_surface"] = cs.read_surface(self.inputs.rh_surface)
        self._results["contrast"] = int(
            cs.bbreg_detect_contrast(self.inputs.in_file, **kwargs)
        )
        return runtime


class CatSurfVolumeRegisterNmiInputSpec(TraitedSpec):
    moving_file = File(
        exists=True, mandatory=True, desc="Moving (source) NIfTI image."
    )
    fixed_file = File(
        exists=True, mandatory=True, desc="Fixed (reference) NIfTI image."
    )
    out_matrix_file = File(
        desc="Output affine transform path (moving RAS → fixed RAS)."
    )
    n_levels = traits.Int(
        4, usedefault=True, desc="Multi-resolution pyramid levels (default 4)."
    )
    n_bins = traits.Int(
        64, usedefault=True, desc="Joint-histogram bins for NMI (default 64)."
    )
    max_iter = traits.Int(
        30, usedefault=True, desc="Maximum optimiser iterations per level."
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfVolumeRegisterNmiOutputSpec(TraitedSpec):
    out_matrix_file = File(desc="4×4 affine transform (moving RAS → fixed RAS).")
    nmi = traits.Float(desc="Final NMI value (higher is better).")


class CatSurfVolumeRegisterNmi(SimpleInterface):
    """Cross-modal rigid registration by Normalised Mutual Information.

    Wraps ``cat_surf.volume_register_nmi(fixed_file, moving_file, n_levels=…,
    n_bins=…, max_iter=…, verbose=…) → (matrix, nmi)`` and writes the 4×4
    affine to ``out_matrix_file`` — an in-process replacement for an ANTs
    cross-modal affine step.

    Examples
    --------
    >>> node = CatSurfVolumeRegisterNmi()
    >>> node.inputs.moving_file = 'sub-01_T1w.nii.gz'  # doctest: +SKIP
    >>> node.inputs.fixed_file = 'template_T1.nii.gz'  # doctest: +SKIP
    >>> res = node.run()                               # doctest: +SKIP
    """

    input_spec = CatSurfVolumeRegisterNmiInputSpec
    output_spec = CatSurfVolumeRegisterNmiOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        matrix, nmi = cs.volume_register_nmi(
            self.inputs.fixed_file,
            self.inputs.moving_file,
            n_levels=self.inputs.n_levels,
            n_bins=self.inputs.n_bins,
            max_iter=self.inputs.max_iter,
            verbose=self.inputs.verbose,
        )
        if isdefined(self.inputs.out_matrix_file):
            out_matrix_file = os.path.abspath(self.inputs.out_matrix_file)
        else:
            out_matrix_file = fname_presuffix(
                self.inputs.moving_file,
                suffix="_nmi.mat",
                newpath=runtime.cwd,
                use_ext=False,
            )
        np.savetxt(out_matrix_file, np.asarray(matrix, dtype=float))
        self._results["out_matrix_file"] = out_matrix_file
        self._results["nmi"] = float(nmi)
        return runtime


class CatSurfVolumeRegisterRobustInputSpec(TraitedSpec):
    moving_file = File(
        exists=True, mandatory=True, desc="Moving (source) NIfTI image."
    )
    fixed_file = File(
        exists=True, mandatory=True, desc="Fixed (reference) NIfTI image."
    )
    out_matrix_file = File(
        desc="Output affine transform path (moving RAS → fixed RAS)."
    )
    n_levels = traits.Int(
        4, usedefault=True, desc="Multi-resolution pyramid levels (default 4)."
    )
    sat_k = traits.Float(
        4.685,
        usedefault=True,
        desc="Tukey biweight saturation constant (default 4.685).",
    )
    max_iter = traits.Int(
        20, usedefault=True, desc="Maximum optimiser iterations per level."
    )
    verbose = traits.Bool(False, usedefault=True, desc="Print diagnostic output.")


class CatSurfVolumeRegisterRobustOutputSpec(TraitedSpec):
    out_matrix_file = File(desc="4×4 affine transform (moving RAS → fixed RAS).")
    residual = traits.Float(desc="Final normalised residual (lower is better).")


class CatSurfVolumeRegisterRobust(SimpleInterface):
    """Same-modality rigid registration via robust (Tukey biweight) M-estimation.

    Wraps ``cat_surf.volume_register_robust(fixed_file, moving_file, n_levels=…,
    sat_k=…, max_iter=…, verbose=…) → (matrix, residual)`` and writes the 4×4
    affine to ``out_matrix_file``.  Less sensitive to intensity outliers
    (e.g. lesions) than the NMI variant; an in-process replacement for an ANTs
    same-modality affine step.

    Examples
    --------
    >>> node = CatSurfVolumeRegisterRobust()
    >>> node.inputs.moving_file = 'sub-01_T1w.nii.gz'         # doctest: +SKIP
    >>> node.inputs.fixed_file = 'sub-01_T1w_ref.nii.gz'      # doctest: +SKIP
    >>> res = node.run()                                      # doctest: +SKIP
    """

    input_spec = CatSurfVolumeRegisterRobustInputSpec
    output_spec = CatSurfVolumeRegisterRobustOutputSpec

    def _run_interface(self, runtime):
        cs = _import_cat_surf()
        matrix, residual = cs.volume_register_robust(
            self.inputs.fixed_file,
            self.inputs.moving_file,
            n_levels=self.inputs.n_levels,
            sat_k=self.inputs.sat_k,
            max_iter=self.inputs.max_iter,
            verbose=self.inputs.verbose,
        )
        if isdefined(self.inputs.out_matrix_file):
            out_matrix_file = os.path.abspath(self.inputs.out_matrix_file)
        else:
            out_matrix_file = fname_presuffix(
                self.inputs.moving_file,
                suffix="_robust.mat",
                newpath=runtime.cwd,
                use_ext=False,
            )
        np.savetxt(out_matrix_file, np.asarray(matrix, dtype=float))
        self._results["out_matrix_file"] = out_matrix_file
        self._results["residual"] = float(residual)
        return runtime
