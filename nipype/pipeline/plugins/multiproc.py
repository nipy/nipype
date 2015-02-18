# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""

from multiprocessing import Process, Pool, cpu_count, pool
import portalocker as pl
from traceback import format_exception
import sys
import time
import os.path as op

from .base import (DistributedPluginBase, report_crash)

def run_node(node, updatehash):
    result = dict(result=None, traceback=None)
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype,eval,etr)
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
    """Execute workflow with multiprocessing

    The plugin_args input to run can be used to control the multiprocessing
    execution. Currently supported options are:

    - n_procs : number of processes to use
    - non_daemon : boolean flag to execute as non-daemon processes

    """

    def __init__(self, plugin_args=None):
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._taskid = 0
        self._livetasks = 0
        self._lockfile = op.abspath('.MultiProcLock')
        non_daemon = True
        n_procs = cpu_count()
        if plugin_args:
            if 'n_procs' in plugin_args:
                n_procs = plugin_args['n_procs']
            if 'non_daemon' in plugin_args:
                non_daemon = plugin_args['non_daemon']
        if non_daemon:
            # run the execution using the non-daemon pool subclass
            self.pool = NonDaemonPool(processes=n_procs)
        else:
            self.pool = Pool(processes=n_procs)

    def _get_result(self, taskid):
        if taskid not in self._taskresult:
            raise RuntimeError('Multiproc task %d not found'%taskid)
        if not self._taskresult[taskid].ready():
            return None
        self._livetasks -= 1
        return self._taskresult[taskid].get()

    def _submit_job(self, node, updatehash=False):
        allworkers = False
        try:
            allworkers = node._allworkers
        except:
            pass

        if allworkers:
            with pl.Lock(self._lockfile) as f:
                while self._livetasks > 0:
                    print 'Waiting other %d worker(s) to finish' % self._livetasks
                    time.sleep(5)
                return self.run_job(node, updatehash)

        return self.run_job(node, updatehash)

    def _run_job(self, node, updatehash=False):
        self._taskid += 1
        try:
            if node.inputs.terminal_output == 'stream':
                node.inputs.terminal_output = 'allatonce'
        except:
            pass

        self._livetasks += 1
        self._taskresult[self._taskid] = self.pool.apply_async(run_node,
                                                               (node,
                                                                updatehash,))
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
