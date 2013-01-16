"""Parallel workflow execution via Condor
"""

import os

from .base import (SGELikeBatchManagerBase, logger, iflogger, logging)

from nipype.interfaces.base import CommandLine

from time import sleep


class CondorPlugin(SGELikeBatchManagerBase):
    """Execute using Condor

    This plugin doesn't work with a plain stock-Condor installation, but
    requires a 'qsub' emulation script for Condor, called 'condor_qsub'.
    This script is shipped with the Condor package from NeuroDebian, or can be
    downloaded from its Git repository at

    http://anonscm.debian.org/gitweb/?p=pkg-exppsy/condor.git;a=blob_plain;f=debian/condor_qsub;hb=HEAD

    The plugin_args input to run can be used to control the Condor execution.
    Currently supported options are:

    - template : template to use for batch job submission. This can be an
                 SGE-style script with the (limited) set of options supported
                 by condor_qsub
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
        super(CondorPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        cmd = CommandLine('condor_q',
                          terminal_output='allatonce')
        cmd.inputs.args = '%d' % taskid
        # check condor cluster
        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName('CRITICAL'))
        result = cmd.run(ignore_exception=True)
        iflogger.setLevel(oldlevel)
        if result.runtime.stdout.count('\n%d' % taskid):
            return True
        return False

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('condor_qsub', environ=os.environ.data,
                          terminal_output='allatonce')
        path = os.path.dirname(scriptfile)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
        if 'qsub_args' in node.plugin_args:
            if 'overwrite' in node.plugin_args and\
               node.plugin_args['overwrite']:
                qsubargs = node.plugin_args['qsub_args']
            else:
                qsubargs += (" " + node.plugin_args['qsub_args'])
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
                    raise RuntimeError('\n'.join((('Could not submit condor '
                                                   'cluster'
                                                   ' for node %s') % node._id,
                                                  str(e))))
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve condor clusterid
        taskid = int(result.runtime.stdout.split(' ')[2])
        self._pending[taskid] = node.output_dir()
        logger.debug('submitted condor cluster: %d for node %s' % (taskid,
                                                                   node._id))
        return taskid
