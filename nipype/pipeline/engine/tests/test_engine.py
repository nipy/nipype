# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""

from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from builtins import open
from copy import deepcopy
from glob import glob
import os, sys

import networkx as nx

import pytest
from ... import engine as pe
from ....interfaces import base as nib


class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')
    input_file = nib.traits.File(desc='Random File')

class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')


class EngineTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs


def test_init():
    with pytest.raises(TypeError): pe.Workflow()
    pipe = pe.Workflow(name='pipe')
    assert type(pipe._graph) == nx.DiGraph


def test_connect():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
    pipe.connect([(mod1, mod2, [('output1', 'input1')])])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()
    assert pipe._graph.get_edge_data(mod1, mod2) == {'connect': [('output1', 'input1')]}


def test_add_nodes():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
    pipe.add_nodes([mod1, mod2])

    assert mod1 in pipe._graph.nodes()
    assert mod2 in pipe._graph.nodes()

# Test graph expansion.  The following set tests the building blocks
# of the graph expansion routine.
# XXX - SG I'll create a graphical version of these tests and actually
# ensure that all connections are tested later

@pytest.mark.parametrize("iterables, expected", [
        ({"1": None}, (1,0)), #test1
        ({"1": dict(input1=lambda: [1, 2], input2=lambda: [1, 2])}, (4,0)) #test2
        ])
def test_1mod(iterables, expected):
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    setattr(mod1, "iterables", iterables["1"])
    pipe.add_nodes([mod1])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    assert len(pipe._execgraph.nodes()) == expected[0]
    assert len(pipe._execgraph.edges()) == expected[1]


@pytest.mark.parametrize("iterables, expected", [
        ({"1": {}, "2": dict(input1=lambda: [1, 2])}, (3,2)), #test3
        ({"1": dict(input1=lambda: [1, 2]), "2": {}}, (4,2)), #test4
        ({"1": dict(input1=lambda: [1, 2]), "2": dict(input1=lambda: [1, 2])}, (6,4)) #test5
        ])
def test_2mods(iterables, expected):
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
    for nr in ["1", "2"]:
        setattr(eval("mod"+nr), "iterables", iterables[nr])
    pipe.connect([(mod1, mod2, [('output1', 'input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    assert len(pipe._execgraph.nodes()) == expected[0]
    assert len(pipe._execgraph.edges()) == expected[1]


@pytest.mark.parametrize("iterables, expected, connect", [
        ({"1": {}, "2": dict(input1=lambda: [1, 2]), "3": {}}, (5,4), ("1-2","2-3")), #test6
        ({"1": dict(input1=lambda: [1, 2]), "2": {}, "3": {}}, (5,4), ("1-3","2-3")), #test7
        ({"1": dict(input1=lambda: [1, 2]), "2":  dict(input1=lambda: [1, 2]), "3": {}},
         (8,8), ("1-3","2-3")), #test8
        ])
def test_3mods(iterables, expected, connect):
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
    mod3 = pe.Node(interface=EngineTestInterface(), name='mod3')
    for nr in ["1", "2", "3"]:
        setattr(eval("mod"+nr), "iterables", iterables[nr])
    if connect == ("1-2","2-3"):
        pipe.connect([(mod1, mod2, [('output1', 'input2')]),
                      (mod2, mod3, [('output1', 'input2')])])
    elif connect == ("1-3","2-3"):
        pipe.connect([(mod1, mod3, [('output1', 'input1')]),
                      (mod2, mod3, [('output1', 'input2')])])
    else:
        raise Exception("connect pattern is not implemented yet within the test function")
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    assert len(pipe._execgraph.nodes()) == expected[0]
    assert len(pipe._execgraph.edges()) == expected[1]

    edgenum = sorted([(len(pipe._execgraph.in_edges(node)) +
                       len(pipe._execgraph.out_edges(node)))
                      for node in pipe._execgraph.nodes()])
    assert edgenum[0] > 0


def test_expansion():
    pipe1 = pe.Workflow(name='pipe1')
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
    pipe1.connect([(mod1, mod2, [('output1', 'input2')])])
    pipe2 = pe.Workflow(name='pipe2')
    mod3 = pe.Node(interface=EngineTestInterface(), name='mod3')
    mod4 = pe.Node(interface=EngineTestInterface(), name='mod4')
    pipe2.connect([(mod3, mod4, [('output1', 'input2')])])
    pipe3 = pe.Workflow(name="pipe3")
    pipe3.connect([(pipe1, pipe2, [('mod2.output1', 'mod4.input1')])])
    pipe4 = pe.Workflow(name="pipe4")
    mod5 = pe.Node(interface=EngineTestInterface(), name='mod5')
    pipe4.add_nodes([mod5])
    pipe5 = pe.Workflow(name="pipe5")
    pipe5.add_nodes([pipe4])
    pipe6 = pe.Workflow(name="pipe6")
    pipe6.connect([(pipe5, pipe3, [('pipe4.mod5.output1', 'pipe2.mod3.input1')])])

    pipe6._flatgraph = pipe6._create_flat_graph()


def test_iterable_expansion():
    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(EngineTestInterface(), name='node1')
    node2 = pe.Node(EngineTestInterface(), name='node2')
    node1.iterables = ('input1', [1, 2])
    wf1.connect(node1, 'output1', node2, 'input2')
    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])
    wf3._flatgraph = wf3._create_flat_graph()
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 12


def test_synchronize_expansion():
    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(EngineTestInterface(), name='node1')
    node1.iterables = [('input1', [1, 2]), ('input2', [3, 4, 5])]
    node1.synchronize = True
    node2 = pe.Node(EngineTestInterface(), name='node2')
    wf1.connect(node1, 'output1', node2, 'input2')
    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])
    wf3._flatgraph = wf3._create_flat_graph()
    # Each expanded graph clone has:
    # 3 node1 expansion nodes and
    # 1 node2 replicate per node1 replicate
    # => 2 * 3 = 6 nodes per expanded subgraph
    # => 18 nodes in the group
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 18


def test_synchronize_tuples_expansion():
    wf1 = pe.Workflow(name='test')

    node1 = pe.Node(EngineTestInterface(), name='node1')
    node2 = pe.Node(EngineTestInterface(), name='node2')
    node1.iterables = [('input1', 'input2'), [(1, 3), (2, 4), (None, 5)]]

    node1.synchronize = True

    wf1.connect(node1, 'output1', node2, 'input2')

    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])

    wf3._flatgraph = wf3._create_flat_graph()
    # Identical to test_synchronize_expansion
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 18


