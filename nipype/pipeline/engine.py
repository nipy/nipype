"""Defines functionality for pipelined execution of interfaces

The `Pipeline` class provides core functionality for batch processing. 
"""

import os
import pwd
import sys
from copy import deepcopy
from time import sleep, strftime
from warnings import warn
import logging
import logging.handlers
from traceback import format_exception

import numpy as np

from nipype.utils.misc import package_check
package_check('networkx', '1.0')
import networkx as nx
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass

from nipype.interfaces.base import CommandLine
from nipype.utils.filemanip import fname_presuffix

#Sets up logging for pipeline and nodewrapper execution
LOG_FILENAME = 'pypeline.log'
logging.basicConfig()
logger = logging.getLogger('engine')
nwlogger = logging.getLogger('nodewrapper')
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
    ids = [n.id for n in supernodes]
    edgeinfo = {}
    for n in subgraph.nodes():
        nidx = ids.index(n.id)
        for edge in supergraph.in_edges_iter(supernodes[nidx]):
                #make sure edge is not part of subgraph
            if edge[0] not in subgraph.nodes():
                if n.id not in edgeinfo.keys():
                    edgeinfo[n.id] = []
                edgeinfo[n.id].append((edge[0],
                                       supergraph.get_edge_data(*edge)))
    supergraph.remove_nodes_from(nodes)
    # Add copies of the subgraph depending on the number of iterables
    for i, params in enumerate(walk(iterables.items())):
        Gc = deepcopy(subgraph)
        ids = [n.id for n in Gc.nodes()]
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
            if node.id in edgeinfo.keys():
                for info in edgeinfo[node.id]:
                    supergraph.add_edges_from([(info[0], node, info[1])])
            node.id += str(i)
    return supergraph

def _report_nodes_not_run(notrun):
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            logger.error("could not run node: %s" % info['node'].id)
            logger.info("crashfile: %s" % info['crashfile'])
            logger.debug("The following dependent nodes were not run")
            for subnode in info['dependents']:
                logger.debug(subnode.id)
        logger.info("***********************************")


class Pipelet(object):
    """ Define basic entities for workflow and nodes
    
    """

    def __init__(self, name=None, **kwargs):
        """
    base_directory : directory
        base output directory (will be hashed before creations)
        default=None, which results in the use of mkdtemp
    overwrite : Boolean
        Whether to overwrite contents of output directory if it
        already exists. If directory exists and hash matches it
        assumes that process has been executed (default : False)
    name : string
        Name of this node. By default node is named
        modulename.classname. But when the same class is being used
        several times, a different name ensures that output directory
        is not overwritten each time the same functionality is run.
        """
        self.base_directory = None
        self.overwrite = None
        if name is None:
            raise Exception("please provide a name")
        self.name = name
        # for compatibility with node expansion using iterables
        self.id = self.name

    def execute(self):
        print "Executing workflow/node"

    def check_outputs(self, parameter):
        raise NotImplementedError
    
    def check_inputs(self, parameter):
        raise NotImplementedError
    
    def __repr__(self):
        return self.id

