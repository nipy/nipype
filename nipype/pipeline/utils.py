"""Defines functionality for pipelined execution of interfaces

The `Pipeline` class provides core functionality for batch processing. 
"""

from copy import deepcopy
import logging.handlers
import os
import pwd
from shutil import rmtree
from socket import gethostname
import sys
from tempfile import mkdtemp
from time import sleep, strftime
from traceback import format_exception
from warnings import warn

import numpy as np

from nipype.utils.misc import package_check
package_check('networkx', '1.0')
import networkx as nx
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass


from nipype.interfaces.base import traits, File, Directory, InputMultiPath,\
    OutputMultiPath, TraitedSpec, CommandLine, Bunch, InterfaceResult,\
    isdefined
from nipype.utils.filemanip import fname_presuffix, save_json, FileNotFoundError,\
    filename_to_list, list_to_filename, copyfiles, fnames_presuffix

#Sets up logging for pipeline and nodewrapper execution
LOG_FILENAME = 'pypeline.log'
logging.basicConfig()
logger = logging.getLogger('workflow')
nwlogger = logging.getLogger('node')
fmlogger = logging.getLogger('filemanip')
hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                            maxBytes=256000,
                                            backupCount=4)
formatter = logging.Formatter(fmt='%(asctime)s,%(msecs)d %(name)-2s '\
                                  '%(levelname)-2s:\n\t %(message)s',
                              datefmt='%y%m%d-%H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)
nwlogger.addHandler(hdlr)
nwlogger.setLevel(logging.INFO)
fmlogger.addHandler(hdlr)
fmlogger.setLevel(logging.INFO)

def walk(children, level=0, path=None, usename=True):
    """Generate all the full paths in a tree, as a dict.
    """
    # Entry point
    if level == 0:
        path = {}
    # Exit condition
    if not children:
        yield path.copy()
        return
    # Tree recursion
    head, tail = children[0], children[1:]
    name, func = head
    for child in func():
        # We can use the arg name or the tree level as a key
        if usename:
            path[name] = child
        else:
            path[level] = child
        # Recurse into the next level
        for child_paths in walk(tail, level+1, path, usename):
            yield child_paths
        
def _create_pickleable_graph(graph, show_connectinfo=False):
    """Create a graph that can be pickled.

    Ensures that edge info is pickleable.
    """
    logger.debug('creating pickleable graph')
    pklgraph = deepcopy(graph)
    for edge in pklgraph.edges():
        data = pklgraph.get_edge_data(*edge)
        pklgraph.remove_edge(*edge)
        if show_connectinfo:
            pklgraph.add_edge(edge[0], edge[1], l=str(data['connect']))
        else:
            pklgraph.add_edge(edge[0], edge[1])
    return pklgraph

def _write_detailed_dot(graph, dotfilename):
    """Create a dot file with connection info

    digraph structs {
    node [shape=record];
    struct1 [label="<f0> left|<f1> mid\ dle|<f2> right"];
    struct2 [label="<f0> one|<f1> two"];
    struct3 [label="hello\nworld |{ b |{c|<here> d|e}| f}| g | h"];
    struct1:f1 -> struct2:f0;
    struct1:f0 -> struct2:f1;
    struct1:f2 -> struct3:here;
    }
    """
    text = ['digraph structs {', 'node [shape=record];']
    # write nodes
    edges = []
    replacefunk = lambda x: x.replace('_', '').replace('.', ''). \
        replace('@', '').replace('-', '')
    for n in graph.nodes():
        nodename = str(n)
        inports = []
        for u, v, d in graph.in_edges_iter(nbunch=n, data=True):
            for cd in d['connect']:
                if isinstance(cd[0], str):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                inport = cd[1]
                ipstrip = replacefunk(inport)
                opstrip = replacefunk(outport)
                edges.append('%s:%s -> %s:%s;' % (str(u).replace('.', ''),
                                                  opstrip,
                                                  str(v).replace('.', ''),
                                                  ipstrip))
                if inport not in inports:
                    inports.append(inport)
        inputstr = '{IN'
        for ip in inports:
            inputstr += '|<%s> %s' % (replacefunk(ip), ip)
        inputstr += '}'
        outports = []
        for u, v, d in graph.out_edges_iter(nbunch=n, data=True):
            for cd in d['connect']:
                if isinstance(cd[0], str):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                if outport not in outports:
                    outports.append(outport)
        outputstr = '{OUT'
        for op in outports:
            outputstr += '|<%s> %s' % (replacefunk(op), op)
        outputstr += '}'
        text += ['%s [label="%s|%s|%s"];' % (nodename.replace('.', ''),
                                             inputstr, nodename,
                                             outputstr)]
    # write edges
    for edge in edges:
        text.append(edge)
    text.append('}')
    filep = open(dotfilename, 'wt')
    filep.write('\n'.join(text))
    filep.close()
    return text

def _merge_graphs(supergraph, nodes, subgraph, nodeid, iterables):
    """Merges two graphs that share a subset of nodes.

    If the subgraph needs to be replicated for multiple iterables, the
    merge happens with every copy of the subgraph. Assumes that edges
    between nodes of supergraph and subgraph contain data.

    Parameters
    ----------
    supergraph : networkx graph
    Parent graph from which subgraph was selected
    nodes : networkx nodes
    Nodes of the parent graph from which the subgraph was initially
    constructed.
    subgraph : networkx graph
    A subgraph that contains as a subset nodes from the supergraph.
    These nodes connect the subgraph to the supergraph
    nodeid : string
    Identifier of a node for which parameterization has been sought
    iterables : dict of functions
    see `pipeline.NodeWrapper` for iterable requirements

    Returns
    -------
    Returns a merged graph containing copies of the subgraph with
    appropriate edge connections to the supergraph.
    
    """
    # Retrieve edge information connecting nodes of the subgraph to other
    # nodes of the supergraph.
    supernodes = supergraph.nodes()
    ids = [n._id for n in supernodes]
    edgeinfo = {}
    for n in subgraph.nodes():
        nidx = ids.index(n._id)
        for edge in supergraph.in_edges_iter(supernodes[nidx]):
                #make sure edge is not part of subgraph
            if edge[0] not in subgraph.nodes():
                if n._id not in edgeinfo.keys():
                    edgeinfo[n._id] = []
                edgeinfo[n._id].append((edge[0],
                                       supergraph.get_edge_data(*edge)))
    supergraph.remove_nodes_from(nodes)
    # Add copies of the subgraph depending on the number of iterables
    for i, params in enumerate(walk(iterables.items())):
        Gc = deepcopy(subgraph)
        ids = [n._id for n in Gc.nodes()]
        nodeidx = ids.index(nodeid)
        paramstr = ''
        for key, val in sorted(params.items()):
            paramstr = '_'.join((paramstr, key,
                                 str(val).replace(os.sep, '_')))
            setattr(Gc.nodes()[nodeidx].inputs, key, val)
        for n in Gc.nodes():
            """
            update parameterization of the node to reflect the location of
            the output directory.  For example, if the iterables along a
            path of the directed graph consisted of the variables 'a' and
            'b', then every node in the path including and after the node
            with iterable 'b' will be placed in a directory
            _a_aval/_b_bval/.
            """
            if n.parameterization:
                n.parameterization = os.path.join(paramstr,
                                                  n.parameterization)
            else:
                n.parameterization = paramstr
        supergraph.add_nodes_from(Gc.nodes())
        supergraph.add_edges_from(Gc.edges(data=True))
        for node in Gc.nodes():
            if node._id in edgeinfo.keys():
                for info in edgeinfo[node._id]:
                    supergraph.add_edges_from([(info[0], node, info[1])])
            node._id += str(i)
    return supergraph

def _report_nodes_not_run(notrun):
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            logger.error("could not run node: %s" % info['node']._id)
            logger.info("crashfile: %s" % info['crashfile'])
            logger.debug("The following dependent nodes were not run")
            for subnode in info['dependents']:
                logger.debug(subnode._id)
        logger.info("***********************************")


def make_output_dir(outdir):
    """Make the output_dir if it doesn't exist.

    Parameters
    ----------
    outdir : output directory to create
    
    """
    if not os.path.exists(os.path.abspath(outdir)):
        # XXX Should this use os.makedirs which will make any
        # necessary parent directories?  I didn't because the one
        # case where mkdir failed because a missing parent
        # directory, something went wrong up-stream that caused an
        # invalid path to be passed in for `outdir`.
        logger.info("Creating %s" % outdir)
        os.mkdir(outdir)
    return outdir

class WorkflowBase(object):
    """ Define common attributes and functions for workflows and nodes
    """

    def __init__(self, name=None, base_dir=None,
                 overwrite=False, **kwargs):
        """ Initialize base parameters of a workflow or node

        Parameters
        ----------
        
        base_dir : directory
            base output directory (will be hashed before creations)
            default=None, which results in the use of mkdtemp
        overwrite : Boolean
            Whether to overwrite contents of output directory if it already
            exists. If directory exists and hash matches it
            assumes that process has been executed (default : False)
        name : string (mandatory)
            Name of this node. By default node is named
            modulename.classname. But when the same class is being used several
            times, a different name ensures that output directory is not
            overwritten each time the same functionality is run. 
        """
        self.base_dir = base_dir
        self.overwrite = overwrite
        if name is None:
            raise Exception("init requires a name for this %s" % self.__class__.__name__)
        self.name = name
        
        # for compatibility with node expansion using iterables
        self._id = self.name

    @property
    def inputs(self):
        raise NotImplementedError

    @property
    def outputs(self):
        raise NotImplementedError

    def clone(self, name):
        if name is None:
            raise Exception('Cloning requires a new name')
        clone = deepcopy(self)
        clone.name = name
        clone._id = name
        return clone

    def check_outputs(self, parameter):
        return hasattr(self.outputs, parameter)
    
    def check_inputs(self, parameter):
        return hasattr(self.inputs, parameter)
    
    def __repr__(self):
        return self._id

    def _output_directory(self):
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        return os.path.abspath(os.path.join(self.base_dir,
                                            self.name))

    def save(self, filename=None):
        if filename is None:
            filename = 'temp.npz'
        np.savez(filename, object=self)

    def load(self, filename):
        np.load(filename)

class Workflow(WorkflowBase):
    """Controls the setup and execution of a pipeline of processes
    """

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self._graph = nx.DiGraph()
        self.ipyclient = None
        self.taskclient = None
        try:
            name = 'IPython.kernel.client'
            __import__(name)
            self.ipyclient = sys.modules[name]
        except ImportError:
            warn("Ipython kernel not found.  Parallel execution will be" \
                     "unavailable", ImportWarning)
        # attributes for running with manager
        self.procs = None
        self.depidx = None
        self.proc_done = None
        self.proc_pending = None
        self._execgraph = None

    def connect(self, *args):
        """Connect nodes in the pipeline.

        This routine also checks if inputs and outputs are actually provided by
        the nodes that are being connected. 

        Creates edges in the directed graph using the nodes and edges specified
        in the `connection_list`.  Uses the NetworkX method
        DiGraph.add_edges_from. 

        Parameters
        ----------
        args : list or a set of four positional arguments

            Four positional arguments of the form::
            
              connect(source, sourceoutput, dest, destinput)
              
            source : nodewrapper node
            sourceoutput : string (must be in source.outputs)
            dest : nodewrapper node
            destinput : string (must be in dest.inputs)
        
            A list of 3-tuples of the following form::

             [(source, target,
                 [('sourceoutput/attribute', 'targetinput'),
                 ...]), 
             ...]
            
            Or::

             [(source, target, [(('sourceoutput1', func, arg2, ...),
                                         'targetinput'), ...]),
             ...]
             sourceoutput1 will always be the first argument to func
             and func will be evaluated and the results sent ot targetinput
        """
        if len(args)==1:
            connection_list = args[0]
        elif len(args)==4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise Exception('unknown set of parameters to connect function')
        not_found = []
        for srcnode, destnode, connects in connection_list:
            for source, dest in connects:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if not (hasattr(destnode, '_interface') and '.io' in str(destnode._interface.__class__)):
                    if not destnode.check_inputs(dest):
                        not_found.append(['in', destnode.name, dest])
                if not (hasattr(srcnode, '_interface') and '.io' in str(srcnode._interface.__class__)):
                    if isinstance(source, tuple):
                        # handles the case that source is specified
                        # with a function
                        sourcename = source[0]
                    elif isinstance(source, str):
                        sourcename = source
                    else:
                        raise Exception('Unknown source specification in' \
                                         'connection from output of %s'%
                                        srcnode.name)
                    if sourcename and not srcnode.check_outputs(sourcename):
                        not_found.append(['out', srcnode.name, sourcename])
        for info in not_found: 
            warn("Module %s has no %sput called %s\n"%(info[1], info[0],
                                                       info[2]))
        if not_found:
            raise Exception('Some connections were not found')
        # add connections
        for srcnode, destnode, connects in connection_list:
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            if edge_data:
                logger.debug('(%s, %s): Edge data exists: %s' % \
                                 (srcnode, destnode, str(edge_data)))
                for data in connects:
                    if data not in edge_data['connect']:
                        edge_data['connect'].append(data)
                self._graph.add_edges_from([(srcnode, destnode, edge_data)])
            else:
                logger.debug('(%s, %s): No edge data' % (srcnode, destnode))
                self._graph.add_edges_from([(srcnode, destnode,
                                             {'connect': connects})])
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            logger.debug('(%s, %s): new edge data: %s'% (srcnode, destnode,
                                                         str(edge_data)))

    def add_nodes(self, nodes):
        """ Wraps the networkx functionality in a more semantically
        relevant function name

        Parameters
        ----------
        nodes : list
            A list of WorkflowBase-based objects
        """
        for node in nodes:
            if not issubclass(node.__class__, WorkflowBase):
                raise Exception('Node %s must be a subclass of WorkflowBase' % str(node))
            self._graph.add_nodes_from([node])

    @property
    def inputs(self):
        return self.get_inputs()

    @property
    def outputs(self):
        return self.get_outputs()

    def get_exec_node(self, name):
        if self._execgraph:
            return [node  for node in self._execgraph.nodes() if name == str(node)]
        return None
    
    def _has_attr(self, parameter, subtype='in'):
        if subtype == 'in':
            subobject = self.inputs
        else:
            subobject = self.outputs
        attrlist = parameter.split('.')
        cur_out = subobject
        for attr in attrlist:
            if not hasattr(cur_out, attr):
                return False
            cur_out = getattr(cur_out, attr)
        return True

    def get_parameter_node(self, parameter, subtype='in'):
        if subtype == 'in':
            subobject = self.inputs
        else:
            subobject = self.outputs
        attrlist = parameter.split('.')
        cur_out = subobject
        for attr in attrlist[:-1]:
            cur_out = getattr(cur_out, attr)
        return cur_out.traits()[attrlist[-1]].node
        
    def check_outputs(self, parameter):
        return self._has_attr(parameter, subtype='out')
    
    def check_inputs(self, parameter):
        return self._has_attr(parameter, subtype='in')
    
    def get_inputs(self):
        inputdict = TraitedSpec()
        for node in self._graph.nodes():
            inputdict.add_trait(node.name, traits.Instance(TraitedSpec))
            if isinstance(node, Workflow):
                setattr(inputdict, node.name, node.inputs)
            else:
                taken_inputs = []
                for _, _, d in self._graph.in_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        taken_inputs.append(cd[1])
                unconnectedinputs = TraitedSpec() 
                for key, trait in node.inputs.items():
                    if key not in taken_inputs:
                        unconnectedinputs.add_trait(key, traits.Trait(trait, node=node))
                        value = getattr(node.inputs, key)
                        setattr(unconnectedinputs, key, value)
                setattr(inputdict, node.name, unconnectedinputs)
                getattr(inputdict, node.name).on_trait_change(self.set_input)
        return inputdict
        
    def get_outputs(self):
        outputdict = TraitedSpec()
        for node in self._graph.nodes():
            outputdict.add_trait(node.name, traits.Instance(TraitedSpec))
            if isinstance(node, Workflow):
                setattr(outputdict, node.name, node.outputs)
            else:
                outputs = TraitedSpec() 
                for key, _ in node.outputs.items():
                    outputs.add_trait(key, traits.Any(node=node))
                    setattr(outputs, key, None)
                setattr(outputdict, node.name, outputs)
        return outputdict
        
    def set_input(self, object, name, newvalue):
        setattr(object.traits()[name].node.inputs, name, newvalue)

    def export_graph(self, show = False, use_execgraph=False,
                     show_connectinfo=False, dotfilename='graph.dot'):
        """ Displays the graph layout of the pipeline

        This function requires that pygraphviz and matplotlib are available on
        the system.

        Parameters
        ----------

        show : boolean
            Indicate whether to generate pygraphviz output fromn
            networkx. default [False]
            
        use_execgraph : boolean
            Indicates whether to use the specification graph or the
            execution graph. default [False]
       
        show_connectioninfo : boolean
            Indicates whether to show the edge data on the graph. This
            makes the graph rather cluttered. default [False]
        """
        if use_execgraph:
            self._generate_expanded_graph()
            graph = deepcopy(self._execgraph)
            logger.debug('using execgraph')
        else:
            graph = deepcopy(self._graph)
            logger.debug('using input graph')
        outfname = fname_presuffix(dotfilename,
                                   suffix='_detailed.dot',
                                   use_ext=False,
                                   newpath=self.base_dir)
        logger.info('Creating detailed dot file: %s'%outfname)
        _write_detailed_dot(graph, outfname)
        cmd = 'dot -Tpng -O %s' % outfname
        res = CommandLine(cmd).run()
        if res.runtime.returncode:
            logger.warn('dot2png: %s', res.runtime.stderr)
        pklgraph = _create_pickleable_graph(graph, show_connectinfo)
        outfname = fname_presuffix(dotfilename,
                                   suffix='.dot',
                                   use_ext=False,
                                   newpath=self.base_dir)
        nx.write_dot(pklgraph, outfname)
        logger.info('Creating dot file: %s' % outfname)
        cmd = 'dot -Tpng -O %s' % outfname
        res = CommandLine(cmd).run()
        if res.runtime.returncode:
            logger.warn('dot2png: %s', res.runtime.stderr)
        if show:
            pos = nx.graphviz_layout(pklgraph, prog='dot')
            nx.draw(pklgraph, pos)
            if show_connectinfo:
                nx.draw_networkx_edge_labels(pklgraph, pos)

    def run(self):
        self._create_flat_graph()
        self._generate_expanded_graph()
        self._execute_with_manager()

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, str):
            val = source.get_output(sourceinfo)
        elif isinstance(sourceinfo, tuple):
            if callable(sourceinfo[1]):
                val = sourceinfo[1](source.get_output(sourceinfo[0]),
                                    *sourceinfo[2:])
        logger.debug('setting input: %s->%s', param, str(val))
        node.set_input(param, deepcopy(val))

    def _execute_in_series(self, updatehash=False, force_execute=None):
        """Executes a pre-defined pipeline in a serial order.

        Parameters
        ----------
        updatehash : boolean
            Allows one to rerun a pipeline and update all the hashes without
            actually executing any of the underlying interfaces. This is useful
            when moving the working directory from one location to another. It
            is also useful when the hashing function itself changes (although
            we hope that this will not happen often). default [False]
        force_execute : list of strings
            This forces execution of a node even if updatehash is True
        """
        # In the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        logger.info("Running serially.")
        self._create_flat_graph()
        self._generate_expanded_graph()
        old_wd = os.getcwd()
        notrun = []
        donotrun = []
        for node in nx.topological_sort(self._execgraph):
            # Assign outputs from dependent executed nodes to current node.
            # The dependencies are stored as data on edges connecting
            # nodes.
            try:
                if node in donotrun:
                    continue
                for edge in self._execgraph.in_edges_iter(node):
                    data = self._execgraph.get_edge_data(*edge)
                    logger.debug('setting input: %s->%s %s',
                                 edge[0], edge[1], str(data))
                    for sourceinfo, destname in data['connect']:
                        self._set_node_input(node, destname,
                                             edge[0], sourceinfo)
                self._set_output_directory_base(node)
                redo = None
                if force_execute:
                    if isinstance(force_execute, str):
                        force_execute = [force_execute]
                    redo = any([node.name.lower()==l.lower() \
                                    for l in force_execute])
                if updatehash and not redo:
                    node.run(updatehash=updatehash)
                else:
                    node.run(force_execute=redo)
            except:
                os.chdir(old_wd)
                # bare except, but i really don't know where a
                # node might fail
                crashfile = self._report_crash(node)
                # remove dependencies from queue
                subnodes = nx.dfs_preorder(self._execgraph, node)
                notrun.append(dict(node = node,
                                   dependents = subnodes,
                                   crashfile = crashfile))
                donotrun.extend(subnodes)
        _report_nodes_not_run(notrun)

                
    def _report_crash(self, node, traceback=None):
        """Writes crash related information to a file
        """
        message = ['Node %s failed to run.' % node._id]
        logger.error(message)
        if not traceback:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback = format_exception(exc_type,
                                         exc_value,
                                         exc_traceback)
        timeofcrash = strftime('%Y%m%d-%H%M%S')
        login_name = pwd.getpwuid(os.geteuid())[0]
        crashfile = 'crash-%s-%s-%s.npz' % (timeofcrash,
                                            login_name,
                                            node._id)
        if hasattr(self, 'config') and self.config['crashdump_dir']:
            crashfile = os.path.join(self.config['crashdump_dir'],
                                     crashfile)
        else:
            crashfile = os.path.join(os.getcwd(), crashfile)
        pklgraph = _create_pickleable_graph(self._execgraph,
                                            show_connectinfo=True)
        logger.info('Saving crash info to %s' % crashfile)
        logger.info(''.join(traceback))
        np.savez(crashfile, node=node, execgraph=pklgraph, traceback=traceback)
        return crashfile

    def _set_output_directory_base(self, node):
        """Determine output directory and create it
        """
        # update parameterization of output directory
        outputdir = self.base_dir
        if node.parameterization:
            outputdir = os.path.join(outputdir, node.parameterization)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        node.base_dir = os.path.abspath(outputdir)
            

    def _generate_expanded_graph(self):
        """Generates an expanded graph based on node parameterization

        Parameterization is controlled using the `iterables` field of the
        pipeline elements.  Thus if there are two nodes with iterables a=[1,2]
        and b=[3,4] this procedure will generate a graph with sub-graphs
        parameterized as (a=1,b=3), (a=1,b=4), (a=2,b=3) and (a=2,b=4). 
        """
        logger.info("PE: expanding iterables")
        graph_in = deepcopy(self._flatgraph)
        moreiterables = True
        # convert list of tuples to dict fields
        for node in graph_in.nodes():
            if isinstance(node.iterables, tuple):
                node.iterables = [node.iterables]
        for node in graph_in.nodes():
            if isinstance(node.iterables, list):
                node.iterables = dict(map(lambda(x):(x[0], lambda:x[1]),
                                          node.iterables))
        while moreiterables:
            nodes = nx.topological_sort(graph_in)
            nodes.reverse()
            inodes = [node for node in nodes if len(node.iterables.keys())>0]
            if inodes:
                node = inodes[0]
                iterables = node.iterables.copy()
                node.iterables = {}
                node._id += 'I'
                subnodes = nx.dfs_preorder(graph_in, node)
                subgraph = graph_in.subgraph(subnodes)
                graph_in = _merge_graphs(graph_in, subnodes,
                                         subgraph, node._id,
                                         iterables)
            else:
                moreiterables = False
        self._execgraph = graph_in
        logger.info("PE: expanding iterables ... done")


    def _create_flat_graph(self):
        workflowcopy = deepcopy(self)
        workflowcopy._generate_execgraph()
        self._flatgraph = workflowcopy._graph
        
    def _generate_execgraph(self):
        nodes2remove = []
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                for u, _, d in self._graph.in_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        logger.info("in: %s" % str (cd))
                        dstnode = node.get_parameter_node(cd[1],subtype='in')
                        srcnode = u
                        srcout = cd[0]
                        dstin = cd[1].split('.')[-1]
                        self.connect(srcnode, srcout, dstnode, dstin)
                for _, v, d in self._graph.out_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        logger.info("out: %s" % str (cd))
                        dstnode = v
                        if isinstance(cd[0], tuple):
                            parameter = cd[0][0]
                        else:
                            parameter = cd[0]
                        srcnode = node.get_parameter_node(parameter, subtype='out')
                        if isinstance(cd[0], tuple):
                            srcout = cd[0]
                            srcout[0] = parameter.split('.')[-1]
                        else:
                            srcout = parameter.split('.')[-1]
                        dstin = cd[1]
                        self.connect(srcnode, srcout, dstnode, dstin)
                # expand the workflow node
                node._generate_execgraph()
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
        if nodes2remove:
            self._graph.remove_nodes_from(nodes2remove)

    def _generate_dependency_list(self):
        """ Generates a dependency list for a list of graphs. Adds the
        following attributes to the pipeline:

        New attributes:
        ---------------
        
        procs: list (N) of underlying interface elements to be
        processed 
        proc_done: a boolean vector (N) signifying whether a process
        has been executed
        proc_pending: a boolean vector (N) signifying whether a
        process is currently running. 
        Note: A process is finished only when both proc_done==True and
        proc_pending==False
        depidx: a boolean matrix (NxN) storing the dependency
        structure accross processes. Process dependencies are derived
        from each column. 
        """
        if not self._execgraph:
            raise Exception('Execution graph has not been generated')
        self.procs = self._execgraph.nodes()
        self.depidx = nx.adj_matrix(self._execgraph).__array__()
        self.proc_done    = np.zeros(len(self.procs), dtype=bool)
        self.proc_pending = np.zeros(len(self.procs), dtype=bool)

    def _remove_node_deps(self, jobid, crashfile):
        subnodes = nx.dfs_preorder(self._execgraph, self.procs[jobid])
        for node in subnodes:
            idx = self.procs.index(node)
            self.proc_done[idx] = True
            self.proc_pending[idx] = False
        return dict(node = self.procs[jobid],
                    dependents = subnodes,
                    crashfile = crashfile)
        
    def _execute_with_manager(self):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # retrieve clients again
        if not self.taskclient:
            try:
                self.taskclient = self.ipyclient.TaskClient()
            except ConnectionRefusedError:
                warn("No clients found, running serially for now.")
                self._execute_in_series()
                return
        logger.info("Running in parallel.")
        self.taskclient.clear()
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list()
        # get number of ipython clients available
        self.pending_tasks = []
        self.readytorun = []
        # setup polling
        notrun = []
        while np.any(self.proc_done==False) | np.any(self.proc_pending==True):
            toappend = []
            # trigger callbacks for any pending results
            while self.pending_tasks:
                taskid, jobid = self.pending_tasks.pop()
                res = self.taskclient.get_task_result(taskid, block=False)
                if res:
                    if res.failure:
                        try:
                            res.raise_exception()
                        except:
                            crashfile = self._report_crash(self.procs[jobid])
                            # remove dependencies from queue
                            notrun.append(self._remove_node_deps(jobid, crashfile))
                    else:
                        self._task_finished_cb(res['result'], jobid)
                else:
                    toappend.insert(0, (taskid, jobid))
            if toappend:
                self.pending_tasks.extend(toappend)
            else:
                self.taskclient.clear()
            self._send_procs_to_workers()
            sleep(2)
        self.taskclient.clear()
        _report_nodes_not_run(notrun)
                
    def _send_procs_to_workers(self):
        """ Sends jobs to workers using ipython's taskclient interface
        """
        while np.any(self.proc_done == False):
            # Check to see if a job is available
            jobids = np.flatnonzero((self.proc_done == False) & \
                                        np.all(self.depidx==0, axis=0))
            if len(jobids)>0:
                # send all available jobs
                logger.info('Submitting %d jobs' % len(jobids))
                for jobid in jobids:
                    # change job status in appropriate queues
                    self.proc_done[jobid] = True
                    self.proc_pending[jobid] = True
                    self._set_output_directory_base(self.procs[jobid])
                    # Send job to task manager and add to pending tasks
                    _, hashvalue = self.procs[jobid].inputs._get_hashval()
                    logger.info('Executing: %s ID: %d H:%s' % \
                                    (self.procs[jobid]._id, jobid, hashvalue))
                    cmdstr = "result = task.run()"
                    task = self.ipyclient.StringTask(cmdstr,
                                                     push = dict(task=self.procs[jobid]),
                                                     pull = 'result')
                    tid = self.taskclient.run(task, block = False)
                    self.pending_tasks.insert(0, (tid, jobid))
            else:
                break

    def _task_finished_cb(self, result, jobid):
        """ Extract outputs and assign to inputs of dependent tasks

        This is called when a job is completed.
        """
        logger.info('[Job finished] jobname: %s jobid: %d' % \
                        (self.procs[jobid]._id, jobid))
        # Update job and worker queues
        self.proc_pending[jobid] = False
        if self.procs[jobid]._result != result:
            self.procs[jobid]._result = result
        # Update the inputs of all tasks that depend on this job's outputs
        graph = self._execgraph
        for edge in graph.out_edges_iter(self.procs[jobid]):
            data = graph.get_edge_data(*edge)
            for sourceinfo, destname in data['connect']:
                logger.debug('%s %s %s %s',edge[1], destname, self.procs[jobid], sourceinfo)
                self._set_node_input(edge[1], destname,
                                     self.procs[jobid], sourceinfo)
        # update the job dependency structure
        self.depidx[jobid, :] = 0.