def test_itersource_expansion():

    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(EngineTestInterface(), name='node1')
    node1.iterables = ('input1', [1, 2])

    node2 = pe.Node(EngineTestInterface(), name='node2')
    wf1.connect(node1, 'output1', node2, 'input1')

    node3 = pe.Node(EngineTestInterface(), name='node3')
    node3.itersource = ('node1', 'input1')
    node3.iterables = [('input1', {1: [3, 4], 2: [5, 6, 7]})]

    wf1.connect(node2, 'output1', node3, 'input1')
    node4 = pe.Node(EngineTestInterface(), name='node4')

    wf1.connect(node3, 'output1', node4, 'input1')

    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])

    wf3._flatgraph = wf3._create_flat_graph()

    # each expanded graph clone has:
    # 2 node1 expansion nodes,
    # 1 node2 per node1 replicate,
    # 2 node3 replicates for the node1 input1 value 1,
    # 3 node3 replicates for the node1 input1 value 2 and
    # 1 node4 successor per node3 replicate
    # => 2 + 2 + (2 + 3) + 5 = 14 nodes per expanded graph clone
    # => 3 * 14 = 42 nodes in the group
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 42


def test_itersource_synchronize1_expansion():
    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(EngineTestInterface(), name='node1')
    node1.iterables = [('input1', [1, 2]), ('input2', [3, 4])]
    node1.synchronize = True
    node2 = pe.Node(EngineTestInterface(), name='node2')
    wf1.connect(node1, 'output1', node2, 'input1')
    node3 = pe.Node(EngineTestInterface(), name='node3')
    node3.itersource = ('node1', ['input1', 'input2'])
    node3.iterables = [('input1', {(1, 3): [5, 6]}),
                       ('input2', {(1, 3): [7, 8], (2, 4): [9]})]
    wf1.connect(node2, 'output1', node3, 'input1')
    node4 = pe.Node(EngineTestInterface(), name='node4')
    wf1.connect(node3, 'output1', node4, 'input1')
    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])
    wf3._flatgraph = wf3._create_flat_graph()

    # each expanded graph clone has:
    # 2 node1 expansion nodes,
    # 1 node2 per node1 replicate,
    # 2 node3 replicates for the node1 input1 value 1,
    # 3 node3 replicates for the node1 input1 value 2 and
    # 1 node4 successor per node3 replicate
    # => 2 + 2 + (2 + 3) + 5 = 14 nodes per expanded graph clone
    # => 3 * 14 = 42 nodes in the group
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 42


