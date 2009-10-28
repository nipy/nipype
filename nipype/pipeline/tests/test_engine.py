from nipype.testing import assert_raises, assert_equal, assert_true, assert_false
import nipype.pipeline.engine as pe
import nipype.pipeline.node_wrapper as nw
import os
from copy import deepcopy
from nipype.interfaces.base import Interface, CommandLine, Bunch, InterfaceResult
from nipype.utils.filemanip import cleandir
import networkx as nx

# nosetests --with-coverage --cover-package=nipype.pipeline.engine nipype/pipeline/tests/test_engine.py


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
    
    def outputs_help(self):
        """
           output1 : None
        """
        print self.outputs_help.__doc__
        
    def aggregate_outputs(self):
        outputs = Bunch(output1=None)
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

def test_init():
    pipe = pe.Pipeline()
    yield assert_equal, type(pipe._graph), nx.DiGraph
    yield assert_equal, pipe.listofgraphs, []
    yield assert_equal, pipe.config['workdir'], '.'
    yield assert_equal, pipe.config['use_parameterized_dirs'], False
    yield assert_equal, pipe.IPython_available, pe.IPython_available

def test_connect():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()
    yield assert_equal, pipe._graph.get_edge_data(mod1,mod2), {'connect':[('output1','input1')]} 

def test_add_modules():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.add_modules([mod1,mod2])

    yield assert_true, mod1 in pipe._graph.nodes()
    yield assert_true, mod2 in pipe._graph.nodes()


def test_generate_parameterized_graphs():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe._generate_parameterized_graphs()
    yield assert_equal, len(pipe.listofgraphs), 1
    
    mod1.iterables = {'input1': lambda : [1,2]}
    pipe._generate_parameterized_graphs()
    yield assert_equal, len(pipe.listofgraphs), 2

def test_generate_dependency_list():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe._generate_parameterized_graphs()
    pipe._generate_dependency_list()
    yield assert_equal, len(pipe.listofgraphs), 1
    yield assert_equal, len(pipe.procs), 2
    yield assert_equal, pipe.proc_hash[1], ''
    yield assert_false, pipe.proc_done[1]
    yield assert_false, pipe.proc_pending[1]
    yield assert_true, pipe.depidx[0,1]
    

def test_run_in_series():
    pipe = pe.Pipeline()
    mod1 = nw.NodeWrapper(interface=BasicInterface(),name='mod1')
    mod2 = nw.NodeWrapper(interface=BasicInterface(),name='mod2')
    pipe.connect([(mod1,mod2,[('output1','input1')])])
    pipe.run_in_series()
    nodes = pipe.listofgraphs[0].nodes()
    names = [n.name for n in nodes]
    i = names.index('mod1')
    yield assert_equal, nodes[i].get_output('output1'), ['ran',None]
    

    
    
