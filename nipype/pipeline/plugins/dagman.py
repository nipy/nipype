# -*- coding: utf-8 -*-
"""Parallel workflow execution via Condor DAGMan
"""
import os
import sys
import uuid
import time
from warnings import warn

from .base import GraphPluginBase, logger
from ...interfaces.base import CommandLine


class CondorDAGManPlugin(GraphPluginBase):
    """Execute using Condor DAGMan

    The plugin_args input to run can be used to control the DAGMan execution.
    The value of most arguments can be a literal string or a filename, where in
    the latter case the content of the file will be used as the argument value.

    Currently supported options are:

    - submit_template : submit spec template for individual jobs in a DAG (see
                 CondorDAGManPlugin.default_submit_template for the default.
    - initial_specs : additional submit specs that are prepended to any job's
                 submit file
    - override_specs : additional submit specs that are appended to any job's
                 submit file
    - wrapper_cmd : path to an executable that will be started instead of a node
                 script. This is useful for wrapper script that execute certain
                 functionality prior or after a node runs. If this option is
                 given the wrapper command is called with the respective Python
                 executable and the path to the node script as final arguments
    - wrapper_args : optional additional arguments to a wrapper command
    - dagman_args : arguments to be prepended to the arguments of the
                    condor_submit_dag call
    - block : if True the plugin call will block until Condor has finished
                 processing the entire workflow (default: False)
    """

    default_submit_template = """
universe = vanilla
notification = Never
executable = %(executable)s
arguments = %(nodescript)s
output = %(basename)s.out
error = %(basename)s.err
log = %(basename)s.log
getenv = True
"""

    def _get_str_or_file(self, arg):
        if os.path.isfile(arg):
            with open(arg) as f:
                content = f.read()
        else:
            content = arg
        return content

    # XXX feature wishlist
    # - infer data file dependencies from jobs
    # - infer CPU requirements from jobs
    # - infer memory requirements from jobs
    # - looks like right now all jobs come in here, regardless of whether they
    #   actually have to run. would be good to be able to decide whether they
    #   actually have to be scheduled (i.e. output already exist).
    def __init__(self, **kwargs):
        for var, id_, val in (
            ("_template", "submit_template", self.default_submit_template),
            ("_initial_specs", "template", ""),
            ("_initial_specs", "initial_specs", ""),
            ("_override_specs", "submit_specs", ""),
            ("_override_specs", "override_specs", ""),
            ("_wrapper_cmd", "wrapper_cmd", None),
            ("_wrapper_args", "wrapper_args", ""),
            ("_block", "block", False),
            ("_dagman_args", "dagman_args", ""),
        ):
            if (
                "plugin_args" in kwargs
                and not kwargs["plugin_args"] is None
                and id_ in kwargs["plugin_args"]
            ):
                if id_ == "wrapper_cmd":
                    val = os.path.abspath(kwargs["plugin_args"][id_])
                elif id_ == "block":
                    val = kwargs["plugin_args"][id_]
                else:
                    val = self._get_str_or_file(kwargs["plugin_args"][id_])
            setattr(self, var, val)
        # TODO remove after some time
        if "plugin_args" in kwargs and not kwargs["plugin_args"] is None:
            plugin_args = kwargs["plugin_args"]
            if "template" in plugin_args:
                warn(
                    "the 'template' argument is deprecated, use 'initial_specs' instead"
                )
            if "submit_specs" in plugin_args:
                warn(
                    "the 'submit_specs' argument is deprecated, use 'override_specs' instead"
                )
        super(CondorDAGManPlugin, self).__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies, nodes):
        # location of all scripts, place dagman output in here too
        batch_dir, _ = os.path.split(pyfiles[0])
        # DAG description filename
        dagfilename = os.path.join(batch_dir, "workflow-%s.dag" % uuid.uuid4())
        with open(dagfilename, "wt") as dagfileptr:
            # loop over all scripts, create submit files, and define them
            # as jobs in the DAG
            for idx, pyscript in enumerate(pyfiles):
                node = nodes[idx]
                # XXX redundant with previous value? or could it change between
                # scripts?
                (
                    template,
                    initial_specs,
                    override_specs,
                    wrapper_cmd,
                    wrapper_args,
                ) = self._get_args(
                    node,
                    [
                        "template",
                        "initial_specs",
                        "override_specs",
                        "wrapper_cmd",
                        "wrapper_args",
                    ],
                )
                # add required slots to the template
                template = "%s\n%s\n%s\nqueue\n" % (
                    "%(initial_specs)s",
                    template,
                    "%(override_specs)s",
                )
                batch_dir, name = os.path.split(pyscript)
                name = ".".join(name.split(".")[:-1])
                specs = dict(
                    # TODO make parameter for this,
                    initial_specs=initial_specs,
                    executable=sys.executable,
                    nodescript=pyscript,
                    basename=os.path.join(batch_dir, name),
                    override_specs=override_specs,
                )
                if wrapper_cmd is not None:
                    specs["executable"] = wrapper_cmd
                    specs["nodescript"] = "%s %s %s" % (
                        wrapper_args % specs,  # give access to variables
                        sys.executable,
                        pyscript,
                    )
                submitspec = template % specs
                # write submit spec for this job
                submitfile = os.path.join(batch_dir, "%s.submit" % name)
                with open(submitfile, "wt") as submitfileprt:
                    submitfileprt.writelines(submitspec)
                    submitfileprt.close()
                # define job in DAG
                dagfileptr.write("JOB %i %s\n" % (idx, submitfile))
            # define dependencies in DAG
            for child in dependencies:
                parents = dependencies[child]
                if len(parents):
                    dagfileptr.write(
                        "PARENT %s CHILD %i\n"
                        % (" ".join([str(i) for i in parents]), child)
                    )
        # hand over DAG to condor_dagman
        cmd = CommandLine(
            "condor_submit_dag",
            environ=dict(os.environ),
            resource_monitor=False,
            terminal_output="allatonce",
        )
        # needs -update_submit or re-running a workflow will fail
        cmd.inputs.args = "%s -update_submit %s" % (self._dagman_args, dagfilename)
        cmd.run()
        logger.info("submitted all jobs to Condor DAGMan")
        if self._block:
            # wait for DAGMan to settle down, no time wasted it is already running
            time.sleep(10)
            if not os.path.exists("%s.condor.sub" % dagfilename):
                raise EnvironmentError(
                    "DAGMan did not create its submit file, please check the logs"
                )
            # wait for completion
            logger.info("waiting for DAGMan to finish")
            lockfilename = "%s.lock" % dagfilename
            while os.path.exists(lockfilename):
                time.sleep(5)
