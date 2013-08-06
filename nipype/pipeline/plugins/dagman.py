"""Parallel workflow execution via Condor DAGMan
"""

import os
import sys
import uuid

from .base import (GraphPluginBase, logger)

from ...interfaces.base import CommandLine


class CondorDAGManPlugin(GraphPluginBase):
    """Execute using Condor DAGMan

    The plugin_args input to run can be used to control the DAGMan execution.
    Currently supported options are:

    - template : submit spec template for individual jobs in a DAG. All
                 generated submit spec components (e.g. executable name and
                 arguments) are appended to this template. This can be a str or
                 a filename. In the latter case the file content is used as a
                 template.
    - submit_specs : additional submit specs that are appended to the generated
                 submit specs to allow for overriding or extending the defaults.
                 This can be a str or a filename.
    - dagman_args : arguments to be prepended to the job execution script in the
                  dagman call
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
            content = open(arg).read()
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
        self._template = self.default_submit_template
        self._initial_specs = ""
        self._override_specs = ""
        self._dagman_args = ""
        if 'plugin_args' in kwargs and not kwargs['plugin_args'] is None:
            plugin_args = kwargs['plugin_args']
            if 'template' in plugin_args:
                self._template = \
                    self._get_str_or_file(plugin_args['template'])
            if 'initial_specs' in plugin_args:
                self._initial_specs = \
                    self._get_str_or_file(plugin_args['initial_specs'])
            if 'override_specs' in plugin_args:
                self._override_specs = \
                    self._get_str_or_file(plugin_args['override_specs'])
            if 'dagman_args' in plugin_args:
                self._dagman_args = plugin_args['dagman_args']
        super(CondorDAGManPlugin, self).__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies, nodes):
        # location of all scripts, place dagman output in here too
        batch_dir, _ = os.path.split(pyfiles[0])
        # DAG description filename
        dagfilename = os.path.join(batch_dir, 'workflow-%s.dag' % uuid.uuid4())
        with open(dagfilename, 'wt') as dagfileptr:
            # loop over all scripts, create submit files, and define them
            # as jobs in the DAG
            for idx, pyscript in enumerate(pyfiles):
                node = nodes[idx]
                # XXX redundant with previous value? or could it change between
                # scripts?
                template, initial_specs, override_specs = self._get_args(
                    node, ["template", "initial_specs", "override_specs"])
                # add required slots to the template
                template = '%s\n%s\n%s\n' % ('%(initial_specs)s',
                                             template,
                                             '%(override_specs)s')
                batch_dir, name = os.path.split(pyscript)
                name = '.'.join(name.split('.')[:-1])
                specs = dict(
                    # TODO make parameter for this,
                    initial_specs=initial_specs,
                    executable=sys.executable,
                    nodescript=pyscript,
                    basename=os.path.join(batch_dir, name),
                    override_specs=override_specs
                    )
                submitspec = template % specs
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
        cmd = CommandLine('condor_submit_dag', environ=os.environ.data,
                          terminal_output='allatonce')
        # needs -update_submit or re-running a workflow will fail
        cmd.inputs.args = '-update_submit %s %s' % (dagfilename,
                                                    self._dagman_args)
        cmd.run()
        logger.info('submitted all jobs to Condor DAGMan')
