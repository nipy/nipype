# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine workflows module
"""
import pytest
import networkx as nx

from ... import engine as pe
from ....interfaces import utility as niu
from .test_base import EngineTestInterface


def test_init():
    with pytest.raises(TypeError):
        pe.Workflow()
    pipe = pe.Workflow(name='pipe')
    assert type(pipe._graph) == nx.DiGraph


def test_connect():
    pipe = pe.Workflow(name='pipe')
    mod2 = pe.Node(EngineTestInterface(), name='mod2')
    mod1 = pe.Node(EngineTestInterface(), name='mod1')
    pipe.connect([(mod1, mod2, [('output1', 'input1')])])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()
    assert pipe._graph.get_edge_data(mod1, mod2) == {
        'connect': [('output1', 'input1')]
    }


def test_add_nodes():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(EngineTestInterface(), name='mod1')
    mod2 = pe.Node(EngineTestInterface(), name='mod2')
    pipe.add_nodes([mod1, mod2])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()


def test_disconnect():
    a = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='a')
    b = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a, 'a', b, 'a')
    flow1.disconnect(a, 'a', b, 'a')
    assert list(flow1._graph.edges()) == []


def test_workflow_add():
    n1 = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='n1')
    n2 = pe.Node(niu.IdentityInterface(fields=['c', 'd']), name='n2')
    n3 = pe.Node(niu.IdentityInterface(fields=['c', 'd']), name='n1')
    w1 = pe.Workflow(name='test')
    w1.connect(n1, 'a', n2, 'c')
    for node in [n1, n2, n3]:
        with pytest.raises(IOError):
            w1.add_nodes([node])
    with pytest.raises(IOError):
        w1.connect([(w1, n2, [('n1.a', 'd')])])


def test_doubleconnect():
    a = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='a')
    b = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a, 'a', b, 'a')
    x = lambda: flow1.connect(a, 'b', b, 'a')
    with pytest.raises(Exception) as excinfo:
        x()
    assert "Trying to connect" in str(excinfo.value)

    c = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='c')
    flow1 = pe.Workflow(name='test2')
    x = lambda: flow1.connect([(a, c, [('b', 'b')]), (b, c, [('a', 'b')])])
    with pytest.raises(Exception) as excinfo:
        x()
    assert "Trying to connect" in str(excinfo.value)


def test_duplicate_node_check():

    wf = pe.Workflow(name="testidentity")

    original_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

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
        (selector1, selector2, [("out", "inlist")]),
        (selector2, selector3, [("out", "inlist")]),
        (selector3, selector4, [("out", "inlist")]),
    ]

    with pytest.raises(IOError) as excinfo:
        wf.connect(wf_connections)
    assert 'Duplicate node name "selector3" found.' == str(excinfo.value)
