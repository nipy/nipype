# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
from distutils.version import LooseVersion

from .info import (LONG_DESCRIPTION as __doc__, URL as __url__, STATUS as
                   __status__, __version__)
from .utils.config import NipypeConfig
from .utils.logger import Logging
from .refs import due
from .pkg_info import get_pkg_info as _get_pkg_info

try:
    import faulthandler
    faulthandler.enable()
except (ImportError, IOError) as e:
    pass

config = NipypeConfig()
logging = Logging(config)


class NipypeTester(object):
    def __call__(self, doctests=True):
        try:
            import pytest
        except:
            raise RuntimeError(
                'py.test not installed, run: pip install pytest')
        params = {'args': []}
        if doctests:
            params['args'].append('--doctest-modules')
        nipype_path = os.path.dirname(__file__)
        params['args'].extend(
            ['-x', '--ignore={}/external'.format(nipype_path), nipype_path])
        pytest.main(**params)


test = NipypeTester()


def get_info():
    """Returns package information"""
    return _get_pkg_info(os.path.dirname(__file__))


from .pipeline import Node, MapNode, JoinNode, Workflow
from .interfaces import (DataGrabber, DataSink, SelectFiles, IdentityInterface,
                         Rename, Function, Select, Merge)
