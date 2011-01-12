# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Pipeline` class provides core functionality for batch processing.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)

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

from enthought.traits.trait_handlers import TraitDictObject, TraitListObject
import numpy as np

from nipype.utils.misc import package_check
import shutil
import cPickle
import gzip
package_check('networkx', '1.0')
import networkx as nx
from IPython.Release import version as IPyversion
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass

from nipype.interfaces.base import (traits, File, Directory, InputMultiPath,
                                    CommandLine, Undefined,
                                    OutputMultiPath, TraitedSpec,
                                    DynamicTraitedSpec,
                                    Bunch, InterfaceResult)
from nipype.utils.misc import isdefined
from nipype.utils.filemanip import (save_json, FileNotFoundError,
                                    filename_to_list, list_to_filename,
                                    copyfiles, fnames_presuffix)

from nipype.pipeline.utils import (_generate_expanded_graph, modify_paths,
                                   _create_pickleable_graph, export_graph,
                                   _report_nodes_not_run, make_output_dir)
from nipype.utils.config import config

#Sets up logging for pipeline and nodewrapper execution
LOG_FILENAME = os.path.join(config.get('logging','log_directory'),
                            'pypeline.log')
logging.basicConfig()
logger = logging.getLogger('workflow')
fmlogger = logging.getLogger('filemanip')
iflogger = logging.getLogger('interface')
hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                            maxBytes=config.get('logging','log_size'),
                                            backupCount=config.get('logging','log_rotate'))
