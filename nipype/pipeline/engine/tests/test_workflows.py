# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine workflows module
"""
from glob import glob
import os
from shutil import rmtree
from itertools import product
import pytest
import networkx as nx

from .... import config
from ....interfaces import utility as niu
from ... import engine as pe
from .test_base import EngineTestInterface
from .test_utils import UtilsTestInterface


def test_init():
    with pytest.raises(TypeError):
        pe.Workflow()
    pipe = pe.Workflow(name="pipe")
    assert type(pipe._graph) == nx.DiGraph


def test_connect():
    pipe = pe.Workflow(name="pipe")
    mod2 = pe.Node(EngineTestInterface(), name="mod2")
    mod1 = pe.Node(EngineTestInterface(), name="mod1")
    pipe.connect([(mod1, mod2, [("output1", "input1")])])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()
    assert pipe._graph.get_edge_data(mod1, mod2) == {"connect": [("output1", "input1")]}


def test_add_nodes():
    pipe = pe.Workflow(name="pipe")
    mod1 = pe.Node(EngineTestInterface(), name="mod1")
    mod2 = pe.Node(EngineTestInterface(), name="mod2")
    pipe.add_nodes([mod1, mod2])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()


def test_disconnect():
    a = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="a")
    b = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="b")
    flow1 = pe.Workflow(name="test")
    flow1.connect(a, "a", b, "a")
    flow1.disconnect(a, "a", b, "a")
    assert list(flow1._graph.edges()) == []


def test_workflow_add():
    n1 = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="n1")
    n2 = pe.Node(niu.IdentityInterface(fields=["c", "d"]), name="n2")
    n3 = pe.Node(niu.IdentityInterface(fields=["c", "d"]), name="n1")
    w1 = pe.Workflow(name="test")
    w1.connect(n1, "a", n2, "c")
    for node in [n1, n2, n3]:
        with pytest.raises(IOError):
            w1.add_nodes([node])
    with pytest.raises(IOError):
        w1.connect([(w1, n2, [("n1.a", "d")])])


def test_doubleconnect():
    a = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="a")
    b = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="b")
    flow1 = pe.Workflow(name="test")
    flow1.connect(a, "a", b, "a")
    with pytest.raises(Exception) as excinfo:
        flow1.connect(a, "b", b, "a")
    assert "Trying to connect" in str(excinfo.value)

    c = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="c")
    flow1 = pe.Workflow(name="test2")
    with pytest.raises(Exception) as excinfo:
        flow1.connect([(a, c, [("b", "b")]), (b, c, [("a", "b")])])
    assert "Trying to connect" in str(excinfo.value)


def test_nested_workflow_doubleconnect():
    # double input with nested workflows
    a = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="a")
    b = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="b")
    c = pe.Node(niu.IdentityInterface(fields=["a", "b"]), name="c")
    flow1 = pe.Workflow(name="test1")
    flow2 = pe.Workflow(name="test2")
    flow3 = pe.Workflow(name="test3")
    flow1.add_nodes([b])
    flow2.connect(a, "a", flow1, "b.a")
    with pytest.raises(Exception) as excinfo:
        flow3.connect(c, "a", flow2, "test1.b.a")
    assert "Some connections were not found" in str(excinfo.value)
    flow3.connect(c, "b", flow2, "test1.b.b")


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


def _test_function(arg1):
    import os

    file1 = os.path.join(os.getcwd(), "file1.txt")
    file2 = os.path.join(os.getcwd(), "file2.txt")
    file3 = os.path.join(os.getcwd(), "file3.txt")
    file4 = os.path.join(os.getcwd(), "subdir", "file4.txt")
    os.mkdir("subdir")
    for filename in [file1, file2, file3, file4]:
        with open(filename, "wt") as fp:
            fp.write("%d" % arg1)
    return file1, file2, os.path.join(os.getcwd(), "subdir")


def _test_function2(in_file, arg):
    import os

    with open(in_file, "rt") as fp:
        in_arg = fp.read()

    file1 = os.path.join(os.getcwd(), "file1.txt")
    file2 = os.path.join(os.getcwd(), "file2.txt")
    file3 = os.path.join(os.getcwd(), "file3.txt")
    files = [file1, file2, file3]
    for filename in files:
        with open(filename, "wt") as fp:
            fp.write("%d" % arg + in_arg)
    return file1, file2, 1


def _test_function3(arg):
    return arg


@pytest.mark.parametrize(
    "plugin, remove_unnecessary_outputs, keep_inputs",
    list(product(["Linear", "MultiProc"], [False, True], [True, False])),
)
def test_outputs_removal_wf(tmpdir, plugin, remove_unnecessary_outputs, keep_inputs):
    config.set_default_config()
    config.set("execution", "remove_unnecessary_outputs", remove_unnecessary_outputs)
    config.set("execution", "keep_inputs", keep_inputs)

    n1 = pe.Node(
        niu.Function(
            output_names=["out_file1", "out_file2", "dir"], function=_test_function
        ),
        name="n1",
        base_dir=tmpdir.strpath,
    )
    n1.inputs.arg1 = 1

    n2 = pe.Node(
        niu.Function(
            output_names=["out_file1", "out_file2", "n"], function=_test_function2
        ),
        name="n2",
        base_dir=tmpdir.strpath,
    )
    n2.inputs.arg = 2

    n3 = pe.Node(
        niu.Function(output_names=["n"], function=_test_function3),
        name="n3",
        base_dir=tmpdir.strpath,
    )

    wf = pe.Workflow(name="node_rem_test" + plugin, base_dir=tmpdir.strpath)

    wf.connect(n1, "out_file1", n2, "in_file")
    wf.run(plugin=plugin)

    # Necessary outputs HAVE to exist
    assert os.path.exists(os.path.join(wf.base_dir, wf.name, n1.name, "file1.txt"))
    assert os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file1.txt"))
    assert os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file2.txt"))

    # Unnecessary outputs exist only iff remove_unnecessary_outputs is True
    assert (
        os.path.exists(os.path.join(wf.base_dir, wf.name, n1.name, "file2.txt"))
        is not remove_unnecessary_outputs
    )
    assert (
        os.path.exists(
            os.path.join(wf.base_dir, wf.name, n1.name, "subdir", "file4.txt")
        )
        is not remove_unnecessary_outputs
    )
    assert (
        os.path.exists(os.path.join(wf.base_dir, wf.name, n1.name, "file3.txt"))
        is not remove_unnecessary_outputs
    )
    assert (
        os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file3.txt"))
        is not remove_unnecessary_outputs
    )

    n4 = pe.Node(UtilsTestInterface(), name="n4", base_dir=tmpdir.strpath)
    wf.connect(n2, "out_file1", n4, "in_file")

    def pick_first(l):
        return l[0]

    wf.connect(n4, ("output1", pick_first), n3, "arg")
    rmtree(os.path.join(wf.base_dir, wf.name))
    wf.run(plugin=plugin)

    # Test necessary outputs
    assert os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file1.txt"))
    assert os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file1.txt"))

    # Test unnecessary outputs
    assert (
        os.path.exists(os.path.join(wf.base_dir, wf.name, n2.name, "file2.txt"))
        is not remove_unnecessary_outputs
    )

    # Test keep_inputs
    assert (
        os.path.exists(os.path.join(wf.base_dir, wf.name, n4.name, "file1.txt"))
        is keep_inputs
    )


def _test_function4():
    raise FileNotFoundError("Generic error")


def test_config_setting(tmpdir):
    tmpdir.chdir()
    wf = pe.Workflow("config")
    wf.base_dir = os.getcwd()

    crashdir = os.path.join(os.getcwd(), "crashdir")
    os.mkdir(crashdir)
    wf.config = {"execution": {"crashdump_dir": crashdir}}

    n1 = pe.Node(niu.Function(function=_test_function4), name="errorfunc")
    wf.add_nodes([n1])
    try:
        wf.run()
    except RuntimeError:
        pass

    fl = glob(os.path.join(crashdir, "crash*"))
    assert len(fl) == 1

    # Now test node overwrite
    crashdir2 = os.path.join(os.getcwd(), "crashdir2")
    os.mkdir(crashdir2)
    crashdir3 = os.path.join(os.getcwd(), "crashdir3")
    os.mkdir(crashdir3)
    wf.config = {"execution": {"crashdump_dir": crashdir3}}
    n1.config = {"execution": {"crashdump_dir": crashdir2}}

    try:
        wf.run()
    except RuntimeError:
        pass

    fl = glob(os.path.join(crashdir2, "crash*"))
    assert len(fl) == 1
    fl = glob(os.path.join(crashdir3, "crash*"))
    assert len(fl) == 0
