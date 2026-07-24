# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.cat_surf.

Only the denoising / registration subset needed to replace FreeSurfer / FSL
(bbreg) / ANTs is wrapped here; each interface is exercised against a fake
``cat_surf`` module so the native library is not required.
"""

import inspect
import types

import numpy as np
import pytest

from nipype.interfaces.base import SimpleInterface
from nipype.interfaces.t1prep import (
    CatSurfBbreg,
    CatSurfBbregDetectContrast,
    CatSurfVolSanlm,
    CatSurfVolumeRegisterNmi,
    CatSurfVolumeRegisterRobust,
)
from nipype.interfaces.t1prep import base as t1prep_base
from nipype.interfaces.t1prep import cat_surf as cat_surf_mod


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


def test_import_cat_surf_raises_when_missing(monkeypatch):
    """If neither t1prep nor cat_surf is importable, the helper should raise."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if (
            name in {"t1prep", "cat_surf"}
            or name.startswith("t1prep.")
            or name.startswith("cat_surf.")
        ):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        t1prep_base.import_cat_surf()


@pytest.mark.skipif(not _have_cat_surf(), reason="cat_surf is not installed")
def test_import_cat_surf_returns_module():
    cs = t1prep_base.import_cat_surf()
    assert hasattr(cs, "read_surface")


def test_CatSurfBbreg_trait_validation():
    """A non-existent in_file should fail trait validation."""
    from nipype.interfaces.base import traits

    node = CatSurfBbreg()
    with pytest.raises(traits.TraitError):
        node.inputs.in_file = "/nonexistent/path/that/does/not/exist.nii.gz"


# ---------------------------------------------------------------------------
# Dispatch coverage: run every wrapper against a fake cat_surf module
# ---------------------------------------------------------------------------


def _fake_cat_surf():
    """Stand-in for the cat_surf C-extension module.

    Registration helpers return ``(matrix, metric)`` and detection returns an
    int, matching the arity the wrappers unpack; ``cli.vol_sanlm`` is a no-op.
    """
    ns = types.SimpleNamespace()
    ns.read_surface = lambda *a, **k: ("V", "F")
    ns.bbreg = lambda *a, **k: (np.eye(4), 0.5)
    ns.bbreg_detect_contrast = lambda *a, **k: 0
    ns.volume_register_nmi = lambda *a, **k: (np.eye(4), 0.9)
    ns.volume_register_robust = lambda *a, **k: (np.eye(4), 0.1)
    ns.cli = types.SimpleNamespace(vol_sanlm=lambda *a, **k: None)
    return ns


def _fake_runtime(tmp_path):
    """Minimal runtime stub exposing the ``cwd`` used for default output names."""
    return types.SimpleNamespace(cwd=str(tmp_path), returncode=0, environ={})


def _catsurf_interfaces():
    out = []
    for name, obj in vars(cat_surf_mod).items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, SimpleInterface)
            and name.startswith("CatSurf")
        ):
            out.append(obj)
    return out


def _set_mandatory_inputs(node, tmp_path):
    """Set every mandatory input to a type-appropriate dummy value."""
    spec = node.input_spec()
    for name, trait in spec.traits().items():
        if name in ("trait_added", "trait_modified") or not trait.mandatory:
            continue
        ttype = type(trait.trait_type).__name__
        if ttype == "File":
            f = tmp_path / f"{node.__class__.__name__}_{name}.nii.gz"
            f.write_bytes(b"")
            setattr(node.inputs, name, str(f))
        elif ttype == "Int":
            setattr(node.inputs, name, 1)
        elif ttype == "Float":
            setattr(node.inputs, name, 1.0)
        elif ttype == "Bool":
            setattr(node.inputs, name, True)
        else:  # Any, Str, etc.
            setattr(node.inputs, name, "dummy")


def test_catsurf_interfaces_discovered():
    """Guard against the discovery helper silently finding nothing."""
    assert len(_catsurf_interfaces()) == 5


@pytest.mark.parametrize("iface", _catsurf_interfaces(), ids=lambda c: c.__name__)
def test_catsurf_dispatch_with_fake_module(iface, tmp_path, monkeypatch):
    """Each wrapper dispatches to cat_surf and records outputs without the C lib."""
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)
    node = iface()
    _set_mandatory_inputs(node, tmp_path)
    node._run_interface(_fake_runtime(tmp_path))
    outputs = node._list_outputs()
    assert isinstance(outputs, dict)


def test_volume_register_nmi_writes_matrix(tmp_path, monkeypatch):
    """NMI registration writes the 4x4 matrix and reports the metric."""
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)

    def mkfile(name):
        f = tmp_path / name
        f.write_bytes(b"")
        return str(f)

    node = CatSurfVolumeRegisterNmi()
    node.inputs.moving_file = mkfile("moving.nii.gz")
    node.inputs.fixed_file = mkfile("fixed.nii.gz")
    node.inputs.out_matrix_file = str(tmp_path / "moving_to_fixed.mat")
    node._run_interface(_fake_runtime(tmp_path))
    outs = node._list_outputs()
    assert outs["nmi"] == pytest.approx(0.9)
    written = np.loadtxt(outs["out_matrix_file"])
    assert written.shape == (4, 4)


def test_bbreg_reads_surfaces_and_reports_cost(tmp_path, monkeypatch):
    """BBR loads the optional surfaces and reports the cost."""
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)

    def mkfile(name):
        f = tmp_path / name
        f.write_bytes(b"")
        return str(f)

    node = CatSurfBbreg()
    node.inputs.in_file = mkfile("bold_ref.nii.gz")
    node.inputs.lh_surface = mkfile("lh.white.gii")
    node.inputs.rh_surface = mkfile("rh.white.gii")
    node.inputs.ref_file = mkfile("T1w.nii.gz")
    node._run_interface(_fake_runtime(tmp_path))
    outs = node._list_outputs()
    assert outs["cost"] == pytest.approx(0.5)
    assert np.loadtxt(outs["out_matrix_file"]).shape == (4, 4)


def test_bbreg_detect_contrast_returns_int(tmp_path, monkeypatch):
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)
    f = tmp_path / "vol.nii.gz"
    f.write_bytes(b"")
    node = CatSurfBbregDetectContrast()
    node.inputs.in_file = str(f)
    node._run_interface(_fake_runtime(tmp_path))
    assert node._list_outputs()["contrast"] == 0


def test_vol_sanlm_default_output_name(tmp_path, monkeypatch):
    """VolSanlm derives a sanlm_ prefixed output when out_file is unset."""
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)
    f = tmp_path / "sub-01_T1w.nii.gz"
    f.write_bytes(b"")
    node = CatSurfVolSanlm()
    node.inputs.in_file = str(f)
    node._run_interface(_fake_runtime(tmp_path))
    out = node._list_outputs()["out_file"]
    assert "sanlm_" in out
