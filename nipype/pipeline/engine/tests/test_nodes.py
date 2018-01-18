# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
from builtins import str
import os
import pytest

from ... import engine as pe
from .test_base import EngineTestInterface

'''
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
'''
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
    with pytest.raises(Exception):
        pe.Node()
    with pytest.raises(IOError):
        pe.Node(EngineTestInterface, name='test')


def test_node_get_output():
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod1.inputs.input1 = 1
    mod1.run()
    assert mod1.get_output('output1') == [1, 1]
    mod1._result = None
    assert mod1.get_output('output1') == [1, 1]


def test_mapnode_iterfield_check():
    mod1 = pe.MapNode(EngineTestInterface(), iterfield=['input1'], name='mod1')
    with pytest.raises(ValueError):
        mod1._check_iterfield()
    mod1 = pe.MapNode(
        EngineTestInterface(), iterfield=['input1', 'input2'], name='mod1')
    mod1.inputs.input1 = [1, 2]
    mod1.inputs.input2 = 3
    with pytest.raises(ValueError):
        mod1._check_iterfield()


@pytest.mark.parametrize("x_inp, f_exp",
                         [(3, [6]), ([2, 3], [4, 6]), ((2, 3), [4, 6]),
                          (range(3), [0, 2, 4]), ("Str", ["StrStr"]),
                          (["Str1", "Str2"], ["Str1Str1", "Str2Str2"])])
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
        Function(input_names=['in1'], output_names=['out'], function=func1),
        iterfield=['in1'],
        nested=True,
        name='n1')
    n1.inputs.in1 = [[1, [2]], 3, [4, 5]]
    n1.run()
    assert n1.get_output('out') == [[2, [3]], 4, [5, 6]]

    n2 = MapNode(
        Function(input_names=['in1'], output_names=['out'], function=func1),
        iterfield=['in1'],
        nested=False,
        name='n1')
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
        Function(function=func1),
        iterfield='in1',
        name='mapnode',
        n_procs=2,
        mem_gb=2)
    mapnode.inputs.in1 = [1, 2]

    for idx, node in mapnode._make_nodes():
        for attr in ('overwrite', 'run_without_submitting', 'plugin_args'):
            assert getattr(node, attr) == getattr(mapnode, attr)
        for attr in ('_n_procs', '_mem_gb'):
            assert (getattr(node, attr) == getattr(mapnode, attr))


def test_node_hash(tmpdir):
    from nipype.interfaces.utility import Function
    tmpdir.chdir()

    def func1():
        return 1

    def func2(a):
        return a + 1

    n1 = pe.Node(
        Function(input_names=[], output_names=['a'], function=func1),
        name='n1')
    n2 = pe.Node(
        Function(input_names=['a'], output_names=['b'], function=func2),
        name='n2')
    w1 = pe.Workflow(name='test')
    modify = lambda x: x + 1
    n1.inputs.a = 1
    w1.connect(n1, ('a', modify), n2, 'a')
    w1.base_dir = os.getcwd()
    # generate outputs
    w1.run(plugin='Linear')
    # ensure plugin is being called
    w1.config['execution'] = {
        'stop_on_first_crash': 'true',
        'local_hash_check': 'false',
        'crashdump_dir': os.getcwd()
    }
    # create dummy distributed plugin class
    from nipype.pipeline.plugins.base import DistributedPluginBase

    # create a custom exception
    class EngineTestException(Exception):
        pass

    class RaiseError(DistributedPluginBase):
        def _submit_job(self, node, updatehash=False):
            raise EngineTestException('Submit called')

    # check if a proper exception is raised
    with pytest.raises(EngineTestException) as excinfo:
        w1.run(plugin=RaiseError())
    assert 'Submit called' == str(excinfo.value)

    # rerun to ensure we have outputs
    w1.run(plugin='Linear')
    # set local check
    w1.config['execution'] = {
        'stop_on_first_crash': 'true',
        'local_hash_check': 'true',
        'crashdump_dir': os.getcwd()
    }

    w1.run(plugin=RaiseError())