def test_itersource_synchronize2_expansion():
    wf1 = pe.Workflow(name='test')

    node1 = pe.Node(EngineTestInterface(), name='node1')
    node1.iterables = [('input1', [1, 2]), ('input2', [3, 4])]
    node1.synchronize = True
    node2 = pe.Node(EngineTestInterface(), name='node2')
    wf1.connect(node1, 'output1', node2, 'input1')
    node3 = pe.Node(EngineTestInterface(), name='node3')
    node3.itersource = ('node1', ['input1', 'input2'])
    node3.synchronize = True
    node3.iterables = [('input1', 'input2'),
                       {(1, 3): [(5, 7), (6, 8)], (2, 4):[(None, 9)]}]
    wf1.connect(node2, 'output1', node3, 'input1')
    node4 = pe.Node(EngineTestInterface(), name='node4')
    wf1.connect(node3, 'output1', node4, 'input1')
    wf3 = pe.Workflow(name='group')
    for i in [0, 1, 2]:
        wf3.add_nodes([wf1.clone(name='test%d' % i)])
    wf3._flatgraph = wf3._create_flat_graph()

    # each expanded graph clone has:
    # 2 node1 expansion nodes,
    # 1 node2 per node1 replicate,
    # 2 node3 replicates for the node1 input1 value 1,
    # 1 node3 replicates for the node1 input1 value 2 and
    # 1 node4 successor per node3 replicate
    # => 2 + 2 + (2 + 1) + 3 = 10 nodes per expanded graph clone
    # => 3 * 10 = 30 nodes in the group
    assert len(pe.generate_expanded_graph(wf3._flatgraph).nodes()) == 30


def test_disconnect():
    from nipype.interfaces.utility import IdentityInterface
    a = pe.Node(IdentityInterface(fields=['a', 'b']), name='a')
    b = pe.Node(IdentityInterface(fields=['a', 'b']), name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a, 'a', b, 'a')
    flow1.disconnect(a, 'a', b, 'a')
    assert flow1._graph.edges() == []


def test_doubleconnect():
    from nipype.interfaces.utility import IdentityInterface
    a = pe.Node(IdentityInterface(fields=['a', 'b']), name='a')
    b = pe.Node(IdentityInterface(fields=['a', 'b']), name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a, 'a', b, 'a')
    x = lambda: flow1.connect(a, 'b', b, 'a')
    with pytest.raises(Exception) as excinfo:
        x()
    assert "Trying to connect" in str(excinfo.value)

    c = pe.Node(IdentityInterface(fields=['a', 'b']), name='c')
    flow1 = pe.Workflow(name='test2')
    x = lambda: flow1.connect([(a, c, [('b', 'b')]), (b, c, [('a', 'b')])])
    with pytest.raises(Exception) as excinfo:
        x()
    assert "Trying to connect" in str(excinfo.value)


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
    with pytest.raises(Exception): pe.Node()
    try:
        node = pe.Node(EngineTestInterface, name='test')
    except IOError:
        exception = True
    else:
        exception = False
    assert exception


def test_workflow_add():
    from nipype.interfaces.utility import IdentityInterface as ii
    n1 = pe.Node(ii(fields=['a', 'b']), name='n1')
    n2 = pe.Node(ii(fields=['c', 'd']), name='n2')
    n3 = pe.Node(ii(fields=['c', 'd']), name='n1')
    w1 = pe.Workflow(name='test')
    w1.connect(n1, 'a', n2, 'c')
    for node in [n1, n2, n3]:
        with pytest.raises(IOError): w1.add_nodes([node])
    with pytest.raises(IOError): w1.connect([(w1, n2, [('n1.a', 'd')])])


def test_node_get_output():
    mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
    mod1.inputs.input1 = 1
    mod1.run()
    assert mod1.get_output('output1') == [1, 1]
    mod1._result = None
    assert mod1.get_output('output1') == [1, 1]


def test_mapnode_iterfield_check():
    mod1 = pe.MapNode(EngineTestInterface(),
                      iterfield=['input1'],
                      name='mod1')
    with pytest.raises(ValueError): mod1._check_iterfield()
    mod1 = pe.MapNode(EngineTestInterface(),
                      iterfield=['input1', 'input2'],
                      name='mod1')
    mod1.inputs.input1 = [1, 2]
    mod1.inputs.input2 = 3
    with pytest.raises(ValueError): mod1._check_iterfield()


