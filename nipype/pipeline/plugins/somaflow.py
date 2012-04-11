"""Parallel workflow execution via PBS/Torque
"""

import os
import sys

from soma.workflow.client import Job, Workflow, WorkflowController, Helper

from .base import (GraphPluginBase, logger)

class SomaFlowPlugin(GraphPluginBase):
    """Execute using Soma workflow
    """

    def _submit_graph(self, pyfiles, dependencies):
        jobs = []
        soma_deps = []
        for idx, fname in enumerate(pyfiles):
            name = os.path.splitext(os.path.split(fname)[1])[0]
            jobs.append(Job(command=[sys.executable,
                                     fname],
                            name=name))
        for key, values in dependencies.items():
            for val in values:
                soma_deps.append((jobs[val], jobs[key]))

        wf = Workflow(jobs, soma_deps)
        logger.info('serializing workflow')
        Helper.serialize('workflow', wf)
        controller = WorkflowController()
        logger.info('submitting workflow')
        controller.submit_workflow(wf)
