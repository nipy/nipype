# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via IPython controller
"""

from cPickle import dumps

import sys

IPython_not_loaded = False
try:
    from IPython import __version__ as IPyversion
    from IPython.parallel.error import TimeoutError
except:
    IPython_not_loaded = True

from .base import (DistributedPluginBase, logger, report_crash)

def execute_task(pckld_task, node_config, updatehash):
    from socket import gethostname
    from traceback import format_exc
    from nipype import config, logging
    traceback=None
    result=None
    try:
        config.update_config(node_config)
        logging.update_logging(config)
        from cPickle import loads
        task = loads(pckld_task)
        result = task.run(updatehash=updatehash)
    except:
        traceback = format_exc()
        result = task.result
    return result, traceback, gethostname()

class IPythonPlugin(DistributedPluginBase):
    """Execute workflow with ipython
    """

    def __init__(self, plugin_args=None):
        if IPython_not_loaded:
            raise ImportError('IPython parallel could not be imported')
        super(IPythonPlugin, self).__init__(plugin_args=plugin_args)
        self.iparallel = None
        self.taskclient = None
        self.taskmap = {}
        self._taskid = 0

    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # retrieve clients again
        try:
            name = 'IPython.parallel'
            __import__(name)
            self.iparallel = sys.modules[name]
        except ImportError:
            raise ImportError("Ipython kernel not found. Parallel execution " \
                              "will be unavailable")
        try:
            self.taskclient = self.iparallel.Client()
        except Exception, e:
            if isinstance(e, TimeoutError):
                raise Exception("No IPython clients found.")
            if isinstance(e, ValueError):
                raise Exception("Ipython kernel not installed")
            raise e
        return super(IPythonPlugin, self).run(graph, config, updatehash=updatehash)

    def _get_result(self, taskid):
        if taskid not in self.taskmap:
            raise ValueError('Task %d not in pending list'%taskid)
        if self.taskmap[taskid].ready():
            result, traceback, hostname = self.taskmap[taskid].get()
            result_out = dict(result=None, traceback=None)
            result_out['result'] = result
            result_out['traceback'] = traceback
            result_out['hostname'] = hostname
            return result_out
        else:
            return None

    def _submit_job(self, node, updatehash=False):
        pckld_node = dumps(node, 2)
        result_object = self.taskclient.load_balanced_view().apply(execute_task,
                                                                   pckld_node,
                                                                   node.config,
                                                                   updatehash)
        self._taskid += 1
        self.taskmap[self._taskid] = result_object
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
        if IPyversion >= '0.11':
            logger.debug("Clearing id: %d"%taskid)
            self.taskclient.purge_results(self.taskmap[taskid])
            del self.taskmap[taskid]
