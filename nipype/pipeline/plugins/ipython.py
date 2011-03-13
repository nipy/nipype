# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via IPython controller
"""

from copy import deepcopy
import shutil
import sys
from time import sleep

import numpy as np
from IPython.Release import version as IPyversion
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass

from .base import (PluginBase, logger, report_crash, report_nodes_not_run)
from ..utils import (nx, dfs_preorder, config)
from ..engine import MapNode

class ipython_runner(PluginBase):
    """Execute workflow with ipython
    """

    def __init__(self):
        self._init_runtime_fields()

    def _init_runtime_fields(self):
        """Reset runtime attributes to none

        procs: list (N) of underlying interface elements to be processed
        proc_done: a boolean vector (N) signifying whether a process has been
            executed
        proc_pending: a boolean vector (N) signifying whether a
            process is currently running. Note: A process is finished only when
            both proc_done==True and
        proc_pending==False
        depidx: a boolean matrix (NxN) storing the dependency structure accross
            processes. Process dependencies are derived from each column.
        """
        self.procs = None
        self.depidx = None
        self.refidx = None
        self.mapnodes = None
        self.mapnodesubids = None
        self.proc_done = None
        self.proc_pending = None
        self.ipyclient = None
        self.taskclient = None

    def run(self, graph, updatehash=False):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # retrieve clients again
        try:
            name = 'IPython.kernel.client'
            __import__(name)
            self.ipyclient = sys.modules[name]
        except ImportError:
            raise ImportError("Ipython kernel not found. Parallel execution will be" \
                     "unavailable")
        try:
            self.taskclient = self.ipyclient.TaskClient()
        except Exception, e:
            if isinstance(e, ConnectionRefusedError):
                raise Exception("No IPython clients found.")
            if isinstance(e, ValueError):
                raise Exception("Ipython kernel not installed")
        logger.info("Running in parallel.")
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list(graph)
        # get number of ipython clients available
        self.pending_tasks = []
        self.readytorun = []
        self.mapnodes = []
        self.mapnodesubids = {}
        # setup polling - TODO: change to threaded model
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
                            crashfile = report_crash(self.procs[jobid],
                                                     traceback=res['traceback'])
                            if jobid in self.mapnodesubids:
                                jobid = self.mapnodesubids[jobid]
                            # remove dependencies from queue
                            notrun.append(self._remove_node_deps(jobid, crashfile, graph))
                        else:
                            self._task_finished_cb(res['result'], jobid)
                            self._remove_node_dirs()
                        if IPyversion >= '0.10.1':
                            logger.debug("Clearing id: %d"%taskid)
                            self.taskclient.clear(taskid)
                    else:
                        toappend.insert(0, (taskid, jobid))
                except:
                    crashfile = report_crash(self.procs[jobid])
                    # remove dependencies from queue
                    if jobid in self.mapnodesubids:
                        jobid = self.mapnodesubids[jobid]
                    notrun.append(self._remove_node_deps(jobid, crashfile))
            if toappend:
                self.pending_tasks.extend(toappend)
            self._send_procs_to_workers(updatehash=updatehash)
            sleep(2)
        self._remove_node_dirs()
        report_nodes_not_run(notrun)

    def _submit_mapnode(self, jobid):
        if jobid in self.mapnodes:
            return True
        self.mapnodes.append(jobid)
        mapnodesubids = self.procs[jobid].get_subnodes()
        numnodes = len(mapnodesubids)
        for i in range(numnodes):
            self.mapnodesubids[self.depidx.shape[0]+i] = jobid
        self.procs.extend(mapnodesubids)
        self.depidx = np.vstack((self.depidx,np.zeros((numnodes,self.depidx.shape[1]))))
        self.depidx = np.hstack((self.depidx,np.zeros((self.depidx.shape[0],numnodes))))
        self.depidx[-numnodes:,jobid] = 1
        self.proc_done = np.concatenate((self.proc_done, np.zeros(numnodes, dtype=bool)))
        self.proc_pending = np.concatenate((self.proc_pending, np.zeros(numnodes, dtype=bool)))
        return False

        
    def _send_procs_to_workers(self, updatehash=False):
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
                    if isinstance(self.procs[jobid], MapNode):
                        submit = self._submit_mapnode(jobid)
                        if not submit:
                            continue
                    # change job status in appropriate queues
                    self.proc_done[jobid] = True
                    self.proc_pending[jobid] = True
                    # Send job to task manager and add to pending tasks
                    _, hashvalue = self.procs[jobid]._get_hashval()
                    logger.info('Executing: %s ID: %d H:%s' % \
                                    (self.procs[jobid]._id, jobid, hashvalue))
                    cmdstr = """import sys
from traceback import format_exception
traceback=None
try:
    result = task.run(updatehash=updatehash)
except:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    result = task.result
"""
                    task = self.ipyclient.StringTask(cmdstr,
                                                     push = dict(task=self.procs[jobid],
                                                                 updatehash=updatehash),
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
        # update the job dependency structure
        self.depidx[jobid, :] = 0.
        if jobid not in self.mapnodesubids:
            self.refidx[np.nonzero(self.refidx[:,jobid]>0)[0],jobid] = 0

    def _generate_dependency_list(self, graph):
        """ Generates a dependency list for a list of graphs.
        """
        self.procs = graph.nodes()
        self.depidx = nx.adj_matrix(graph).__array__()
        self.refidx = deepcopy(self.depidx>0)
        self.refidx.dtype = np.int8
        self.proc_done    = np.zeros(len(self.procs), dtype=bool)
        self.proc_pending = np.zeros(len(self.procs), dtype=bool)

    def _remove_node_deps(self, jobid, crashfile, graph):
        subnodes = [s for s in dfs_preorder(graph, self.procs[jobid])]
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
                if idx in self.mapnodesubids:
                    continue
                if self.proc_done[idx] and (not self.proc_pending[idx]):
                    self.refidx[idx,idx] = -1
                    outdir = self.procs[idx]._output_directory()
                    logger.info(('[node dependencies finished] '
                                 'removing node: %s from directory %s') % \
                                    (self.procs[idx]._id,
                                     outdir))
                    shutil.rmtree(outdir)

