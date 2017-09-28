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
from traceback import format_exception
import sys

from copy import deepcopy
import numpy as np

from ... import logging, config
from ...utils.misc import str2bool
from ...utils.profiler import get_system_total_memory_gb
from ..engine import MapNode
from .base import DistributedPluginBase

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
        result['traceback'] = format_exception(*sys.exc_info())
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
    """
    Execute workflow with multiprocessing, not sending more jobs at once
    than the system can support.

    The plugin_args input to run can be used to control the multiprocessing
    execution and defining the maximum amount of memory and threads that
    should be used. When those parameters are not specified,
    the number of threads and memory of the system is used.

    System consuming nodes should be tagged::

      memory_consuming_node.mem_gb = 8
      thread_consuming_node.n_procs = 16

    The default number of threads and memory are set at node
    creation, and are 1 and 0.25GB respectively.

    Currently supported options are:

    - non_daemon : boolean flag to execute as non-daemon processes
    - n_procs: maximum number of threads to be executed in parallel
    - memory_gb: maximum memory (in GB) that can be used at once.
    - raise_insufficient: raise error if the requested resources for
        a node over the maximum `n_procs` and/or `memory_gb`.

    """

    def __init__(self, plugin_args=None):
        # Init variables and instance attributes
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._task_obj = {}
        self._taskid = 0
        self._timeout = 2.0

        # Read in options or set defaults.
        non_daemon = self.plugin_args.get('non_daemon', True)
        self.processors = self.plugin_args.get('n_procs', cpu_count())
        self.memory_gb = self.plugin_args.get('memory_gb',  # Allocate 90% of system memory
                                              get_system_total_memory_gb() * 0.9)
        self.raise_insufficient = self.plugin_args.get('raise_insufficient', True)

        # Instantiate different thread pools for non-daemon processes
        logger.debug('MultiProcPlugin starting in "%sdaemon" mode (n_procs=%d, mem_gb=%0.2f)',
                     'non' if non_daemon else '', self.processors, self.memory_gb)
        self.pool = (NonDaemonPool if non_daemon else Pool)(processes=self.processors)

    def _async_callback(self, args):
        self._taskresult[args['taskid']] = args

    def _get_result(self, taskid):
        return self._taskresult.get(taskid)

    def _clear_task(self, taskid):
        del self._task_obj[taskid]

    def _submit_job(self, node, updatehash=False):
        self._taskid += 1
        if getattr(node.inputs, 'terminal_output', '') == 'stream':
            node.inputs.terminal_output = 'allatonce'

        self._task_obj[self._taskid] = self.pool.apply_async(
            run_node, (node, updatehash, self._taskid),
            callback=self._async_callback)
        return self._taskid

    def _close(self):
        self.pool.close()
        return True

    def _prerun_check(self, graph):
        tasks_mem_gb = []
        tasks_num_th = []
        for node in graph.nodes():
            tasks_mem_gb.append(node.get_mem_gb())
            tasks_num_th.append(node.get_n_procs())

        if np.any(np.array(tasks_mem_gb) > self.memory_gb):
            logger.warning(
                'Some nodes exceed the total amount of memory available '
                '(%0.2fGB).', self.memory_gb)
            if self.raise_insufficient:
                raise RuntimeError('Insufficient resources available for job')

        if np.any(np.array(tasks_num_th) > self.processors):
            logger.warning(
                'Some nodes demand for more threads than available (%d).',
                self.processors)
            if self.raise_insufficient:
                raise RuntimeError('Insufficient resources available for job')

    def _check_resources(self, running_tasks):
        """
        Make sure there are resources available
        """
        free_memory_gb = self.memory_gb
        free_processors = self.processors
        for _, jobid in running_tasks:
            free_memory_gb -= min(self.procs[jobid].get_mem_gb(), self.memory_gb)
            free_processors -= min(self.procs[jobid].get_n_procs(), self.processors)

        return free_memory_gb, free_processors

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        """
        Sends jobs to workers when system resources are available.
        """

        # Check all jobs without dependency not run
        jobids = np.flatnonzero(
            ~self.proc_done & (self.depidx.sum(axis=0) == 0).__array__())

        # Check available system resources by summing all threads and memory used
        free_memory_gb, free_processors = self._check_resources(self.pending_tasks)

        logger.info('Currently running %d tasks, and %d jobs ready. '
                     'Free memory (GB): %0.2f/%0.2f, Free processors: %d/%d',
                     len(self.pending_tasks), len(jobids),
                     free_memory_gb, self.memory_gb, free_processors, self.processors)


        if (len(jobids) + len(self.pending_tasks)) == 0:
            logger.debug('No tasks are being run, and no jobs can '
                         'be submitted to the queue. Potential deadlock')
            return

        # Sort jobs ready to run first by memory and then by number of threads
        # The most resource consuming jobs run first
        # jobids = sorted(jobids,
        #                 key=lambda item: (self.procs[item]._get_mem_gb(),
        #                                   self.procs[item]._get_n_procs()))

        # While have enough memory and processors for first job
        # Submit first job on the list
        for jobid in jobids:
            # First expand mapnodes
            if isinstance(self.procs[jobid], MapNode):
                try:
                    num_subnodes = self.procs[jobid].num_subnodes()
                except Exception:
                    traceback = format_exception(*sys.exc_info())
                    self._report_crash(self.procs[jobid], traceback=traceback)
                    self._clean_queue(jobid, graph)
                    self.proc_pending[jobid] = False
                    continue
                if num_subnodes > 1:
                    submit = self._submit_mapnode(jobid)
                    if not submit:
                        continue

            # Check requirements of this job
            next_job_gb = min(self.procs[jobid].get_mem_gb(), self.memory_gb)
            next_job_th = min(self.procs[jobid].get_n_procs(), self.processors)

            # If node does not fit, skip at this moment
            if next_job_th > free_processors or next_job_gb > free_memory_gb:
                logger.debug('Cannot allocate job %d (%0.2fGB, %d threads).',
                             jobid, next_job_gb, next_job_th)
                continue

            free_memory_gb -= next_job_gb
            free_processors -= next_job_th
            logger.info('Allocating %s ID=%d (%0.2fGB, %d threads). Free: %0.2fGB, %d threads.',
                        self.procs[jobid]._id, jobid, next_job_gb, next_job_th,
                        free_memory_gb, free_processors)

            # change job status in appropriate queues
            self.proc_done[jobid] = True
            self.proc_pending[jobid] = True

            if str2bool(self.procs[jobid].config['execution']['local_hash_check']):
                logger.debug('checking hash locally')
                try:
                    hash_exists, _, _, _ = self.procs[jobid].hash_exists()
                    overwrite = self.procs[jobid].overwrite
                    always_run = self.procs[jobid]._interface.always_run
                    if (hash_exists and (overwrite is False or
                                         (overwrite is None and not always_run))):
                        logger.debug('Skipping cached node %s with ID %s.',
                                     self.procs[jobid]._id, jobid)
                        self._task_finished_cb(jobid)
                        self._remove_node_dirs()
                        continue
                except Exception:
                    traceback = format_exception(*sys.exc_info())
                    self._report_crash(self.procs[jobid], traceback=traceback)
                    self._clean_queue(jobid, graph)
                    self.proc_pending[jobid] = False
                    continue
                finally:
                    logger.debug('Finished checking hash')

            if self.procs[jobid].run_without_submitting:
                logger.debug('Running node %s on master thread',
                             self.procs[jobid])
                try:
                    self.procs[jobid].run()
                except Exception:
                    traceback = format_exception(*sys.exc_info())
                    self._report_crash(self.procs[jobid], traceback=traceback)

                # Release resources
                self._task_finished_cb(jobid)
                self._remove_node_dirs()
                free_memory_gb += next_job_gb
                free_processors += next_job_th
                continue

            # Task should be submitted to workers
            # Send job to task manager and add to pending tasks
            logger.debug('MultiProc submitting job ID %d', jobid)
            if self._status_callback:
                self._status_callback(self.procs[jobid], 'start')
            tid = self._submit_job(deepcopy(self.procs[jobid]),
                                   updatehash=updatehash)
            if tid is None:
                self.proc_done[jobid] = False
                self.proc_pending[jobid] = False
            else:
                self.pending_tasks.insert(0, (tid, jobid))
