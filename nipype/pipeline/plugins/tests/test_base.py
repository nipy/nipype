# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str

# Py2 compat: http://python-future.org/compatible_idioms.html#collections-counter-and-ordereddict
from future import standard_library
standard_library.install_aliases()

from copy import deepcopy
import numpy as np
import scipy.sparse as ssp
import re

from .. import base as pb


def test_scipy_sparse():
    foo = ssp.lil_matrix(np.eye(3, k=1))
    goo = foo.getrowview(0)
    goo[goo.nonzero()] = 0
    assert foo[0, 1] == 0


def test_report_crash(tmpdir):
    import os
    os.chdir(str(tmpdir))

    from .... import Node, Function, config
    def func(arg1):
        return arg1
    node1 = Node(Function(['arg1'], ['out'], function=func), name='node1')
    node1.config = deepcopy(config._sections)
    node1.config['execution']['crashdump_dir'] = os.getcwd()
    node1.base_dir = os.getcwd()

    from socket import gethostname
    from traceback import format_exception
    import sys
    try:
        traceback = None
        result = node1._interface.run()
    except TypeError as e:
        etype, eval, etr = sys.exc_info()
        traceback = format_exception(etype, eval, etr)
    actual_crashfile = pb.report_crash(node1, traceback, gethostname())
    expected_crashfile = re.compile('.*/crash-.*-node1-[0-9a-f\-]*.pklz')
    assert expected_crashfile.match(actual_crashfile).group() == actual_crashfile
