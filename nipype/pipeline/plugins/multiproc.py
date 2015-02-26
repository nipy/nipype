# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""

from multiprocessing import (Process, Pool, cpu_count, pool,
                             Manager, TimeoutError)
from copy import deepcopy
from traceback import format_exception
import sys
import signal
from time import sleep
import os.path as op
from .base import (DistributedPluginBase, report_crash, report_nodes_not_run)
from ..engine import (MapNode, str2bool)
import numpy as np
from ... import logging
logger = logging.getLogger('workflow')


def run_node(args):
    jobid = args[0]
    node = args[1]
    updatehash = args[2]

    jres = dict(result=None, traceback=None)
    logger.info('[Starting] Job %d %s' % (jobid, str(node._id)))
    try:
        jres['result'] = node.run(updatehash=updatehash)
        logger.info('[Terminated] Job %d %s' % (jobid, str(node._id)))
    except:
        etype, eval, etr = sys.exc_info()
        jres['traceback'] = format_exception(etype, eval, etr)
        jres['result'] = node.result
        logger.info('[Error] Job %d: %s' % (jobid, jres['traceback']))
    return (jobid, jres)


class NonDaemonProcess(Process):

    """
    A non-daemon process to support internal multiprocessing.
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

    def _start_pool(self):
        """
        Start a new pool with default parameters. Try-except is aimed
        to retry when using python <2.7 (pool can't be initialized with
        maxtasksperchild)
        """
        try:
            # run the execution using the appropriate pool subclass
            self.pool = NonDaemonPool(**self._poolcfg) \
                if self._non_daemon else Pool(**self.poolcfg)
            logger.info('Started new %s pool with %d processes' %
                        ('non-daemon' if self._non_daemon else 'daemon',
                         self._poolcfg['processes']))
        except TypeError:
            del self._poolcfg['maxtasksperchild']
            self._start_pool()

    def __init__(self, plugin_args=None):
        """
        Uses safe dictionaries from multiprocessing.Manager, see
        http://stackoverflow.com/questions/25071910/multiprocessing-pool-\
