# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype interfaces for the T1Prep segmentation pipeline.

:class:`T1Prep`     – full pipeline (skull-strip → segment → surface).
:class:`T1PrepSegment` – segmentation stage (``python -m t1prep.segment``).
"""

import os

from ..base import (
    CommandLineInputSpec,
    TraitedSpec,
    File,
    Directory,
    InputMultiPath,
    traits,
    isdefined,
)
from .base import T1PrepCommand

__docformat__ = "restructuredtext"


# ---------------------------------------------------------------------------
# T1Prep – full pipeline
# ---------------------------------------------------------------------------


class T1PrepInputSpec(CommandLineInputSpec):
    """Input specification for :class:`T1Prep`."""

    in_files = InputMultiPath(
        File(exists=True),
        argstr="%s",
        position=-1,
        mandatory=True,
        desc="Input T1-weighted NIfTI file(s) (.nii or .nii.gz).",
    )

    # --- Save options -------------------------------------------------------

    out_dir = Directory(
        argstr="--out-dir %s",
        desc=(
            "Base output directory.  If unset, results are placed in "
            "subfolders of the input file's directory."
        ),
    )
    bids = traits.Bool(
        argstr="--bids",
        desc="Use BIDS derivatives naming conventions for output files.",
    )
    gz = traits.Bool(
        argstr="--gz",
        desc="Write compressed (.nii.gz) NIfTI outputs.",
    )
    no_overwrite = traits.Str(
        argstr="--no-overwrite %s",
        desc=(
            "Skip a subject when files matching this glob pattern already "
            "exist (e.g. 'surf/lh.thickness.')."
        ),
    )

    # --- Processing flags ---------------------------------------------------

    no_surf = traits.Bool(
        argstr="--no-surf",
        desc="Skip cortical surface and thickness estimation.",
    )
    no_seg = traits.Bool(
        argstr="--no-seg",
        desc="Skip tissue segmentation (surface processing only).",
    )
    skullstrip_only = traits.Bool(
        argstr="--skullstrip-only",
        xor=["skip_skullstrip"],
        desc=(
            "Run skull-stripping only, write skull-stripped image and brain "
            "mask to the MRI output folder, then exit."
        ),
    )
    skip_skullstrip = traits.Bool(
        argstr="--skip-skullstrip",
        xor=["skullstrip_only"],
        desc=(
            "Skip skull-stripping (assumes the input is already "
            "skull-stripped with background close to zero)."
        ),
    )
    no_sphere_reg = traits.Bool(
        argstr="--no-sphere-reg",
        desc="Skip spherical surface registration and atlas resampling.",
    )
    pial_white = traits.Bool(
        argstr="--pial-white",
        desc="Estimate and save pial and white matter surfaces.",
    )
    no_correct_folding = traits.Bool(
        argstr="--no-correct-folding",
        desc="Disable cortical thickness correction for folding effects.",
    )
    no_mwp = traits.Bool(
        argstr="--no-mwp",
        desc=(
            "Disable saving of modulated warped (MNI-space) segmentations "
            "(they are saved by default)."
        ),
    )
    no_atlas = traits.Bool(
        argstr="--no-atlas",
        desc="Disable atlas labelling and ROI volume export.",
    )

    # --- Additional save flags ----------------------------------------------

    wp = traits.Bool(
        argstr="--wp",
        desc="Additionally save non-modulated warped (MNI-space) segmentations.",
    )
    rp = traits.Bool(
        argstr="--rp",
        desc="Additionally save affine-registered segmentations.",
    )
    p = traits.Bool(
        argstr="--p",
        desc="Additionally save native-space segmentation maps.",
    )
    csf = traits.Bool(
        argstr="--csf",
        desc=(
            "Additionally save CSF segmentation (GM and WM are always saved "
            "when --p or --rp are set)."
        ),
    )
    lesions = traits.Bool(
        argstr="--lesions",
        desc=(
            "Additionally save white-matter hyperintensity (WMH) lesion "
            "segmentation in native and/or affine space."
        ),
    )
    fmriprep = traits.Bool(
        argstr="--fmriprep",
        desc=(
            "Save fMRIPrep-compatible outputs: ANTs/ITK .h5 deformation "
            "fields, dseg files, cortex mask, inflated surfaces, and "
            "spatially registered data at 2 mm resolution."
        ),
    )
    amap = traits.Bool(
        argstr="--amap",
        desc=(
            "Use AMAP segmentation for a refined tissue classification after "
            "the initial DeepMriPrep estimate."
        ),
    )

    # --- Atlas options ------------------------------------------------------

    atlas = traits.Str(
        argstr="--atlas %s",
        desc=(
            "Comma-separated volumetric atlas list for ROI estimation, "
            "e.g. \"'neuromorphometrics','suit'\".  "
            "Default: \"'neuromorphometrics', 'cobra'\"."
        ),
    )
    atlas_surf = traits.Str(
        argstr="--atlas-surf %s",
        desc=(
            "Comma-separated surface atlas list, "
            "e.g. \"'aparc_DK40.freesurfer','aparc_a2009s.freesurfer'\"."
        ),
    )

    # --- Longitudinal / advanced flags --------------------------------------

    long_data = Directory(
        argstr="--long-data %s",
        desc=(
            "Longitudinal mode: process the volume at PATH but keep output "
            "naming and folder structure based on the primary input file."
        ),
    )
    initial_surf = File(
        argstr="--initial-surf %s",
        desc="Pre-existing central surface file for longitudinal processing.",
    )

    # --- Expert options -----------------------------------------------------

    pre_fwhm = traits.Float(
        argstr="--pre-fwhm %g",
        desc="Pre-smoothing FWHM (mm) applied before marching cubes surface extraction.",
    )
    downsample = traits.Float(
        argstr="--downsample %g",
        desc="Mesh downsampling factor for the initial surface extraction step.",
    )
    median_filter = traits.Int(
        argstr="--median-filter %d",
        desc="Number of median filter passes applied before surface extraction.",
    )
    vessel = traits.Float(
        argstr="--vessel %g",
        desc="Blood-vessel correction strength (0 = disabled; default 1.0).",
    )
    thickness_method = traits.Enum(
        1,
        2,
        3,
        argstr="--thickness-method %d",
        desc=(
            "Cortical thickness estimation method: "
            "1 = Tfs-distance (FreeSurfer-like, PBT-based); "
            "2 = pial-to-white surface distance; "
            "3 = pure projection-based thickness (PBT)."
        ),
    )
    seed = traits.Int(
        argstr="--seed %d",
        desc="Random seed for deterministic processing.",
    )
    debug = traits.Bool(
        argstr="--debug",
        desc="Enable verbose output and retain all intermediate files.",
    )
    no_retry = traits.Bool(
        argstr="--no-retry",
        desc=(
            "Disable automatic retry of failed processing steps "
            "(by default a failed step is retried once)."
        ),
    )
    quiet = traits.Bool(
        argstr="--quiet",
        desc="Suppress progress messages (overrides the default verbose mode).",
    )


class T1PrepOutputSpec(TraitedSpec):
    """Output specification for :class:`T1Prep`."""

    out_dir = Directory(desc="Top-level output directory.")
    mri_dir = Directory(desc="MRI sub-directory (segmentations, brain mask, etc.).")
    surf_dir = Directory(desc="Surface sub-directory (central, pial, white surfaces).")
    report_dir = Directory(desc="Report sub-directory (logs, QC JSON).")
    label_dir = Directory(desc="Label sub-directory (atlas ROI JSON).")


class T1Prep(T1PrepCommand):
    """Nipype interface for the T1Prep T1-weighted MRI preprocessing pipeline.

    T1Prep preprocesses T1-weighted MRI data through three stages:

    1. **Skull-stripping** – deep-learning-based brain extraction via
       DeepMriPrep / deepbet.
    2. **Tissue segmentation** – GM / WM / CSF probability maps and optional
       nonlinear warp to MNI space via DeepMriPrep; optionally refined with
       AMAP.
    3. **Cortical surface estimation** – central, pial and white matter
       surfaces, thickness, area, sulcal depth, and optional spherical
       atlas-based parcellation via CAT-Surface (``cat-surf``).

    Output naming follows CAT12 conventions by default; BIDS derivatives
    naming is selected with ``bids=True``.

    This interface invokes ``python -m t1prep.t1prep`` (the pure-Python
    pipeline entry point).  For multi-subject parallelism prefer running
    multiple nodes in a nipype workflow rather than using ``--multi``.

    Examples
    --------
    Full pipeline with BIDS naming:

    >>> t1 = T1Prep()
    >>> t1.inputs.in_files = ['sub-01_T1w.nii.gz']  # doctest: +SKIP
    >>> t1.inputs.out_dir = 'derivatives'
    >>> t1.inputs.bids = True
    >>> t1.cmdline  # doctest: +SKIP
    'python -m t1prep.t1prep --bids --out-dir derivatives sub-01_T1w.nii.gz'

    Segmentation only (skip surface estimation):

    >>> t1 = T1Prep()
    >>> t1.inputs.in_files = ['sub-01_T1w.nii.gz']  # doctest: +SKIP
    >>> t1.inputs.no_surf = True
    >>> t1.inputs.p = True
    >>> t1.cmdline  # doctest: +SKIP
    'python -m t1prep.t1prep --no-surf --p sub-01_T1w.nii.gz'

    References
    ----------
    https://github.com/ChristianGaser/T1Prep
    """

    _module = "t1prep.t1prep"
    input_spec = T1PrepInputSpec
    output_spec = T1PrepOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_dir):
            base = os.path.abspath(self.inputs.out_dir)
        else:
            # Default: results go into sub-directories of the input file's parent
            base = os.path.dirname(os.path.abspath(self.inputs.in_files[0]))
        outputs["out_dir"] = base
        outputs["mri_dir"] = os.path.join(base, "mri")
        outputs["surf_dir"] = os.path.join(base, "surf")
        outputs["report_dir"] = os.path.join(base, "report")
        outputs["label_dir"] = os.path.join(base, "label")
        return outputs


# ---------------------------------------------------------------------------
# T1PrepSegment – segmentation stage
# ---------------------------------------------------------------------------


class T1PrepSegmentInputSpec(CommandLineInputSpec):
    """Input specification for :class:`T1PrepSegment`."""

    in_file = File(
        exists=True,
        argstr="--input %s",
        mandatory=True,
        desc="Input T1-weighted NIfTI image (.nii or .nii.gz).",
    )
    mri_dir = Directory(
        argstr="--mri_dir %s",
        mandatory=True,
        desc="Output directory for MRI volumes (segmentations, brain mask, deformations).",
    )
    report_dir = Directory(
        argstr="--report_dir %s",
        mandatory=True,
        desc="Output directory for report log files.",
    )
    label_dir = Directory(
        argstr="--label_dir %s",
        mandatory=True,
        desc="Output directory for label and atlas-ROI JSON outputs.",
    )

    # --- Atlas options ------------------------------------------------------

    atlas = traits.Str(
        argstr="--atlas %s",
        desc=(
            "Comma-separated atlas list for ROI estimation, "
            "e.g. \"Neuromorphometrics,SUIT\".  "
            "Leave empty to disable ROI export."
        ),
    )

    # --- Output content flags -----------------------------------------------

    surf = traits.Bool(
        argstr="--surf",
        desc=(
            "Save partitioned hemisphere segmentation maps (p0 left/right) "
            "required for the subsequent surface estimation stage."
        ),
    )
    csf = traits.Bool(
        argstr="--csf",
        desc="Save CSF segmentation probability map in addition to GM and WM.",
    )
    mwp = traits.Bool(
        argstr="--mwp",
        desc="Save modulated warped (MNI-space) GM and WM segmentation maps.",
    )
    wp = traits.Bool(
        argstr="--wp",
        desc="Save non-modulated warped (MNI-space) segmentation maps.",
    )
    p = traits.Bool(
        argstr="--p",
        desc="Save native-space probability segmentation maps.",
    )
    rp = traits.Bool(
        argstr="--rp",
        desc="Save affine-registered segmentation maps.",
    )
    lesions = traits.Bool(
        argstr="--lesions",
        desc=(
            "Save white-matter hyperintensity (WMH) lesion segmentation in "
            "native and/or affine space."
        ),
    )
    save_fmriprep = traits.Bool(
        argstr="--save-fmriprep",
        desc=(
            "Save ANTs/ITK-compatible HDF5 (.h5) deformation fields, discrete "
            "segmentation (dseg), and brain mask for fMRIPrep compatibility."
        ),
    )

    # --- Naming / format flags ----------------------------------------------

    bids = traits.Bool(
        argstr="--bids",
        desc="Use BIDS derivatives naming conventions for output files.",
    )
    gz = traits.Bool(
        argstr="--gz",
        desc="Save compressed NIfTI outputs (.nii.gz).",
    )

    # --- Segmentation options -----------------------------------------------

    amap = traits.Bool(
        argstr="--amap",
        desc=(
            "Refine the initial DeepMriPrep segmentation using AMAP "
            "(Adaptive Maximum A Posteriori) tissue classification."
        ),
    )
    vessel = traits.Float(
        argstr="--vessel %g",
        desc=(
            "Blood-vessel correction strength (0 = disabled; default 1.0).  "
            "Reduces vessel-related intensity artefacts before segmentation."
        ),
    )
    skullstrip_only = traits.Bool(
        argstr="--skullstrip-only",
        xor=["skip_skullstrip"],
        desc="Run skull-stripping only, save outputs, then exit.",
    )
    skip_skullstrip = traits.Bool(
        argstr="--skip-skullstrip",
        xor=["skullstrip_only"],
        desc="Skip skull-stripping (input is already skull-stripped).",
    )
    seed = traits.Int(
        argstr="--seed %d",
        desc="Random seed for reproducibility.",
    )

    # --- Verbosity / debugging ----------------------------------------------

    verbose = traits.Bool(
        argstr="--verbose",
        desc="Print progress output.",
    )
    debug = traits.Bool(
        argstr="--debug",
        desc="Enable verbose output and retain all temporary files.",
    )

    # --- Internal / pipeline flags ------------------------------------------

    count = traits.Int(
        argstr="--count %d",
        desc=(
            "Total number of pipeline steps for the progress bar "
            "(used when called from the T1Prep orchestration script)."
        ),
    )


class T1PrepSegmentOutputSpec(TraitedSpec):
    """Output specification for :class:`T1PrepSegment`."""

    mri_dir = Directory(desc="MRI output directory with segmentation volumes.")
    report_dir = Directory(desc="Report output directory with log files.")
    label_dir = Directory(desc="Label output directory with atlas ROI JSON files.")


class T1PrepSegment(T1PrepCommand):
    """Nipype interface for the T1Prep segmentation module (``t1prep.segment``).

    Performs skull-stripping, bias field correction, and tissue segmentation
    (GM / WM / CSF) on a single T1-weighted NIfTI image using DeepMriPrep.
    Optionally applies AMAP refinement, blood-vessel correction, WMH lesion
    detection, nonlinear warping to MNI space, and atlas-based ROI volume
    export.

    This is the segmentation stage of the T1Prep pipeline and can be run
    independently of surface estimation.  Pass ``surf=True`` to also emit the
    hemisphere partition maps (p0 left/right) needed for the surface stage.

    Invoked as ``python -m t1prep.segment``.

    Examples
    --------
    >>> seg = T1PrepSegment()
    >>> seg.inputs.in_file = 'sub-01_T1w.nii.gz'  # doctest: +SKIP
    >>> seg.inputs.mri_dir = 'out/mri'
    >>> seg.inputs.report_dir = 'out/report'
    >>> seg.inputs.label_dir = 'out/label'
    >>> seg.inputs.surf = True
    >>> seg.inputs.gz = True
    >>> seg.cmdline  # doctest: +SKIP
    'python -m t1prep.segment --gz --surf --input sub-01_T1w.nii.gz --label_dir out/label --mri_dir out/mri --report_dir out/report'

    Save native-space GM and WM maps plus CSF:

    >>> seg = T1PrepSegment()
    >>> seg.inputs.in_file = 'sub-01_T1w.nii.gz'  # doctest: +SKIP
    >>> seg.inputs.mri_dir = 'out/mri'
    >>> seg.inputs.report_dir = 'out/report'
    >>> seg.inputs.label_dir = 'out/label'
    >>> seg.inputs.p = True
    >>> seg.inputs.csf = True
    >>> seg.cmdline  # doctest: +SKIP
    'python -m t1prep.segment --csf --p --input sub-01_T1w.nii.gz --label_dir out/label --mri_dir out/mri --report_dir out/report'
    """

    _module = "t1prep.segment"
    input_spec = T1PrepSegmentInputSpec
    output_spec = T1PrepSegmentOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["mri_dir"] = os.path.abspath(self.inputs.mri_dir)
        outputs["report_dir"] = os.path.abspath(self.inputs.report_dir)
        outputs["label_dir"] = os.path.abspath(self.inputs.label_dir)
        return outputs
