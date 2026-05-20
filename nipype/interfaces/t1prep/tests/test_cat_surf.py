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
