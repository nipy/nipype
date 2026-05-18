# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.surface."""

import os
import sys

import pytest

from nipype.interfaces.t1prep import T1PrepSurfaceEstimation


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
