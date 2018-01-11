"""Parallel workflow execution via PBS/Torque
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import open

import os
import sys

from ...interfaces.base import CommandLine
from .sgegraph import SGEGraphPlugin
from .base import logger


class PBSGraphPlugin(SGEGraphPlugin):
    """Execute using PBS/Torque

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """
    _template = """
#PBS -V
"""

    def _submit_graph(self, pyfiles, dependencies, nodes):
        batch_dir, _ = os.path.split(pyfiles[0])
        submitjobsfile = os.path.join(batch_dir, 'submit_jobs.sh')
        with open(submitjobsfile, 'wt') as fp:
            fp.writelines('#!/usr/bin/env sh\n')
            for idx, pyscript in enumerate(pyfiles):
                node = nodes[idx]
                template, qsub_args = self._get_args(node,
                                                     ["template", "qsub_args"])

                batch_dir, name = os.path.split(pyscript)
                name = '.'.join(name.split('.')[:-1])
                batchscript = '\n'.join((template, '%s %s' % (sys.executable,
                                                              pyscript)))
                batchscriptfile = os.path.join(batch_dir,
                                               'batchscript_%s.sh' % name)
                with open(batchscriptfile, 'wt') as batchfp:
                    batchfp.writelines(batchscript)
                    batchfp.close()
                deps = ''
                if idx in dependencies:
                    values = [
                        '$job%05d' % jobid for jobid in dependencies[idx]
                    ]
                    if len(values):
                        deps = '-W depend=afterok:%s' % ':'.join(values)
                fp.writelines('job%05d=`qsub %s %s %s`\n' %
                              (idx, deps, qsub_args, batchscriptfile))
        cmd = CommandLine(
            'sh',
            environ=dict(os.environ),
            resource_monitor=False,
            terminal_output='allatonce')
        cmd.inputs.args = '%s' % submitjobsfile
        cmd.run()
        logger.info('submitted all jobs to queue')
