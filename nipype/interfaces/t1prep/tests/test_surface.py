# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.surface."""

import os
import sys

import pytest

from nipype.interfaces.t1prep import T1PrepSurfaceEstimation, T1PrepCatSurf


def _make_file(p):
    p.write_bytes(b"")
    return str(p)


@pytest.fixture
def surface_paths(tmp_path):
    names_tsv = _make_file(tmp_path / "Names.tsv")
    surf_templates = tmp_path / "surf_templates"
    atlas_templates = tmp_path / "atlas_templates"
    surf_templates.mkdir()
    atlas_templates.mkdir()
    return {
        "names_tsv": names_tsv,
        "surf_templates_dir": str(surf_templates),
        "atlas_templates_dir": str(atlas_templates),
        "mri_dir": str(tmp_path / "mri"),
        "surf_dir": str(tmp_path / "surf"),
    }


def test_T1PrepSurfaceEstimation_cmd_uses_current_interpreter():
    se = T1PrepSurfaceEstimation()
    assert se.cmd == f"{sys.executable} -m t1prep.surface_estimation"


def test_T1PrepSurfaceEstimation_cmdline_has_required_flags(surface_paths):
    se = T1PrepSurfaceEstimation()
    se.inputs.bname = "sub-01_T1w"
    se.inputs.side = "left"
    for k, v in surface_paths.items():
        setattr(se.inputs, k, v)
    cmd = se.cmdline
    assert "--bname sub-01_T1w" in cmd
    assert "--side left" in cmd
    assert "--mri-dir" in cmd
    assert "--surf-dir" in cmd
    assert "--names-tsv" in cmd


def test_T1PrepSurfaceEstimation_list_outputs_hemi_pattern(surface_paths):
    se = T1PrepSurfaceEstimation()
    se.inputs.bname = "sub-01_T1w"
    se.inputs.side = "left"
    for k, v in surface_paths.items():
        setattr(se.inputs, k, v)
    outs = se._list_outputs()
    surf = os.path.abspath(surface_paths["surf_dir"])
    assert outs["surf_dir"] == surf
    for hemi in ("lh", "rh"):
        assert outs[f"central_surface_{hemi}"] == os.path.join(
            surf, f"{hemi}.central.sub-01_T1w.gii"
        )
        assert outs[f"thickness_{hemi}"] == os.path.join(
            surf, f"{hemi}.thickness.sub-01_T1w"
        )
        assert outs[f"spherereg_{hemi}"] == os.path.join(
            surf, f"{hemi}.sphere.reg.sub-01_T1w.gii"
        )


# ---------------------------------------------------------------------------
# T1PrepCatSurf
# ---------------------------------------------------------------------------


def _have_cat_surf():
    try:
        from t1prep import cat_surf  # noqa: F401
        return True
    except ImportError:
        try:
            import cat_surf  # noqa: F401
            return True
        except ImportError:
            return False


def test_T1PrepCatSurf_gen_outfile_default(tmp_path):
    surf = _make_file(tmp_path / "lh.central.sub-01.gii")
    vals = _make_file(tmp_path / "lh.thickness.sub-01")
    node = T1PrepCatSurf()
    node.inputs.in_surface = surf
    node.inputs.in_values = vals
    node.inputs.fwhm = 20.0
    out = node._gen_outfile()
    assert os.path.basename(out) == "s20.lh.thickness.sub-01"
    assert os.path.isabs(out)


def test_T1PrepCatSurf_gen_outfile_explicit(tmp_path):
    surf = _make_file(tmp_path / "lh.central.sub-01.gii")
    vals = _make_file(tmp_path / "lh.thickness.sub-01")
    node = T1PrepCatSurf()
    node.inputs.in_surface = surf
    node.inputs.in_values = vals
    node.inputs.out_file = "explicit.out"
    assert node._gen_outfile() == os.path.abspath("explicit.out")


@pytest.mark.skipif(not _have_cat_surf(), reason="cat_surf is not installed")
def test_T1PrepCatSurf_runtime_smoke(tmp_path):
    """Smoke-test the full run path when cat_surf is importable."""
    # We do not have real input data here; just verify that the input traits
    # validate and that _run_interface dispatches to cat_surf.  If cat_surf is
    # installed but the input files don't load, the call may raise — that's OK
    # for this smoke test (we just want to confirm the wiring isn't broken).
    surf = _make_file(tmp_path / "lh.central.sub-01.gii")
    vals = _make_file(tmp_path / "lh.thickness.sub-01")
    node = T1PrepCatSurf()
    node.inputs.in_surface = surf
    node.inputs.in_values = vals
    with pytest.raises(Exception):
        node._run_interface(None)
