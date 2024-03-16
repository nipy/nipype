# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from copy import deepcopy
import pytest

from .... import config
from ....interfaces import utility as niu
from ....interfaces import base as nib
from ... import engine as pe
from ..utils import merge_dict
from .test_base import EngineTestInterface
from .test_utils import UtilsTestInterface

"""
Test for order of iterables

import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

wf1 = pe.Workflow(name='wf1')
node1 = pe.Node(interface=niu.IdentityInterface(fields=['a1','b1']), name='node1')
node1.iterables = ('a1', [1,2])
wf1.add_nodes([node1])

wf2 = pe.Workflow(name='wf2')
node2 = pe.Node(interface=niu.IdentityInterface(fields=['a2','b2']), name='node2')
wf2.add_nodes([node2])
wf1.connect(node1, 'a1', wf2, 'node2.a2')

node4 = pe.Node(interface=niu.IdentityInterface(fields=['a4','b4']), name='node4')
#node4.iterables = ('a4', [5,6])
wf2.connect(node2, 'b2', node4, 'b4')

wf3 = pe.Workflow(name='wf3')
node3 = pe.Node(interface=niu.IdentityInterface(fields=['a3','b3']), name='node3')
node3.iterables = ('b3', [3,4])
wf3.add_nodes([node3])
wf1.connect(wf3, 'node3.b3', wf2, 'node2.b2')

wf1.base_dir = os.path.join(os.getcwd(),'testit')
wf1.run(inseries=True, createdirsonly=True)

wf1.write_graph(graph2use='exec')
"""
'''
import nipype.pipeline.engine as pe
import nipype.interfaces.spm as spm
import os
from io import StringIO
from nipype.utils.config import config

config.readfp(StringIO("""
[execution]
remove_unnecessary_outputs = true
"""))


segment = pe.Node(interface=spm.Segment(), name="segment")
segment.inputs.data = os.path.abspath("data/T1.nii")
segment.inputs.gm_output_type = [True, True, True]
segment.inputs.wm_output_type = [True, True, True]


smooth_gm = pe.Node(interface=spm.Smooth(), name="smooth_gm")

workflow = pe.Workflow(name="workflow_cleanup_test")
workflow.base_dir = os.path.abspath('./workflow_cleanup_test')

workflow.connect([(segment, smooth_gm, [('native_gm_image','in_files')])])

workflow.run()

#adding new node that uses one of the previously deleted outputs of segment; this should force segment to rerun
smooth_wm = pe.Node(interface=spm.Smooth(), name="smooth_wm")

workflow.connect([(segment, smooth_wm, [('native_wm_image','in_files')])])

workflow.run()

workflow.run()
'''

# Node


def test_node_init():
    with pytest.raises(TypeError):
        pe.Node()
    with pytest.raises(IOError):
        pe.Node(EngineTestInterface, name="test")


def test_node_get_output():
    mod1 = pe.Node(interface=EngineTestInterface(), name="mod1")
    mod1.inputs.input1 = 1
    mod1.run()
    assert mod1.get_output("output1") == [1, 1]
    mod1._result = None
    assert mod1.get_output("output1") == [1, 1]


def test_mapnode_iterfield_check():
    mod1 = pe.MapNode(EngineTestInterface(), iterfield=["input1"], name="mod1")
    with pytest.raises(ValueError):
        mod1._check_iterfield()
    mod1 = pe.MapNode(
        EngineTestInterface(), iterfield=["input1", "input2"], name="mod1"
    )
    mod1.inputs.input1 = [1, 2]
    mod1.inputs.input2 = 3
    with pytest.raises(ValueError):
        mod1._check_iterfield()


@pytest.mark.parametrize(
    "x_inp, f_exp",
    [
        (3, [6]),
        ([2, 3], [4, 6]),
        ((2, 3), [4, 6]),
        (range(3), [0, 2, 4]),
        ("Str", ["StrStr"]),
        (["Str1", "Str2"], ["Str1Str1", "Str2Str2"]),
    ],
)
def test_mapnode_iterfield_type(x_inp, f_exp):
    from nipype import MapNode, Function

    def double_func(x):
        return 2 * x

    double = Function(["x"], ["f_x"], double_func)

    double_node = MapNode(double, name="double", iterfield=["x"])
    double_node.inputs.x = x_inp

    res = double_node.run()
    assert res.outputs.f_x == f_exp


