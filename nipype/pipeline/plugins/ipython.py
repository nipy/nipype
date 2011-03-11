# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via IPython controller
"""

import shutil
import sleep

from IPython.Release import version as IPyversion
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass

from .base import PluginBase

class ipython_runner(PluginBase):
    """Execute workflow with ipython
    """

    def __init__(self):
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

    def run(self, graph):
        self._execute_with_manager(graph)
        pass

    def _execute_with_manager(self, graph):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
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
        if len(graph.out_edges(self.procs[jobid])):
            self.procs[jobid]._result = None
        # update the job dependency structure
        self.depidx[jobid, :] = 0.
        self.refidx[np.nonzero(self.refidx[:,jobid]>0)[0],jobid] = 0

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
        subnodes = [s for s in dfs_preorder(self._execgraph, self.procs[jobid])]
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