def test_mapnode_nested(tmpdir):
    os.chdir(str(tmpdir))
    from nipype import MapNode, Function

    def func1(in1):
        return in1 + 1
    n1 = MapNode(Function(input_names=['in1'],
                          output_names=['out'],
                          function=func1),
                 iterfield=['in1'],
                 nested=True,
                 name='n1')
    n1.inputs.in1 = [[1, [2]], 3, [4, 5]]
    n1.run()
    print(n1.get_output('out'))
    assert n1.get_output('out') == [[2, [3]], 4, [5, 6]]

    n2 = MapNode(Function(input_names=['in1'],
                          output_names=['out'],
                          function=func1),
                 iterfield=['in1'],
                 nested=False,
                 name='n1')
    n2.inputs.in1 = [[1, [2]], 3, [4, 5]]

    with pytest.raises(Exception) as excinfo:
        n2.run()
    assert "can only concatenate list" in str(excinfo.value)


def test_node_hash(tmpdir):
    wd = str(tmpdir)
    os.chdir(wd)
    from nipype.interfaces.utility import Function

    def func1():
        return 1

    def func2(a):
        return a + 1
    n1 = pe.Node(Function(input_names=[],
                          output_names=['a'],
                          function=func1),
                 name='n1')
    n2 = pe.Node(Function(input_names=['a'],
                          output_names=['b'],
                          function=func2),
                 name='n2')
    w1 = pe.Workflow(name='test')
    modify = lambda x: x + 1
    n1.inputs.a = 1
    w1.connect(n1, ('a', modify), n2, 'a')
    w1.base_dir = wd
    # generate outputs
    w1.run(plugin='Linear')
    # ensure plugin is being called
    w1.config['execution'] = {'stop_on_first_crash': 'true',
                              'local_hash_check': 'false',
                              'crashdump_dir': wd}
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
    w1.config['execution'] = {'stop_on_first_crash': 'true',
                              'local_hash_check': 'true',
                              'crashdump_dir': wd}

    w1.run(plugin=RaiseError())


def test_old_config(tmpdir):
    wd = str(tmpdir)
    os.chdir(wd)
    from nipype.interfaces.utility import Function

    def func1():
        return 1

    def func2(a):
        return a + 1
    n1 = pe.Node(Function(input_names=[],
                          output_names=['a'],
                          function=func1),
                 name='n1')
    n2 = pe.Node(Function(input_names=['a'],
                          output_names=['b'],
                          function=func2),
                 name='n2')
    w1 = pe.Workflow(name='test')
    modify = lambda x: x + 1
    n1.inputs.a = 1
    w1.connect(n1, ('a', modify), n2, 'a')
    w1.base_dir = wd

    w1.config['execution']['crashdump_dir'] = wd
    # generate outputs

    w1.run(plugin='Linear')


def test_mapnode_json(tmpdir):
    """Tests that mapnodes don't generate excess jsons
    """
    wd = str(tmpdir)
    os.chdir(wd)
    from nipype import MapNode, Function, Workflow

    def func1(in1):
        return in1 + 1
    n1 = MapNode(Function(input_names=['in1'],
                          output_names=['out'],
                          function=func1),
                 iterfield=['in1'],
                 name='n1')
    n1.inputs.in1 = [1]
    w1 = Workflow(name='test')
    w1.base_dir = wd
    w1.config['execution']['crashdump_dir'] = wd
    w1.add_nodes([n1])
    w1.run()
    n1.inputs.in1 = [2]
    w1.run()
    # should rerun
    n1.inputs.in1 = [1]
    eg = w1.run()

    node = eg.nodes()[0]
    outjson = glob(os.path.join(node.output_dir(), '_0x*.json'))
    assert len(outjson) == 1

    # check that multiple json's don't trigger rerun
    with open(os.path.join(node.output_dir(), 'test.json'), 'wt') as fp:
        fp.write('dummy file')
    w1.config['execution'].update(**{'stop_on_first_rerun': True})

    w1.run()


