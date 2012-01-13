"""Parallel workflow execution via SGE
"""

import os

from .base import (SGELikeBatchManagerBase, logger, iflogger, logging)

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
        template = """
#$ -V
#$ -S /bin/sh
        """
        self._retry_timeout = 2
        self._max_tries = 2
        if 'plugin_args' in kwargs and kwargs['plugin_args']:
            if 'retry_timeout' in kwargs['plugin_args']:
                self._retry_timeout = kwargs['plugin_args']['retry_timeout']
            if  'max_tries' in kwargs['plugin_args']:
                self._max_tries = kwargs['plugin_args']['max_tries']
        super(SGEPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        cmd = CommandLine('qstat')
        cmd.inputs.args = '-j %d' % taskid
        # check sge task
        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName('CRITICAL'))
        result = cmd.run(ignore_exception=True)
        iflogger.setLevel(oldlevel)
        if result.runtime.stdout.startswith('='):
            return True
        return False

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('qsub', environ=os.environ.data)
        path = os.path.dirname(scriptfile)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
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
                    raise RuntimeError('\n'.join((('Could not submit sge task'
                                                   ' for node %s') % node._id,
                                                  str(e))))
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve sge taskid
        taskid = int(result.runtime.stdout.split(' ')[2])
        self._pending[taskid] = node.output_dir()
        logger.debug('submitted sge task: %d for node %s' % (taskid, node._id))
        return taskid
