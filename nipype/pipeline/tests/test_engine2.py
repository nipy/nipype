"""Tests for the engine module
"""
import os
from copy import deepcopy
from tempfile import mkdtemp
from shutil import rmtree
from nose import with_setup

import networkx as nx

from nipype.testing import (assert_raises, assert_equal, assert_true,
                            assert_false)
from nipype.interfaces.base import (Interface, CommandLine, Bunch,
                                    InterfaceResult)
from nipype.utils.filemanip import cleandir
import nipype.pipeline.engine2 as pe
import nipype.pipeline.node_wrapper as nw


class BasicInterface(Interface):
    """Basic interface class for testing nodewrapper
    """
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.ran = None
        
    def _populate_inputs(self):
        self.inputs = Bunch(input1=None,
                            input2=None,
                            returncode=0)
    
    def get_input_info(self):
        return []
    
    def outputs(self):
        """
           output1 : None
        """
        return Bunch(output1=None)
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.ran is not None:
            outputs.output1 = [self.ran,self.inputs.input1]
        return outputs
    
    def run(self,**kwargs):
        """Execute this module.
        """
        runtime = Bunch(returncode=self.inputs.returncode,
                        stdout=None,
                        stderr=None)
        self.ran = 'ran'
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

working_dir = os.getcwd()
temp_dir = None
def setup_pipe():
    global temp_dir
    temp_dir = mkdtemp(prefix='test_engine_')
    os.chdir(temp_dir)
def teardown_pipe():
    os.chdir(working_dir)
    rmtree(temp_dir)

def test_init():
    pipe = pe.Pipeline()
    yield assert_equal, type(pipe._graph), nx.DiGraph
    yield assert_equal, pipe._execgraph, None
    yield assert_equal, pipe.config['workdir'], '.'
    yield assert_equal, pipe.config['use_parameterized_dirs'], True

def test_connect():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()
    yield assert_equal, pipe._graph.get_edge_data(mod1,mod2), {'connect':[('output1','input1')]} 

def test_add_nodes():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.add_nodes([mod1,mod2])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()


def test_generate_dependency_list():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe._generate_expanded_graph()
    pipe._generate_dependency_list()
    yield assert_false, pipe._execgraph == None
    yield assert_equal, len(pipe.procs), 2
    yield assert_false, pipe.proc_done[1]
    yield assert_false, pipe.proc_pending[1]
    yield assert_equal, pipe.depidx[0,1], 1

@with_setup(setup_pipe, teardown_pipe)
def test_run_in_series():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe.run_in_series()
    nodes = pipe._execgraph.nodes()
    names = [n.name for n in nodes]
    i = names.index('mod1')
    result = nodes[i].get_output('output1')
    # NOTE: yield statements in nose cause the setup function to be
    # called at this point in the code, after all of the above is
    # executed!
    assert_equal(result, ['ran', None])

# Test graph expansion.  The following set tests the building blocks
# of the graph expansion routine.
# XXX - SG I'll create a graphical version of these tests and actually
# ensure that all connections are tested later

def test1():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    pipe.add_nodes([mod1])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 1
    yield assert_equal, len(pipe._execgraph.edges()), 0

def test2():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod1.iterables = dict(input1=lambda:[1,2],input2=lambda:[1,2])
    pipe.add_nodes([mod1])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 4
    yield assert_equal, len(pipe._execgraph.edges()), 0
    
def test3():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod1.iterables = {}
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 3
    yield assert_equal, len(pipe._execgraph.edges()), 2
    
def test4():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 4
    yield assert_equal, len(pipe._execgraph.edges()), 2

def test5():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    pipe.connect([(mod1,mod2,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 6
    yield assert_equal, len(pipe._execgraph.edges()), 4

def test6():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod3 = nw.NodeWrapper(interface=BasicInterface(),name='mod3')
    mod1.iterables = {}
    mod2.iterables = dict(input1=lambda:[1,2])
    mod3.iterables = {}
    pipe.connect([(mod1,mod2,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 5
    yield assert_equal, len(pipe._execgraph.edges()), 4

def test7():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod3 = nw.NodeWrapper(interface=BasicInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = {}
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 5
    yield assert_equal, len(pipe._execgraph.edges()), 4

def test8():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    mod3 = nw.NodeWrapper(interface=BasicInterface(),name='mod3')
    mod1.iterables = dict(input1=lambda:[1,2])
    mod2.iterables = dict(input1=lambda:[1,2])
    mod3.iterables = {}
    pipe.connect([(mod1,mod3,[('output1','input2')]),
                  (mod2,mod3,[('output1','input2')])])
    pipe._generate_expanded_graph()
    yield assert_equal, len(pipe._execgraph.nodes()), 8
    yield assert_equal, len(pipe._execgraph.edges()), 8
    edgenum = sorted([(len(pipe._execgraph.in_edges(node)) + \
                           len(pipe._execgraph.out_edges(node))) \
                          for node in pipe._execgraph.nodes()])
    yield assert_true, edgenum[0]>0
    
    
