"""Parallel workflow execution via PBS/Torque
"""

import os
import sys

from .base import (GraphPluginBase, logger)

from ...interfaces.base import CommandLine


class PBSGraphPlugin(GraphPluginBase):
    """Execute using PBS/Torque

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    def __init__(self, **kwargs):
        self._template = """
#PBS -V
        """
        self._qsub_args = None
        if 'plugin_args' in kwargs:
            plugin_args = kwargs['plugin_args']
            if 'template' in plugin_args:
                self._template = plugin_args['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if 'qsub_args' in plugin_args:
                self._qsub_args = plugin_args['qsub_args']
        super(PBSGraphPlugin, self).__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies):
        batch_dir, _ = os.path.split(pyfiles[0])
        submitjobsfile = os.path.join(batch_dir, 'submit_jobs.sh')
        with open(submitjobsfile, 'wt') as fp:
            fp.writelines('#!/usr/bin/env sh\n')
            for idx, pyscript in enumerate(pyfiles):
                batch_dir, name = os.path.split(pyscript)
                name = '.'.join(name.split('.')[:-1])
                batchscript = '\n'.join((self._template,
                                         '%s %s' % (sys.executable, pyscript)))
                batchscriptfile = os.path.join(batch_dir,
                                               'batchscript_%s.sh' % name)
                with open(batchscriptfile, 'wt') as batchfp:
                    batchfp.writelines(batchscript)
                    batchfp.close()
                deps = ''
                if idx in dependencies:
                    values = ['$job%05d' % jobid for jobid in dependencies[idx]]
                    if len(values):
                        deps = '-W depend=afterok:%s' % ':'.join(values)
                fp.writelines('job%05d=`qsub %s %s %s`\n' % (idx, deps,
                                                             self._qsub_args,
                                                             batchscriptfile))
        cmd = CommandLine('sh', environ=os.environ.data)
        cmd.inputs.args = '%s' % submitjobsfile
        cmd.run()
        logger.info('submitted all jobs to queue')

