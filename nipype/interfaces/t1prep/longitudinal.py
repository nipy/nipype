# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype interfaces for T1Prep longitudinal processing.

:class:`T1PrepRealignLongitudinal`
    Rigid realignment of a series of 3D NIfTI volumes acquired from the
    same subject (longitudinal time-points), mirroring SPM's realign module.
    Wraps ``python -m t1prep.realign_longitudinal``.
"""

import os

from ..base import (
    CommandLineInputSpec,
    TraitedSpec,
    File,
    Directory,
    InputMultiPath,
    traits,
)
from .base import T1PrepCommand

__docformat__ = "restructuredtext"


class T1PrepRealignLongitudinalInputSpec(CommandLineInputSpec):
    """Input specification for :class:`T1PrepRealignLongitudinal`."""

    in_files = InputMultiPath(
        File(exists=True),
        argstr="--inputs %s",
        mandatory=True,
        desc="Input NIfTI images (one per longitudinal time-point).",
    )
    out_dir = Directory(
        argstr="--out-dir %s",
        mandatory=True,
        desc="Output directory for realigned volumes and transforms.",
    )
    out_subfolders = traits.List(
        traits.Str,
        argstr="--out-subfolders %s",
        desc=("Per-input output subfolder names (must match the number of " "inputs)."),
    )

    iterations = traits.Int(
        argstr="--iterations %d",
        desc="Number of multi-scale alignment passes (default 3).",
    )
    max_fwhm_mm = traits.Float(
        argstr="--max-fwhm-mm %g",
        desc="Maximum smoothing FWHM in mm for the multi-scale pyramid (default 6.0).",
    )
    no_intensity_scale = traits.Bool(
        argstr="--no-intensity-scale",
        desc="Disable SPM-like per-volume intensity scaling.",
    )
    overlap_penalty_weight = traits.Float(
        argstr="--overlap-penalty-weight %g",
        desc="Weight of the overlap penalty term (default 0.0).",
    )
    sample_strategy = traits.Enum(
        "grid",
        "gradient",
        argstr="--sample-strategy %s",
        desc="Sample-point selection: 'grid' (default) or 'gradient'.",
    )
    grad_quantile = traits.Float(
        argstr="--grad-quantile %g",
        desc=(
            "Quantile threshold for the gradient sampler "
            "(only used when sample_strategy='gradient'; default 0.80)."
        ),
    )
    device = traits.Str(
        argstr="--device %s",
        desc="Compute device (currently reserved; default 'cpu').",
    )

    save_template = traits.Bool(
        argstr="--save-template",
        desc="Save the reference volume used as the alignment target.",
    )
    save_resampled = traits.Bool(
        argstr="--save-resampled",
        desc="Write resampled copies of the inputs in reference space.",
    )
    update_headers = traits.Bool(
        argstr="--update-headers",
        desc=(
            "Only update the NIfTI headers with the estimated affines; "
            "do not write resampled volumes."
        ),
    )
    set_zooms_from_sform = traits.Bool(
        argstr="--set-zooms-from-sform",
        desc="Copy pixdim/zooms from the sform when updating headers.",
    )
    force_template_zooms = traits.Bool(
        argstr="--force-template-zooms",
        desc="Force the reference (template) zooms on all outputs.",
    )
    inverse_consistent = traits.Bool(
        argstr="--inverse-consistent",
        desc="Re-center rigid transforms around their SE(3) barycenter.",
    )
    register_to_first = traits.Bool(
        argstr="--register-to-first",
        desc="Register all volumes to the first input (skip mean-template refinement).",
    )
    output_naming = traits.Enum(
        "bids",
        "legacy",
        argstr="--output-naming %s",
        desc="Output naming convention: 'bids' (default) or 'legacy'.",
    )
    use_skullstrip = traits.Bool(
        argstr="--use-skullstrip",
        desc="Estimate transforms on skull-stripped copies of the inputs.",
    )
    verbose = traits.Bool(
        argstr="--verbose",
        desc="Print optimizer diagnostics.",
    )


class T1PrepRealignLongitudinalOutputSpec(TraitedSpec):
    """Output specification for :class:`T1PrepRealignLongitudinal`."""

    out_dir = Directory(desc="Top-level output directory.")


class T1PrepRealignLongitudinal(T1PrepCommand):
    """Nipype interface for the T1Prep longitudinal realignment module.

    Estimates per-timepoint rigid (6-DoF) transforms and optionally refines
    them against a mean template, then writes resampled volumes and/or
    updates NIfTI headers in place.  Mirrors SPM's realign module.

    Invoked as ``python -m t1prep.realign_longitudinal``.

    Examples
    --------
    >>> ra = T1PrepRealignLongitudinal()
    >>> ra.inputs.in_files = ['sub-01_ses-01_T1w.nii.gz', 'sub-01_ses-02_T1w.nii.gz']  # doctest: +SKIP
    >>> ra.inputs.out_dir = 'derivatives/realign'
    >>> ra.inputs.save_resampled = True
    >>> ra.cmdline  # doctest: +SKIP
    'python -m t1prep.realign_longitudinal --inputs sub-01_ses-01_T1w.nii.gz sub-01_ses-02_T1w.nii.gz --out-dir derivatives/realign --save-resampled'

    References
    ----------
    https://github.com/ChristianGaser/T1Prep
    """

    _module = "t1prep.realign_longitudinal"
    input_spec = T1PrepRealignLongitudinalInputSpec
    output_spec = T1PrepRealignLongitudinalOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_dir"] = os.path.abspath(self.inputs.out_dir)
        return outputs
