"""
Base class for nipy.pipeline processing modules
"""

import hashlib
import os
import copy
from time import sleep
from warnings import warn

import networkx as nx
import numpy as np

try:
    from IPython.kernel import client
    IPython_available = True
except:
    warn("Ipython kernel not found", ImportWarning)
    IPython_available = False

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
        

class Pipeline(object):
    """Controls the setup and execution of a pipeline of processes

    Attributes
    ----------

    config: a dict containing various options for controlling the
    pipeline

    config['workdir']: What diskspace to use for pipeline operations

    config['use_parameterized_dirs']: Controls whether pipeline
    outputs are stored in some hiearachical 2-level structure based on
    parameterization or all output directories are created in the same
    location.

    config['hash_outputdir_names']: Whether or not to hash the names
    of the directories. In general it's a good idea.
    """

    def __init__(self):
        """
        """
        super(Pipeline,self).__init__()
        self.graph        = nx.DiGraph()
        self.listofgraphs = []
        self.config       = {}
        self.config['workdir'] = '.'
        self.config['use_parameterized_dirs'] = False
        self.IPython_available = IPython_available

    def connect(self,connection_list):
        """ Wraps the networkx functionality in a more semantically
        relevant function name

        Parameters
        -----------
        
        - `connection_list`: A list of 3-tuples of the following form
        [(source1,destination1,[('namedoutput1','namedinput1'),...]),...]
        """
        self.graph.add_edges_from([(u,v,{'connect':d}) for u,v,d in connection_list])
        print "PE: checking connections:\n"
        for u,v,d in connection_list:
            for source,dest in d:
                try:
                    if v.inputs.__dict__.has_key(dest) is not True:
                        print "Module %s has no input called %s\n"%(v.name,dest)
                except:
                    print "unable to query inputs of module %s\n"%v.name
                try:
                    if not source in u.interface.outputs_help.__doc__:
                        print "Module %s has no output called %s\n"%(u.name,source)
                except:
                    print "unable to query outputs of module %s\n"%u.name
        print "PE: finished checking connections\n"

    def addmodules(self,modules):
        """ Wraps the networkx functionality in a more semantically
        relevant function name

        Parameters
        -----------
        
        - `modules`: A list of modules such as [mod1,mod2,mod3,...]
        """
        self.graph.add_nodes_from(modules)

    def showgraph(self,prog='dot'):
        """ Displays the graph layout of the pipeline
        """
        pos = nx.shell_layout(self.graph)
        nx.draw(self.graph,pos)
        #nx.draw_graphviz(self.graph,prog=prog)

    def generate_parameterized_graphs(self):
        """ Generates a new graph for each unique parameterization of
        the modules. Parameterization is controlled using the
        `iterables` field of the pipeline elements. Thus if there are
        two nodes with iterables a=[1,2] and b=[3,4] this procedure
        will generate 4 graphs parameterized as (a=1,b=3), (a=1,b=4),
        (a=2,b=3) and (a=2,b=4). 
        """
        iterables = []
        self.listofgraphs = []
        # Create a list of iterables
        for i,node in enumerate(nx.topological_sort(self.graph)):
            for key,func in node.iterables.items():
                iterables.append(((i,key),func))
        # return a copy of the graph if there are no iterables
        if len(iterables) == 0:
            self.listofgraphs.append(copy.deepcopy(self.graph))
            return
        # Walk through the list of iterables generating a unique set
        # of parameters.
        for i,params in enumerate(walk(iterables)):
            # copy the graph
            graphcopy = copy.deepcopy(self.graph)
            self.listofgraphs.append(graphcopy)
            # I don't know if the following is kosher, but it appears
            # to work
            self.listofgraphs[-1].__dict__.update(name='')
            order = nx.topological_sort(graphcopy)
            for key,val in params.items():
                # assign values to the nodes
                order[key[0]].inputs[key[1]] = val
                # update name of graph based on parameterization
                name = self.listofgraphs[-1].__dict__['name']
                newname = ''.join((name,'_',key[1],'_',str(val)))
                self.listofgraphs[-1].__dict__.update(name=newname)

    def generate_dependency_list(self):
        """ Generates a dependency list for a list of graphs. Adds the
        following attributes to the pipeline:

        New attributes:
        ---------------
        
        procs: list (N) of underlying interface elements to be
        processed 
        procs_graph_id: identifier of the graph that the process came
        from
        proc_hash: a hash of the inputs to a process to uniquely
        identify each process and to determine redundant processes

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
        self.procs      = []
        self.procs_graph_id = []
        proc_deps  = []
        for i,graph in enumerate(self.listofgraphs):
            order = nx.topological_sort(graph)
            for node in order:
                deps = []
                for edge in graph.in_edges_iter(node):
                    deps.append(edge[0])
                node.iterables = {}
                self.procs.append(node)
                self.procs_graph_id.append(i)
                proc_deps.append(deps)
        nprocs = len(self.procs)
        self.proc_hash    = np.zeros(nprocs,dtype='|S32')
        self.proc_done    = np.zeros(nprocs,dtype=bool)
        self.proc_pending = np.zeros(nprocs,dtype=bool)
        self.depidx       = np.zeros((nprocs,nprocs),dtype=bool)
        for i,proc in enumerate(self.procs):
            # print i,proc.name
            for deps in proc_deps[i]:
                self.depidx[self.procs.index(deps),i] = True
                # print "dep:", deps.name

    def run(self):
        """ Executes the pipeline in serial or parallel mode depending
        on availability of ipython engines (clients/workers)
        """
        if self.IPython_available:
            try:
                self.mec = client.MultiEngineClient()
            except:
                print "No clients found. running serially"
                self.IPython_available = False
        if self.IPython_available:
            self.run_with_manager()
        else:
            self.run_in_series()

    def run_in_series(self):
        """Executes a pre-defined pipeline in a serial order.
        """
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self.listofgraphs = []
        self.generate_parameterized_graphs()

        for graph in self.listofgraphs:
            order = nx.topological_sort(graph)
            for node in order:
                # Assign outputs from dependent executed nodes to
                # current node The dependencies are stored as data on
                # edges connecting nodes
                for edge in graph.in_edges_iter(node):
                    data = graph.get_edge_data(*edge)
                    for sourcename,destname in data['connect']:
                        node.set_input(destname,edge[0].get_output(sourcename))
                print "Executing: %s H: %s" % (node.name, node.hash_inputs())
                # For a disk node, provide it with an appropriate
                # output directory
                if node.diskbased:
                    outputdir = self.config['workdir']
                    if self.config['use_parameterized_dirs'] and (graph.__dict__['name'] is not ''):
                        outputdir = os.path.join(outputdir,graph.__dict__['name'])
                    if not os.path.exists(outputdir):
                        os.mkdir(outputdir)
                    node.output_directory_base = os.path.abspath(outputdir)
                node.parameterization = graph.__dict__['name']
                node.run()

    def run_with_manager(self):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # in the absence of a dirty bit on the object, generate the
        # parameterization each time before running
        self.listofgraphs = []
        self.generate_parameterized_graphs()
        # Generate appropriate structures for worker-manager model
        self.generate_dependency_list()
        # retrieve clients again
        if self.IPython_available:
            try:
                self.mec = client.MultiEngineClient()
            except:
                print "No clients found. running serially"
                self.IPython_available = False
        if not self.IPython_available:
            self.run_in_series()
            return
        # execute pipeline
        self.workeravailable = np.zeros(np.max(self.mec.get_ids())+1,dtype=bool)
        self.workeravailable[self.mec.get_ids()] = True
        self.pendingresults  = []
        self.readytorun = []
        # setup polling
        while np.any(self.proc_done==False) | np.any(self.proc_pending==True):
            toappend = []
            # trigger callbacks for any pending results
            while len(self.pendingresults)>0:
                a = self.pendingresults.pop()
                res = a.get_result(default=False)
                if res is False:
                    toappend.append(a)
            self.pendingresults.extend(toappend)
            self.send_procs_to_workers()
            sleep(2)
                
    def jobavailable(self,):
        """ Evaluates dependencies that have been completed to
        determine which if the pending jobs are now ready to run

        Returns
        --------

        jobexists: A boolean flag indicating presence of a job
        jobid: An identifier for which job to run
        """
        jobexists = False
        jobid     = -1
        # first determine which processes have their dependencies satisfied
        idx = np.flatnonzero((self.proc_done == False) & np.all(self.depidx==False,axis=0))
        # calculate the hashes of these processes
        for i in idx:
            self.proc_hash[i] = self.procs[i].hash_inputs()
        # get only the unique hashes
        hashes,i = np.unique1d(self.proc_hash[idx],return_index=True)
        # add these to readytorun queue
        idx = idx.take(np.sort(i))
        self.readytorun.extend(np.setdiff1d(idx,self.readytorun))
        try:
            jobid = self.readytorun[0]
            self.readytorun.remove(jobid)
            jobexists = True
        except:
            pass
        return jobexists,jobid
    

    def send_procs_to_workers(self):
        """ Sends jobs to workers depending on availability of jobs
        and workers. This function should be executed in a critical
        section for a true distributed approach.
        """
        while np.any(self.proc_done==False) and np.any(self.workeravailable==True):
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
                graph = self.listofgraphs[self.procs_graph_id[jobid]]
                outputdir = self.config['workdir']
                if self.config['use_parameterized_dirs'] and (graph.__dict__['name'] is not ''):
                    outputdir = os.path.join(outputdir,graph.__dict__['name'])
                self.procs[jobid].parameterization = graph.__dict__['name']
                self.procs[jobid].output_directory_base = os.path.abspath(outputdir)
                # Send job to worker, add callback and add to pending results
                print 'Executing: %s ID: %d WID=%d H:%s' % (self.procs[jobid].name,jobid,workerid,self.procs[jobid].hash_inputs())
                self.mec.push(dict(task=self.procs[jobid],hashout=self.config['hash_outputdir_names']),targets=workerid,block=True)
                cmdstr = 'task.execute(hashoutputdir=hashout)'
                self.pendingresults.append(self.mec.execute(cmdstr,targets=workerid,block=False))
                self.pendingresults[-1].add_callback(self.notifymanagercb,jobid=jobid,workerid=workerid)
            else:
                break

    def notifymanagercb(self,result,*args,**kwargs):
        """ This is called when a job is completed. Currently this
        triggered by a call to get_results, but hopefully will be
        automatic in the near future.
        """
        jobid = kwargs['jobid']
        workerid = kwargs['workerid']
        print '[Job finished] jobname: %s jobid: %d workerid: %d' % (self.procs[jobid].name,jobid,workerid)
        # Update job and worker queues
        self.proc_pending[jobid] = False
        self.workeravailable[workerid] = True
        task = self.mec.pull('task',targets=workerid,block=True).pop()
        self.procs[jobid].output = copy.deepcopy(task.output)
        # Update the inputs of all tasks that depend on this job's outputs
        graph = self.listofgraphs[self.procs_graph_id[jobid]]
        for edge in graph.out_edges_iter(self.procs[jobid]):
            data = graph.get_edge_data(*edge)
            for sourcename,destname in data['connect']:
                edge[1].set_input(destname,self.procs[jobid].get_output(sourcename))
        # update the job dependency structure
        self.depidx[jobid,:] = False
        

