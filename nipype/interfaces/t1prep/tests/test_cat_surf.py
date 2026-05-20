# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.cat_surf."""

import pytest

from nipype.interfaces.t1prep import (
    CatSurfReadSurface,
    CatSurfSmoothHeatkernel,
    CatSurfVolMarchingCubes,
)
from nipype.interfaces.t1prep import base as t1prep_base


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


def test_import_cat_surf_returns_none_when_missing(monkeypatch):
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


def test_CatSurfReadSurface_trait_validation(tmp_path):
    """Non-existent in_file should fail validation."""
    from nipype.interfaces.base import traits

    node = CatSurfReadSurface()
    with pytest.raises(traits.TraitError):
        node.inputs.in_file = "/nonexistent/path/that/does/not/exist.gii"


def test_CatSurfSmoothHeatkernel_default_fwhm():
    node = CatSurfSmoothHeatkernel()
    # fwhm has usedefault=True with default 20.0
    assert node.inputs.fwhm == 20.0


def test_CatSurfVolMarchingCubes_input_mandatory(tmp_path):
    """Missing mandatory inputs raises at _check_mandatory_inputs()."""
    node = CatSurfVolMarchingCubes()
    with pytest.raises(ValueError):
        node._check_mandatory_inputs()


# ---------------------------------------------------------------------------
# Dispatch coverage: run every CatSurf* wrapper against a fake cat_surf module
# ---------------------------------------------------------------------------

import inspect
import types

from nipype.interfaces.base import BaseInterface
from nipype.interfaces.t1prep import cat_surf as cat_surf_mod


def _fake_cat_surf():
    """A stand-in for the cat_surf C-extension module.

    Each function returns a value of the same arity the wrappers unpack, so
    every ``_run_interface`` body executes without the native library.
    """
    ns = types.SimpleNamespace()
    ns.read_surface = lambda *a, **k: ("V", "F")
    ns.write_surface = lambda *a, **k: None
    ns.read_values = lambda *a, **k: "VALS"
    ns.write_values = lambda *a, **k: None
    ns.get_area = lambda *a, **k: ("AREA", 12.0)
    ns.get_area_normalized = lambda *a, **k: "AREA_NORM"
    ns.euler_characteristic = lambda *a, **k: (2, 0)
    ns.sphere_radius = lambda *a, **k: 100.0
    ns.hausdorff_distance = lambda *a, **k: 1.5
    ns.point_distance = lambda *a, **k: "DISTS"
    ns.point_distance_mean = lambda *a, **k: ("DISTS", 2.0)
    ns.count_intersections = lambda *a, **k: 0
    ns.remove_intersections = lambda *a, **k: ("V", "F")
    ns.reduce_mesh = lambda *a, **k: ("V", "F")
    ns.surf_deform = lambda *a, **k: ("V", "F")
    ns.surf_to_pial_white = lambda *a, **k: ("PV", "PF", "WV", "WF")
    ns.surf_to_sphere = lambda *a, **k: ("SV", "SF")
    ns.surf_warp = lambda *a, **k: None
    ns.surf_average = lambda *a, **k: None
    ns.resample_to_sphere = lambda *a, **k: None
    ns.resample_annot = lambda *a, **k: None
    ns.smooth_heatkernel = lambda *a, **k: "SMOOTH"
    ns.smooth_mesh = lambda *a, **k: ("V", "F")
    ns.smoothed_curvatures = lambda *a, **k: "CURV"
    ns.surf_curvature = lambda *a, **k: "CURV"
    ns.sulcus_depth = lambda *a, **k: "DEPTH"
    ns.correct_thickness_folding = lambda *a, **k: "THICK"
    ns.vol_sanlm = lambda *a, **k: "VOL"
    ns.vol_marching_cubes = lambda *a, **k: ("V", "F")
    ns.vol2surf = lambda *a, **k: ("VALS", "GRID")
    ns.vol_thickness_pbt = lambda *a, **k: ("GMT", "PPM", "DCSF", "DWM")
    ns.vol_amap = lambda *a, **k: ("PROB", "LAB", "MEANS")
    ns.vol_blood_vessel_correction = lambda *a, **k: "VOL"
    ns.bbreg = lambda *a, **k: "RESULT"
    ns.bbreg_detect_contrast = lambda *a, **k: "t1"
    ns.volume_register_nmi = lambda *a, **k: None
    ns.volume_register_robust = lambda *a, **k: None
    return ns


def _catsurf_interfaces():
    out = []
    for name, obj in vars(cat_surf_mod).items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseInterface)
            and name.startswith("CatSurf")
        ):
            out.append(obj)
    return out


