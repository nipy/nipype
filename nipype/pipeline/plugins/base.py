# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Common graph operations for execution
"""

from copy import deepcopy
import logging
import os
import pwd
import shutil
from socket import gethostname
import sys
from time import strftime, sleep
from traceback import format_exception

import numpy as np
import scipy.sparse as ssp

from ..utils import (nx, dfs_preorder, config)
from ..engine import MapNode

logger = logging.getLogger('workflow')

def report_crash(node, traceback=None):
    """Writes crash related information to a file
    """
    name = node._id
    if node.result and hasattr(node.result, 'runtime') and \
            node.result.runtime:
        if isinstance(node.result.runtime, list):
            host = node.result.runtime[0].hostname
        else:
            host = node.result.runtime.hostname
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
    if hasattr(node, 'config') and ('crashdump_dir' in node.config.keys()):
        if not os.path.exists(node.config['crashdump_dir']):
            os.makedirs(node.config['crashdump_dir'])
        crashfile = os.path.join(node.config['crashdump_dir'],
                                 crashfile)
    else:
        crashfile = os.path.join(os.getcwd(), crashfile)
    logger.info('Saving crash info to %s' % crashfile)
    logger.info(''.join(traceback))
    np.savez(crashfile, node=node, traceback=traceback)
    return crashfile

def report_nodes_not_run(notrun):
    """List nodes that crashed with crashfile info

    Optionally displays dependent nodes that weren't executed as a result of
    the crash.
    """
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            logger.error("could not run node: %s" % '.'.join((info['node']._hierarchy,
                                                              info['node']._id)))
            logger.info("crashfile: %s" % info['crashfile'])
            logger.debug("The following dependent nodes were not run")
            for subnode in info['dependents']:
                logger.debug(subnode._id)
        logger.info("***********************************")
        raise RuntimeError('Workflow did not execute cleanly. Check log for details')

class PluginBase(object):
    """Base class for plugins"""

    def __init__(self, plugin_args=None):
        pass

    def run(self, graph):
        raise NotImplementedError


class DistributedPluginBase(PluginBase):
    """Execute workflow with a distribution engine
    """
    
    def __init__(self, plugin_args=None):
        """Initialize runtime attributes to none

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

    def run(self, graph, updatehash=False):
        """Executes a pre-defined pipeline using distributed approaches
        """
        logger.info("Running in parallel.")
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list(graph)
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
                    result = self._get_result(taskid)
                    if result:
                        if result['traceback']:
                            crashfile = self._report_crash(self.procs[jobid],
                                                           result)
                            if jobid in self.mapnodesubids:
                                jobid = self.mapnodesubids[jobid]
                            # remove dependencies from queue
                            notrun.append(self._remove_node_deps(jobid,
                                                                 crashfile,
                                                                 graph))
                        else:
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                        self._clear_task(taskid)
                    else:
                        toappend.insert(0, (taskid, jobid))
                except:
                    crashfile = self._report_crash(self.procs[jobid])
                    # remove dependencies from queue
                    if jobid in self.mapnodesubids:
                        jobid = self.mapnodesubids[jobid]
                    notrun.append(self._remove_node_deps(jobid, crashfile,
                                                         graph))
            if toappend:
                self.pending_tasks.extend(toappend)
            self._send_procs_to_workers(updatehash=updatehash)
            sleep(2)
        self._remove_node_dirs()
        report_nodes_not_run(notrun)

    def _get_result(self, taskid):
        raise NotImplementedError

    def _submit_job(self, node, updatehash=False):
        raise NotImplementedError

    def _report_crash(self, node, result=None):
        raise NotImplementedError

    def _clear_task(self, taskid):
        raise NotImplementedError

    def _submit_mapnode(self, jobid):
        if jobid in self.mapnodes:
            return True
        self.mapnodes.append(jobid)
        mapnodesubids = self.procs[jobid].get_subnodes()
        numnodes = len(mapnodesubids)
        logger.info('Adding %d jobs for mapnode %s'%(numnodes, self.procs[jobid]._id))
        for i in range(numnodes):
            self.mapnodesubids[self.depidx.shape[0]+i] = jobid
        self.procs.extend(mapnodesubids)
        self.depidx = ssp.vstack((self.depidx,
                                  ssp.lil_matrix(np.zeros((numnodes, self.depidx.shape[1])))),
                                 'lil')
        self.depidx = ssp.hstack((self.depidx,
                                  ssp.lil_matrix(np.zeros((self.depidx.shape[0], numnodes)))),
                                 'lil')
        self.depidx[-numnodes:, jobid] = 1
        self.proc_done = np.concatenate((self.proc_done,
                                         np.zeros(numnodes, dtype=bool)))
        self.proc_pending = np.concatenate((self.proc_pending,
                                            np.zeros(numnodes, dtype=bool)))
        return False

    def _send_procs_to_workers(self, updatehash=False):
        """ Sends jobs to workers using ipython's taskclient interface
        """
        while np.any(self.proc_done == False):
            # Check to see if a job is available
            jobids = np.flatnonzero((self.proc_done == False) & \
                                        (self.depidx.sum(axis=0)==0).__array__())
            if len(jobids)>0:
                # send all available jobs
                logger.info('Submitting %d jobs' % len(jobids))
                for jobid in jobids:
                    if isinstance(self.procs[jobid], MapNode) and \
                            self.procs[jobid].num_subnodes()>1:
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
                    tid = self._submit_job(self.procs[jobid],
                                           updatehash=updatehash)
                    self.pending_tasks.insert(0, (tid, jobid))
            else:
                break

    def _task_finished_cb(self, jobid):
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
            self.refidx[self.refidx[:,jobid].nonzero()[0],jobid] = 0

    def _generate_dependency_list(self, graph):
        """ Generates a dependency list for a list of graphs.
        """
        self.procs = graph.nodes()
        self.depidx = ssp.lil_matrix(nx.adj_matrix(graph).__array__())
        self.refidx = deepcopy(self.depidx)
        self.refidx.astype = np.int
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
            for idx in np.nonzero((self.refidx.sum(axis=1)==0).__array__())[0]:
                if idx in self.mapnodesubids:
                    continue
                if self.proc_done[idx] and (not self.proc_pending[idx]):
                    self.refidx[idx,idx] = -1
                    outdir = self.procs[idx]._output_directory()
                    logger.info(('[node dependencies finished] '
                                 'removing node: %s from directory %s') % \
                                (self.procs[idx]._id, outdir))
                    shutil.rmtree(outdir)
