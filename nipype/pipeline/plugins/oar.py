# -*- coding: utf-8 -*-
"""Parallel workflow execution via OAR http://oar.imag.fr
"""
import os
import stat
from time import sleep
import subprocess
import simplejson as json

from ... import logging
from ...interfaces.base import CommandLine
from .base import SGELikeBatchManagerBase, logger

iflogger = logging.getLogger("nipype.interface")


class OARPlugin(SGELikeBatchManagerBase):
    """Execute using OAR

    The plugin_args input to run can be used to control the OAR execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - oarsub_args : arguments to be prepended to the job execution
                    script in the oarsub call
    - max_jobname_len: maximum length of the job name.  Default 15.

    """

    # Addtional class variables
    _max_jobname_len = 15
    _oarsub_args = ""

    def __init__(self, **kwargs):
        template = """
# oarsub -J
        """
        self._retry_timeout = 2
        self._max_tries = 2
        self._max_jobname_length = 15
        if "plugin_args" in kwargs and kwargs["plugin_args"]:
            if "oarsub_args" in kwargs["plugin_args"]:
                self._oarsub_args = kwargs["plugin_args"]["oarsub_args"]
            if "retry_timeout" in kwargs["plugin_args"]:
                self._retry_timeout = kwargs["plugin_args"]["retry_timeout"]
            if "max_tries" in kwargs["plugin_args"]:
                self._max_tries = kwargs["plugin_args"]["max_tries"]
            if "max_jobname_len" in kwargs["plugin_args"]:
                self._max_jobname_len = kwargs["plugin_args"]["max_jobname_len"]
        super(OARPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        #  subprocess.Popen requires taskid to be a string
        proc = subprocess.Popen(
            ["oarstat", "-J", "-s", "-j", taskid],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        o, e = proc.communicate()
        parsed_result = json.loads(o)[taskid].lower()
        is_pending = ("error" not in parsed_result) and (
            "terminated" not in parsed_result
        )
        return is_pending

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine(
            "oarsub",
            environ=dict(os.environ),
            resource_monitor=False,
            terminal_output="allatonce",
        )
        path = os.path.dirname(scriptfile)
        oarsubargs = ""
        if self._oarsub_args:
            oarsubargs = self._oarsub_args
        if "oarsub_args" in node.plugin_args:
            if "overwrite" in node.plugin_args and node.plugin_args["overwrite"]:
                oarsubargs = node.plugin_args["oarsub_args"]
            else:
                oarsubargs += " " + node.plugin_args["oarsub_args"]

        if node._hierarchy:
            jobname = ".".join((dict(os.environ)["LOGNAME"], node._hierarchy, node._id))
        else:
            jobname = ".".join((dict(os.environ)["LOGNAME"], node._id))
        jobnameitems = jobname.split(".")
        jobnameitems.reverse()
        jobname = ".".join(jobnameitems)
        jobname = jobname[0 : self._max_jobname_len]

        if "-O" not in oarsubargs:
            oarsubargs = "%s -O %s" % (
                oarsubargs,
                os.path.join(path, jobname + ".stdout"),
            )
        if "-E" not in oarsubargs:
            oarsubargs = "%s -E %s" % (
                oarsubargs,
                os.path.join(path, jobname + ".stderr"),
            )
        if "-J" not in oarsubargs:
            oarsubargs = "%s -J" % (oarsubargs)

        os.chmod(scriptfile, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
        cmd.inputs.args = "%s -n %s -S %s" % (oarsubargs, jobname, scriptfile)

        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName("CRITICAL"))
        tries = 0
        while True:
            try:
                result = cmd.run()
            except Exception as e:
                if tries < self._max_tries:
                    tries += 1
                    sleep(self._retry_timeout)
                    # sleep 2 seconds and try again.
                else:
                    iflogger.setLevel(oldlevel)
                    raise RuntimeError(
                        "\n".join(
                            (
                                ("Could not submit OAR task" " for node %s") % node._id,
                                str(e),
                            )
                        )
                    )
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve OAR taskid

        o = ""
        add = False
        for line in result.runtime.stdout.splitlines():
            if line.strip().startswith("{"):
                add = True
            if add:
                o += line + "\n"
            if line.strip().startswith("}"):
                break
        taskid = json.loads(o)["job_id"]
        self._pending[taskid] = node.output_dir()
        logger.debug("submitted OAR task: %s for node %s" % (taskid, node._id))
        return taskid
