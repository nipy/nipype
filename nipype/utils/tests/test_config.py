# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import sys
import pytest
from nipype import config
from unittest.mock import MagicMock

try:
    import xvfbwrapper

    has_Xvfb = True
except ImportError:
    has_Xvfb = False

# Define mocks for xvfbwrapper. Do not forget the spec to ensure that
# hasattr() checks return False with missing attributes.
xvfbpatch = MagicMock(spec=["Xvfb"])
xvfbpatch.Xvfb.return_value = MagicMock(
    spec=["new_display", "start", "stop"], new_display=2010
)

# Mock the legacy xvfbwrapper.Xvfb class (changed display attribute name)
xvfbpatch_old = MagicMock(spec=["Xvfb"])
xvfbpatch_old.Xvfb.return_value = MagicMock(
    spec=["vdisplay_num", "start", "stop"], vdisplay_num=2010
)


@pytest.mark.parametrize("dispvar", [":12", "localhost:12", "localhost:12.1"])
def test_display_parse(monkeypatch, dispvar):
    """Check that when $DISPLAY is defined, the display is correctly parsed"""
    config._display = None
    config._config.remove_option("execution", "display_variable")
    monkeypatch.setenv("DISPLAY", dispvar)
    assert config.get_display() == ":12"
    # Test that it was correctly cached
    assert config.get_display() == ":12"


@pytest.mark.parametrize("dispnum", range(5))
def test_display_config(monkeypatch, dispnum):
    """Check that the display_variable option is used ($DISPLAY not set)"""
    config._display = None
    dispstr = ":%d" % dispnum
    config.set("execution", "display_variable", dispstr)
    monkeypatch.delitem(os.environ, "DISPLAY", raising=False)
    assert config.get_display() == config.get("execution", "display_variable")
    # Test that it was correctly cached
    assert config.get_display() == config.get("execution", "display_variable")


@pytest.mark.parametrize("dispnum", range(5))
def test_display_system(monkeypatch, dispnum):
    """Check that when only a $DISPLAY is defined, it is used"""
    config._display = None
    config._config.remove_option("execution", "display_variable")
    dispstr = ":%d" % dispnum
    monkeypatch.setenv("DISPLAY", dispstr)
    assert config.get_display() == dispstr
    # Test that it was correctly cached
    assert config.get_display() == dispstr


def test_display_config_and_system(monkeypatch):
    """Check that when only both config and $DISPLAY are defined, the config
    takes precedence"""
    config._display = None
    dispstr = ":10"
    config.set("execution", "display_variable", dispstr)
    monkeypatch.setenv("DISPLAY", ":0")
    assert config.get_display() == dispstr
    # Test that it was correctly cached
    assert config.get_display() == dispstr


def test_display_noconfig_nosystem_patched(monkeypatch):
    """Check that when no $DISPLAY nor option are specified, a virtual Xvfb is
    used"""
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.delitem(os.environ, "DISPLAY", raising=False)
    monkeypatch.setitem(sys.modules, "xvfbwrapper", xvfbpatch)
    monkeypatch.setattr(sys, "platform", value="linux")
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ":2010"

    # Check that raises in Mac
    config._display = None
    monkeypatch.setattr(sys, "platform", value="darwin")
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_empty_patched(monkeypatch):
    """
    Check that when $DISPLAY is empty string and no option is specified,
    a virtual Xvfb is used
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.setenv("DISPLAY", "")
    monkeypatch.setitem(sys.modules, "xvfbwrapper", xvfbpatch)
    monkeypatch.setattr(sys, "platform", value="linux")
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ":2010"

    # Check that raises in Mac
    config._display = None
    monkeypatch.setattr(sys, "platform", value="darwin")
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_noconfig_nosystem_patched_oldxvfbwrapper(monkeypatch):
    """
    Check that when no $DISPLAY nor option are specified,
    a virtual Xvfb is used (with a legacy version of xvfbwrapper).
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.delitem(os.environ, "DISPLAY", raising=False)
    monkeypatch.setitem(sys.modules, "xvfbwrapper", xvfbpatch_old)
    monkeypatch.setattr(sys, "platform", value="linux")
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ":2010"

    # Check that raises in Mac
    config._display = None
    monkeypatch.setattr(sys, "platform", value="darwin")
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_empty_patched_oldxvfbwrapper(monkeypatch):
    """
    Check that when $DISPLAY is empty string and no option is specified,
    a virtual Xvfb is used (with a legacy version of xvfbwrapper).
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.setenv("DISPLAY", "")
    monkeypatch.setitem(sys.modules, "xvfbwrapper", xvfbpatch_old)
    monkeypatch.setattr(sys, "platform", value="linux")
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ":2010"

    # Check that raises in Mac
    config._display = None
    monkeypatch.setattr(sys, "platform", value="darwin")
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_noconfig_nosystem_notinstalled(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is not installed
    but necessary (no config and $DISPLAY unset)
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setitem(sys.modules, "xvfbwrapper", None)
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_empty_notinstalled(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is not installed
    but necessary (no config and $DISPLAY empty)
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.setenv("DISPLAY", "")
    monkeypatch.setitem(sys.modules, "xvfbwrapper", None)
    with pytest.raises(RuntimeError):
        config.get_display()


@pytest.mark.skipif(not has_Xvfb, reason="xvfbwrapper not installed")
@pytest.mark.skipif("darwin" in sys.platform, reason="macosx requires root for Xvfb")
def test_display_noconfig_nosystem_installed(monkeypatch):
    """
    Check that actually uses xvfbwrapper when installed (not mocked)
    and necessary (no config and $DISPLAY unset)
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.delenv("DISPLAY", raising=False)
    newdisp = config.get_display()
    assert int(newdisp.split(":")[-1]) > 1000
    # Test that it was correctly cached
    assert config.get_display() == newdisp


