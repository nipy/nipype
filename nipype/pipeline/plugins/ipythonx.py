# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via IPython controller
"""

import sys

from IPython import __version__ as IPyversion
try:
    from IPython.kernel.contexts import ConnectionRefusedError
except:
    pass

from .base import (DistributedPluginBase, logger, report_crash)

class IPythonXPlugin(DistributedPluginBase):
    """Execute workflow with ipython
    """

    def __init__(self, plugin_args=None):
        super(IPythonXPlugin, self).__init__(plugin_args=plugin_args)
        self.ipyclient = None
        self.taskclient = None

    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's parallel processing interface
        """
        # retrieve clients again
        try:
            name = 'IPython.kernel.client'
            __import__(name)
            self.ipyclient = sys.modules[name]
        except ImportError:
            raise ImportError("Ipython kernel not found. Parallel execution " \
                              "will be unavailable")
        try:
            self.taskclient = self.ipyclient.TaskClient()
        except Exception, e:
            if isinstance(e, ConnectionRefusedError):
                raise Exception("No IPython clients found.")
            if isinstance(e, ValueError):
                raise Exception("Ipython kernel not installed")
        return super(IPythonXPlugin, self).run(graph, config, updatehash=updatehash)

    def _get_result(self, taskid):
        return self.taskclient.get_task_result(taskid, block=False)

    def _submit_job(self, node, updatehash=False):
        cmdstr = """import sys
from traceback import format_exception
traceback=None
result=None
try:
    result = task.run(updatehash=updatehash)
except:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    result = task.result
"""
        task = self.ipyclient.StringTask(cmdstr,
                                         push = dict(task=node,
                                                     updatehash=updatehash),
                                         pull = ['result','traceback'])
        return self.taskclient.run(task, block = False)

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        if IPyversion >= '0.10.1':
            logger.debug("Clearing id: %d"%taskid)
            self.taskclient.clear(taskid)
