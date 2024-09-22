"""Parallel workflow execution via SGE
"""

import os
import sys

from ...interfaces.base import CommandLine
from .base import GraphPluginBase, logger


def node_completed_status(checknode):
    """
    A function to determine if a node has previously completed it's work
    :param checknode: The node to check the run status
    :return: boolean value True indicates that the node does not need to be run.
    """
    """ TODO: place this in the base.py file and refactor """
    node_state_does_not_require_overwrite = checknode.overwrite is False or (
        checknode.overwrite is None and not checknode._interface.always_run
    )
    hash_exists = False
    try:
        hash_exists, _, _, _ = checknode.hash_exists()
    except Exception:
        hash_exists = False
    return hash_exists and node_state_does_not_require_overwrite


class SGEGraphPlugin(GraphPluginBase):
    """Execute using SGE

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    _template = """
#!/bin/bash
#$ -V
#$ -S /bin/bash
"""

    def __init__(self, **kwargs):
        self._qsub_args = ""
        self._dont_resubmit_completed_jobs = False
        if kwargs.get("plugin_args"):
            plugin_args = kwargs["plugin_args"]
            if "template" in plugin_args:
                self._template = plugin_args["template"]
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if "qsub_args" in plugin_args:
                self._qsub_args = plugin_args["qsub_args"]
            if "dont_resubmit_completed_jobs" in plugin_args:
                self._dont_resubmit_completed_jobs = plugin_args[
                    "dont_resubmit_completed_jobs"
                ]
        super().__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies, nodes):
        def make_job_name(jobnumber, nodeslist):
            """
            - jobnumber: The index number of the job to create
            - nodeslist: The name of the node being processed
            - return: A string representing this job to be displayed by SGE
            """
            job_name = f"j{jobnumber}_{nodeslist[jobnumber]._id}"
            # Condition job_name to be a valid bash identifier (i.e. - is invalid)
            job_name = job_name.replace("-", "_").replace(".", "_").replace(":", "_")
            return job_name

        batch_dir, _ = os.path.split(pyfiles[0])
        submitjobsfile = os.path.join(batch_dir, "submit_jobs.sh")

        cache_doneness_per_node = dict()
        if (
            self._dont_resubmit_completed_jobs
        ):  # A future parameter for controlling this behavior could be added here
            for idx, pyscript in enumerate(pyfiles):
                node = nodes[idx]
                node_status_done = node_completed_status(node)

                # if the node itself claims done, then check to ensure all
                # dependencies are also done
                if node_status_done and idx in dependencies:
                    for child_idx in dependencies[idx]:
                        if child_idx in cache_doneness_per_node:
                            child_status_done = cache_doneness_per_node[child_idx]
                        else:
                            child_status_done = node_completed_status(nodes[child_idx])
                        node_status_done = node_status_done and child_status_done

                cache_doneness_per_node[idx] = node_status_done

        with open(submitjobsfile, "w") as fp:
            fp.writelines("#!/usr/bin/env bash\n")
            fp.writelines("# Condense format attempted\n")
            for idx, pyscript in enumerate(pyfiles):
                node = nodes[idx]
                if cache_doneness_per_node.get(idx, False):
                    continue
                else:
                    template, qsub_args = self._get_args(
                        node, ["template", "qsub_args"]
                    )

                    batch_dir, name = os.path.split(pyscript)
                    name = ".".join(name.split(".")[:-1])
                    batchscript = "\n".join((template, f"{sys.executable} {pyscript}"))
                    batchscriptfile = os.path.join(
                        batch_dir, "batchscript_%s.sh" % name
                    )

                    batchscriptoutfile = batchscriptfile + ".o"
                    batchscripterrfile = batchscriptfile + ".e"

                    with open(batchscriptfile, "w") as batchfp:
                        batchfp.writelines(batchscript)
                        batchfp.close()
                    deps = ""
                    if idx in dependencies:
                        values = " "
                        for jobid in dependencies[idx]:
                            # Avoid dependencies of done jobs
                            if (
                                not self._dont_resubmit_completed_jobs
                                or not cache_doneness_per_node[jobid]
                            ):
                                values += f"${{{make_job_name(jobid, nodes)}}},"
                        if (
                            values != " "
                        ):  # i.e. if some jobs were added to dependency list
                            values = values.rstrip(",")
                            deps = "-hold_jid%s" % values
                    jobname = make_job_name(idx, nodes)
                    # Do not use default output locations if they are set in self._qsub_args
                    stderrFile = ""
                    if self._qsub_args.count("-e ") == 0:
                        stderrFile = f"-e {batchscripterrfile}"
                    stdoutFile = ""
                    if self._qsub_args.count("-o ") == 0:
                        stdoutFile = f"-o {batchscriptoutfile}"
                    full_line = "{jobNm}=$(qsub {outFileOption} {errFileOption} {extraQSubArgs} {dependantIndex} -N {jobNm} {batchscript} | awk '/^Your job/{{print $3}}')\n".format(
                        jobNm=jobname,
                        outFileOption=stdoutFile,
                        errFileOption=stderrFile,
                        extraQSubArgs=qsub_args,
                        dependantIndex=deps,
                        batchscript=batchscriptfile,
                    )
                    fp.writelines(full_line)
        cmd = CommandLine(
            "bash",
            environ=dict(os.environ),
            resource_monitor=False,
            terminal_output="allatonce",
        )
        cmd.inputs.args = "%s" % submitjobsfile
        cmd.run()
        logger.info("submitted all jobs to queue")