@pytest.mark.skipif(not has_Xvfb, reason="xvfbwrapper not installed")
@pytest.mark.skipif("darwin" in sys.platform, reason="macosx requires root for Xvfb")
def test_display_empty_installed(monkeypatch):
    """
    Check that actually uses xvfbwrapper when installed (not mocked)
    and necessary (no config and $DISPLAY empty)
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.setenv("DISPLAY", "")
    newdisp = config.get_display()
    assert int(newdisp.split(":")[-1]) > 1000
    # Test that it was correctly cached
    assert config.get_display() == newdisp


def test_display_empty_macosx(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is necessary
    (no config and $DISPLAY unset) but platform is OSX. See
    https://github.com/nipy/nipype/issues/1400
    """
    config._display = None
    if config.has_option("execution", "display_variable"):
        config._config.remove_option("execution", "display_variable")
    monkeypatch.delenv("DISPLAY", "")

    monkeypatch.setattr(sys, "platform", "darwin")
    with pytest.raises(RuntimeError):
        config.get_display()


def test_cwd_cached(tmpdir):
    """Check that changing dirs does not change nipype's cwd"""
    oldcwd = config.cwd
    tmpdir.chdir()
    assert config.cwd == oldcwd


def test_debug_mode():
    from ... import logging

    sofc_config = config.get("execution", "stop_on_first_crash")
    ruo_config = config.get("execution", "remove_unnecessary_outputs")
    ki_config = config.get("execution", "keep_inputs")
    wf_config = config.get("logging", "workflow_level")
    if_config = config.get("logging", "interface_level")
    ut_config = config.get("logging", "utils_level")

    wf_level = logging.getLogger("nipype.workflow").level
    if_level = logging.getLogger("nipype.interface").level
    ut_level = logging.getLogger("nipype.utils").level

    config.enable_debug_mode()

    # Check config is updated and logging levels, too
    assert config.get("execution", "stop_on_first_crash") == "true"
    assert config.get("execution", "remove_unnecessary_outputs") == "false"
    assert config.get("execution", "keep_inputs") == "true"
    assert config.get("logging", "workflow_level") == "DEBUG"
    assert config.get("logging", "interface_level") == "DEBUG"
    assert config.get("logging", "utils_level") == "DEBUG"

    assert logging.getLogger("nipype.workflow").level == 10
    assert logging.getLogger("nipype.interface").level == 10
    assert logging.getLogger("nipype.utils").level == 10

    # Restore config and levels
    config.set("execution", "stop_on_first_crash", sofc_config)
    config.set("execution", "remove_unnecessary_outputs", ruo_config)
    config.set("execution", "keep_inputs", ki_config)
    config.set("logging", "workflow_level", wf_config)
    config.set("logging", "interface_level", if_config)
    config.set("logging", "utils_level", ut_config)
    logging.update_logging(config)

    assert config.get("execution", "stop_on_first_crash") == sofc_config
    assert config.get("execution", "remove_unnecessary_outputs") == ruo_config
    assert config.get("execution", "keep_inputs") == ki_config
    assert config.get("logging", "workflow_level") == wf_config
    assert config.get("logging", "interface_level") == if_config
    assert config.get("logging", "utils_level") == ut_config

    assert logging.getLogger("nipype.workflow").level == wf_level
    assert logging.getLogger("nipype.interface").level == if_level
    assert logging.getLogger("nipype.utils").level == ut_level
