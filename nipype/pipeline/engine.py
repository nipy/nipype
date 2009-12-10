"""Defines functionality for pipelined execution of interfaces

The `Pipeline` class provides core functionality for batch processing. 
"""

import os
import sys
from copy import deepcopy
from time import sleep, strftime
from warnings import warn
import logging
import logging.handlers
from traceback import extract_tb

import networkx as nx
import numpy as np

from nipype.interfaces.base import CommandLine
from nipype.utils.filemanip import fname_presuffix

LOG_FILENAME = 'pypeline.log'
logging.basicConfig()
logger = logging.getLogger('engine')
nwlogger = logging.getLogger('nodewrapper')
hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                            maxBytes=50000,
                                            backupCount=5)
formatter = logging.Formatter('%(asctime)s %(name)-2s '\
                        '%(levelname)-2s:\n\t %(message)s')
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

    def connect(self, connection_list):
        """Connect nodes in the pipeline.

        This routine also checks if inputs and outputs are actually provided by
        the nodes that are being connected. 

        Creates edges in the directed graph using the nodes and edges specified
        in the `connection_list`.  Uses the NetworkX method
        DiGraph.add_edges_from. 

        Parameters
        ----------
        connection_list : list
            A list of 3-tuples of the following form::

             [(source1, destination1, [('namedoutput1', 'namedinput1'),
               ...]), 
             ...]
            
            Or::

             [(source1, destination1, [(('namedoutput1', func, arg2, ...),
                                         'namedinput1'), ...]),
             ...]
             namedoutput1 will always be the first argument to func.
        """
        logger.info("checking connections:")
        not_found = []
        for u, v, d in connection_list:
            for source, dest in d:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if '.io' not in v.name:
                    if dest not in v.inputs.__dict__:
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
                    if not sourcename in u.interface.outputs().__dict__:
                        not_found.append(['out',u.name,sourcename])
        logger.info("checking connections: done")
        for c in not_found: 
            warn("Module %s has no %sput called %s\n"%(c[1],c[0],c[2]))
        if not_found:
            raise Exception('Some connections were not found')
        self._graph.add_edges_from([(u, v, {'connect':d}) 
                                    for u, v, d in connection_list])

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
        S = deepcopy(graph)
        for e in S.edges():
            data = S.get_edge_data(*e)
            S.remove_edge(*e)
            if show_connectinfo:
                S.add_edge(e[0], e[1], l=str(data['connect']))
            else:
                S.add_edge(e[0], e[1])
        return S

    def export_graph(self, show = True, use_execgraph=False, show_connectinfo=False, dotfilename='graph.dot'):
        """ Displays the graph layout of the pipeline

        Parameters
        ----------
        use_execgraph : boolean
            Indicates whether to use the specification graph or the
            execution graph. default [False]
       
        show_connectioninfo : boolean
            Indicates whether to show the edge data on the graph. This
            makes the graph rather cluttered. default [False]
        """
        if self._execgraph and use_execgraph:
            S = deepcopy(self._execgraph)
            logger.debug('using execgraph')
        else:
            S = deepcopy(self._graph)
            logger.debug('using input graph')
        S = self._create_pickleable_graph(S, show_connectinfo)
        dotfilename = fname_presuffix(dotfilename,
                                      suffix='.dot',
                                      use_ext=False,
                                      newpath=self.config['workdir'])
        nx.write_dot(S, dotfilename)
        logger.info('Creating dot file: %s'%dotfilename)
        cmd = 'dot -Tpng -O %s'%dotfilename
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

    def run_in_series(self, relocate=False):
        """Executes a pre-defined pipeline in a serial order.

        Parameters
        ----------
        relocate : boolean
            Allows one to rerun a pipeline and update all the hashes without
            actually executing any of the underlying interfaces. This is useful
            when moving the working directory from one location to another. It
            is also useful when the hashing function itself changes (although
            we hope that this will not happen often). default [False]
        """
        # In the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self._generate_expanded_graph()
        for node in nx.topological_sort(self._execgraph):
            # Assign outputs from dependent executed nodes to current node.
            # The dependencies are stored as data on edges connecting nodes.
            for edge in self._execgraph.in_edges_iter(node):
                data = self._execgraph.get_edge_data(*edge)
                logger.debug('setting input: %s->%s %s',edge[0],edge[1],str(data))
                for sourcename, destname in data['connect']:
                    if isinstance(sourcename, str):
                        node.set_input(destname,
                                       edge[0].get_output(sourcename))
                    else: # tuple
                        node.set_input(destname, sourcename[1],
                                       edge[0].get_output(sourcename[0]),
                                       *sourcename[2:])
            #hashed_inputs, hashvalue = node.inputs._get_bunch_hash()
            #logger.info("Executing: %s H: %s" % (node.name, hashvalue))
            # For a disk node, provide it with an appropriate
            # output directory
            if node.disk_based:
                outputdir = self.config['workdir']
                if self.config['use_parameterized_dirs']:
                    outputdir = os.path.join(outputdir, node.parameterization)
                if not os.path.exists(outputdir):
                    os.makedirs(outputdir)
                node.output_directory_base = os.path.abspath(outputdir)
            if relocate:
                node.run(updatehash=relocate)
            else:
                try:
                    old_wd = os.getcwd()
                    node.run()
                except:
                    os.chdir(old_wd)
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    # bare except, but i really don't know where a
                    # node might fail
                    message = ['Node %s failed to run.'%node.id]
                    logger.error(message)
                    self._report_crash(node, extract_tb(exceptionTraceback))
                    raise
                
    def _report_crash(self, node, traceback):
        """Writes crash related information to a file
        """
        timeofcrash = strftime('%Y%m%d-%H%M%S')
        crashfile = 'crashdump-%s-%s.npz'%(timeofcrash,
                                           os.getlogin())
        if self.config['crashdump_dir']:
            crashfile = os.path.join(self.config['crashdump_dir'],
                                     crashfile)
        else:
            crashfile = os.path.join(os.getcwd(),crashfile)
        S = self._create_pickleable_graph(self._execgraph, show_connectinfo=True)
        logger.info('Saving crash info to %s'%crashfile)
        np.savez(crashfile, node=node, execgraph=S, traceback=traceback)

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
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self._generate_expanded_graph()
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list()
        # retrieve clients again
        if not self.mec:
            try:
                self.mec = self.ipythonclient.MultiEngineClient()
            except ConnectionRefusedError:
                warn("No clients found, running serially for now.")
                self.run_in_series()
                return
        self.mec.reset()
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
                res = a.get_result(block=False)
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
                # update parameterization of output directory
                outputdir = self.config['workdir']
                if self.config['use_parameterized_dirs']:
                    outputdir = os.path.join(outputdir,
                                             self.procs[jobid].parameterization)
                if not os.path.exists(outputdir):
                    os.makedirs(outputdir)
                self.procs[jobid].output_directory_base = os.path.abspath(outputdir)
                # Send job to worker, add callback and add to pending results
                hashed_inputs, hashvalue = self.procs[jobid].inputs._get_bunch_hash()
                logger.info('Executing: %s ID: %d WID=%d H:%s' % \
                    (self.procs[jobid].name, jobid, workerid, hashvalue))
                self.mec.push(dict(task=self.procs[jobid]),
                              targets=workerid,
                              block=True)
                cmdstr = "task.run()"
                self.pendingresults.append(self.mec.execute(cmdstr,
                                                            targets=workerid,
                                                            block=False))
                self.pendingresults[-1].add_callback(self.notifymanagercb,
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
        if issubclass(self.procs[jobid]._interface.__class__,CommandLine):
            logger.info('cmd: ' + self.procs[jobid]._interface.cmdline)
        # Update the inputs of all tasks that depend on this job's outputs
        graph = self._execgraph
        for edge in graph.out_edges_iter(self.procs[jobid]):
            data = graph.get_edge_data(*edge)
            for sourcename,destname in data['connect']:
                if isinstance(sourcename,str):
                    edge[1].set_input(destname,
                                   self.procs[jobid].get_output(sourcename))
                else:
                    edge[1].set_input(destname, sourcename[1],
                                   self.procs[jobid].get_output(sourcename[0]),
                                   *sourcename[2:])
        # update the job dependency structure
        self.depidx[jobid,:] = 0.

    def _merge_graphs(self, supergraph, nodes, subgraph, nodeid, iterables):
        """Merges two graphs that share a subset of nodes.

        If the subgraph needs to be replicated, the merge happens with every
        copy of the subgraph
        """
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
                    #if len(edge)==3:
                    edgeinfo[n.id].append((edge[0],supergraph.get_edge_data(*edge)))
                    #else:
                    #    edgeinfo[n.id].append((edge[0],None))
        supergraph.remove_nodes_from(nodes)
        for i,params in enumerate(walk(iterables.items())):
            Gc = deepcopy(subgraph)
            ids = [n.id for n in Gc.nodes()]
            nodeidx = ids.index(nodeid)
            paramstr = ''
            for key,val in sorted(params.items()):
                paramstr = '_'.join((paramstr, key, str(val)))
                setattr(Gc.nodes()[nodeidx].inputs, key, val)
            for n in Gc.nodes():
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
                        #if ei[1]:
                        supergraph.add_edges_from([(ei[0], n, ei[1])])
                        #else:
                        #    supergraph.add_edges_from([(ei[0], n)])
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
        while moreiterables:
            nodes = nx.topological_sort(graph_in)
            nodes.reverse()
            inodes = [node for node in nodes if len(node.iterables.keys())>0]
            if len(inodes)==0:
                moreiterables = False
            else:
                node = inodes[0]
                iterables = node.iterables.copy()
                node.iterables = {}
                node.id += 'I'
                subnodes = nx.dfs_preorder(graph_in,node)
                Gn = graph_in.subgraph(subnodes)
                graph_in = self._merge_graphs(graph_in, subnodes, Gn, node.id,
                                              iterables)
        self._execgraph = graph_in
        logger.info("PE: expanding iterables ... done")

