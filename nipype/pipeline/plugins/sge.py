"""Parallel workflow execution via SGE
"""

import os

from .base import (SGELikeBatchManagerBase, logger)

from nipype.interfaces.base import CommandLine

class SGEPlugin(SGELikeBatchManagerBase):
    """Execute using SGE (OGE not tested)

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    def __init__(self, **kwargs):
        template="""#$ -V\n#$ -S /bin/sh\n"""
        super(SGEPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        cmd = CommandLine('qstat')
        cmd.inputs.args = '-j %d'%taskid
        # check sge task
        result = cmd.run(ignore_exception=True)
        if result.runtime.stdout.startswith('='):
            return True
        return False

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('qsub', environ=os.environ.data)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
        cmd.inputs.args = '%s %s'%(qsubargs, scriptfile)
        try:
            result = cmd.run()
        except Exception, e:
            raise RuntimeError('\n'.join(('Could not submit sge task for node %s'%node._id,
                                          str(e))))
        else:
            # retrieve sge taskid
            taskid = int(result.runtime.stdout.split(' ')[2])
            self._pending[taskid] = node.output_dir()
            logger.debug('submitted sge task: %d for node %s'%(taskid, node._id))
        return taskid