def test_mapnode_nested(tmpdir):
    tmpdir.chdir()
    from nipype import MapNode, Function

    def func1(in1):
        return in1 + 1

    n1 = MapNode(
        Function(input_names=["in1"], output_names=["out"], function=func1),
        iterfield=["in1"],
        nested=True,
        name="n1",
    )
    n1.inputs.in1 = [[1, [2]], 3, [4, 5]]
    n1.run()
    assert n1.get_output("out") == [[2, [3]], 4, [5, 6]]

    n2 = MapNode(
        Function(input_names=["in1"], output_names=["out"], function=func1),
        iterfield=["in1"],
        nested=False,
        name="n1",
    )
    n2.inputs.in1 = [[1, [2]], 3, [4, 5]]

    with pytest.raises(Exception) as excinfo:
        n2.run()
    assert "can only concatenate list" in str(excinfo.value)


def test_mapnode_expansion(tmpdir):
    tmpdir.chdir()
    from nipype import MapNode, Function

    def func1(in1):
        return in1 + 1

    mapnode = MapNode(
        Function(function=func1), iterfield="in1", name="mapnode", n_procs=2, mem_gb=2
    )
    mapnode.inputs.in1 = [1, 2]

    for idx, node in mapnode._make_nodes():
        for attr in ("overwrite", "run_without_submitting", "plugin_args"):
            assert getattr(node, attr) == getattr(mapnode, attr)
        for attr in ("_n_procs", "_mem_gb"):
            assert getattr(node, attr) == getattr(mapnode, attr)


def test_node_hash(tmpdir):
    from nipype.interfaces.utility import Function

    tmpdir.chdir()

    config.set_default_config()
    config.set("execution", "stop_on_first_crash", True)
    config.set("execution", "crashdump_dir", os.getcwd())

    def func1():
        return 1

    def func2(a):
        return a + 1

    n1 = pe.Node(
        Function(input_names=[], output_names=["a"], function=func1), name="n1"
    )
    n2 = pe.Node(
        Function(input_names=["a"], output_names=["b"], function=func2), name="n2"
    )
    w1 = pe.Workflow(name="test")

    def modify(x):
        return x + 1

    n1.inputs.a = 1
    w1.connect(n1, ("a", modify), n2, "a")
    w1.base_dir = os.getcwd()

    # create dummy distributed plugin class
    from nipype.pipeline.plugins.base import DistributedPluginBase

    # create a custom exception
    class EngineTestException(Exception):
        pass

    class RaiseError(DistributedPluginBase):
        def _submit_job(self, node, updatehash=False):
            raise EngineTestException(
                "Submit called - cached=%s, updated=%s" % node.is_cached()
            )

    # check if a proper exception is raised
    with pytest.raises(EngineTestException) as excinfo:
        w1.run(plugin=RaiseError())
    assert str(excinfo.value).startswith("Submit called")

    # generate outputs
    w1.run(plugin="Linear")
    # ensure plugin is being called
    config.set("execution", "local_hash_check", False)

    # rerun to ensure we have outputs
    w1.run(plugin="Linear")

    # set local check
    config.set("execution", "local_hash_check", True)
    w1 = pe.Workflow(name="test")
    w1.connect(n1, ("a", modify), n2, "a")
    w1.base_dir = os.getcwd()
    w1.run(plugin=RaiseError())