def test_parameterize_dirs_false(tmpdir):
    from ....interfaces.utility import IdentityInterface
    from ....testing import example_data

    input_file = example_data('fsl_motion_outliers_fd.txt')

    n1 = pe.Node(EngineTestInterface(), name='Node1')
    n1.iterables = ('input_file', (input_file, input_file))
    n1.interface.inputs.input1 = 1

    n2 = pe.Node(IdentityInterface(fields='in1'), name='Node2')

    wf = pe.Workflow(name='Test')
    wf.base_dir = str(tmpdir)
    wf.config['execution']['parameterize_dirs'] = False
    wf.connect([(n1, n2, [('output1', 'in1')])])


    wf.run()


def test_serial_input(tmpdir):
    wd = str(tmpdir)
    os.chdir(wd)
    from nipype import MapNode, Function, Workflow

    def func1(in1):
        return in1
    n1 = MapNode(Function(input_names=['in1'],
                          output_names=['out'],
                          function=func1),
                 iterfield=['in1'],
                 name='n1')
    n1.inputs.in1 = [1, 2, 3]

    w1 = Workflow(name='test')
    w1.base_dir = wd
    w1.add_nodes([n1])
    # set local check
    w1.config['execution'] = {'stop_on_first_crash': 'true',
                              'local_hash_check': 'true',
                              'crashdump_dir': wd,
                              'poll_sleep_duration': 2}

    # test output of num_subnodes method when serial is default (False)
    assert n1.num_subnodes() == len(n1.inputs.in1)

    # test running the workflow on default conditions
    w1.run(plugin='MultiProc')

    # test output of num_subnodes method when serial is True
    n1._serial = True
    assert n1.num_subnodes() == 1

    # test running the workflow on serial conditions
    w1.run(plugin='MultiProc')


def test_write_graph_runs(tmpdir):
    os.chdir(str(tmpdir))

    for graph in ('orig', 'flat', 'exec', 'hierarchical', 'colored'):
        for simple in (True, False):
            pipe = pe.Workflow(name='pipe')
            mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
            mod2 = pe.Node(interface=EngineTestInterface(), name='mod2')
            pipe.connect([(mod1, mod2, [('output1', 'input1')])])
            try:
                pipe.write_graph(graph2use=graph, simple_form=simple,
                                 format='dot')
            except Exception:
                assert False, \
                    'Failed to plot {} {} graph'.format(
                    'simple' if simple else 'detailed', graph)

            assert os.path.exists('graph.dot') or os.path.exists('graph_detailed.dot')
            try:
                os.remove('graph.dot')
            except OSError:
                pass
            try:
                os.remove('graph_detailed.dot')
            except OSError:
                pass


def test_deep_nested_write_graph_runs(tmpdir):
    os.chdir(str(tmpdir))

    for graph in ('orig', 'flat', 'exec', 'hierarchical', 'colored'):
        for simple in (True, False):
            pipe = pe.Workflow(name='pipe')
            parent = pipe
            for depth in range(10):
                sub = pe.Workflow(name='pipe_nest_{}'.format(depth))
                parent.add_nodes([sub])
                parent = sub
            mod1 = pe.Node(interface=EngineTestInterface(), name='mod1')
            parent.add_nodes([mod1])
            try:
                pipe.write_graph(graph2use=graph, simple_form=simple,
                                 format='dot')
            except Exception as e:
                assert False, \
                    'Failed to plot {} {} deep graph: {!s}'.format(
                    'simple' if simple else 'detailed', graph, e)

            assert os.path.exists('graph.dot') or os.path.exists('graph_detailed.dot')
            try:
                os.remove('graph.dot')
            except OSError:
                pass
            try:
                os.remove('graph_detailed.dot')
            except OSError:
                pass


def test_io_subclass():
    """Ensure any io subclass allows dynamic traits"""
    from nipype.interfaces.io import IOBase
    from nipype.interfaces.base import DynamicTraitedSpec

    class TestKV(IOBase):
        _always_run = True
        output_spec = DynamicTraitedSpec

        def _list_outputs(self):
            outputs = {}
            outputs['test'] = 1
            outputs['foo'] = 'bar'
            return outputs

    wf = pe.Workflow('testkv')

    def testx2(test):
        return test * 2

    kvnode = pe.Node(TestKV(), name='testkv')
    from nipype.interfaces.utility import Function
    func = pe.Node(
        Function(input_names=['test'], output_names=['test2'], function=testx2),
        name='func')
    exception_not_raised = True
    try:
        wf.connect(kvnode, 'test', func, 'test')
    except Exception as e:
        if 'Module testkv has no output called test' in e:
            exception_not_raised = False
    assert exception_not_raised
