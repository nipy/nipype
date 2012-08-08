"""Parallel workflow execution via SGE
"""

import os
import sys

from .base import (GraphPluginBase, logger)

from ...interfaces.base import CommandLine


class SGEGraphPlugin(GraphPluginBase):
    """Execute using SGE

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    def __init__(self, **kwargs):
        self._template = """
#!/bin/bash
#$ -V
#$ -S /bin/bash
        """
        self._qsub_args = ''
        if 'plugin_args' in kwargs:
            plugin_args = kwargs['plugin_args']
            if 'template' in plugin_args:
                self._template = plugin_args['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if 'qsub_args' in plugin_args:
                self._qsub_args = plugin_args['qsub_args']
        super(SGEGraphPlugin, self).__init__(**kwargs)

    def _submit_graph(self, pyfiles, dependencies):
        batch_dir, _ = os.path.split(pyfiles[0])
        submitjobsfile = os.path.join(batch_dir, 'submit_jobs.sh')
        with open(submitjobsfile, 'wt') as fp:
            fp.writelines('#!/usr/bin/env bash\n')
            for idx, pyscript in enumerate(pyfiles):
                batch_dir, name = os.path.split(pyscript)
                name = '.'.join(name.split('.')[:-1])
                batchscript = '\n'.join((self._template,
                                         '%s %s' % (sys.executable, pyscript)))
                batchscriptfile = os.path.join(batch_dir,
                                               'batchscript_%s.sh' % name)

                batchscriptoutfile = batchscriptfile + '.o'
                batchscripterrfile = batchscriptfile + '.e'

                with open(batchscriptfile, 'wt') as batchfp:
                    batchfp.writelines(batchscript)
                    batchfp.close()
                deps = ''
                if idx in dependencies:
                    values = ' '
                    for jobid in dependencies[idx]:
                        values += 'job%05d,' % jobid
                    if 'job' in values:
                        values = values.rstrip(',')
                        deps = '-hold_jid%s' % values
                jobname = 'job%05d' % ( idx )
                ## Do not use default output locations if they are set in self._qsub_args
                stderrFile = ''
                if self._qsub_args.count('-e ') == 0:
                        stderrFile='-e {errFile}'.format(errFile=batchscripterrfile)
                stdoutFile = ''
                if self._qsub_args.count('-o ') == 0:
                        stdoutFile='-o {outFile}'.format(outFile=batchscriptoutfile)
                full_line = '{jobNm}=$(qsub {outFileOption} {errFileOption} {extraQSubArgs} {dependantIndex} -N {jobNm} {batchscript})\n'.format(
                             jobNm=jobname,
                             outFileOption=stdoutFile,
                             errFileOption=stderrFile,
                             extraQSubArgs=self._qsub_args,
                             dependantIndex=deps,
                             batchscript=batchscriptfile)
                fp.writelines( full_line )

        cmd = CommandLine('bash', environ=os.environ.data)
        cmd.inputs.args = '%s' % submitjobsfile
        cmd.run()
        logger.info('submitted all jobs to queue')
