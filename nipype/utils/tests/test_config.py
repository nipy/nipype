# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, division, unicode_literals, absolute_import
import os
import sys
import pytest
from nipype import config
from mock import MagicMock
from builtins import object

try:
    import xvfbwrapper
    has_Xvfb = True
except ImportError:
    has_Xvfb = False

# Define mocks for xvfbwrapper. Do not forget the spec to ensure that
# hasattr() checks return False with missing attributes.
xvfbpatch = MagicMock(spec=['Xvfb'])
xvfbpatch.Xvfb.return_value = MagicMock(spec=['new_display', 'start', 'stop'],
                                        new_display=2010)

# Mock the legacy xvfbwrapper.Xvfb class (changed display attribute name)
xvfbpatch_old = MagicMock(spec=['Xvfb'])
xvfbpatch_old.Xvfb.return_value = MagicMock(spec=['vdisplay_num', 'start', 'stop'],
                                            vdisplay_num=2010)


@pytest.mark.parametrize('dispnum', range(5))
def test_display_config(monkeypatch, dispnum):
    """Check that the display_variable option is used ($DISPLAY not set)"""
    config._display = None
    dispstr = ':%d' % dispnum
    config.set('execution', 'display_variable', dispstr)
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    assert config.get_display() == config.get('execution', 'display_variable')
    # Test that it was correctly cached
    assert config.get_display() == config.get('execution', 'display_variable')


@pytest.mark.parametrize('dispnum', range(5))
def test_display_system(monkeypatch, dispnum):
    """Check that when only a $DISPLAY is defined, it is used"""
    config._display = None
    config._config.remove_option('execution', 'display_variable')
    dispstr = ':%d' % dispnum
    monkeypatch.setitem(os.environ, 'DISPLAY', dispstr)
    assert config.get_display() == dispstr
    # Test that it was correctly cached
    assert config.get_display() == dispstr


def test_display_config_and_system(monkeypatch):
    """Check that when only both config and $DISPLAY are defined, the config takes precedence"""
    config._display = None
    dispstr = ':10'
    config.set('execution', 'display_variable', dispstr)
    monkeypatch.setitem(os.environ, 'DISPLAY', ':0')
    assert config.get_display() == dispstr
    # Test that it was correctly cached
    assert config.get_display() == dispstr


def test_display_noconfig_nosystem_patched(monkeypatch):
    """Check that when no $DISPLAY nor option are specified, a virtual Xvfb is used"""
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', xvfbpatch)
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ':2010'


def test_display_empty_patched(monkeypatch):
    """
    Check that when $DISPLAY is empty string and no option is specified,
    a virtual Xvfb is used
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.setitem(os.environ, 'DISPLAY', '')
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', xvfbpatch)
    assert config.get_display() == ':2010'
    # Test that it was correctly cached
    assert config.get_display() == ':2010'


def test_display_noconfig_nosystem_patched_oldxvfbwrapper(monkeypatch):
    """
    Check that when no $DISPLAY nor option are specified,
    a virtual Xvfb is used (with a legacy version of xvfbwrapper).
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', xvfbpatch_old)
    assert config.get_display() == ":2010"
    # Test that it was correctly cached
    assert config.get_display() == ':2010'


def test_display_empty_patched_oldxvfbwrapper(monkeypatch):
    """
    Check that when $DISPLAY is empty string and no option is specified,
    a virtual Xvfb is used (with a legacy version of xvfbwrapper).
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.setitem(os.environ, 'DISPLAY', '')
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', xvfbpatch_old)
    assert config.get_display() == ':2010'
    # Test that it was correctly cached
    assert config.get_display() == ':2010'


def test_display_noconfig_nosystem_notinstalled(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is not installed
    but necessary (no config and $DISPLAY unset)
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', None)
    with pytest.raises(RuntimeError):
        config.get_display()


def test_display_empty_notinstalled(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is not installed
    but necessary (no config and $DISPLAY empty)
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.setitem(os.environ, 'DISPLAY', '')
    monkeypatch.setitem(sys.modules, 'xvfbwrapper', None)
    with pytest.raises(RuntimeError):
        config.get_display()


@pytest.mark.skipif(not has_Xvfb, reason='xvfbwrapper not installed')
def test_display_noconfig_nosystem_installed(monkeypatch):
    """
    Check that actually uses xvfbwrapper when installed (not mocked)
    and necessary (no config and $DISPLAY unset)
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    newdisp = config.get_display()
    assert int(newdisp.split(':')[-1]) > 1000
    # Test that it was correctly cached
    assert config.get_display() == newdisp


@pytest.mark.skipif(not has_Xvfb, reason='xvfbwrapper not installed')
def test_display_empty_installed(monkeypatch):
    """
    Check that actually uses xvfbwrapper when installed (not mocked)
    and necessary (no config and $DISPLAY empty)
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.setitem(os.environ, 'DISPLAY', '')
    newdisp = config.get_display()
    assert int(newdisp.split(':')[-1]) > 1000
    # Test that it was correctly cached
    assert config.get_display() == newdisp


def test_display_empty_macosx(monkeypatch):
    """
    Check that an exception is raised if xvfbwrapper is necessary
    (no config and $DISPLAY unset) but platform is OSX. See
    https://github.com/nipy/nipype/issues/1400
    """
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', '')

    monkeypatch.setattr(sys, 'platform', 'darwin')
    with pytest.raises(RuntimeError):
        config.get_display()