class Node(WorkflowBase):
    """Wraps interface objects for use in pipeline
    

    Parameters
    ----------
    interface : interface object
        node specific interface  (fsl.Bet(), spm.Coregister())
    iterables : generator
        input field and list to iterate using the pipeline engine
        for example to iterate over different frac values in fsl.Bet()
        for a single field the input can be a tuple, otherwise a list
        of tuples
        node.iterables = ('frac',[0.5,0.6,0.7])
        node.iterables = [('fwhm',[2,4]),('fieldx',[0.5,0.6,0.7])]
    
    Notes
    -----
    creates output directory
    copies/discovers files to work with
    saves a hash.json file to indicate that a process has been completed

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> realign = Node(interface=spm.Realign(), base_directory='test2')
    >>> realign.inputs.infile = os.path.abspath('data/funcrun.nii')
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """
    def __init__(self, interface, iterables={}, **kwargs):
        # interface can only be set at initialization
        super(Node, self).__init__(**kwargs)
        if interface is None:
            raise Exception('Interface must be provided')
        self._interface  = interface
        self._result     = None
        self.iterables  = iterables
        self.parameterization = None

    @property
    def interface(self):
        return self._interface
    
    @property
    def result(self):
        return self._result

    @property
    def inputs(self):
        return self._interface.inputs

    @property
    def outputs(self):
        return self._interface._outputs()

    def set_input(self, parameter, val):
        """ Set interface input value or nodewrapper attribute

        Priority goes to interface.
        """
        setattr(self._interface.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        val = None
        if self._result:
            val = getattr(self._result.outputs, parameter)
        return val

    def _save_hashfile(self, hashfile, hashed_inputs):
        try:
            save_json(hashfile, hashed_inputs)
        except (IOError, TypeError):
            err_type = sys.exc_info()[0]
            if err_type is TypeError:
                # XXX - SG current workaround is to just
                # create the hashed file and not put anything
                # in it
                fd = open(hashfile,'wt')
                fd.writelines(str(hashed_inputs))
                fd.close()
                logger.warn('Unable to write a particular type to the json '\
                                'file') 
            else:
                logger.critical('Unable to open the file in write mode: %s'% \
                                    hashfile)
        
        
    def run(self,updatehash=None,force_execute=False):
        """Executes an interface within a directory.
        """
        # check to see if output directory and hash exist
        logger.info("Node: %s"%self._id)
        outdir = self._output_directory()
        outdir = make_output_dir(outdir)
        logger.info("in dir: %s"%outdir)
        # Get a dictionary with hashed filenames and a hashvalue
        # of the dictionary itself.
        hashed_inputs, hashvalue = self.inputs._get_hashval()
        hashfile = os.path.join(outdir, '_0x%s.json' % hashvalue)
        if updatehash:
            logger.info("Updating hash: %s"%hashvalue)
            self._save_hashfile(hashfile,hashed_inputs)
        if force_execute or (not updatehash and (self.overwrite or not os.path.exists(hashfile))):
            logger.info("Node hash: %s"%hashvalue)
            if os.path.exists(outdir):
                logger.debug("Removing old %s and its contents"%outdir)
                rmtree(outdir)
                outdir = make_output_dir(outdir)
            self._run_interface(execute=True, cwd=outdir)
            if isinstance(self._result.runtime, list):
                # XXX In what situation is runtime ever a list?
                # Normally it's a Bunch.
                # Ans[SG]: Runtime is a list when we are iterating
                # over an input field using iterfield
                returncode = max([r.returncode for r in self._result.runtime])
            else:
                returncode = self._result.runtime.returncode
            if returncode == 0:
                self._save_hashfile(hashfile,hashed_inputs)
            else:
                msg = "Could not run %s" % self.name
                msg += "\nwith inputs:\n%s" % self.inputs
                msg += "\n\tstderr: %s" % self._result.runtime.stderr
                raise RuntimeError(msg)
        else:
            logger.debug("Hashfile exists. Skipping execution\n")
            self._run_interface(execute=False, cwd=outdir)
        return self._result

    def _run_interface(self, execute=True, cwd=None):
        old_cwd = os.getcwd()
        if not cwd:
            cwd = self._output_directory()
        os.chdir(cwd)
        self._result = self._run_command(execute, cwd)
        os.chdir(old_cwd)
            
    def _run_command(self, execute, cwd, copyfiles=True):
        if execute and copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
        if copyfiles:
            self._copyfiles_to_wd(cwd,execute)
        resultsfile = os.path.join(cwd, 'result_%s.npz' % self._id)
        if execute:
            if issubclass(self._interface.__class__, CommandLine):
                cmd = self._interface.cmdline
                logger.info('cmd: %s'%cmd)
                cmdfile = os.path.join(cwd,'command.txt')
                fd = open(cmdfile,'wt')
                fd.writelines(cmd)
                fd.close()
            logger.info('Executing node')
            try:
                result = self._interface.run()
            except:
                runtime = Bunch(returncode = 1, environ = deepcopy(os.environ.data), hostname = gethostname())
                result = InterfaceResult(interface=None,
                                         runtime=runtime,
                                         outputs=None)
                self._result = result
                raise
            if result.runtime.returncode:
                logger.error('STDERR:' + result.runtime.stderr)
                logger.error('STDOUT:' + result.runtime.stdout)
                self._result = result
                raise RuntimeError(result.runtime.stderr)
            else:
                # to remove problem with thread unsafeness of savez
                outdict = {'result_%s' % self._id : result}
                np.savez(resultsfile, **outdict)
        else:
            # Likewise, cwd could go in here
            logger.info("Collecting precomputed outputs:")
            try:
                aggouts = self._interface.aggregate_outputs()
                result = InterfaceResult(interface=None,
                                         runtime=None,
                                         outputs=aggouts)
            except FileNotFoundError:
                logger.info("Some of the outputs were not found: rerunning node.")
                result = self._run_command(execute=True, cwd=cwd, copyfiles=False)
        return result
    
    def _copyfiles_to_wd(self, outdir, execute):
        """ copy files over and change the inputs"""
        if hasattr(self._interface,'_get_filecopy_info'):
            for info in self._interface._get_filecopy_info():
                files = self.inputs.get().get(info['key'])
                if not isdefined(files):
                    continue
                if files:
                    infiles = filename_to_list(files)
                    if execute:
                        newfiles = copyfiles(infiles, [outdir], copy=info['copy'])
                    else:
                        newfiles = fnames_presuffix(infiles, newpath=outdir)
                    if not isinstance(files, list):
                        newfiles = list_to_filename(newfiles)
                    setattr(self.inputs, info['key'], newfiles)

    def update(self, **opts):
        self.inputs.update(**opts)
        

class MapNode(Node):
    
    def __init__(self, interface, iterfield=None, **kwargs):
        """

        Parameters
        ----------

        iterfield : 1+-element list
        key(s) over which to repeatedly call the interface.
        for example, to iterate FSL.Bet over multiple files, one can
        set node.iterfield = ['infile'].  If this list has more than 1 item
        then the inputs are selected in order simultaneously from each of these
        fields and each field will need to have the same number of members.
        """
        super(MapNode, self).__init__(interface, **kwargs)
        self.iterfield  = iterfield
        if self.iterfield is None:
            raise Exception("Iterfield must be provided")
        self._inputs = deepcopy(self._interface.inputs)
        for field in iterfield:
            trait_type = self._inputs.traits()[field].trait_type
            if isinstance(trait_type, (File, Directory)):
                self._inputs.remove_trait(field) # XX NOT SURE IF NECESSARY
                self._inputs.add_trait(field, InputMultiPath(trait_type))
            else:
                self._inputs.remove_trait(field)
                self._inputs.add_trait(field, traits.List(trait_type))

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs()
    
    def _outputs(self):
        outputs = self._interface._outputs()
        for field in outputs.get().keys():
            trait_type = outputs.traits()[field].trait_type
            if isinstance(trait_type, (File, Directory)):
                outputs.remove_trait(field)
                outputs.add_trait(field, OutputMultiPath(trait_type))
            else:
                outputs.remove_trait(field)
                outputs.add_trait(field, traits.List(trait_type))
        return outputs

    def _run_interface(self, execute=True, cwd=None):
        old_cwd = os.getcwd()
        if not cwd:
            cwd = self._output_directory()
        os.chdir(cwd)

        iterflow = Workflow()
        for i in enumerate(self.iterfield):
            newnode = Node(deepcopy(self.interface), name=self.name+i)
            for field in self.iterfield:
                setattr(newnode.inputs, field,
                        getattr(self.inputs, field)[i])
            iterflow.add_nodes([newnode])
        # TODO set output directory
        #iterflow... 
        iterflow.execute()
        # TODO collect results
        # TODO ensure workflow returns results
        self._result = InterfaceResult(interface=[], runtime=[],
                                       outputs=Bunch())
        for i, node in enumerate(self._execgraph.nodes()):
            self._result.interface.insert(i, result.interface)
            self._result.runtime.insert(i, result.runtime)
            for key, val in node.result.outputs.get().items():
                try:
                    # This has funny default behavior if the length of the
                    # list is < i - 1. I'd like to simply use append... feel
                    # free to second my vote here!
                    self._result.outputs.get(key).append(val)
                except AttributeError:
                    # .insert(i, val) is equivalent to the following if
                    # outputs.key == None, so this is far less likely to
                    # produce subtle errors down the road!
                    setattr(self._result.outputs, key, [val])
        os.chdir(old_cwd)
