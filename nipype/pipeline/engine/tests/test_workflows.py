# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine workflows module
"""
import pytest

from ... import engine as pe
from ....interfaces import utility as niu


def test_duplicate_node_check():

    wf = pe.Workflow(name="testidentity")

    original_list = [0,1,2,3,4,5,6,7,8,9]

    selector1 = pe.Node(niu.Select(), name="selector1")
    selector1.inputs.index = original_list[:-1]
    selector1.inputs.inlist = original_list
    selector2 = pe.Node(niu.Select(), name="selector2")
    selector2.inputs.index = original_list[:-2]
    selector3 = pe.Node(niu.Select(), name="selector3")
    selector3.inputs.index = original_list[:-3]
    selector4 = pe.Node(niu.Select(), name="selector3")
    selector4.inputs.index = original_list[:-4]

    wf_connections = [
            (selector1, selector2, [("out","inlist")]),
            (selector2, selector3, [("out","inlist")]),
            (selector3, selector4, [("out","inlist")]),
            ]

    with pytest.raises(IOError) as excinfo:
        wf.connect(wf_connections)
    assert 'Duplicate node name "selector3" found.' == str(excinfo.value)
