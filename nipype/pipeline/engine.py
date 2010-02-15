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
from traceback import format_tb

import numpy as np

from nipype.utils.misc import package_check
from IPython.kernel.error import CompositeError
package_check('networkx', '1.0')
import networkx as nx

from nipype.interfaces.base import CommandLine
from nipype.utils.filemanip import fname_presuffix

"""Sets up logging for pipeline and nodewrapper execution.
"""
LOG_FILENAME = 'pypeline.log'
logging.basicConfig()
logger = logging.getLogger('engine')
nwlogger = logging.getLogger('nodewrapper')
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
        

class Pipeline(object):
    """Controls the setup and execution of a pipeline of processes

    Attributes
    ----------

    config : dict
        A dictionary containing various options for controlling the pipeline.

    config['workdir'] : str
        Path for which diskspace to use for pipeline operations.

    config['use_parameterized_dirs'] : bool
        Controls whether pipeline outputs are stored in some hierarchical
        2-level structure based on parameterization or all output directories
        are created in the same location. 
        default [True]
        
    config['crashdump_dir'] ; string
        Specifies where crashdumps will be stored. Default = cwd
    """

    def __init__(self):
        self._graph = nx.DiGraph()
        self._execgraph = None
        self.config = {}
        self.config['workdir'] = '.'
        self.config['use_parameterized_dirs'] = True
        self.config['crashdump_dir'] = None
        self.ipythonclient = None
        self.mec = None
        try:
            name = 'IPython.kernel.client'
            __import__(name)
            self.ipythonclient = sys.modules[name]
        except ImportError:
            warn("Ipython kernel not found.  Parallel execution will be" \
                     "unavailable", ImportWarning)
        # attributes for running with manager
        self.procs = None
        self.depidx = None
        self.proc_done = None
        self.proc_pending = None

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
            connection_list = [(args[0],args[2],[(args[1],args[3])])]
        else:
             raise Exception('unknown set of parameters to connect function')                   
        not_found = []
        for u, v, d in connection_list:
            for source, dest in d:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if '.io' not in v.name:
                    if not v.check_inputs(dest):
                        not_found.append(['in',v.name,dest])
                if '.io' not in u.name:
                    if isinstance(source,tuple):
                        # handles the case that source is specified
                        # with a function
                        sourcename = source[0]
                    elif isinstance(source,str):
                        sourcename = source
                    else:
                        raise Exception('Unknown source specification in' \
                                         'connection from output of %s'%
                                        u.name)
                    if sourcename and not u.check_outputs(sourcename):
                        not_found.append(['out',u.name,sourcename])
        for c in not_found: 
            warn("Module %s has no %sput called %s\n"%(c[1],c[0],c[2]))
        if not_found:
            raise Exception('Some connections were not found')
        for u, v, d in connection_list:
            edge_data = self._graph.get_edge_data(u,v,None)
            if edge_data:
                logger.debug('(%s, %s): Edge data exists: %s' % \
                                 (u, v, str(edge_data)))
                for data in d:
                    if data not in edge_data['connect']:
                        edge_data['connect'].append(data)
                self._graph.add_edges_from([(u, v, edge_data)])
            else:
                logger.debug('(%s, %s): No edge data' % (u, v))
                self._graph.add_edges_from([(u, v, {'connect':d})])
            edge_data = self._graph.get_edge_data(u,v,None)
            logger.debug('(%s, %s): new edge data: %s'% (u, v, str(edge_data)))

    def add_nodes(self,nodes):
        """ Wraps the networkx functionality in a more semantically
        relevant function name

        Parameters
        ----------
        nodes : list
            A list of node-wrapped interfaces
        """
        self._graph.add_nodes_from(nodes)

    def _create_pickleable_graph(self, graph, show_connectinfo=False):
        """Create a graph that can be pickled.

        Ensures that edge info is pickleable.
        """
        logger.debug('creating pickleable graph')
        S = deepcopy(graph)
        for e in S.edges():
            data = S.get_edge_data(*e)
            S.remove_edge(*e)
            if show_connectinfo:
                S.add_edge(e[0], e[1], l=str(data['connect']))
            else:
                S.add_edge(e[0], e[1])
        return S

    def _write_detailed_dot(self, graph, dotfilename):
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
        text = ['digraph structs {','node [shape=record];']
        # write nodes
        edges = []
        replacefunk = lambda x: x.replace('_','').replace('.','').replace('@','').replace('-','')
        for n in graph.nodes():
            nodename = str(n)
            inports = []
            for u,v,d in graph.in_edges_iter(nbunch=n,data=True):
                for cd in d['connect']:
                    if isinstance(cd[0],str):
                        outport = cd[0]
                    else:
                        outport = cd[0][0]
                    inport = cd[1]
                    ipstrip = replacefunk(inport)
                    opstrip = replacefunk(outport)
                    edges.append('%s:%s -> %s:%s;'%(str(u).replace('.',''),opstrip,
                                                   str(v).replace('.',''),ipstrip))
                    if inport not in inports:
                        inports.append(inport)
            inputstr = '{IN'
            for ip in inports:
                inputstr += '|<%s> %s'%(replacefunk(ip),ip)
            inputstr += '}'
            outports = []
            for u,v,d in graph.out_edges_iter(nbunch=n,data=True):
                for cd in d['connect']:
                    if isinstance(cd[0],str):
                        outport = cd[0]
                    else:
                        outport = cd[0][0]
                    if outport not in outports:
                        outports.append(outport)
            outputstr = '{OUT'
            for op in outports:
                outputstr += '|<%s> %s'%(replacefunk(op),op)
            outputstr += '}'
            text += ['%s [label="%s|%s|%s"];'%(nodename.replace('.',''),
                                               inputstr,
                                               nodename,
                                               outputstr)]
        # write edges
        for e in edges:
            text.append(e)
        text.append('}')
        fp = open(dotfilename,'wt')
        fp.write('\n'.join(text))
        fp.close()
        return text
        
        
    def export_graph(self, show = False, use_execgraph=False, show_connectinfo=False, dotfilename='graph.dot'):
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
            S = deepcopy(self._execgraph)
            logger.debug('using execgraph')
        else:
            S = deepcopy(self._graph)
            logger.debug('using input graph')
        outfname = fname_presuffix(dotfilename,
                                      suffix='_detailed.dot',
                                      use_ext=False,
                                      newpath=self.config['workdir'])
        logger.info('Creating detailed dot file: %s'%outfname)
        self._write_detailed_dot(S,outfname)
        cmd = 'dot -Tpng -O %s'%outfname
        res = CommandLine(cmd).run()
        if res.runtime.returncode:
            logger.warn('dot2png: %s',res.runtime.stderr)
        S = self._create_pickleable_graph(S, show_connectinfo)
        outfname = fname_presuffix(dotfilename,
                                      suffix='.dot',
                                      use_ext=False,
                                      newpath=self.config['workdir'])
        nx.write_dot(S, outfname)
        logger.info('Creating dot file: %s'%outfname)
        cmd = 'dot -Tpng -O %s'%outfname
        res = CommandLine(cmd).run()
        if res.runtime.returncode:
            logger.warn('dot2png: %s',res.runtime.stderr)
        if show:
            pos = nx.graphviz_layout(S, prog='dot')
            nx.draw(S, pos)
            if show_connectinfo:
                nx.draw_networkx_edge_labels(S, pos)

    def run(self):
        """ Executes the pipeline in serial or parallel mode depending
        on availability of ipython engines (clients/workers)
        """
        self.mec = None
        if self.ipythonclient:
            try:
                self.mec = self.ipythonclient.MultiEngineClient()
            except:
                logger.warn("No clients found, running serially for now.")
        if self.mec:
            self.run_with_manager()
        else:
            self.run_in_series()

    def updatehash(self, force_execute=[]):
        """Updates the hashfile for each diskbased node.

        This function allows one to rerun a pipeline and update all the hashes
        without actually executing any of the underlying interfaces. This is
        useful when moving the working directory from one location to
        another. It is also useful when the hashing function itself changes
        (although we hope that this will not happen often).

        Parameters
        ----------
        force_execute : list of node names
            This forces execution of a node even if updatehash is True
        """
        self.run_in_series(updatehash=True, force_execute=force_execute)

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, str):
            val = source.get_output(sourceinfo)
        elif isinstance(sourceinfo,tuple):
            if callable(sourceinfo[1]):
                val = sourceinfo[1](source.get_output(sourceinfo[0]),
                                    *sourceinfo[2:])
        logger.debug('setting input: %s->%s',param,str(val))
        node.set_input(param, deepcopy(val))

    def run_in_series(self, updatehash=False, force_execute=[]):
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
        self._generate_expanded_graph()
        old_wd = os.getcwd()
        for node in nx.topological_sort(self._execgraph):
            # Assign outputs from dependent executed nodes to current node.
            # The dependencies are stored as data on edges connecting
            # nodes.
            try:
                for edge in self._execgraph.in_edges_iter(node):
                    data = self._execgraph.get_edge_data(*edge)
                    logger.debug('setting input: %s->%s %s',
                                 edge[0],edge[1],str(data))
                    for sourceinfo, destname in data['connect']:
                        self._set_node_input(node, destname,
                                             edge[0], sourceinfo)
                self._set_output_directory_base(node)
                redo = any([node.name.lower()==l.lower() for l in force_execute])
                if updatehash and not redo:
                    node.run(updatehash=updatehash)
                else:
                    node.run(force_execute=redo)
            except:
                os.chdir(old_wd)
                # bare except, but i really don't know where a
                # node might fail
                self._report_crash(node)
                raise
                
    def _report_crash(self, node):
        """Writes crash related information to a file
        """
        message = ['Node %s failed to run.'%node.id]
        logger.error(message)
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        traceback = repr(format_tb(exceptionTraceback))
        timeofcrash = strftime('%Y%m%d-%H%M%S')
        login_name = pwd.getpwuid(os.geteuid())[0]
        crashfile = 'crashdump-%s-%s.npz'%(timeofcrash,
                                           login_name)
        if self.config['crashdump_dir']:
            crashfile = os.path.join(self.config['crashdump_dir'],
                                     crashfile)
        else:
            crashfile = os.path.join(os.getcwd(),crashfile)
        S = self._create_pickleable_graph(self._execgraph, show_connectinfo=True)
        logger.info('Saving crash info to %s'%crashfile)
        np.savez(crashfile, node=node, execgraph=S, traceback=traceback)

    def _set_output_directory_base(self, node):
        if node.disk_based:
            # update parameterization of output directory
            outputdir = self.config['workdir']
            if self.config['use_parameterized_dirs'] and \
                    node.parameterization:
                outputdir = os.path.join(outputdir, node.parameterization)
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
            node.output_directory_base = os.path.abspath(outputdir)
            
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
        self.proc_done    = np.zeros(len(self.procs),dtype=bool)
        self.proc_pending = np.zeros(len(self.procs),dtype=bool)

    def run_with_manager(self):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # retrieve clients again
        if not self.mec:
            try:
                self.mec = self.ipythonclient.MultiEngineClient()
            except ConnectionRefusedError:
                warn("No clients found, running serially for now.")
                self.run_in_series()
                return
        logger.info("Running in parallel.")
        self.mec.reset()
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self._generate_expanded_graph()
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list()
        # get number of ipython clients available
        self.workeravailable = np.zeros(np.max(self.mec.get_ids())+1, dtype=bool)
        self.workeravailable[self.mec.get_ids()] = True
        self.pendingresults = []
        self.readytorun = []
        # setup polling
        while np.any(self.proc_done==False) | np.any(self.proc_pending==True):
            toappend = []
            # trigger callbacks for any pending results
            while self.pendingresults:
                a = self.pendingresults.pop()
                try:
                    res = a[0].get_result(block=False)
                except CompositeError, e:
                    self._report_crash(self.procs[a[1]])
                    e.print_tracebacks()
                    e.raise_exception()
                except:
                    # bare except, but i really don't know where a
                    # node might fail
                    self._report_crash(self.procs[a[1]])
                    raise
                if not res:
                    toappend.append(a)
            self.pendingresults.extend(toappend)
            self.send_procs_to_workers()
            sleep(2)
                
    def jobavailable(self):
        """ Evaluates dependencies that have been completed to
        determine which if the pending jobs are now ready to run

        Returns
        --------

        jobexists: A boolean flag indicating presence of a job
        jobid: An identifier for which job to run
        """
        jobexists = False
        jobid = -1
        # first determine which processes have their dependencies satisfied
        idx = np.flatnonzero((self.proc_done == False) & \
                                 np.all(self.depidx==0,axis=0))
        self.readytorun.extend(np.setdiff1d(idx,self.readytorun))
        if self.readytorun:
            jobid = self.readytorun[0]
            self.readytorun.remove(jobid)
            jobexists = True
        return jobexists,jobid
    

    def send_procs_to_workers(self):
        """ Sends jobs to workers depending on availability of jobs
        and workers. This function should be executed in a critical
        section for a true distributed approach.
        """
        while np.any(self.proc_done==False) and \
                np.any(self.workeravailable==True):
            # Check to see if a job is available
            (jobexists,jobid) = self.jobavailable()
            if jobexists:
                # change job status in appropriate queues
                self.proc_done[jobid] = True
                self.proc_pending[jobid] = True
                # change worker status in appropriate queues
                workerid = self.workeravailable.tolist().index(True)
                self.workeravailable[workerid] = False
                self._set_output_directory_base(self.procs[jobid])
                # Send job to worker, add callback and add to pending results
                hashed_inputs, hashvalue = self.procs[jobid].inputs._get_bunch_hash()
                logger.info('Executing: %s ID: %d WID=%d H:%s' % \
                    (self.procs[jobid].name, jobid, workerid, hashvalue))
                self.mec.push(dict(task=self.procs[jobid]),
                              targets=workerid,
                              block=True)
                cmdstr = "task.run()"
                self.pendingresults.append((self.mec.execute(cmdstr,
                                                            targets=workerid,
                                                            block=False),
                                            jobid))
                self.pendingresults[-1][0].add_callback(self.notifymanagercb,
                                                        jobid=jobid,
                                                        workerid=workerid)
            else:
                break

    def notifymanagercb(self,result,*args,**kwargs):
        """ This is called when a job is completed. Currently this
        triggered by a call to get_results, but hopefully will be
        automatic in the near future.
        """
        jobid = kwargs['jobid']
        workerid = kwargs['workerid']
        logger.info('[Job finished] jobname: %s jobid: %d workerid: %d' % \
                        (self.procs[jobid].name,jobid,workerid))
        # Update job and worker queues
        self.proc_pending[jobid] = False
        self.workeravailable[workerid] = True
        task = self.mec.pull('task',targets=workerid,block=True).pop()
        self.procs[jobid]._result = deepcopy(task.result)
        # Update the inputs of all tasks that depend on this job's outputs
        graph = self._execgraph
        for edge in graph.out_edges_iter(self.procs[jobid]):
            data = graph.get_edge_data(*edge)
            for sourceinfo,destname in data['connect']:
                self._set_node_input(edge[1], destname,
                                     self.procs[jobid], sourceinfo)
        # update the job dependency structure
        self.depidx[jobid,:] = 0.

    def _merge_graphs(self, supergraph, nodes, subgraph, nodeid, iterables):
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
                    edgeinfo[n.id].append((edge[0],supergraph.get_edge_data(*edge)))
        supergraph.remove_nodes_from(nodes)
        # Add copies of the subgraph depending on the number of iterables
        for i,params in enumerate(walk(iterables.items())):
            Gc = deepcopy(subgraph)
            ids = [n.id for n in Gc.nodes()]
            nodeidx = ids.index(nodeid)
            paramstr = ''
            for key,val in sorted(params.items()):
                paramstr = '_'.join((paramstr, key, str(val).replace(os.sep,'_')))
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
            for n in Gc.nodes():
                if n.id in edgeinfo.keys():
                    for ei in edgeinfo[n.id]:
                        supergraph.add_edges_from([(ei[0], n, ei[1])])
                n.id += str(i)
        return supergraph

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
                node.iterables = dict(map(lambda(x):(x[0],lambda:x[1]),
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
                subnodes = nx.dfs_preorder(graph_in,node)
                Gn = graph_in.subgraph(subnodes)
                graph_in = self._merge_graphs(graph_in, subnodes, Gn, node.id,
                                              iterables)
            else:
                moreiterables = False
        self._execgraph = graph_in
        logger.info("PE: expanding iterables ... done")

