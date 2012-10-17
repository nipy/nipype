"""Parallel workflow execution via Condor DAGMan
"""

import os
import sys

from .base import (GraphPluginBase, logger)

from ...interfaces.base import CommandLine


class CondorDAGManPlugin(GraphPluginBase):
    """Execute using Condor DAGMan

    The plugin_args input to run can be used to control the DAGMan execution.
    Currently supported options are:

    - template : submit spec template to use for job submission. The template
                 all generated submit specs are appended to this template. This
                 can be a str or a filename.
    - submit_specs : additional submit specs that are appended to the generated
                 submit specs to allow for overriding or extending the defaults.
                 This can be a str or a filename.
    - dagman_args : arguments to be prepended to the job execution script in the
                  dagman call
    """
    # XXX feature wishlist
    # - infer data file dependencies from jobs
    # - infer CPU requirements from jobs
    # - infer memory requirements from jobs
    # - looks like right now all jobs come in here, regardless of whether they
    #   actually have to run. would be good to be able to decide whether they
    #   actually have to be scheduled (i.e. output already exist).
    def __init__(self, **kwargs):
        self._template = "universe = vanilla\nnotification = Never"
        self._submit_specs = ""
        self._dagman_args = ""
        if 'plugin_args' in kwargs and not kwargs['plugin_args'] is None:
            plugin_args = kwargs['plugin_args']
            if 'template' in plugin_args:
                self._template = plugin_args['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if 'submit_specs' in plugin_args:
                self._submit_specs = plugin_args['submit_specs']
                if os.path.isfile(self._submit_specs):
                    self._submit_specs = open(self._submit_specs).read()
            if 'dagman_args' in plugin_args:
                self._dagman_args = plugin_args['dagman_args']
        super(CondorDAGManPlugin, self).__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies):
        # location of all scripts, place dagman output in here too
        batch_dir, _ = os.path.split(pyfiles[0])
        # DAG description filename
        dagfilename = os.path.join(batch_dir, 'workflow.dag')
        with open(dagfilename, 'wt') as dagfileptr:
            # loop over all scripts, create submit files, and define them
            # as jobs in the DAG
            for idx, pyscript in enumerate(pyfiles):
                # XXX redundant with previous value? or could it change between
                # scripts?
                batch_dir, name = os.path.split(pyscript)
                name = '.'.join(name.split('.')[:-1])
                submitspec = '\n'.join(
                                (self._template,
                                 'executable = %s' % sys.executable,
                                 'arguments = %s' % pyscript,
                                 'output = %s' % os.path.join(batch_dir,
                                                             '%s.out' % name),
                                 'error = %s' % os.path.join(batch_dir,
                                                             '%s.err' % name),
                                 'log = %s' % os.path.join(batch_dir,
                                                           '%s.log' % name),
                                 'getenv = True',
                                 self._submit_specs,
                                 'queue'
                                 ))
                # write submit spec for this job
                submitfile = os.path.join(batch_dir,
                                               '%s.submit' % name)
                with open(submitfile, 'wt') as submitfileprt:
                    submitfileprt.writelines(submitspec)
                    submitfileprt.close()
                # define job in DAG
                dagfileptr.write('JOB %i %s\n' % (idx, submitfile))
            # define dependencies in DAG
            for child in dependencies:
                parents = dependencies[child]
                if len(parents):
                    dagfileptr.write('PARENT %s CHILD %i\n'
                                     % (' '.join([str(i) for i in parents]),
                                        child))
        # hand over DAG to condor_dagman
        cmd = CommandLine('condor_submit_dag', environ=os.environ.data)
        # needs -update_submit or re-running a workflow will fail
        cmd.inputs.args = '-update_submit %s %s' % (dagfilename,
                                                    self._dagman_args)
        cmd.run()
        logger.info('submitted all jobs to Condor DAGMan')