def test_outputs_removal(tmpdir):
    def test_function(arg1):
        import os

        file1 = os.path.join(os.getcwd(), "file1.txt")
        file2 = os.path.join(os.getcwd(), "file2.txt")
        with open(file1, "w") as fp:
            fp.write("%d" % arg1)
        with open(file2, "w") as fp:
            fp.write("%d" % arg1)
        return file1, file2

    n1 = pe.Node(
        niu.Function(
            input_names=["arg1"],
            output_names=["file1", "file2"],
            function=test_function,
        ),
        base_dir=tmpdir.strpath,
        name="testoutputs",
    )
    n1.inputs.arg1 = 1
    n1.config = {"execution": {"remove_unnecessary_outputs": True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    assert tmpdir.join(n1.name, "file1.txt").check()
    assert tmpdir.join(n1.name, "file1.txt").check()
    n1.needed_outputs = ["file2"]
    n1.run()
    assert not tmpdir.join(n1.name, "file1.txt").check()
    assert tmpdir.join(n1.name, "file2.txt").check()


def test_inputs_removal(tmpdir):
    file1 = tmpdir.join("file1.txt")
    file1.write("dummy_file")
    n1 = pe.Node(UtilsTestInterface(), base_dir=tmpdir.strpath, name="testinputs")
    n1.inputs.in_file = file1.strpath
    n1.config = {"execution": {"keep_inputs": True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    assert tmpdir.join(n1.name, "file1.txt").check()
    n1.inputs.in_file = file1.strpath
    n1.config = {"execution": {"keep_inputs": False}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.overwrite = True
    n1.run()
    assert not tmpdir.join(n1.name, "file1.txt").check()


def test_outputmultipath_collapse(tmpdir):
    """Test an OutputMultiPath whose initial value is ``[[x]]`` to ensure that
    it is returned as ``[x]``, regardless of how accessed."""
    select_if = niu.Select(inlist=[[1, 2, 3], [4]], index=1)
    select_nd = pe.Node(niu.Select(inlist=[[1, 2, 3], [4]], index=1), name="select_nd")

    ifres = select_if.run()
    ndres = select_nd.run()

    assert ifres.outputs.out == [4]
    assert ndres.outputs.out == [4]
    assert select_nd.result.outputs.out == [4]


@pytest.mark.timeout(30)
def test_mapnode_single(tmpdir):
    tmpdir.chdir()

    def _producer(num=1, deadly_num=7):
        if num == deadly_num:
            raise RuntimeError("Got the deadly num (%d)." % num)
        return num + 1

    pnode = pe.MapNode(
        niu.Function(function=_producer), name="ProducerNode", iterfield=["num"]
    )
    pnode.inputs.num = [7]
    wf = pe.Workflow(name="PC_Workflow")
    wf.add_nodes([pnode])
    wf.base_dir = os.path.abspath("./test_output")
    with pytest.raises(RuntimeError):
        wf.run(plugin="MultiProc")


class FailCommandLine(nib.CommandLine):
    input_spec = nib.CommandLineInputSpec
    output_spec = nib.TraitedSpec
    _cmd = 'nipype-node-execution-fail'


def test_NodeExecutionError(tmp_path, monkeypatch):
    import stat

    monkeypatch.chdir(tmp_path)

    # create basic executable and add to PATH
    exebin = tmp_path / 'bin'
    exebin.mkdir()
    exe = exebin / 'nipype-node-execution-fail'
    exe.write_text(
        '#!/bin/bash\necho "Running"\necho "This should fail" >&2\nexit 1',
        encoding='utf-8',
    )
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(exe.parent.absolute()), prepend=os.pathsep)

    # Test with cmdline interface
    cmd = pe.Node(FailCommandLine(), name="cmd-fail", base_dir='cmd')
    with pytest.raises(pe.nodes.NodeExecutionError) as exc:
        cmd.run()
    error_msg = str(exc.value)

    for attr in ("Cmdline:", "Stdout:", "Stderr:", "Traceback:"):
        assert attr in error_msg
    assert "This should fail" in error_msg

    # Test with function interface
    def fail():
        raise Exception("Functions can fail too")

    func = pe.Node(niu.Function(function=fail), name='func-fail', base_dir='func')
    with pytest.raises(pe.nodes.NodeExecutionError) as exc:
        func.run()
    error_msg = str(exc.value)
    assert "Traceback:" in error_msg
    assert "Cmdline:" not in error_msg
    assert "Functions can fail too" in error_msg