calling-helper-functions-when-using-apply-asyncs-callback
        """
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        # m = Manager()
        self._results = {}   # Save results here
        self._notrun = []    # Gather errored nodes here

        # Initialize settings, using dic.get we define defaults
        if plugin_args is None:
            plugin_args = {}

        self._poolcfg = dict(
            processes=plugin_args.get('n_proc', cpu_count()),
            initializer=self._init_worker,
            maxtasksperchild=plugin_args.get('maxtasksperchild', 5))
        self._non_daemon = plugin_args.get('non_daemon', True)
        self._start_pool()
        # self._sem = Semaphore(2 * self._poolcfg['processes'])

    def _submit_jobs(self, jobids, updatehash=False):
        jobids = np.atleast_1d(jobids).tolist()

        logger.info('Submitting %s' % str(jobids))
        jobargs = []
        active = []
        for jobid in jobids:
            if jobid not in self._results.keys():
                node = deepcopy(self.procs[jobid])
                try:
                    if node.inputs.terminal_output == 'stream':
                        node.inputs.terminal_output = 'allatonce'
                except:
                    pass
                active.append(jobid)
                jobargs.append((jobid, node, updatehash,))

        logger.info('Current pool is %s' % str(active))
        cur_batch = self.pool.map(run_node, jobargs)

        processed = []
        notrun = []
        for el in cur_batch:
            jobid = el[0]
            if el[1]['traceback'] is not None:
                notrun.append(jobid)
            else:
                processed.append(jobid)

            self.proc_done[jobid] = True
            self.pending_tasks.remove(jobid)
            self._results[jobid] = el[1]
            self._task_finished_cb(jobid)
            self._remove_node_dirs()

        return (processed, notrun)

    # def _sem_release(self):
    #     self._sem.release()

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _send_procs_to_workers(self, jobids, updatehash=False, graph=None):
        """
        Sends jobs to workers
        """
        jobids = np.atleast_1d(jobids).tolist()
        forkjids = []
        num_jobs = len(jobids)
        if np.isinf(self.max_jobs):
            slots = None
        else:
            slots = max(0, self.max_jobs - num_jobs)

        if num_jobs > 0:
            # send all available jobs
            logger.info('Check %d jobs and submit' % len(jobids[:slots]))
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
                self.proc_pending[jobid] = True
                # Send job to task manager and add to pending tasks
                if self._status_callback:
                    self._status_callback(self.procs[jobid], 'start')
                continue_with_submission = True
                if str2bool(self.procs[jobid].config['execution']
                            ['local_hash_check']):
                    try:
                        logger.info('checking hash locally')
                        hash_exists, _, _, _ = self.procs[
                            jobid].hash_exists()
                        overwrite = getattr(
                            self.procs[jobid], 'overwrite', False)
                        always_run = getattr(
                            self.procs[jobid]._interface, 'always_run', False)

                        # Is cached and run enforced
                        if (hash_exists and not overwrite and not always_run):
                            continue_with_submission = False
                            self.proc_done[jobid] = True
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                            logger.info(('Node %s (%d) is cached or does'
                                         ' not require being run') %
                                        (self.procs[jobid], jobid))
                    except Exception:
                        self._clean_queue(jobid, graph)
                        self.proc_pending[jobid] = False
                        continue_with_submission = False
                        logger.warn(('Node %s (%d) raised exception') %
                                    (self.procs[jobid], jobid))

                if continue_with_submission:
                    self.pending_tasks.insert(0, jobid)
                    sworker = getattr(self.procs[jobid]._interface,
                                      '_singleworker', True)
                    nosubmit = getattr(self.procs[jobid],
                                       'run_without_submitting', False)
                    if sworker and not nosubmit:
                        forkjids.append(jobid)
                    else:
                        self._run_mthread(jobid, updatehash)

        if len(forkjids) > 0:
            p, n = self._submit_jobs(forkjids)

            for jid in n:
                self._notrun.append(self._clean_queue(jid, graph))

    def run(self, graph, config, updatehash=False):
        """
        Executes a pre-defined pipeline using distributed approaches
        """
        try:
            logger.info('Running in parallel.')
            self._config = config
            # Generate appropriate structures for worker-manager model
            self._generate_dependency_list(graph)
            self.pending_tasks = []
            self.readytorun = []
            self.mapnodes = []
            self.mapnodesubids = {}

            it = 0
            while not np.all(self.proc_done):
                # Check to see if there are jobs available
                undone = np.logical_not(self.proc_done).astype(np.uint8)
                jobdeps = (self.depidx.sum(axis=0) == 0).__array__()
                jobids = np.flatnonzero(undone * jobdeps)
                logger.info(('Polling [%02d]: Jobs ready/remaining/total='
                             '%d/%d/%d') % (it, len(jobids), undone.sum(),
                                            len(self.proc_done)))

                if len(jobids) >= self.max_jobs:
                    jobids = jobids[:self.max_jobs]

                if len(jobids) == 0:
                    logger.info('No more ready jobs, exit')
                    break

                self._send_procs_to_workers(jobids, updatehash=updatehash,
                                            graph=graph)
                it += 1

        except KeyboardInterrupt:
            logger.info('User interrupt')
            self._notrun.extend([self._clean_queue(jid, graph) for jid, v in
                                 enumerate(self.proc_done) if not v])
            self.pool.terminate()

        self._remove_node_dirs()
        report_nodes_not_run(self._notrun)

    def _job_callback(self, result):
        jobid = result.keys()[0]
        self._results[jobid] = result[jobid]['result']

    def _get_result(self, jobid):
        return self._results.get(jobid,
                                 {'result': None,
                                  'traceback': 'Result not found',
                                  'jobid': jobid})

    def _run_mthread(self, jobid, updatehash=False):
        """
        Run task in master thread
        """
        logger.info('Running node %s (%d) on master thread' %
                    (self.procs[jobid], jobid))

        try:
            self.procs[jobid].run()
        except Exception:
            self._notrun.append(self._clean_queue(jobid, graph))
        self.pending_tasks.remove(jobid)
        self._task_finished_cb(jobid)
        self._remove_node_dirs()
