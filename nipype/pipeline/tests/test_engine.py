# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""
from copy import deepcopy
import os
from shutil import rmtree
from tempfile import mkdtemp

import networkx as nx

from nipype.testing import (assert_raises, assert_equal, assert_true,
                            assert_false)
import nipype.interfaces.base as nib
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


# Workflow
def test_init():
    yield assert_raises, Exception, pe.Workflow
    pipe = pe.Workflow(name='pipe')
    yield assert_equal, type(pipe._graph), nx.DiGraph

def test_connect():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()
    yield assert_equal, pipe._graph.get_edge_data(mod1,mod2), {'connect':[('output1','input1')]}

def test_add_nodes():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    pipe.add_nodes([mod1,mod2])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()

# Test graph expansion.  The following set tests the building blocks
# of the graph expansion routine.
# XXX - SG I'll create a graphical version of these tests and actually
# ensure that all connections are tested later

def test1():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    pipe.add_nodes([mod1])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 1
    yield assert_equal, len(pipe._execgraph.edges()), 0

def test2():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod1.iterables = dict(input1=lambda:[1,2],input2=lambda:[1,2])
    pipe.add_nodes([mod1])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 4
    yield assert_equal, len(pipe._execgraph.edges()), 0

def test3():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod1.iterables = {}
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 3
    yield assert_equal, len(pipe._execgraph.edges()), 2

def test4():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 4
    yield assert_equal, len(pipe._execgraph.edges()), 2

def test5():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 6
    yield assert_equal, len(pipe._execgraph.edges()), 4

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
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 5
    yield assert_equal, len(pipe._execgraph.edges()), 4

def test7():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input1')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 5
    yield assert_equal, len(pipe._execgraph.edges()), 4

