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
                            assert_false, skipif, parametric)
import nipype.interfaces.base as nib
from nipype.utils.filemanip import cleandir
import nipype.pipeline.engine as pe

class InputSpec(nib.TraitedSpec):
    input1 = nib.traits.Int(desc='a random int')
    input2 = nib.traits.Int(desc='a random int')
    
class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')
    
class TestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1, self.inputs.input1]
        return outputs



@parametric
def test_init():
    yield assert_raises(Exception, pe.Workflow)
    pipe = pe.Workflow(name='pipe')
    yield assert_equal(type(pipe._graph), nx.DiGraph)
    yield assert_equal(pipe._execgraph, None)

@parametric
def test_connect():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])

    yield assert_true(mod1 in pipe._graph.nodes())
    yield assert_true(mod2 in pipe._graph.nodes())
    yield assert_equal(pipe._graph.get_edge_data(mod1,mod2), {'connect':[('output1','input1')]})

@parametric
def test_add_nodes():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe.add_nodes([mod1,mod2])

    yield assert_true(mod1 in pipe._graph.nodes())
    yield assert_true(mod2 in pipe._graph.nodes())

@parametric
def test_generate_dependency_list():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    pipe._generate_dependency_list()
    yield assert_false(pipe._execgraph == None)
    yield assert_equal(len(pipe.procs), 2)
    yield assert_false(pipe.proc_done[1])
    yield assert_false(pipe.proc_pending[1])
    yield assert_equal(pipe.depidx[0,1], 1)

@parametric
def test_run_in_series():
    cur_dir = os.getcwd()
    temp_dir = mkdtemp(prefix='test_engine_')
    os.chdir(temp_dir)

    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.MapNode(interface=TestInterface(),
                      iterfield=['input1'],
                      name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe.base_dir = os.getcwd()
    mod1.inputs.input1 = 1
    pipe.run(inseries=True)
    node = pipe.get_exec_node('pipe.mod1')
    result = node.get_output('output1')
    # NOTE: yield statements in nose cause the setup function to be
    # called at this point in the code, after all of the above is
    # executed!
    yield assert_equal(result, [1, 1])
    os.chdir(cur_dir)
    rmtree(temp_dir)

# Test graph expansion.  The following set tests the building blocks
# of the graph expansion routine.
# XXX - SG I'll create a graphical version of these tests and actually
# ensure that all connections are tested later

@parametric
def test1():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    pipe.add_nodes([mod1])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 1)
    yield assert_equal(len(pipe._execgraph.edges()), 0)

@parametric
def test2():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod1.iterables = dict(input1=lambda:[1,2],input2=lambda:[1,2])
    pipe.add_nodes([mod1])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 4)
    yield assert_equal(len(pipe._execgraph.edges()), 0)
    
@parametric
def test3():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod1.iterables = {}
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 3)
    yield assert_equal(len(pipe._execgraph.edges()), 2)
    
@parametric
def test4():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 4)
    yield assert_equal(len(pipe._execgraph.edges()), 2)

@parametric
def test5():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 6)
    yield assert_equal(len(pipe._execgraph.edges()), 4)

@parametric
def test6():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod1.iterables = {}
    mod2.iterables = dict(input1=lambda:[1,2])
    mod3.iterables = {}
    pipe.connect([(mod1,mod2,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 5)
    yield assert_equal(len(pipe._execgraph.edges()), 4)

@parametric
def test7():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 5)
    yield assert_equal(len(pipe._execgraph.edges()), 4)

@parametric
def test8():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._create_flat_graph()
    pipe._execgraph = pe._generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal(len(pipe._execgraph.nodes()), 8)
    yield assert_equal(len(pipe._execgraph.edges()), 8)
    edgenum = sorted([(len(pipe._execgraph.in_edges(node)) + \
                           len(pipe._execgraph.out_edges(node))) \
                          for node in pipe._execgraph.nodes()])
    yield assert_true(edgenum[0]>0)

@parametric
def test_expansion():
    pipe1 = pe.Workflow(name='pipe1')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe1.connect([(mod1,mod2,[('output1','input2')])])
    pipe2 = pe.Workflow(name='pipe2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod4 = pe.Node(interface=TestInterface(),name='mod4')
    pipe2.connect([(mod3,mod4,[('output1','input2')])])
    pipe3 = pe.Workflow(name="pipe3")
    pipe3.connect([(pipe1, pipe2, [('mod2.output1','mod4.input1')])])
    pipe4 = pe.Workflow(name="pipe4")
    mod5 = pe.Node(interface=TestInterface(),name='mod5')
    pipe4.add_nodes([mod5])
    pipe5 = pe.Workflow(name="pipe5")
    pipe5.add_nodes([pipe4])
    pipe6 = pe.Workflow(name="pipe6")
    pipe6.connect([(pipe5, pipe3, [('pipe4.mod5.output1','pipe2.mod3.input1')])])
    error_raised = False
    try:
        pipe6._create_flat_graph()
    except:
        error_raised = True
    yield assert_false(error_raised)

@parametric
def test_iterable_expansion():
    import nipype.pipeline.engine as pe
    from nipype.interfaces.utility import IdentityInterface
    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(IdentityInterface(fields=['in1']),name='node1')
    node2 = pe.Node(IdentityInterface(fields=['in2']),name='node2')
    node1.iterables = ('in1',[1,2])
    wf1.connect(node1,'in1', node2, 'in2')
    wf3 = pe.Workflow(name='group')
    for i in [0,1,2]:
        wf3.add_nodes([wf1.clone(name='test%d'%i)])
    wf3._create_flat_graph()
    yield assert_equal(len(pe._generate_expanded_graph(wf3._flatgraph).nodes()),12)

def test_disconnect():
    import nipype.pipeline.engine as pe
    from nipype.interfaces.utility import IdentityInterface
    a = pe.Node(IdentityInterface(fields=['a','b']),name='a')
    b = pe.Node(IdentityInterface(fields=['a','b']),name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a,'a',b,'a')
    flow1.disconnect(a,'a',b,'a')
    yield assert_equal, flow1._graph.edges(), []

def test_doubleconnect():
    import nipype.pipeline.engine as pe
    from nipype.interfaces.utility import IdentityInterface
    a = pe.Node(IdentityInterface(fields=['a','b']),name='a')
    b = pe.Node(IdentityInterface(fields=['a','b']),name='b')
    flow1 = pe.Workflow(name='test')
    flow1.connect(a,'a',b,'a')
    x = lambda: flow1.connect(a,'b',b,'a')
    yield assert_raises, Exception, x


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
