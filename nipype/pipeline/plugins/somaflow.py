# -*- coding: utf-8 -*-
"""Parallel workflow execution via PBS/Torque
"""

import os
import sys

from .base import GraphPluginBase, logger

soma_not_loaded = False
try:
    from soma.workflow.client import Job, Workflow, WorkflowController, Helper
except:
    soma_not_loaded = True


class SomaFlowPlugin(GraphPluginBase):
    """Execute using Soma workflow"""

    def __init__(self, plugin_args=None):
        if soma_not_loaded:
            raise ImportError("SomaFlow could not be imported")
        super(SomaFlowPlugin, self).__init__(plugin_args=plugin_args)

    def _submit_graph(self, pyfiles, dependencies, nodes):
        jobs = []
        soma_deps = []
        for idx, fname in enumerate(pyfiles):
            name = os.path.splitext(os.path.split(fname)[1])[0]
            jobs.append(Job(command=[sys.executable, fname], name=name))
        for key, values in list(dependencies.items()):
            for val in values:
                soma_deps.append((jobs[val], jobs[key]))

        wf = Workflow(jobs, soma_deps)
        logger.info("serializing workflow")
        Helper.serialize("workflow", wf)
        controller = WorkflowController()
        logger.info("submitting workflow")
        wf_id = controller.submit_workflow(wf)
        Helper.wait_workflow(wf_id, controller)
