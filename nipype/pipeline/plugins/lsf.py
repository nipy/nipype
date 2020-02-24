# -*- coding: utf-8 -*-
"""Parallel workflow execution via LSF
"""

import os
import re
from time import sleep

from ... import logging
from ...interfaces.base import CommandLine
from .base import SGELikeBatchManagerBase, logger

iflogger = logging.getLogger("nipype.interface")


class LSFPlugin(SGELikeBatchManagerBase):
    """Execute using LSF Cluster Submission

    The plugin_args input to run can be used to control the LSF execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - bsub_args : arguments to be prepended to the job execution script in the
                  bsub call

    """

    def __init__(self, **kwargs):
        template = """
#$ -S /bin/sh
        """
        self._retry_timeout = 2
        self._max_tries = 2
        self._bsub_args = ""
        if "plugin_args" in kwargs and kwargs["plugin_args"]:
            if "retry_timeout" in kwargs["plugin_args"]:
                self._retry_timeout = kwargs["plugin_args"]["retry_timeout"]
            if "max_tries" in kwargs["plugin_args"]:
                self._max_tries = kwargs["plugin_args"]["max_tries"]
            if "bsub_args" in kwargs["plugin_args"]:
                self._bsub_args = kwargs["plugin_args"]["bsub_args"]
        super(LSFPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        """LSF lists a status of 'PEND' when a job has been submitted but is
        waiting to be picked up, and 'RUN' when it is actively being processed.
        But _is_pending should return True until a job has finished and is
        ready to be checked for completeness. So return True if status is
        either 'PEND' or 'RUN'"""
        cmd = CommandLine("bjobs", resource_monitor=False, terminal_output="allatonce")
        cmd.inputs.args = "%d" % taskid
        # check lsf task
        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName("CRITICAL"))
        result = cmd.run(ignore_exception=True)
        iflogger.setLevel(oldlevel)
        # logger.debug(result.runtime.stdout)
        if "DONE" in result.runtime.stdout or "EXIT" in result.runtime.stdout:
            return False
        else:
            return True

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine(
            "bsub",
            environ=dict(os.environ),
            resource_monitor=False,
            terminal_output="allatonce",
        )
        bsubargs = ""
        if self._bsub_args:
            bsubargs = self._bsub_args
        if "bsub_args" in node.plugin_args:
            if "overwrite" in node.plugin_args and node.plugin_args["overwrite"]:
                bsubargs = node.plugin_args["bsub_args"]
            else:
                bsubargs += " " + node.plugin_args["bsub_args"]
        if "-o" not in bsubargs:  # -o outfile
            bsubargs = "%s -o %s" % (bsubargs, scriptfile + ".log")
        if "-e" not in bsubargs:
            # -e error file
            bsubargs = "%s -e %s" % (bsubargs, scriptfile + ".log")
        if node._hierarchy:
            jobname = ".".join((dict(os.environ)["LOGNAME"], node._hierarchy, node._id))
        else:
            jobname = ".".join((dict(os.environ)["LOGNAME"], node._id))
        jobnameitems = jobname.split(".")
        jobnameitems.reverse()
        jobname = ".".join(jobnameitems)
        cmd.inputs.args = "%s -J %s sh %s" % (
            bsubargs,
            jobname,
            scriptfile,
        )  # -J job_name_spec
        logger.debug("bsub " + cmd.inputs.args)
        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName("CRITICAL"))
        tries = 0
        while True:
            try:
                result = cmd.run()
            except Exception as e:
                if tries < self._max_tries:
                    tries += 1
                    sleep(self._retry_timeout)  # sleep 2 seconds and try again.
                else:
                    iflogger.setLevel(oldlevel)
                    raise RuntimeError(
                        "\n".join(
                            (
                                ("Could not submit lsf task" " for node %s") % node._id,
                                str(e),
                            )
                        )
                    )
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve lsf taskid
        match = re.search(r"<(\d*)>", result.runtime.stdout)
        if match:
            taskid = int(match.groups()[0])
        else:
            raise IOError(
                "Can't parse submission job output id: %s" % result.runtime.stdout
            )
        self._pending[taskid] = node.output_dir()
        logger.debug("submitted lsf task: %d for node %s" % (taskid, node._id))
        return taskid