formatter = logging.Formatter(fmt='%(asctime)s,%(msecs)d %(name)-2s '\
                                  '%(levelname)-2s:\n\t %(message)s',
                              datefmt='%y%m%d-%H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.getLevelName(config.get('logging','workflow_level')))
fmlogger.addHandler(hdlr)
fmlogger.setLevel(logging.getLevelName(config.get('logging','filemanip_level')))
iflogger.addHandler(hdlr)
iflogger.setLevel(logging.getLevelName(config.get('logging','interface_level')))

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
            Name of this node. Name must be alphanumeric and not contain any
            special characters (e.g., '.', '@').
        """
        self.base_dir = base_dir
        self.overwrite = overwrite
        self.config = {}
        if name is None:
            raise Exception("init requires a name for this %s" % self.__class__.__name__)
        if '.' in name:
            raise Exception('the name keyword-arg must not contain a period "."')
        self.name = name
        # for compatibility with node expansion using iterables
        self._id = self.name
        self._hierarchy = None

    @property
    def inputs(self):
        raise NotImplementedError

    @property
    def outputs(self):
        raise NotImplementedError

    def clone(self, name):
        """Clone a workflowbase object

        Parameters
        ----------

        name : string (mandatory)
            A clone of node or workflow must have a new name
        """
        if (name is None) or (name == self.name):
            raise Exception('Cloning requires a new name')
        clone = deepcopy(self)
        clone.name = name
        clone._id = name
        return clone

    def _check_outputs(self, parameter):
        return hasattr(self.outputs, parameter)

    def _check_inputs(self, parameter):
        return hasattr(self.inputs, parameter)

    def __repr__(self):
        if self._hierarchy:
            return '.'.join((self._hierarchy, self._id))
        else:
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
        return np.load(filename)

    def _report_crash(self, traceback=None, execgraph=None):
        """Writes crash related information to a file
        """
        name = self._id
        if self.result and hasattr(self.result, 'runtime') and \
                self.result.runtime:
            if isinstance(self.result.runtime, list):
                host = self.result.runtime[0].hostname
            else:
                host = self.result.runtime.hostname
        else:
            host = gethostname()
        message = ['Node %s failed to run on host %s.' % (name,
                                                          host)]
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
                                            name)
        if hasattr(self, 'config') and ('crashdump_dir' in self.config.keys()):
            if not os.path.exists(self.config['crashdump_dir']):
                os.makedirs(self.config['crashdump_dir'])
            crashfile = os.path.join(self.config['crashdump_dir'],
                                     crashfile)
        else:
            crashfile = os.path.join(os.getcwd(), crashfile)
        pklgraph = _create_pickleable_graph(execgraph,
                                            show_connectinfo=True)
        logger.info('Saving crash info to %s' % crashfile)
        logger.info(''.join(traceback))
        np.savez(crashfile, node=self, execgraph=pklgraph, traceback=traceback)
        return crashfile

class Workflow(WorkflowBase):
    """Controls the setup and execution of a pipeline of processes
    """

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self._graph = nx.DiGraph()
        self._init_runtime_fields()

    def _init_runtime_fields(self):
        """Reset runtime attributes to none
        """
        self.procs = None
        self.depidx = None
        self.refidx = None
        self.proc_done = None
        self.proc_pending = None
        self._flatgraph = None
        self._execgraph = None
        self.ipyclient = None
        self.taskclient = None

    # PUBLIC API
    def clone(self, name):
        """Clone a workflow

        .. note::

        Will reset attributes used for executing workflow. See
        _init_runtime_fields. 

        Parameters
        ----------

        name: string (mandatory )
            every clone requires a new name
            
        """
        self._init_runtime_fields()
        clone = super(Workflow, self).clone(name)
        clone._reset_hierarchy()
        return clone

    def disconnect(self, *args):
        """Disconnect two nodes

        See the docstring for connect for format.
        """
        # yoh: explicit **dict was introduced for compatibility with Python 2.5
        return self.connect(*args, **dict(disconnect=True))

    def connect(self, *args, **kwargs):
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
        if not kwargs:
            disconnect = False
        else:
            disconnect = kwargs['disconnect']
        not_found = []
        newnodes = []
        for srcnode, destnode, _ in connection_list:
            if (srcnode not in newnodes) and (srcnode not in self._graph.nodes()):
                newnodes.append(srcnode)
            if (destnode not in newnodes) and (destnode not in self._graph.nodes()):
                newnodes.append(destnode)
        if newnodes:
            self._check_nodes(newnodes)
            for node in newnodes:
                if node._hierarchy is None:
                    node._hierarchy = self.name
        for srcnode, destnode, connects in connection_list:
            connected_ports = []
            # check to see which ports of destnode are already
            # connected. 
            if not disconnect and (destnode in self._graph.nodes()):
                for edge in self._graph.in_edges_iter(destnode):
                    data = self._graph.get_edge_data(*edge)
                    for sourceinfo, destname in data['connect']:
                        connected_ports += [destname]
            for source, dest in connects:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if dest in connected_ports:
                    raise Exception('Input %s of node %s is already ' \
                                        'connected'%(dest,destnode))
                if not (hasattr(destnode, '_interface') and '.io' in str(destnode._interface.__class__)):
                    if not destnode._check_inputs(dest):
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
                    if sourcename and not srcnode._check_outputs(sourcename):
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
                    if disconnect:
                        logger.debug('Removing connection: %s'%str(data))
                        edge_data['connect'].remove(data)
                if edge_data['connect']:
                    self._graph.add_edges_from([(srcnode, destnode, edge_data)])
                else:
                    #pass
                    logger.debug('Removing connection: %s->%s'%(srcnode,destnode))
                    self._graph.remove_edges_from([(srcnode, destnode)])
            elif not disconnect:
                logger.debug('(%s, %s): No edge data' % (srcnode, destnode))
                self._graph.add_edges_from([(srcnode, destnode,
                                             {'connect': connects})])
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            logger.debug('(%s, %s): new edge data: %s'% (srcnode, destnode,
                                                         str(edge_data)))

    def add_nodes(self, nodes):
        """ Add nodes to a workflow

        Parameters
        ----------
        nodes : list
            A list of WorkflowBase-based objects
        """
        newnodes = [node for node in nodes if node not in self._graph.nodes()]
        if not newnodes:
            logger.debug('no new nodes to add')
            return
        for node in newnodes:
            if not issubclass(node.__class__, WorkflowBase):
                raise Exception('Node %s must be a subclass of WorkflowBase' % str(node))
        self._check_nodes(newnodes)
        for node in newnodes:
            if node._hierarchy is None:
                node._hierarchy = self.name
        self._graph.add_nodes_from(newnodes)

    def remove_nodes(self, nodes):
        """ Remove nodes from a workflow

        Parameters
        ----------
        nodes : list
            A list of WorkflowBase-based objects
        """
        self._graph.remove_nodes_from(nodes)
        
    @property
    def inputs(self):
        return self._get_inputs()

    @property
    def outputs(self):
        return self._get_outputs()

    def execnodes(self):
        if self._execgraph:
            return self._execgraph.nodes()
        return None
        
    def get_exec_node(self, name):
        if self._execgraph:
            return [node  for node in self._execgraph.nodes() if name == str(node)].pop()
        return None

    def get_node(self, name):
        """Return an internal node by name
        """
        nodenames = name.split('.')
        nodename = nodenames[0]
        outnode = [node for node in self._graph.nodes() if str(node).endswith('.'+nodename)]
        if outnode:
            outnode = outnode[0]
            if nodenames[1:] and issubclass(outnode.__class__, Workflow):
                outnode = outnode.get_node('.'.join(nodenames[1:]))
        else:
            outnode = None
        return outnode

    def write_graph(self, dotfilename='graph.dot', graph2use='flat'):
        """Generates a graphviz dot file and a png file

        Parameters
        ----------
        
        graph2use: 'orig', 'flat' (default), 'exec'
            orig - creates a top level graph without expanding internal
                   workflow nodes
            flat - expands workflow nodes recursively
            exec - expands workflows to depict iterables
            
        """
        graph = self._graph
        if graph2use in ['flat', 'exec']:
            if self._flatgraph is None:
                self._create_flat_graph()
            graph = self._flatgraph
        if graph2use == 'exec':
            graph = self._execgraph
            if graph is None:
                graph = _generate_expanded_graph(deepcopy(self._flatgraph))
        export_graph(graph, self.base_dir, dotfilename=dotfilename)

    def run(self, inseries=False, updatehash=False, createdirsonly=False):
        """ Execute the workflow

        Parameters
        ----------
        
        inseries: Boolean
            Execute workflow in series
        """
        self._init_runtime_fields()
        self._create_flat_graph()
        self._execgraph = _generate_expanded_graph(deepcopy(self._flatgraph))
        for node in self._execgraph.nodes():
            node.config = self.config
        if inseries or createdirsonly:
            self._execute_in_series(createdirsonly=createdirsonly)
        else:
            self._execute_with_manager()
        
    # PRIVATE API AND FUNCTIONS

    def _check_nodes(self, nodes):
        """Checks if any of the nodes are already in the graph
        
        """
        node_names = [node.name for node in self._graph.nodes()]
        node_lineage = [node._hierarchy for node in self._graph.nodes()]
        for node in nodes:
            if node.name in node_names:
                idx = node_names.index(node.name)
                if node._hierarchy == node_lineage[idx]:
                    raise Exception('Duplicate node name %s found.'%node.name)
            else:
                node_names.append(node.name)

    def _has_attr(self, parameter, subtype='in'):
        """Checks if a parameter is available as an input or output
        """
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

    def _get_parameter_node(self, parameter, subtype='in'):
        """Returns the underlying node corresponding to an input or
        output parameter
        """
        if subtype == 'in':
            subobject = self.inputs
        else:
            subobject = self.outputs
        attrlist = parameter.split('.')
        cur_out = subobject
        for attr in attrlist[:-1]:
            cur_out = getattr(cur_out, attr)
        return cur_out.traits()[attrlist[-1]].node

    def _check_outputs(self, parameter):
        return self._has_attr(parameter, subtype='out')

    def _check_inputs(self, parameter):
        return self._has_attr(parameter, subtype='in')

    def _get_inputs(self):
        """Returns the inputs of a workflow

        This function does not return any input ports that are already connected
        """
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
                getattr(inputdict, node.name).on_trait_change(self._set_input)
        return inputdict

    def _get_outputs(self):
        """Returns all possible output ports that are not already connected
        """
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

    def _set_input(self, object, name, newvalue):
        """Trait callback function to update a node input
        """
        object.traits()[name].node.set_input(name, newvalue)

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, str):
            val = source.get_output(sourceinfo)
        elif isinstance(sourceinfo, tuple):
            if callable(sourceinfo[1]):
                val = sourceinfo[1](source.get_output(sourceinfo[0]),
                                    *sourceinfo[2:])
        newval = val
        if isinstance(val, TraitDictObject):
            newval = dict(val)
        if isinstance(val, TraitListObject):
            newval = val[:]
        logger.debug('setting node input: %s->%s', param, str(newval))
        node.set_input(param, deepcopy(newval))

    def _create_flat_graph(self):
        """Turn a hierarchical DAG into a simple DAG where no node is a workflow
        """
        logger.debug('Creating flat graph for workflow: %s', self.name)
        self._init_runtime_fields()
        workflowcopy = deepcopy(self)
        workflowcopy._generate_flatgraph()
        self._flatgraph = workflowcopy._graph

    def _reset_hierarchy(self):
        """Reset the hierarchy on a graph
        """
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                node._reset_hierarchy()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = '.'.join((self.name,innernode._hierarchy))
            else:
                node._hierarchy = self.name

    def _generate_flatgraph(self):
        """Generate a graph containing only Nodes or MapNodes
        """
        logger.debug('expanding workflow: %s', self)
        nodes2remove = []
        if not nx.is_directed_acyclic_graph(self._graph):
            raise Exception('Workflow: %s is not a directed acyclic graph (DAG)'%self.name)
        nodes = nx.topological_sort(self._graph)
        for node in nodes:
            logger.debug('processing node: %s'%node)
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                # use in_edges instead of in_edges_iter to allow
                # disconnections to take place properly. otherwise, the
                # edge dict is modified.
                for u, _, d in self._graph.in_edges(nbunch=node, data=True):
                    logger.debug('in: connections-> %s'%str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("in: %s" % str (cd))
                        dstnode = node._get_parameter_node(cd[1],subtype='in')
                        srcnode = u
                        srcout = cd[0]
                        dstin = cd[1].split('.')[-1]
                        logger.debug('in edges: %s %s %s %s'%(srcnode, srcout, dstnode, dstin))
                        self.disconnect(u, cd[0], node, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # do not use out_edges_iter for reasons stated in in_edges
                for _, v, d in self._graph.out_edges(nbunch=node, data=True):
                    logger.debug('out: connections-> %s'%str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("out: %s" % str (cd))
                        dstnode = v
                        if isinstance(cd[0], tuple):
                            parameter = cd[0][0]
                        else:
                            parameter = cd[0]
                        srcnode = node._get_parameter_node(parameter, subtype='out')
                        if isinstance(cd[0], tuple):
                            srcout = list(cd[0])
                            srcout[0] = parameter.split('.')[-1]
                            srcout = tuple(srcout)
                        else:
                            srcout = parameter.split('.')[-1]
                        dstin = cd[1]
                        logger.debug('out edges: %s %s %s %s'%(srcnode, srcout, dstnode, dstin))
                        self.disconnect(node, cd[0], v, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # expand the workflow node
                #logger.debug('expanding workflow: %s', node)
                node._generate_flatgraph()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = '.'.join((self.name,innernode._hierarchy))
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
        if nodes2remove:
            self._graph.remove_nodes_from(nodes2remove)
        logger.debug('finished expanding workflow: %s', self)

    def _execute_in_series(self, updatehash=False, createdirsonly=False, force_execute=None):
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
        if createdirsonly:
            logger.info("Creating directories only.")
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
                if not createdirsonly:
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
                    if createdirsonly:
                        outdir = node._output_directory()
                        outdir = make_output_dir(outdir)
                        logger.info('node: %s dir: %s'%(node, outdir))
                    else:
                        node.run(force_execute=redo)
            except:
                os.chdir(old_wd)
                if config.getboolean('execution', 'stop_on_first_crash'):
                    raise
                # bare except, but i really don't know where a
                # node might fail
                crashfile = node._report_crash(execgraph=self._execgraph)
                # remove dependencies from queue
                subnodes = nx.dfs_preorder(self._execgraph, node)
                notrun.append(dict(node = node,
                                   dependents = subnodes,
                                   crashfile = crashfile))
                donotrun.extend(subnodes)
        _report_nodes_not_run(notrun)


    def _set_output_directory_base(self, node):
        """Determine output directory and create it
        """
        # update parameterization of output directory
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        outputdir = self.base_dir
        if node._hierarchy:
            outputdir = os.path.join(outputdir, *node._hierarchy.split('.'))
        if node.parameterization:
            outputdir = os.path.join(outputdir, *node.parameterization)
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        node.base_dir = os.path.abspath(outputdir)

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
        self.refidx = deepcopy(self.depidx>0)
        self.refidx.dtype = np.int8
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

    def _remove_node_dirs(self):
        """Removes directories whose outputs have already been used up
        """
        if config.getboolean('execution', 'remove_node_directories'):
            for idx in np.nonzero(np.all(self.refidx==0,axis=1))[0]:
                if self.proc_done[idx] and (not self.proc_pending[idx]):
                    self.refidx[idx,idx] = -1
                    outdir = self.procs[idx]._output_directory()
                    logger.info(('[node dependencies finished] '
                                 'removing node: %s from directory %s') % \
                                    (self.procs[idx]._id,
                                     outdir))
                    shutil.rmtree(outdir)
        

    def _execute_with_manager(self):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        if config.getboolean('execution', 'run_in_series'):
            self._execute_in_series()
            return
        # retrieve clients again
        try:
            name = 'IPython.kernel.client'
            __import__(name)
            self.ipyclient = sys.modules[name]
        except ImportError:
            warn("Ipython kernel not found.  Parallel execution will be" \
                     "unavailable", ImportWarning)
        if not self.taskclient:
            try:
                self.taskclient = self.ipyclient.TaskClient()
            except Exception, e:
                if isinstance(e, ConnectionRefusedError):
                    warn("No clients found, running serially for now.")
                if isinstance(e, ValueError):
                    warn("Ipython kernel not installed")
                self._execute_in_series()
                return
        logger.info("Running in parallel.")
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
                try:
                    res = self.taskclient.get_task_result(taskid, block=False)
                    if res:
                        if res['traceback']:
                            self.procs[jobid]._result = res['result']
                            self.procs[jobid]._traceback = res['traceback']
                            crashfile = self.procs[jobid]._report_crash(traceback=res['traceback'],
                                                                        execgraph=self._execgraph)
                            # remove dependencies from queue
                            notrun.append(self._remove_node_deps(jobid, crashfile))
                        else:
                            self._task_finished_cb(res['result'], jobid)
                            self._remove_node_dirs()
                        if IPyversion >= '0.10.1':
                            logger.debug("Clearing id: %d"%taskid)
                            self.taskclient.clear(taskid)
                    else:
                        toappend.insert(0, (taskid, jobid))
                except:
                    crashfile = self.procs[jobid]._report_crash(execgraph=self._execgraph)
                    # remove dependencies from queue
                    notrun.append(self._remove_node_deps(jobid, crashfile))
            if toappend:
                self.pending_tasks.extend(toappend)
            self._send_procs_to_workers()
            sleep(2)
        self._remove_node_dirs()
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
                    _, hashvalue = self.procs[jobid]._get_hashval()
                    logger.info('Executing: %s ID: %d H:%s' % \
                                    (self.procs[jobid]._id, jobid, hashvalue))
                    cmdstr = """import sys
from traceback import format_exception
traceback=None
try:
    result = task.run()
except:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    result = task.result
"""
                    task = self.ipyclient.StringTask(cmdstr,
                                                     push = dict(task=self.procs[jobid]),
                                                     pull = ['result','traceback'])
                    tid = self.taskclient.run(task, block = False)
                    #logger.info('Task id: %d' % tid)
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
        self.refidx[np.nonzero(self.refidx[:,jobid]>0)[0],jobid] = 0

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
    >>> realign = Node(interface=spm.Realign(), name='realign')
    >>> realign.inputs.in_files = 'functional.nii'
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
        logger.debug('setting nodelevel input %s = %s' % (parameter, str(val)))
        setattr(self.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        val = None
        if self._result:
            val = getattr(self._result.outputs, parameter)
        return val

    def _get_hashval(self):
        return self.inputs.hashval

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
                logger.debug('Unable to write a particular type to the json '\
                                 'file')
            else:
                logger.critical('Unable to open the file in write mode: %s'% \
                                    hashfile)


    def run(self, updatehash=None, force_execute=False):
        """Executes an interface within a directory.
        """
        # check to see if output directory and hash exist
        outdir = self._output_directory()
        outdir = make_output_dir(outdir)
        logger.info("Executing node %s in dir: %s"%(self._id,outdir))
        # Get a dictionary with hashed filenames and a hashvalue
        # of the dictionary itself.
        hashed_inputs, hashvalue = self._get_hashval()
        hashfile = os.path.join(outdir, '_0x%s.json' % hashvalue)
        if updatehash:
            #if isinstance(self, MapNode):
            #    self._run_interface(updatehash=True)
            logger.debug("Updating hash: %s" % hashvalue)
            self._save_hashfile(hashfile, hashed_inputs)
        if force_execute or (not updatehash and (self.overwrite or not os.path.exists(hashfile))):
            logger.debug("Node hash: %s"%hashvalue)
            
            hashfile_unfinished = os.path.join(outdir, '_0x%s_unfinished.json' % hashvalue)
            if os.path.exists(outdir) and not (os.path.exists(hashfile_unfinished) and self._interface.can_resume):
                logger.debug("Removing old %s and its contents"%outdir)
                rmtree(outdir)
                outdir = make_output_dir(outdir)
            else:
                logger.debug("%s found and can_resume is True - resuming execution" % hashfile_unfinished)
            self._save_hashfile(hashfile_unfinished, hashed_inputs)
            self._run_interface(execute=True, cwd=outdir)
            if isinstance(self._result.runtime, list):
                # Handle MapNode
                returncode = max([r.returncode for r in self._result.runtime])
            else:
                returncode = self._result.runtime.returncode
            if returncode == 0:
                shutil.move(hashfile_unfinished, hashfile)
            else:
                msg = "Could not run %s" % self.name
                msg += "\nwith inputs:\n%s" % self.inputs
                msg += "\n\tstderr: %s" % self._result.runtime.stderr
                os.remove(hashfile_unfinished)
                raise RuntimeError(msg)
        else:
            logger.debug("Hashfile exists. Skipping execution\n")
            self._run_interface(execute=False, updatehash=updatehash, cwd=outdir)
        return self._result

    def _run_interface(self, execute=True, updatehash=False, cwd=None):
        old_cwd = os.getcwd()
        if not cwd:
            cwd = self._output_directory()
        os.chdir(cwd)
        self._result = self._run_command(execute, cwd)
        os.chdir(old_cwd)

    def _run_command(self, execute, cwd, copyfiles=True):
        if execute and copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
        resultsfile = os.path.join(cwd, 'result_%s.pklz' % self.name)
        if issubclass(self._interface.__class__, CommandLine):
            cmd = self._interface.cmdline
            logger.info('cmd: %s'%cmd)
        if execute:
            if copyfiles:
                self._copyfiles_to_wd(cwd, execute)
            if issubclass(self._interface.__class__, CommandLine):
                cmdfile = os.path.join(cwd,'command.txt')
                fd = open(cmdfile,'wt')
                fd.writelines(cmd)
                fd.close()
            logger.debug('Executing node')
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
                pkl_file = gzip.open(resultsfile, 'wb')
                if result.outputs:
                    outputs = result.outputs.get()
                    result.outputs.set(**modify_paths(outputs, relative=True, basedir=cwd))
                cPickle.dump(result, pkl_file)
                pkl_file.close()
                if result.outputs:
                    result.outputs.set(**outputs)
        else:
            # Likewise, cwd could go in here
            logger.debug("Collecting precomputed outputs:")
            try:
                aggregate = True
                if os.path.exists(resultsfile):
                    pkl_file = gzip.open(resultsfile, 'rb')
                    try:
                        result = cPickle.load(pkl_file)
                    except traits.TraitError:
                        logger.debug('some file does not exist. hence trait cannot be set')
                    else:
                        if result.outputs:
                            try:
                                result.outputs.set(**modify_paths(result.outputs.get(), relative=False, basedir=cwd))
                            except FileNotFoundError:
                                logger.debug('conversion to full path does results in non existent file')
                            else:
                                aggregate = False
                    pkl_file.close()
                logger.debug('Aggregate: %s', aggregate)
                # try aggregating first
                if aggregate:
                    self._copyfiles_to_wd(cwd, True, linksonly=True)
                    aggouts = self._interface.aggregate_outputs()
                    runtime = Bunch(cwd=cwd,returncode = 0, environ = deepcopy(os.environ.data), hostname = gethostname())
                    result = InterfaceResult(interface=None,
                                             runtime=runtime,
                                             outputs=aggouts)
                    pkl_file = gzip.open(resultsfile, 'wb')
                    if result.outputs:
                        outputs = result.outputs.get()
                        result.outputs.set(**modify_paths(outputs, relative=True, basedir=cwd))
                    cPickle.dump(result, pkl_file)
                    pkl_file.close()
                    if result.outputs:
                        result.outputs.set(**outputs)
            except FileNotFoundError:
                # if aggregation does not work, rerun the node
                logger.debug("Some of the outputs were not found: rerunning node.")
                result = self._run_command(execute=True, cwd=cwd, copyfiles=False)
        return result

    def _copyfiles_to_wd(self, outdir, execute, linksonly=False):
        """ copy files over and change the inputs"""
        if hasattr(self._interface,'_get_filecopy_info'):
            for info in self._interface._get_filecopy_info():
                files = self.inputs.get().get(info['key'])
                if not isdefined(files):
                    continue
                if files:
                    infiles = filename_to_list(files)
                    if execute:
                        if linksonly:
                            if info['copy'] == False:
                                newfiles = copyfiles(infiles, [outdir], copy=info['copy'], create_new=True)
                            else:
                                newfiles = fnames_presuffix(infiles, newpath=outdir)
                        else:
                            newfiles = copyfiles(infiles, [outdir], copy=info['copy'], create_new=True)
                    else:
                        newfiles = fnames_presuffix(infiles, newpath=outdir)
                    if not isinstance(files, list):
                        newfiles = list_to_filename(newfiles)
                    setattr(self.inputs, info['key'], newfiles)

    def update(self, **opts):
        self.inputs.update(**opts)


class MapNode(Node):
    """Wraps interface objects that need to be iterated on a list of inputs.

    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> realign = MapNode(interface=fsl.MCFLIRT(), name='realign', iterfield=['in_file']) # doctest: +SKIP
    >>> realign.inputs.in_file = ['functional.nii', 'functional2.nii', 'functional3.nii'] # doctest: +SKIP
    >>> realign.run() # doctest: +SKIP
    
    """

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
        elif isinstance(self.iterfield, str):
            self.iterfield = [self.iterfield]
        self._inputs = self._create_dynamic_traits(self._interface.inputs,
                                                   fields=self.iterfield)
        self._inputs.on_trait_change(self._set_mapnode_input)

    def _create_dynamic_traits(self, basetraits, fields=None, nitems=None):
        """Convert specific fields of a trait to accept multiple inputs
        """
        output = DynamicTraitedSpec()
        if fields is None:
            fields = basetraits.copyable_trait_names()
        for name, spec in basetraits.items():
            if name in fields and ((nitems is None) or (nitems > 1)):
                logger.debug('adding multipath trait: %s'%name)
                output.add_trait(name, InputMultiPath(spec.trait_type))
            else:
                output.add_trait(name, traits.Trait(spec))
            setattr(output, name, Undefined)
            value = getattr(output, name)
        return output

    def set_input(self, parameter, val):
        """ Set interface input value or nodewrapper attribute

        Priority goes to interface.
        """
        logger.debug('setting nodelevel input %s = %s' % (parameter, str(val)))
        self._set_mapnode_input(self.inputs, parameter, deepcopy(val))

    def _set_mapnode_input(self, object, name, newvalue):
        logger.debug('setting mapnode input: %s -> %s' %(name, str(newvalue)))
        if name in self.iterfield:
            setattr(self._inputs, name, newvalue)
        else:
            setattr(self._interface.inputs, name, newvalue)

    def _get_hashval(self):
        """ Compute hash including iterfield lists
        """
        hashinputs = deepcopy(self._interface.inputs)
        for name in self.iterfield:
            hashinputs.remove_trait(name)
            hashinputs.add_trait(name, InputMultiPath(self._interface.inputs.traits()[name].trait_type))
            logger.debug('setting hashinput %s-> %s'%(name,getattr(self._inputs, name)))
            setattr(hashinputs, name, getattr(self._inputs, name))
        return hashinputs.hashval

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        if self._interface._outputs():
            return Bunch(self._interface._outputs().get())
        else:
            return None

    def _run_interface(self, execute=True, updatehash=False, cwd=None):
        old_cwd = os.getcwd()
        if not cwd:
            cwd = self._output_directory()
        os.chdir(cwd)

        nitems = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
        newnodes = []
        nodenames = []
        for i in range(nitems):
            nodenames.insert(i, '_' + self.name+str(i))
            newnodes.insert(i, Node(deepcopy(self._interface), name=nodenames[i]))
            newnodes[i]._interface.inputs.set(**deepcopy(self._interface.inputs.get()))
            for field in self.iterfield:
                fieldvals = filename_to_list(getattr(self.inputs, field))
                logger.debug('setting input %d %s %s'%(i, field,
                                                      fieldvals[i])) 
                setattr(newnodes[i].inputs, field,
                        fieldvals[i])
        workflowname = 'mapflow'
        iterflow = Workflow(name=workflowname)
        iterflow.base_dir = cwd
        iterflow.config = self.config
        iterflow.add_nodes(newnodes)
        iterflow.run(inseries=True, updatehash=updatehash)
        self._result = InterfaceResult(interface=[], runtime=[],
                                       outputs=self.outputs)
        for i in range(nitems):
            node = iterflow.get_exec_node('.'.join((workflowname,
                                                    nodenames[i])))
            runtime = Bunch(returncode = 0, environ = deepcopy(os.environ.data), hostname = gethostname())
            self._result.runtime.insert(i, runtime)
            if node.result and hasattr(node.result, 'runtime'):
                self._result.runtime[i] = node.result.runtime
                if node.result.runtime.returncode != 0:
                    raise Exception('iternode %s:%d did not run'%(node._id, i))
                self._result.interface.insert(i, node.result.interface)
        for key, _ in self.outputs.items():
            values = []
            for i in range(nitems):
                node = iterflow.get_exec_node('.'.join((workflowname,
                                                        nodenames[i])))
                if node.result.outputs:
                    values.insert(i, node.result.outputs.get()[key])
                else:
                    values.insert(i, None)
            if any([val != Undefined for val in values]) and self._result.outputs:
                #logger.debug('setting key %s with values %s' %(key, str(values)))
                setattr(self._result.outputs, key, values)
            #else:
            #    logger.debug('no values for key %s' %key)
        os.chdir(old_cwd)