def test8():
    pipe = pe.Workflow(name='pipe')
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod2 = pe.Node(interface=TestInterface(),name='mod2')
    mod3 = pe.Node(interface=TestInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input1')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._flatgraph = pipe._create_flat_graph()
    pipe._execgraph = pe.generate_expanded_graph(deepcopy(pipe._flatgraph))
    yield assert_equal, len(pipe._execgraph.nodes()), 8
    yield assert_equal, len(pipe._execgraph.edges()), 8
    edgenum = sorted([(len(pipe._execgraph.in_edges(node)) + \
                           len(pipe._execgraph.out_edges(node))) \
                          for node in pipe._execgraph.nodes()])
    yield assert_true, edgenum[0]>0

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
        pipe6._flatgraph = pipe6._create_flat_graph()
    except:
        error_raised = True
    yield assert_false, error_raised

def test_iterable_expansion():
    import nipype.pipeline.engine as pe
    wf1 = pe.Workflow(name='test')
    node1 = pe.Node(TestInterface(),name='node1')
    node2 = pe.Node(TestInterface(),name='node2')
    node1.iterables = ('input1',[1,2])
    wf1.connect(node1,'output1', node2, 'input2')
    wf3 = pe.Workflow(name='group')
    for i in [0,1,2]:
        wf3.add_nodes([wf1.clone(name='test%d'%i)])
    wf3._flatgraph = wf3._create_flat_graph()
    yield assert_equal, len(pe.generate_expanded_graph(wf3._flatgraph).nodes()),12

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
    c = pe.Node(IdentityInterface(fields=['a','b']),name='c')
    flow1 = pe.Workflow(name='test2')
    x = lambda : flow1.connect([(a, c, [('b', 'b')]), (b, c, [('a', 'b')])])
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

'''
import nipype.pipeline.engine as pe
import nipype.interfaces.spm as spm
import os
from nipype.utils.config import config
from StringIO import StringIO

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
    yield assert_raises, Exception, pe.Node
    try:
        node = pe.Node(TestInterface, name='test')
    except IOError:
        exception = True
    else:
        exception = False
    yield assert_true, exception

def test_workflow_add():
    from nipype.interfaces.utility import IdentityInterface as ii
    n1 = pe.Node(ii(fields=['a','b']),name='n1')
    n2 = pe.Node(ii(fields=['c','d']),name='n2')
    n3 = pe.Node(ii(fields=['c','d']),name='n1')
    w1 = pe.Workflow(name='test')
    w1.connect(n1,'a',n2,'c')
    yield assert_raises, IOError, w1.add_nodes, [n1]
    yield assert_raises, IOError, w1.add_nodes, [n2]
    yield assert_raises, IOError, w1.add_nodes, [n3]
    yield assert_raises, IOError, w1.connect, [(w1,n2,[('n1.a','d')])]


def test_node_get_output():
    mod1 = pe.Node(interface=TestInterface(),name='mod1')
    mod1.inputs.input1 = 1
    mod1.run()
    yield assert_equal, mod1.get_output('output1'), [1, 1]
    mod1._result = None
    yield assert_equal, mod1.get_output('output1'), [1, 1]


def test_mapnode_iterfield_check():
    mod1 = pe.MapNode(TestInterface(),
                      iterfield=['input1'],
                      name='mod1')
    yield assert_raises, ValueError, mod1._check_iterfield
    mod1 = pe.MapNode(TestInterface(),
                      iterfield=['input1', 'input2'],
                      name='mod1')
    mod1.inputs.input1 = [1,2]
    mod1.inputs.input2 = 3
    yield assert_raises, ValueError, mod1._check_iterfield


def test_node_hash():
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)
    from nipype.interfaces.utility import Function
    def func1():
        return 1
    def func2(a):
        return a+1
    n1 = pe.Node(Function(input_names=[],
                          output_names=['a'],
                          function=func1),
                 name='n1')
    n2 = pe.Node(Function(input_names=['a'],
                          output_names=['b'],
                          function=func2),
                 name='n2')
    w1 = pe.Workflow(name='test')
    modify = lambda x: x+1
    n1.inputs.a = 1
    w1.connect(n1, ('a', modify), n2,'a')
    w1.base_dir = wd
    # generate outputs
    w1.run(plugin='Linear')
    # ensure plugin is being called
    w1.config['execution'] = {'stop_on_first_crash': 'true',
                              'local_hash_check': 'false',
                              'crashdump_dir': wd}
    error_raised = False
    # create dummy distributed plugin class
    from nipype.pipeline.plugins.base import DistributedPluginBase
    class RaiseError(DistributedPluginBase):
        def _submit_job(self, node, updatehash=False):
            raise Exception('Submit called')
    try:
        w1.run(plugin=RaiseError())
    except Exception, e:
        pe.logger.info('Exception: %s' % str(e))
        error_raised = True
    yield assert_true, error_raised
    #yield assert_true, 'Submit called' in e
    # rerun to ensure we have outputs
    w1.run(plugin='Linear')
    # set local check
    w1.config['execution'] = {'stop_on_first_crash': 'true',
                              'local_hash_check': 'true',
                              'crashdump_dir': wd}
    error_raised = False
    try:
        w1.run(plugin=RaiseError())
    except Exception, e:
        pe.logger.info('Exception: %s' % str(e))
        error_raised = True
    yield assert_false, error_raised
    os.chdir(cwd)
    rmtree(wd)

def test_old_config():
    cwd = os.getcwd()
    wd = mkdtemp()
    os.chdir(wd)
    from nipype.interfaces.utility import Function
    def func1():
        return 1
    def func2(a):
        return a+1
    n1 = pe.Node(Function(input_names=[],
                          output_names=['a'],
                          function=func1),
                 name='n1')
    n2 = pe.Node(Function(input_names=['a'],
                          output_names=['b'],
                          function=func2),
                 name='n2')
    w1 = pe.Workflow(name='test')
    modify = lambda x: x+1
    n1.inputs.a = 1
    w1.connect(n1, ('a', modify), n2,'a')
    w1.base_dir = wd

    w1.config = {'crashdump_dir': wd}
    # generate outputs
    error_raised = False
    try:
        w1.run(plugin='Linear')
    except Exception, e:
        pe.logger.info('Exception: %s' % str(e))
        error_raised = True
    yield assert_false, error_raised
    os.chdir(cwd)
    rmtree(wd)
