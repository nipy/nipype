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

    jres = dict()
    jres[jobid] = dict(result=None, traceback=None)
    logger.info('[Starting] Job %d' % jobid)
    try:
        jres[jobid]['result'] = node.run(updatehash=updatehash)
        logger.info('[Terminated] Job %d' % jobid)
    except:
        etype, eval, etr = sys.exc_info()
        jres[jobid]['traceback'] = format_exception(etype, eval, etr)
        jres[jobid]['result'] = node.result
        logger.info('[Error] Job %d' % jobid)
    return jres


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
            logger.info('Started new %s pool' % 'non-daemon'
                        if self._non_daemon else 'daemon')
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
        self._active = []    # Save active tasks here (AsyncResult)

        # Initialize settings, using dic.get we define defaults
        if plugin_args is None:
            plugin_args = {}

        self._poolcfg = dict(
            processes=plugin_args.get('n_procs', cpu_count()),
            initializer=self._init_worker,
            maxtasksperchild=plugin_args.get('maxtasksperchild', 5))
        self._non_daemon = plugin_args.get('non_daemon', True)
        self._start_pool()
        # Do not allow the _active queue grow too much
        # self._sem = Semaphore(2 * self._poolcfg['processes'])

    def _submit_jobs(self, jobids, updatehash=False):
        jobids = np.atleast_1d(jobids).tolist()

        jobargs = []
        for jobid in jobids:
            if jobid in self._results.keys():
                logger.info('Job %d is already processed')
            elif jobid in self._active:
                logger.info('Job %d is currently being processed')
            else:
                self._results[jobid] = None
                self.pending_tasks.insert(0, jobid)
                node = deepcopy(self.procs[jobid])
                try:
                    if node.inputs.terminal_output == 'stream':
                        node.inputs.terminal_output = 'allatonce'
                except:
                    pass

                jobargs.append((jobid, node, updatehash,))
                self._active.append(jobid)

        self._results = dict(
            self._results.items() +
            self.pool.map(run_node, jobargs).items())

        logger.info('Submitted job %d %s' % (jobid, node._id))
        logger.info('Current pool is %s' % str(self._active))
        return True

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

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        """
        Sends jobs to workers
        """
        while not np.all(self.proc_done):
            num_jobs = len(self.pending_tasks)
            if np.isinf(self.max_jobs):
                slots = None
            else:
                slots = max(0, self.max_jobs - num_jobs)

            if (num_jobs >= self.max_jobs) or (slots == 0):
                break
            # Check to see if a job is available
            undone = np.logical_not(self.proc_done).astype(np.uint8)
            jobdeps = (self.depidx.sum(axis=0) == 0).__array__()
            jobids = np.flatnonzero(undone * jobdeps)

            logger.info(('Slots available: %s. Jobs avail./undone/total='
                         '%d/%d/%d') % (slots, len(jobids), undone.sum(),
                                        len(self.proc_done)))

            if len(jobids) > 0:
                joblist = []

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
                        logger.info('checking hash locally')
                        try:
                            hash_exists, _, _, _ = self.procs[
                                jobid].hash_exists()
                            overwrite = getattr(self.procs[jobid],
                                                'overwrite', False)
                            always_run = getattr(self.procs[jobid]._interface,
                                                 'always_run', False)
                            logger.info('Hash exists %s' % str(hash_exists))

                            if (hash_exists and not overwrite
                                    and not always_run):
                                continue_with_submission = False
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
                        sworker = getattr(self.procs[jobid]._interface,
                                          '_singleworker', True)
                        nosubmit = getattr(self.procs[jobid],
                                           'run_without_submitting', False)

                        if sworker and not nosubmit:
                            joblist.append(jobid)
                        else:
                            if not sworker:
                                logger.info('Node %s claimed all workers' %
                                            self.procs[jobid])
                                killedjobs = self._wait_pool()
                                logger.info(
                                    ('All workers clean, running %s on '
                                     'master thread') % self.procs[jobid])

                            self._run_mthread(jobid, updatehash)

                            if not sworker:
                                self._start_pool()
                                joblist = list(set(joblist.extend(killedjobs)))

                    self._submit_jobs(joblist)
            else:
                break

    def run(self, graph, config, updatehash=False):
        """
        Executes a pre-defined pipeline using distributed approaches
        """
        logger.info('Running in parallel.')
        self._config = config
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list(graph)
        self.pending_tasks = []
        self.readytorun = []
        self.mapnodes = []
        self.mapnodesubids = {}
        # setup polling - TODO: change to threaded model
        notrun = []
        it = 0
        while (not np.all(self.proc_done) or np.any(self.proc_pending)):
            logger.info(('All processes done: %r. Any process is pending: '
                         '%r.') % (np.all(self.proc_done),
                                   np.any(self.proc_pending)))
            toappend = []
            # trigger callbacks for any pending results
            while self.pending_tasks:
                jobid = self.pending_tasks.pop()
                logger.info('Getting result %d: %s' %
                            (jobid, self.procs[jobid]))
                try:
                    result = self._get_result(jobid)
                except Exception:
                    result = {'traceback': format_exc()}

                if result is None:
                    logger.info('Inserting %d: %s' %
                                (jobid, self.procs[jobid]))
                    toappend.insert(0, jobid)
                else:
                    self._task_finished_cb(jobid)
                    self._remove_node_dirs()

                    if result['traceback'] is not None:
                        notrun.append(self._clean_queue(jobid, graph,
                                                        result=result))
                        logger.info(('Node %d will not be run, '
                                     'reason: %s') % (jobid,
                                                      result['traceback']))

            if toappend:
                self.pending_tasks.extend(toappend)

            num_jobs = len(self.pending_tasks)
            logger.info('Number of pending tasks: %d' % num_jobs)
            if num_jobs < self.max_jobs:
                self._send_procs_to_workers(updatehash=updatehash,
                                            graph=graph)
            else:
                logger.info('Not submitting')

            undone = self.proc_done.astype(np.uint8).sum()
            pending = self.proc_pending.astype(np.uint8).sum()

            logger.info(('Polling processes [%02d]: Undone=%d/%d; '
                         'Pending=%d/%d') % (it,
                                             undone, len(self.proc_done),
                                             pending, len(self.proc_pending)))

            sleep(float(self._config['execution']['poll_sleep_duration']))
            it += 1

        self._remove_node_dirs()
        report_nodes_not_run(notrun)

    def _job_callback(self, result):
        jobid = result.keys()[0]
        self._results[jobid] = result[jobid]['result']
        self._active.remove(jobid)

    def _get_result(self, jobid):
        if jobid in self._active:
            return None

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
            self._clean_queue(jobid, graph)
        self._task_finished_cb(jobid)
        self._remove_node_dirs()

    def _wait_pool(self):
        self.pool.close()
        error = False

        killedjobs = []
        for jobid, task in self._active.iteritems():
            try:
                logger.info('Waiting for job %d' % jobid)
                task.wait()
            except TimeoutError:
                logger.warn(
                    'TimeoutError, killing job %d' % jobid)
                # self._sem.release()
                error = True
                killedjobs.append(jobid)
                del self._active[jobid]

        if error:
            self.pool.terminate()
            logger.info('Pool terminated, killed jobs: %s' %
                        str(killedjobs))

        if len(self._active) > 0:
            logger.warn('Some elements remain active after wait')

        return killedjobs
