"""Parallel workflow execution via PBS/Torque
"""

import os

from .base import (SGELikeBatchManagerBase, logger)

from nipype.interfaces.base import CommandLine

class PBSPlugin(SGELikeBatchManagerBase):
    """Execute using PBS/Torque

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for batch job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    def __init__(self, **kwargs):
        template="""
#PBS -V
        """
        super(PBSPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        cmd = CommandLine('qstat')
        cmd.inputs.args = '%s'%taskid
        # check pbs task
        result = cmd.run(ignore_exception=True)
        if 'Unknown Job Id' in result.runtime.stderr:
            return False
        return True

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('qsub', environ=os.environ.data)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
        cmd.inputs.args = '%s -N %s %s'%(qsubargs,
                                         '.'.join((os.environ.data['LOGNAME'],
                                                   node._id)),
                                         scriptfile)
        try:
            result = cmd.run()
        except Exception, e:
            raise RuntimeError('\n'.join(('Could not submit pbs task for node %s'%node._id,
                                          str(e))))
        else:
            # retrieve pbs taskid
            taskid = result.runtime.stdout.split('.')[0]
            self._pending[taskid] = node.output_dir()
            logger.debug('submitted pbs task: %s for node %s'%(taskid, node._id))

        return taskid
