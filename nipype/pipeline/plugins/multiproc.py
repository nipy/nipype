# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""

from multiprocessing import Process, Pool, cpu_count, pool
from copy import deepcopy
from traceback import format_exception
import sys
import signal
import time
import os.path as op
from .base import (DistributedPluginBase, report_crash)
from ..engine import (MapNode, str2bool)
import numpy as np
from ... import logging
logger = logging.getLogger('workflow')


def run_node(node, updatehash):
    result = dict(result=None, traceback=None)
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype, eval, etr)
        result['result'] = node.result
    return result


class NonDaemonProcess(Process):
    """A non-daemon process to support internal multiprocessing.
    """
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)


class NonDaemonPool(pool.Pool):
    """A process pool with non-daemon processes.
    """
    Process = NonDaemonProcess


class MultiProcPlugin(DistributedPluginBase):
    """
    Execute workflow with multiprocessing

    The plugin_args input to run can be used to control the multiprocessing
    execution. Currently supported options are:

    - n_procs : number of processes to use
    - non_daemon : boolean flag to execute as non-daemon processes

    """

    def _init_worker(self):
        """
        Ignore interrupt signal, handle in main thread
        https://noswap.com/blog/python-multiprocessing-keyboardinterrupt
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def __init__(self, plugin_args=None):
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._taskid = 0
        self._non_daemon = True
        self._n_procs = cpu_count()

        self._maxtasks = None
        if plugin_args:
            if 'n_procs' in plugin_args:
                self._n_procs = plugin_args['n_procs']
            if 'non_daemon' in plugin_args:
                self._non_daemon = plugin_args['non_daemon']
            if 'maxtasksperchild' in plugin_args:
                self._maxtasks = plugin_args['maxtasksperchild']
        self._start_pool()

    def _start_pool(self):
        logger.info('Starting %s pool' % 'non-daemon'
                    if self._non_daemon else 'daemon')
        # set maxtasksperchild 5 to refresh workers with that frequency
        if self._non_daemon:
            # run the execution using the non-daemon pool subclass
            self.pool = NonDaemonPool(processes=self._n_procs,
                                      maxtasksperchild=self._maxtasks,
                                      initializer=self._init_worker)
        else:
            self.pool = Pool(processes=self._n_procs,
                             maxtasksperchild=self._maxtasks,
                             initializer=self._init_worker)

    def _wait_pool(self):
        self.pool.close()
        self.pool.join()

    def _get_result(self, taskid):
        if taskid not in self._taskresult:
            raise RuntimeError('Multiproc task %d not found' % taskid)
        if not self._taskresult[taskid].ready():
            return None
        return self._taskresult[taskid].get()

    def _submit_job(self, node, updatehash=False):
        self._taskid += 1
        try:
            if node.inputs.terminal_output == 'stream':
                node.inputs.terminal_output = 'allatonce'
        except:
            pass

        self._taskresult[self._taskid] = self.pool.apply_async(
            run_node, (node, updatehash,))
        return self._taskid

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        del self._taskresult[taskid]

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        """ Sends jobs to workers
        """
        while not np.all(self.proc_done):
            num_jobs = len(self.pending_tasks)
            if np.isinf(self.max_jobs):
                slots = None
            else:
                slots = max(0, self.max_jobs - num_jobs)
            logger.debug('Slots available: %s' % slots)
            if (num_jobs >= self.max_jobs) or (slots == 0):
                break
            # Check to see if a job is available
            jobids = np.flatnonzero((self.proc_done == False) &
                                    (self.depidx.sum(axis=0) == 0).__array__())
            if len(jobids) > 0:
                # send all available jobs
                logger.info('Submitting %d jobs' % len(jobids[:slots]))
                for jobid in jobids[:slots]:
                    if isinstance(self.procs[jobid], MapNode):
                        try:
                            num_subnodes = self.procs[jobid].num_subnodes()
                        except Exception:
                            self._clean_queue(jobid, graph)
                            self.proc_pending[jobid] = False
                            continue
                        if num_subnodes > 1:
                            submit = self._submit_mapnode(jobid)
                            if not submit:
                                continue
                    # change job status in appropriate queues
                    self.proc_done[jobid] = True
                    self.proc_pending[jobid] = True
                    # Send job to task manager and add to pending tasks
                    logger.info('Executing: %s ID: %d' %
                                (self.procs[jobid]._id, jobid))
                    if self._status_callback:
                        self._status_callback(self.procs[jobid], 'start')
                    continue_with_submission = True
                    if str2bool(self.procs[jobid].config['execution']
                                ['local_hash_check']):
                        logger.debug('checking hash locally')
                        try:
                            hash_exists, _, _, _ = self.procs[
                                jobid].hash_exists()
                            logger.debug('Hash exists %s' % str(hash_exists))
                            if (hash_exists and
                                    (self.procs[jobid].overwrite == False or
                                     (self.procs[jobid].overwrite == None and
                                              not self.procs[jobid]._interface.always_run)
                                     )
                                    ):
                                continue_with_submission = False
                                self._task_finished_cb(jobid)
                                self._remove_node_dirs()
                        except Exception:
                            self._clean_queue(jobid, graph)
                            self.proc_pending[jobid] = False
                            continue_with_submission = False
                    logger.debug('Finished checking hash %s' %
                                 str(continue_with_submission))
                    if continue_with_submission:
                        sworker = getattr(self.procs[jobid]._interface,
                                          '_singleworker', True)

                        if not sworker:
                            logger.info('Node %s claimed all workers' %
                                        self.procs[jobid])
                            self._wait_pool()
                            logger.info(('All workers clean, running %s on '
                                        'master thread') % self.procs[jobid])
                            try:
                                self.procs[jobid].run()
                            except Exception:
                                self._clean_queue(jobid, graph)
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                            self._start_pool()
                        elif self.procs[jobid].run_without_submitting:
                            logger.debug('Running node %s on master thread' %
                                         self.procs[jobid])
                            try:
                                self.procs[jobid].run()
                            except Exception:
                                self._clean_queue(jobid, graph)
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                        else:
                            tid = self._submit_job(deepcopy(self.procs[jobid]),
                                                   updatehash=updatehash)
                            if tid is None:
                                self.proc_done[jobid] = False
                                self.proc_pending[jobid] = False
                            else:
                                self.pending_tasks.insert(0, (tid, jobid))
            else:
                break
