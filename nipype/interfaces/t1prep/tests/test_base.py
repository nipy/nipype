# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.base."""

import sys
import types

import pytest

from nipype.interfaces.t1prep import base as t1prep_base
from nipype.interfaces.t1prep.base import Info, T1PrepCommand, import_cat_surf


@pytest.fixture(autouse=True)
def _reset_version_cache():
    """Info caches the version on the class; reset around each test."""
    saved = Info._version
    Info._version = None
    yield
    Info._version = saved


def test_info_version_none_when_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "t1prep", None)  # force ImportError
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "t1prep" or name.startswith("t1prep."):
            raise ImportError(name)
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert Info.version() is None


def test_info_version_reads_dunder(monkeypatch):
    fake = types.ModuleType("t1prep")
    fake.__version__ = "9.9.9"
    monkeypatch.setitem(sys.modules, "t1prep", fake)
    assert Info.version() == "9.9.9"


def test_info_version_missing_dunder(monkeypatch):
    fake = types.ModuleType("t1prep")  # no __version__
    monkeypatch.setitem(sys.modules, "t1prep", fake)
    assert Info.version() is None


def test_info_version_cached():
    """A pre-populated cache is returned without re-importing t1prep."""
    Info._version = "cached-1.0"
    assert Info.version() == "cached-1.0"


def test_parse_version_identity():
    assert Info.parse_version("1.2.3") == "1.2.3"


def test_import_cat_surf_prefers_t1prep(monkeypatch):
    fake_pkg = types.ModuleType("t1prep")
    fake_cs = types.ModuleType("t1prep.cat_surf")
    fake_pkg.cat_surf = fake_cs
    monkeypatch.setitem(sys.modules, "t1prep", fake_pkg)
    monkeypatch.setitem(sys.modules, "t1prep.cat_surf", fake_cs)
    assert import_cat_surf() is fake_cs


def test_t1prepcommand_cmd_requires_module():
    """A subclass without _module must raise on cmd access."""
    cmd = T1PrepCommand()
    with pytest.raises(NotImplementedError):
        cmd.cmd


def test_t1prepcommand_version_delegates_to_info(monkeypatch):
    fake = types.ModuleType("t1prep")
    fake.__version__ = "1.0.0"
    monkeypatch.setitem(sys.modules, "t1prep", fake)
    cmd = T1PrepCommand()
    assert cmd.version == "1.0.0"


def test_t1prepcommand_cmd_with_module():
    class _Dummy(T1PrepCommand):
        _module = "t1prep.dummy"

    assert _Dummy().cmd == f"{sys.executable} -m t1prep.dummy"
