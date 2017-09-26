# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""
from __future__ import print_function, division, unicode_literals, absolute_import

# Import packages
from multiprocessing import Process, Pool, cpu_count, pool
import threading
from traceback import format_exception
import sys

from copy import deepcopy
import numpy as np

from ... import logging, config
from ...utils.misc import str2bool
from ...utils.profiler import get_system_total_memory_gb
from ..engine import MapNode
from .base import (DistributedPluginBase, report_crash)

# Init logger
logger = logging.getLogger('workflow')


# Run node
def run_node(node, updatehash, taskid):
    """Function to execute node.run(), catch and log any errors and
    return the result dictionary

    Parameters
    ----------
    node : nipype Node instance
        the node to run
    updatehash : boolean
        flag for updating hash

    Returns
    -------
    result : dictionary
        dictionary containing the node runtime results and stats
    """

    from nipype import logging
    logger = logging.getLogger('workflow')

    logger.debug('run_node called on %s', node.name)
    # Init variables
    result = dict(result=None, traceback=None, taskid=taskid)

    # Try and execute the node via node.run()
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype, eval, etr)
        result['result'] = node.result

    # Return the result dictionary
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
    """Execute workflow with multiprocessing, not sending more jobs at once
    than the system can support.

    The plugin_args input to run can be used to control the multiprocessing
    execution and defining the maximum amount of memory and threads that
    should be used. When those parameters are not specified,
    the number of threads and memory of the system is used.

    System consuming nodes should be tagged:
    memory_consuming_node.interface.estimated_memory_gb = 8
    thread_consuming_node.interface.num_threads = 16

    The default number of threads and memory for a node is 1.

    Currently supported options are:

    - non_daemon : boolean flag to execute as non-daemon processes
    - n_procs: maximum number of threads to be executed in parallel
    - memory_gb: maximum memory (in GB) that can be used at once.

    """

    def __init__(self, plugin_args=None):
        # Init variables and instance attributes
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._task_obj = {}
        self._taskid = 0
        self._timeout = 2.0
        # self._event = threading.Event()

        # Read in options or set defaults.
        non_daemon = self.plugin_args.get('non_daemon', True)
        self.processors = self.plugin_args.get('n_procs', cpu_count())
        self.memory_gb = self.plugin_args.get('memory_gb',  # Allocate 90% of system memory
                                              get_system_total_memory_gb() * 0.9)
        self.raise_insufficient = self.plugin_args.get('raise_insufficient', True)

        # Instantiate different thread pools for non-daemon processes
        logger.debug('MultiProcPlugin starting in "%sdaemon" mode (n_procs=%d, mem_gb=%0.2f)',
                     'non' if non_daemon else '', self.processors, self.memory_gb)
        self.pool = (NonDaemonPool(processes=self.processors)
                     if non_daemon else Pool(processes=self.processors))

    # def _wait(self):
    #     if len(self.pending_tasks) > 0:
    #         if self._config['execution']['poll_sleep_duration']:
    #             self._timeout = float(self._config['execution']['poll_sleep_duration'])
    #         sig_received = self._event.wait(self._timeout)
    #         if not sig_received:
    #             logger.debug('MultiProcPlugin timeout before signal received. Deadlock averted??')
    #         self._event.clear()

    def _async_callback(self, args):
        self._taskresult[args['taskid']] = args
        # self._event.set()

    def _get_result(self, taskid):
        return self._taskresult.get(taskid)

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        del self._task_obj[taskid]

    def _submit_job(self, node, updatehash=False):
        self._taskid += 1
        if hasattr(node.inputs, 'terminal_output'):
            if node.inputs.terminal_output == 'stream':
                node.inputs.terminal_output = 'allatonce'

        self._task_obj[self._taskid] = \
            self.pool.apply_async(run_node,
                                  (node, updatehash, self._taskid),
                                  callback=self._async_callback)
        return self._taskid

    def _close(self):
        self.pool.close()
        return True

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        """ Sends jobs to workers when system resources are available.
            Check memory (gb) and cores usage before running jobs.
        """
        executing_now = []

        # Check to see if a job is available
        currently_running_jobids = np.flatnonzero(
            self.proc_pending & (self.depidx.sum(axis=0) == 0).__array__())

        # Check available system resources by summing all threads and memory used
        busy_memory_gb = 0
        busy_processors = 0
        for jobid in currently_running_jobids:
            est_mem_gb = self.procs[jobid]._interface.estimated_memory_gb
            est_num_th = self.procs[jobid]._interface.num_threads

            if est_mem_gb > self.memory_gb:
                logger.warning(
                    'Job %s - Estimated memory (%0.2fGB) exceeds the total amount'
                    ' available (%0.2fGB).', self.procs[jobid].name, est_mem_gb, self.memory_gb)
                if self.raise_insufficient:
                    raise RuntimeError('Insufficient resources available for job')

            if est_num_th > self.processors:
                logger.warning(
                    'Job %s - Requested %d threads, but only %d are available.',
                    self.procs[jobid].name, est_num_th, self.processors)
                if self.raise_insufficient:
                    raise RuntimeError('Insufficient resources available for job')

            busy_memory_gb += min(est_mem_gb, self.memory_gb)
            busy_processors += min(est_num_th, self.processors)

        free_memory_gb = self.memory_gb - busy_memory_gb
        free_processors = self.processors - busy_processors

        # Check all jobs without dependency not run
        jobids = np.flatnonzero((self.proc_done == False) &
                                (self.depidx.sum(axis=0) == 0).__array__())

        # Sort jobs ready to run first by memory and then by number of threads
        # The most resource consuming jobs run first
        jobids = sorted(jobids,
                        key=lambda item: (self.procs[item]._interface.estimated_memory_gb,
                                          self.procs[item]._interface.num_threads))

        resource_monitor = str2bool(config.get('execution', 'resource_monitor', 'false'))
        if resource_monitor:
            logger.debug('Free memory (GB): %d, Free processors: %d',
                         free_memory_gb, free_processors)

        # While have enough memory and processors for first job
        # Submit first job on the list
        for jobid in jobids:
            if resource_monitor:
                logger.debug('Next Job: %d, memory (GB): %d, threads: %d' \
                             % (jobid,
                                self.procs[jobid]._interface.estimated_memory_gb,
                                self.procs[jobid]._interface.num_threads))

            if self.procs[jobid]._interface.estimated_memory_gb <= free_memory_gb and \
               self.procs[jobid]._interface.num_threads <= free_processors:
                logger.info('Executing: %s ID: %d' %(self.procs[jobid]._id, jobid))
                executing_now.append(self.procs[jobid])

                if isinstance(self.procs[jobid], MapNode):
                    try:
                        num_subnodes = self.procs[jobid].num_subnodes()
                    except Exception:
                        etype, eval, etr = sys.exc_info()
                        traceback = format_exception(etype, eval, etr)
                        report_crash(self.procs[jobid], traceback=traceback)
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

                free_memory_gb -= self.procs[jobid]._interface.estimated_memory_gb
                free_processors -= self.procs[jobid]._interface.num_threads

                # Send job to task manager and add to pending tasks
                if self._status_callback:
                    self._status_callback(self.procs[jobid], 'start')
                if str2bool(self.procs[jobid].config['execution']['local_hash_check']):
                    logger.debug('checking hash locally')
                    try:
                        hash_exists, _, _, _ = self.procs[
                            jobid].hash_exists()
                        logger.debug('Hash exists %s' % str(hash_exists))
                        if hash_exists and not self.procs[jobid].overwrite and \
                           not self.procs[jobid]._interface.always_run:
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                            continue
                    except Exception:
                        etype, eval, etr = sys.exc_info()
                        traceback = format_exception(etype, eval, etr)
                        report_crash(self.procs[jobid], traceback=traceback)
                        self._clean_queue(jobid, graph)
                        self.proc_pending[jobid] = False
                        continue
                logger.debug('Finished checking hash')

                if self.procs[jobid].run_without_submitting:
                    logger.debug('Running node %s on master thread',
                                 self.procs[jobid])
                    try:
                        self.procs[jobid].run()
                    except Exception:
                        etype, eval, etr = sys.exc_info()
                        traceback = format_exception(etype, eval, etr)
                        report_crash(self.procs[jobid], traceback=traceback)
                    self._task_finished_cb(jobid)
                    self._remove_node_dirs()

                else:
                    logger.debug('MultiProcPlugin submitting %s', str(jobid))
                    tid = self._submit_job(deepcopy(self.procs[jobid]),
                                           updatehash=updatehash)
                    if tid is None:
                        self.proc_done[jobid] = False
                        self.proc_pending[jobid] = False
                    else:
                        self.pending_tasks.insert(0, (tid, jobid))
            else:
                break
