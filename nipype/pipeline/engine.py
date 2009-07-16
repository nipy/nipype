"""
Base class for nipy.pipeline processing modules
"""

import hashlib
import os
import copy
from subprocess import call
import networkx as nx
import numpy as np
# unused from matplotlib import mlab

def walk(children,level=0,path=None):
    """Generate all the full paths in a tree, as a dict.
    """
    # Entry point
    if level==0: path = {}
    
    # Exit condition
    if not children:
        yield path.copy()
        return

    # Tree recursion
    head, tail = children[0],children[1:]
    name,func = head
    for child in func():
        # We can use the arg name or the tree level as a key
        path[name] = child
        #path[level] = child

        # Recurse into the next level
        for child_paths in walk(tail,level+1,path):
            yield child_paths
        
class DiskNodeDirExists(Exception):
    pass


class PipelineNode(object):
    """Make a basic pipeline element that takes an arbitrary callable object
    """
    class NoObjectError():
        pass
    
    def __init__(self,obj=None,**kwargs):
        '''Make a PipelineNode'''
        if obj is not None:
            self.node = obj
        else:
            self.node.name = None
            self.node.inputs = {}
            self.node.outputs = {}

    def execute(self):
        if self.node:
            call(self.node)
        else:
            raise NoObjectError()
        
    def cleaner(self):
        pass


class MemoryNode(PipelineNode):
    """All interface processing elements should inherit this class
    """

    def __init__(self,io_object=None,**kwargs):
        '''Make a MemoryNode'''

        super(MemoryNode,self).__init__(io_object)
        self.iterables = {}

    @property
    def name(self):
        return self.node.name

    @property
    def inputs(self):
        return self.node.inputs

    @property
    def outputs(self):
        return self.node.outputs

    def __str__(self):
        return self.node.name

    def hash_inputs(self):
        return hashlib.md5(str(self.node.inputs)).hexdigest()


    def execute(self,cwd=None):
        """Execute node
        """
        if cwd:
            return self.node.run(cwd=cwd)
        else:
            return self.node.run()

    def extended_help(self):
        """see extended_help(self)
        """
        if self.node.name != 'base':
            call([self.node.name])
        print "Email: matthew.brett@gmail.com"


class DiskNode(MemoryNode):
    """Pipeline module to extract the brain using FSL bet
    """
    def __init__(self,interfaceobj=None,iterables={},output_directory='.'):
        # call baseclass __init__ to initialize state dictionary
        super(DiskNode,self).__init__(interfaceobj)
        self.output_directory_base  = output_directory

    def output_directory(self):
        return os.path.join(self.output_directory_base,
                            ''.join((self.node.name, '_0x', self.hash_inputs())))

    def make_output_dir(self):
        """Make the output_dir if it doesn't exist, else raise an exception
        """
        # This needs to be changed to update dynamically based on a hash of
        # CURRENT instance attributes
        odir = os.path.abspath(self.output_directory())
        if os.path.exists(odir):
            raise DiskNodeDirExists(odir)
        os.mkdir(odir)
        return odir

    def execute(self, overwrite=False):
        """Set up appropriate directories and execute the cmd
        """
        try:
            odir = self.make_output_dir()
        except DiskNodeDirExists:
            if not overwrite:
                odir = os.path.abspath(self.output_directory())
                try:
                    self.node.pre_execute(cwd=odir)
                    self.node.post_execute(cwd=odir)
                    return
                except:
                    print '=============================================='
                    print 'PSSSS: Not cleaning directory to let you debug'
                    print 'Make sure to remove %s before you run again'  %  odir
                    print "=============================================="
                    raise
               
        cwd = os.path.abspath(os.path.curdir)

        try:
            super(DiskNode,self).execute(cwd=odir)
        except:
            #self.cleaner()
            print "=============================================="
            print "PSSSS: Not cleaning directory to let you debug"
            print "Make sure to remove %s before you run again"  %  odir 
            print "=============================================="
            raise

    def cleaner(self):
        odir = self.output_directory()
        os.rmdir(odir)


def generate_pipeline_node(io_object):
    if io_object.diskbased:
        return DiskNode(io_object)
    else:
        return MemoryNode(io_object)

class Pipeline(nx.DiGraph):
    """Setup and execution of a neuroimaging pipeline
    """

    def __init__(self):
        """
        """
        super(Pipeline,self).__init__()
        self.listofgraphs = []
        self.config       = {}
        self.config['workdir'] = '.'
        self.config['distribute'] = False
        self.config['nworkers'] = 1

    def runserially(self):
        """Executes a pre-defined pipeline
        
        Arguments:
        - `self`: 
        """
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self.listofgraphs = []
        self.generate_parameterized_graphs()

        for graph in self.listofgraphs:
            order = nx.topological_sort(graph)
            for node in order:
                # the following block needs to executed whenever the
                # node is actually executed.
                for edge in graph.in_edges_iter(node):
                    data = graph.get_edge_data(*edge)
                    for sourcename,destname in data:
                        #sourcename,destname = data[0]
                        node.inputs[destname] = edge[0].outputs[sourcename]
                #print "Executing: ",node.node.name
                # print node.node.inputs
                if node.diskbased:
                    node.output_directory_base = os.path.abspath(self.config['workdir'])
                node.execute()

    def generate_parameterized_graphs(self):
        """        
        Arguments:
        - `self`:
        """
        iterables = []
        for i,node in enumerate(nx.topological_sort(self)):
            for key,func in node.iterables.items():
                iterables.append(((i,key),func))
        if len(iterables) == 0:
            self.listofgraphs.append(copy.deepcopy(self))
            return
        for i,params in enumerate(walk(iterables)):
            # copy the graph
            graphcopy = copy.deepcopy(self)
            self.listofgraphs.append(graphcopy)
            order = nx.topological_sort(graphcopy)
            for key,val in params.items():
                # assign values to the nodes
                #order[key[0]].inputs[key[1]] = val
                order[key[0]].update(**{key[1]:val})
    def run_with_manager(self):
        """Executes a pre-defined pipeline
        
        Arguments:
        - `self`: 
        """
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self.listofgraphs = []
        self.generate_parameterized_graphs()
        listofprocesses = []
        for graph in self.listofgraphs:
            order = nx.topological_sort(graph)
            for node in order:
                # the following block needs to executed whenever the
                # node is actually executed.
                deps = []
                for edge in graph.in_edges_iter(node):
                    deps.append(edge[0])
                listofprocesses.append([node,deps])
        for i,process in enumerate(listofprocesses):
            print i,process[0].name
            for deps in process[1]:
                print "dep:", deps.name
    
    def connect(self,connection_list):
        """
        Arguments:
        - `self`:
        - `connection_list`:
        """
        self.add_edges_from(connection_list)

    def addmodules(self,modules):
        """
        
        Arguments:
        - `self`:
        - `modules`:
        """
        self.add_nodes_from(modules)

    def showgraph(self,prog='dot'):
        """
        
        Arguments:
        - `self`:
        """
        nx.draw_graphviz(self,prog=prog)
    
