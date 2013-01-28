"""Parallel workflow execution via PBS/Torque
"""

import os
from time import sleep
import subprocess

from .base import (SGELikeBatchManagerBase, logger, iflogger, logging)

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
        template = """
#PBS -V
        """
        self._retry_timeout = 2
        self._max_tries = 2
        if 'plugin_args' in kwargs and kwargs['plugin_args']:
            if 'retry_timeout' in kwargs['plugin_args']:
                self._retry_timeout = kwargs['plugin_args']['retry_timeout']
            if  'max_tries' in kwargs['plugin_args']:
                self._max_tries = kwargs['plugin_args']['max_tries']
        super(PBSPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        #  subprocess.Popen requires taskid to be a string
        proc = subprocess.Popen(["qstat", str(taskid)],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        _, e = proc.communicate()
        errmsg = 'Unknown Job Id' # %s' % taskid
        return  errmsg not in e

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('qsub', environ=os.environ.data,
                          terminal_output='allatonce')
        path = os.path.dirname(scriptfile)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
        if 'qsub_args' in node.plugin_args:
            if 'overwrite' in node.plugin_args and \
               node.plugin_args['overwrite']:
                qsubargs = node.plugin_args['qsub_args']
            else:
                qsubargs += (" " + node.plugin_args['qsub_args'])
        if '-o' not in qsubargs:
            qsubargs = '%s -o %s' % (qsubargs, path)
        if '-e' not in qsubargs:
            qsubargs = '%s -e %s' % (qsubargs, path)
        if node._hierarchy:
            jobname = '.'.join((os.environ.data['LOGNAME'],
                                node._hierarchy,
                                node._id))
        else:
            jobname = '.'.join((os.environ.data['LOGNAME'],
                                node._id))
        jobnameitems = jobname.split('.')
        jobnameitems.reverse()
        jobname = '.'.join(jobnameitems)
        cmd.inputs.args = '%s -N %s %s' % (qsubargs,
                                           jobname,
                                           scriptfile)

        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName('CRITICAL'))
        tries = 0
        while True:
            try:
                result = cmd.run()
            except Exception, e:
                if tries < self._max_tries:
                    tries += 1
                    sleep(self._retry_timeout)  # sleep 2 seconds and try again.
                else:
                    iflogger.setLevel(oldlevel)
                    raise RuntimeError('\n'.join((('Could not submit pbs task'
                                                   ' for node %s') % node._id,
                                                  str(e))))
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve pbs taskid
        taskid = result.runtime.stdout.split('.')[0]
        self._pending[taskid] = node.output_dir()
        logger.debug('submitted pbs task: %s for node %s' % (taskid, node._id))

        return taskid
