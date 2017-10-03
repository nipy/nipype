# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, division, unicode_literals, absolute_import
import os
import pytest
from nipype import config

@pytest.mark.parametrize('dispnum', range(5))
def test_display_config(monkeypatch, dispnum):
    """Check that the display_variable option is used"""
    config._display = None
    dispstr = ':%d' % dispnum
    config.set('execution', 'display_variable', dispstr)
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    assert config.get_display() == config.get('execution', 'display_variable')

@pytest.mark.parametrize('dispnum', range(5))
def test_display_system(monkeypatch, dispnum):
    """Check that when only a $DISPLAY is defined, it is used"""
    config._display = None
    config._config.remove_option('execution', 'display_variable')
    dispstr = ':%d' % dispnum
    monkeypatch.setitem(os.environ, 'DISPLAY', dispstr)
    assert config.get_display() == dispstr

def test_display_config_and_system(monkeypatch):
    """Check that when only both config and $DISPLAY are defined, the config takes precedence"""
    config._display = None
    dispstr = ':10'
    config.set('execution', 'display_variable', dispstr)
    monkeypatch.setitem(os.environ, 'DISPLAY', dispstr)
    assert config.get_display() == dispstr

def test_display_noconfig_nosystem(monkeypatch):
    """Check that when no display is specified, a virtual Xvfb is used"""
    config._display = None
    if config.has_option('execution', 'display_variable'):
        config._config.remove_option('execution', 'display_variable')
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    assert int(config.get_display().split(':')[-1]) > 80