class Workflow(Pipelet):
    """Controls the setup and execution of a pipeline of processes
    """

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self._graph = nx.DiGraph()

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
                if not destnode.check_inputs(dest):
                    not_found.append(['in', destnode.name, dest])
                # TODO XXX
                if '.io' not in srcnode.name:
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
            A list of node-wrapped interfaces
        """
        self._graph.add_nodes_from(nodes)

    def get_inputs(self):
        inputdict = {}
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                for key, value in node.get_inputs().items():
                    nodename = '.'.join((node.name, key))
                    inputdict[nodename] = value
            else:
                taken_inputs = []
                for _, _, d in self._graph.in_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        taken_inputs.append(cd[1])
                for key in node.inputs.copyable_trait_names():
                    if key not in taken_inputs:
                        nodename = '.'.join((node.name, key))
                        inputdict[nodename] = node
        return inputdict
        
    def get_outputs(self):
        outputdict = {}
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                for key, value in node.get_outputs().items():
                    nodename = '.'.join((node.name, key))
                    outputdict[nodename] = value
            else:
                for key in node.outputs.copyable_trait_names():
                    nodename = '.'.join((node.name, key))
                    outputdict[nodename] = node
        return outputdict
        
    def check_outputs(self, parameter):
        return parameter in self.get_outputs().keys()
    
    def check_inputs(self, parameter):
        return parameter in self.get_inputs().keys()

    def set_input(self, key, value):
        inputdict = self.get_inputs()
        nodeinput = key.split('.')[-1]
        setattr(inputdict[key].inputs, nodeinput, value)

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
                                   newpath=self.config['workdir'])
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
                                   newpath=self.config['workdir'])
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
        execgraph = generate_execgraph(self._graph)
        fullgraph = self.generate_expanded_graph(execgraph)
        self.execute(fullgraph)
        
    def _generate_expanded_graph(self):
        """Generates an expanded graph based on node parameterization

        Parameterization is controlled using the `iterables` field of the
        pipeline elements.  Thus if there are two nodes with iterables a=[1,2]
        and b=[3,4] this procedure will generate a graph with sub-graphs
        parameterized as (a=1,b=3), (a=1,b=4), (a=2,b=3) and (a=2,b=4). 
        """
        logger.info("PE: expanding iterables")
        graph_in = deepcopy(self._graph)
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
                node.id += 'I'
                subnodes = nx.dfs_preorder(graph_in, node)
                subgraph = graph_in.subgraph(subnodes)
                graph_in = _merge_graphs(graph_in, subnodes,
                                         subgraph, node.id,
                                         iterables)
            else:
                moreiterables = False
        self._execgraph = graph_in
        logger.info("PE: expanding iterables ... done")


    def generate_execgraph(self):
        # TODO : change from in-place to copy modification
        nodes2remove = []
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                node.generate_execgraph()
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
                for u, _, d in self._graph.in_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        print "in", cd
                        dstnode = node.get_inputs()[cd[1]]
                        srcnode = u
                        # XX simple source format used here.
                        # TODO implement functional format
                        srcout = cd[0]
                        dstin = cd[1].split('.')[-1]
                        self.connect(srcnode, srcout, dstnode, dstin)
                for _, v, d in self._graph.out_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        print "out", cd
                        dstnode = v
                        srcnode = node.get_outputs()[cd[0]]
                        # XX simple source format used here.
                        # TODO implement functional format
                        srcout = cd[0].split('.')[-1]
                        dstin = cd[1]
                        self.connect(srcnode, srcout, dstnode, dstin)
        if nodes2remove:
            print nodes2remove
            self._graph.remove_nodes_from(nodes2remove)
    
class Node(Pipelet):
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
    base_directory : directory
        base output directory (will be hashed before creations)
        default=None, which results in the use of mkdtemp
    overwrite : Boolean
        Whether to overwrite contents of output directory if it
        already exists. If directory exists and hash matches it
        assumes that process has been executed (default : False)
    name : string
        Name of this node. By default node is named
        modulename.classname. But when the same class is being used
        several times, a different name ensures that output directory
        is not overwritten each time the same functionality is run.
    
    Notes
    -----
    creates output directory
    copies/discovers files to work with
    saves a hash.json file to indicate that a process has been completed

    Examples
    --------
    >>> import nipype.interfaces.spm as spm
    >>> realign = NodeWrapper(interface=spm.Realign(), base_directory='test2', \
            diskbased=True)
    >>> realign.inputs.infile = os.path.abspath('data/funcrun.nii')
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """
    def __init__(self, interface=None,
                 iterables={}, base_directory=None,
                 overwrite=False, **kwargs):
        # interface can only be set at initialization
        super(Node, self).__init__(**kwargs)
        if interface is None:
            raise Exception('Interface must be provided')
        self._interface  = interface
        self._result     = None
        self.iterables  = iterables
        self.parameterization = None
        self.output_directory_base  = base_directory
        self.overwrite = None

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
        if hasattr(self._interface.inputs, parameter):
            setattr(self._interface.inputs, parameter, deepcopy(val))
        elif hasattr(self, parameter):
            setattr(self, parameter, deepcopy(val))
        else:
            setattr(self._interface.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        val = None
        if self._result:
            if hasattr(self._result.outputs, parameter):
                val = getattr(self._result.outputs, parameter)
            else:
                val = getattr(self, parameter)
        return val

    def check_outputs(self, parameter):
        return hasattr(self, parameter) or \
            hasattr(self._interface._outputs(), parameter)
    
    def check_inputs(self, parameter):
        return hasattr(self._interface.inputs, parameter) or \
            hasattr(self, parameter)

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
        logger.info("Node: %s"%self.id)
        if self.disk_based:
            outdir = self._output_directory()
            outdir = self._make_output_dir(outdir)
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
                    outdir = self._make_output_dir(outdir)
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
        else:
            self._run_interface(execute=True)
        return self._result

    def _run_interface(self, execute=True, cwd=None):
        old_cwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        if not cwd and self.disk_based:
            cwd = self._output_directory()
            os.chdir(cwd)
        basewd = cwd
        self._result = self._run_command(execute, cwd)
        if cwd:
            os.chdir(old_cwd)
            
    def _run_command(self, execute, cwd, copyfiles=True):
        if execute and copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
        if copyfiles:
            self._copyfiles_to_wd(cwd,execute)
        if self.disk_based:
            resultsfile = os.path.join(cwd, 'result_%s.npz' % self.id)
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
                if self.disk_based:
                    # to remove problem with thread unsafeness of savez
                    outdict = {'result_%s' % self.id : result}
                    #np.savez(resultsfile,**outdict)
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
        if hasattr(self._interface,'_get_filecopy_info') and self.disk_based:
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
        
    def _output_directory(self):
        if self.output_directory_base is None:
            self.output_directory_base = mkdtemp()
        return os.path.abspath(os.path.join(self.output_directory_base,
                                            self.name))

    def _make_output_dir(self, outdir):
        """Make the output_dir if it doesn't exist.
        """
        if not os.path.exists(os.path.abspath(outdir)):
            # XXX Should this use os.makedirs which will make any
            # necessary parent directories?  I didn't because the one
            # case where mkdir failed because a missing parent
            # directory, something went wrong up-stream that caused an
            # invalid path to be passed in for `outdir`.
            logger.info("Creating %s"%outdir)
            os.mkdir(outdir)
        return outdir

class MapNode(Node):
    
    def __init__(self, iterfield=None, **kwargs):
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
        super(MapNode, self).__init__(**kwargs)
        if self.iterfield is None:
            raise Exception("Iterfield must be provided")
        self.iterfield  = iterfield
        self._inputs = deepcopy(self._interface.inputs)
        # TODO modify iterields to lists
        for field in iterfield:
            self._inputs.add_trait(field, List(self._inputs.traits()[field].trait_type.__class__))

    @property
    def inputs(self):
        return self._inputs

    def _outputs():
        outputs = self._interface._outputs()
        for field in outputs.get().keys():
            outputs.add_trait(field, List(outputs.traits()[field].trait_type.__class__))
        
    @property
    def outputs(self):
        return self._outputs()

    def _run_interface(self, execute=True, cwd=None):
        old_cwd = os.getcwd()
        if cwd:
            os.chdir(cwd)
        if not cwd and self.disk_based:
            cwd = self._output_directory()
            os.chdir(cwd)
        basewd = cwd

        iterflow = Workflow()
        for i in enumerate(self.iterfield):
            newnode = Node(deepcopy(self.interface), name=self.name+i)
            # TODO set inputs
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
        if cwd:
            os.chdir(old_cwd)
