# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Nipype interfaces for T1Prep surface processing.

:class:`T1PrepSurfaceEstimation`
    Cortical surface reconstruction for one hemisphere.
    Wraps ``python -m t1prep.surface_estimation``.

"""

import os

from ..base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    CommandLineInputSpec,
    TraitedSpec,
    File,
    Directory,
    traits,
    isdefined,
)
from .base import T1PrepCommand, import_cat_surf

__docformat__ = "restructuredtext"


# ---------------------------------------------------------------------------
# T1PrepSurfaceEstimation – surface reconstruction for one hemisphere
# ---------------------------------------------------------------------------


class T1PrepSurfaceEstimationInputSpec(CommandLineInputSpec):
    """Input specification for :class:`T1PrepSurfaceEstimation`."""

    # --- Required arguments -------------------------------------------------

    bname = traits.Str(
        argstr="--bname %s",
        mandatory=True,
        desc=(
            "Subject basename – the filename stem of the T1w NIfTI without "
            "path or extension (e.g. 'sub-01_T1w')."
        ),
    )
    side = traits.Enum(
        "left",
        "right",
        argstr="--side %s",
        mandatory=True,
        desc="Hemisphere to process ('left' or 'right').",
    )
    mri_dir = Directory(
        argstr="--mri-dir %s",
        mandatory=True,
        desc=(
            "Directory containing the MRI volumes produced by "
            "``t1prep.segment`` (e.g. hemisphere partition maps p0 left/right)."
        ),
    )
    surf_dir = Directory(
        argstr="--surf-dir %s",
        mandatory=True,
        desc="Output directory for surface files.",
    )
    names_tsv = File(
        exists=True,
        argstr="--names-tsv %s",
        mandatory=True,
        desc=(
            "Path to the Names.tsv file that defines the mapping between "
            "internal pipeline codes and output filenames for both CAT12 and "
            "BIDS naming conventions."
        ),
    )
    surf_templates_dir = Directory(
        argstr="--surf-templates-dir %s",
        mandatory=True,
        desc=(
            "Directory containing the FreeSurfer-average surface template "
            "files used for spherical registration "
            "(e.g. ``templates_surfaces_32k``)."
        ),
    )
    atlas_templates_dir = Directory(
        argstr="--atlas-templates-dir %s",
        mandatory=True,
        desc=(
            "Directory containing surface atlas annotation files used for "
            "atlas-based parcellation "
            "(e.g. ``atlases_surfaces_32k``)."
        ),
    )

    # --- Processing parameters (all have defaults) -------------------------

    estimate_spherereg = traits.Int(
        1,
        argstr="--estimate-spherereg %d",
        usedefault=True,
        desc=(
            "Perform spherical inflation + DARTEL registration + atlas "
            "resampling (0 = skip, 1 = run; default 1)."
        ),
    )
    thickness_method = traits.Enum(
        3,
        1,
        2,
        argstr="--thickness-method %d",
        usedefault=True,
        desc=(
            "Cortical thickness estimation method: "
            "1 = Tfs-distance (FreeSurfer-like, PBT-based); "
            "2 = pial-to-white surface distance; "
            "3 = pure projection-based thickness (PBT; default)."
        ),
    )
    save_pial_white = traits.Int(
        1,
        argstr="--save-pial-white %d",
        usedefault=True,
        desc="Estimate and save pial and white matter surfaces (0 = no, 1 = yes; default 1).",
    )
    pre_fwhm = traits.Float(
        1.0,
        argstr="--pre-fwhm %g",
        usedefault=True,
        desc="Pre-smoothing FWHM (mm) applied to the hemisphere volume before marching cubes (default 1.0).",
    )
    median_filter = traits.Int(
        2,
        argstr="--median-filter %d",
        usedefault=True,
        desc="Number of median filter passes applied before surface extraction (default 2).",
    )
    downsample = traits.Float(
        0.0,
        argstr="--downsample %g",
        usedefault=True,
        desc=(
            "Target mesh downsampling factor.  0 = apply a fixed 4:1 "
            "quadric-based reduction after marching cubes; "
            ">0 = keep the mesh at native resolution (default 0)."
        ),
    )
    vessel = traits.Int(
        1,
        argstr="--vessel %d",
        usedefault=True,
        desc="Apply blood-vessel intensity correction to the thickness volume (0 = no, 1 = yes; default 1).",
    )
    correct_folding = traits.Int(
        0,
        argstr="--correct-folding %d",
        usedefault=True,
        desc="Apply folding-based cortical thickness correction (0 = no, 1 = yes; default 0).",
    )
    debug = traits.Int(
        0,
        argstr="--debug %d",
        usedefault=True,
        desc="Retain intermediate files and write extra debug outputs (0 = no, 1 = yes; default 0).",
    )
    multi = traits.Int(
        -1,
        argstr="--multi %d",
        usedefault=True,
        desc=(
            "Number of parallel worker threads for CAT-Surface operations "
            "(-1 = auto-detect available CPUs; default -1)."
        ),
    )
    nii_ext = traits.Str(
        "nii.gz",
        argstr="--nii-ext %s",
        usedefault=True,
        desc="File extension for NIfTI volume outputs (default 'nii.gz').",
    )
    bids_naming = traits.Int(
        0,
        argstr="--bids-naming %d",
        usedefault=True,
        desc="Use BIDS derivatives naming conventions (0 = CAT12-style, 1 = BIDS; default 0).",
    )
    fmriprep = traits.Int(
        0,
        argstr="--fmriprep %d",
        usedefault=True,
        desc=(
            "Generate additional fMRIPrep-compatible surface outputs: "
            "curvature (sulcal depth), cortex mask, and mid-surface inflated "
            "sphere (0 = no, 1 = yes; default 0)."
        ),
    )

    # --- Optional arguments -------------------------------------------------

    report_log = File(
        argstr="--report-log %s",
        desc="Path to the subject's log file for timing and step information.",
    )
    atlas_surf = traits.Str(
        argstr="--atlas-surf %s",
        desc=(
            "Comma-separated surface atlas list for annotation resampling, "
            "e.g. 'aparc_DK40.freesurfer,aparc_a2009s.freesurfer'."
        ),
    )
    initial_surface = File(
        argstr="--initial-surface %s",
        desc=(
            "Path to a pre-existing central surface file.  When provided the "
            "marching-cubes step is skipped and this surface is used as the "
            "starting point (longitudinal processing)."
        ),
    )

    # --- Progress-bar plumbing (used by the T1Prep orchestration script) ----

    progress_bar_script = File(
        argstr="--progress-bar %s",
        desc="Path to the progress_bar_multi.sh script.",
    )
    progress_count_file = File(
        argstr="--progress-count-file %s",
        desc="Path to the shared progress counter file (updated by all hemisphere processes).",
    )
    progress_end_count = traits.Int(
        argstr="--progress-end-count %d",
        desc="Total number of pipeline steps shown by the progress bar.",
    )
    progress_start_count = traits.Int(
        argstr="--progress-start-count %d",
        desc="Initial count offset for the progress bar (used when resuming).",
    )


class T1PrepSurfaceEstimationOutputSpec(TraitedSpec):
    """Output specification for :class:`T1PrepSurfaceEstimation`."""

    surf_dir = Directory(desc="Surface output directory.")
    central_surface_lh = File(
        desc="Left-hemisphere central surface (GIFTI .gii, CAT12 naming)."
    )
    central_surface_rh = File(
        desc="Right-hemisphere central surface (GIFTI .gii, CAT12 naming)."
    )
    pial_surface_lh = File(
        desc="Left-hemisphere pial surface (saved when save_pial_white=1)."
    )
    pial_surface_rh = File(
        desc="Right-hemisphere pial surface (saved when save_pial_white=1)."
    )
    white_surface_lh = File(
        desc="Left-hemisphere white matter surface (saved when save_pial_white=1)."
    )
    white_surface_rh = File(
        desc="Right-hemisphere white matter surface (saved when save_pial_white=1)."
    )
    thickness_lh = File(desc="Left-hemisphere cortical thickness per-vertex file.")
    thickness_rh = File(desc="Right-hemisphere cortical thickness per-vertex file.")
    area_lh = File(desc="Left-hemisphere surface area per-vertex file.")
    area_rh = File(desc="Right-hemisphere surface area per-vertex file.")
    sphere_lh = File(
        desc="Left-hemisphere inflated sphere surface (saved when estimate_spherereg=1)."
    )
    sphere_rh = File(
        desc="Right-hemisphere inflated sphere surface (saved when estimate_spherereg=1)."
    )
    spherereg_lh = File(
        desc="Left-hemisphere DARTEL-registered sphere (saved when estimate_spherereg=1)."
    )
    spherereg_rh = File(
        desc="Right-hemisphere DARTEL-registered sphere (saved when estimate_spherereg=1)."
    )


class T1PrepSurfaceEstimation(T1PrepCommand):
    """Nipype interface for the T1Prep surface estimation module.

    Reconstructs the cortical central surface from hemisphere partition
    maps (produced by :class:`T1PrepSegment`) and computes per-vertex
    cortical thickness, surface area, and optionally pial/white surfaces,
    spherical inflation, and DARTEL-based atlas registration.

    The module mirrors the ``surface_estimation()`` bash function in
    ``scripts/T1Prep`` but runs entirely in-process via the ``cat_surf``
    Python bindings.  Run it separately for each hemisphere (``side='left'``
    and ``side='right'``).

    Invoked as ``python -m t1prep.surface_estimation``.

    Examples
    --------
    Left hemisphere with default settings:

    >>> surf = T1PrepSurfaceEstimation()
    >>> surf.inputs.bname = 'sub-01_T1w'
    >>> surf.inputs.side = 'left'
    >>> surf.inputs.mri_dir = 'out/mri'
    >>> surf.inputs.surf_dir = 'out/surf'
    >>> surf.inputs.names_tsv = '/opt/T1Prep/src/t1prep/data/Names.tsv'  # doctest: +SKIP
    >>> surf.inputs.surf_templates_dir = '/opt/T1Prep/src/t1prep/data/templates_surfaces_32k'
    >>> surf.inputs.atlas_templates_dir = '/opt/T1Prep/src/t1prep/data/atlases_surfaces_32k'
    >>> surf.cmdline  # doctest: +SKIP
    'python -m t1prep.surface_estimation --bname sub-01_T1w --side left ...'

    Skip spherical registration (faster, no atlas parcellation):

    >>> surf.inputs.estimate_spherereg = 0
    >>> surf.inputs.save_pial_white = 0

    References
    ----------
    https://github.com/ChristianGaser/T1Prep
    https://github.com/ChristianGaser/CAT-Surface
    """

    _module = "t1prep.surface_estimation"
    input_spec = T1PrepSurfaceEstimationInputSpec
    output_spec = T1PrepSurfaceEstimationOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        surf = os.path.abspath(self.inputs.surf_dir)
        outputs["surf_dir"] = surf
        bname = self.inputs.bname
        # CAT12-style naming: {hemi}.{type}.{bname}[.gii]
        for hemi in ("lh", "rh"):
            outputs[f"central_surface_{hemi}"] = os.path.join(
                surf, f"{hemi}.central.{bname}.gii"
            )
            outputs[f"pial_surface_{hemi}"] = os.path.join(
                surf, f"{hemi}.pial.{bname}.gii"
            )
            outputs[f"white_surface_{hemi}"] = os.path.join(
                surf, f"{hemi}.white.{bname}.gii"
            )
            outputs[f"thickness_{hemi}"] = os.path.join(
                surf, f"{hemi}.thickness.{bname}"
            )
            outputs[f"area_{hemi}"] = os.path.join(surf, f"{hemi}.area.{bname}")
            outputs[f"sphere_{hemi}"] = os.path.join(
                surf, f"{hemi}.sphere.{bname}.gii"
            )
            outputs[f"spherereg_{hemi}"] = os.path.join(
                surf, f"{hemi}.sphere.reg.{bname}.gii"
            )
        return outputs