def _set_mandatory_inputs(node, tmp_path):
    """Set every mandatory input to a type-appropriate dummy value."""
    spec = node.input_spec()
    counter = 0
    for name, trait in spec.traits().items():
        if name in ("trait_added", "trait_modified"):
            continue
        if not trait.mandatory:
            continue
        ttype = type(trait.trait_type).__name__
        counter += 1
        if ttype == "File":
            f = tmp_path / f"{node.__class__.__name__}_{name}.dat"
            f.write_bytes(b"")
            setattr(node.inputs, name, str(f))
        elif ttype == "Directory":
            d = tmp_path / f"{node.__class__.__name__}_{name}_dir"
            d.mkdir(exist_ok=True)
            setattr(node.inputs, name, str(d))
        elif ttype in ("List", "InputMultiPath"):
            f = tmp_path / f"{node.__class__.__name__}_{name}_item.dat"
            f.write_bytes(b"")
            setattr(node.inputs, name, [str(f)])
        elif ttype == "Int":
            setattr(node.inputs, name, 1)
        elif ttype == "Float":
            setattr(node.inputs, name, 1.0)
        elif ttype == "Bool":
            setattr(node.inputs, name, True)
        elif ttype == "Enum":
            setattr(node.inputs, name, trait.trait_type.values[0])
        else:  # Any, Str, etc.
            setattr(node.inputs, name, "dummy")
    return counter


@pytest.mark.parametrize(
    "iface", _catsurf_interfaces(), ids=lambda c: c.__name__
)
def test_catsurf_dispatch_with_fake_module(iface, tmp_path, monkeypatch):
    """Each wrapper dispatches to cat_surf and maps outputs without the C lib."""
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)
    node = iface()
    _set_mandatory_inputs(node, tmp_path)
    node._run_interface(None)
    outputs = node._list_outputs()
    assert isinstance(outputs, dict)


def test_catsurf_interfaces_discovered():
    """Guard against the discovery helper silently finding nothing."""
    assert len(_catsurf_interfaces()) >= 36


def test_euler_characteristic_scalar_result(monkeypatch):
    """The scalar (non-tuple) return path computes defects from the Euler no."""
    from nipype.interfaces.t1prep import CatSurfEulerCharacteristic

    fake = _fake_cat_surf()
    fake.euler_characteristic = lambda *a, **k: 0  # scalar -> 1 defect
    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", lambda: fake)
    node = CatSurfEulerCharacteristic()
    node.inputs.vertices = "V"
    node.inputs.faces = "F"
    node._run_interface(None)
    outs = node._list_outputs()
    assert outs["euler_number"] == 0
    assert outs["defects"] == 1


def test_optional_input_branches(tmp_path, monkeypatch):
    """Exercise the isdefined() branches for optional inputs."""
    from nipype.interfaces.t1prep import (
        CatSurfGetAreaNormalized,
        CatSurfResampleToSphere,
        CatSurfBbreg,
        CatSurfVolumeRegisterNmi,
        CatSurfVolumeRegisterRobust,
    )

    monkeypatch.setattr(cat_surf_mod, "_import_cat_surf", _fake_cat_surf)

    def mkfile(name):
        f = tmp_path / name
        f.write_bytes(b"")
        return str(f)

    gan = CatSurfGetAreaNormalized()
    gan.inputs.vertices = "V"
    gan.inputs.faces = "F"
    gan.inputs.reference_area = 1000.0
    gan._run_interface(None)
    gan._list_outputs()

    rts = CatSurfResampleToSphere()
    rts.inputs.source_surface_file = mkfile("src.gii")
    rts.inputs.source_sphere_file = mkfile("srcsph.gii")
    rts.inputs.target_sphere_file = mkfile("tgtsph.gii")
    rts.inputs.output_surface_file = str(tmp_path / "out.gii")
    rts.inputs.input_values_file = mkfile("vals.in")
    rts.inputs.output_values_file = str(tmp_path / "vals.out")
    rts._run_interface(None)
    outs = rts._list_outputs()
    assert "output_values_file" in outs

    bb = CatSurfBbreg()
    bb.inputs.moving_file = mkfile("mov.nii")
    bb.inputs.fixed_file = mkfile("fix.nii")
    bb.inputs.out_matrix_file = str(tmp_path / "bb.mat")
    bb.inputs.dof = 6
    bb._run_interface(None)
    outs = bb._list_outputs()
    assert "out_matrix_file" in outs

    for cls in (CatSurfVolumeRegisterNmi, CatSurfVolumeRegisterRobust):
        node = cls()
        node.inputs.moving_file = mkfile(f"{cls.__name__}_mov.nii")
        node.inputs.fixed_file = mkfile(f"{cls.__name__}_fix.nii")
        node.inputs.out_matrix_file = str(tmp_path / f"{cls.__name__}.mat")
        node.inputs.dof = 12
        node._run_interface(None)
        node._list_outputs()
