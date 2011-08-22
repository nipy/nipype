# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""
import os
from copy import deepcopy
from tempfile import mkdtemp
from shutil import rmtree
from nose import with_setup

import networkx as nx

from nipype.testing import (assert_raises, assert_equal, assert_true,
                            assert_false, skipif)
import nipype.interfaces.base as nib
from nipype.utils.filemanip import cleandir
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

def test_identitynode_removal():

    def test_function(arg1, arg2, arg3):
        import numpy as np
        return (np.array(arg1)+arg2+arg3).tolist()

    wf = pe.Workflow(name="testidentity")

    n1 = pe.Node(niu.IdentityInterface(fields=['a','b']), name='src')
    n1.iterables = ('b', [0,1,2,3])
    n1.inputs.a = [0,1,2,3]

    n2 = pe.Node(niu.Select(), name='selector')
    wf.connect(n1, ('a', test_function, 1, -1), n2, 'inlist')
    wf.connect(n1, 'b', n2, 'index')

    n3 = pe.Node(niu.IdentityInterface(fields=['c','d']), name='passer')
    n3.inputs.c = [1,2,3,4]
    wf.connect(n2, 'out', n3, 'd')

    n4 = pe.Node(niu.Select(), name='selector2')
    wf.connect(n3, ('c', test_function, 1, -1), n4, 'inlist')
    wf.connect(n3, 'd', n4, 'index')

    fg = wf._create_flat_graph()
    wf._set_needed_outputs(fg)
    eg = pe.generate_expanded_graph(deepcopy(fg))
    yield assert_equal, len(eg.nodes()), 8
