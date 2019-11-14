# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via IPython controller
"""
from pickle import dumps

import sys
from .base import DistributedPluginBase, logger, report_crash

IPython_not_loaded = False
try:
    from IPython import __version__ as IPyversion
    from ipyparallel.error import TimeoutError
except:
    IPython_not_loaded = True


def execute_task(pckld_task, node_config, updatehash):
    from socket import gethostname
    from traceback import format_exc
    from nipype import config, logging

    traceback = None
    result = None
    import os

    cwd = os.getcwd()
    try:
        config.update_config(node_config)
        logging.update_logging(config)
        from pickle import loads

        task = loads(pckld_task)
        result = task.run(updatehash=updatehash)
    except:
        traceback = format_exc()
        from pickle import loads

        task = loads(pckld_task)
        result = task.result
    os.chdir(cwd)
    return result, traceback, gethostname()


class IPythonPlugin(DistributedPluginBase):
    """Execute workflow with ipython
    """

    def __init__(self, plugin_args=None):
        if IPython_not_loaded:
            raise ImportError("Please install ipyparallel to use this plugin.")
        super(IPythonPlugin, self).__init__(plugin_args=plugin_args)
        valid_args = (
            "url_file",
            "profile",
            "cluster_id",
            "context",
            "debug",
            "timeout",
            "config",
            "username",
            "sshserver",
            "sshkey",
            "password",
            "paramiko",
        )
        self.client_args = {
            arg: plugin_args[arg] for arg in valid_args if arg in plugin_args
        }
        self.iparallel = None
        self.taskclient = None
        self.taskmap = {}
        self._taskid = 0

    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline is distributed approaches
        based on IPython's ipyparallel processing interface
        """
        # retrieve clients again
        try:
            name = "ipyparallel"
            __import__(name)
            self.iparallel = sys.modules[name]
        except ImportError as e:
            raise ImportError(
                "ipyparallel not found. Parallel execution " "will be unavailable"
            ) from e
        try:
            self.taskclient = self.iparallel.Client(**self.client_args)
        except Exception as e:
            if isinstance(e, TimeoutError):
                raise Exception("No IPython clients found.") from e
            if isinstance(e, IOError):
                raise Exception("ipcluster/ipcontroller has not been started") from e
            if isinstance(e, ValueError):
                raise Exception("Ipython kernel not installed") from e
            else:
                raise e
        return super(IPythonPlugin, self).run(graph, config, updatehash=updatehash)

    def _get_result(self, taskid):
        if taskid not in self.taskmap:
            raise ValueError("Task %d not in pending list" % taskid)
        if self.taskmap[taskid].ready():
            result, traceback, hostname = self.taskmap[taskid].get()
            result_out = dict(result=None, traceback=None)
            result_out["result"] = result
            result_out["traceback"] = traceback
            result_out["hostname"] = hostname
            return result_out
        else:
            return None

    def _submit_job(self, node, updatehash=False):
        pckld_node = dumps(node, 2)
        result_object = self.taskclient.load_balanced_view().apply(
            execute_task, pckld_node, node.config, updatehash
        )
        self._taskid += 1
        self.taskmap[self._taskid] = result_object
        return self._taskid

    def _report_crash(self, node, result=None):
        if result and result["traceback"]:
            node._result = result["result"]
            node._traceback = result["traceback"]
            return report_crash(node, traceback=result["traceback"])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        if IPyversion >= "0.11":
            logger.debug("Clearing id: %d" % taskid)
            self.taskclient.purge_results(self.taskmap[taskid])
            del self.taskmap[taskid]
