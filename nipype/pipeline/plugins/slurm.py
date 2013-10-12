'''
Created on Aug 2, 2013

@author: chadcumba

Parallel workflow execution with SLURM
'''

import os
import re
import subprocess
from time import sleep

from .base import (SGELikeBatchManagerBase, logger, iflogger, logging)

from nipype.interfaces.base import CommandLine




class SLURMPlugin(SGELikeBatchManagerBase):
    '''
    Execute using SLURM

    The plugin_args input to run can be used to control the SLURM execution.
    Currently supported options are:

    - template : template to use for batch job submission

    - sbatch_args: arguments to pass prepend to the sbatch call


    '''


    def __init__(self, **kwargs):

        template="#!/bin/bash"

        self._retry_timeout = 2
        self._max_tries = 2
        self._template = template
        self._sbatch_args = None

        if 'plugin_args' in kwargs and kwargs['plugin_args']:
            if 'retry_timeout' in kwargs['plugin_args']:
                self._retry_timeout = kwargs['plugin_args']['retry_timeout']
            if  'max_tries' in kwargs['plugin_args']:
                self._max_tries = kwargs['plugin_args']['max_tries']
            if 'template' in kwargs['plugin_args']:
                self._template = kwargs['plugin_args']['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if 'sbatch_args' in kwargs['plugin_args']:
                self._sbatch_args = kwargs['plugin_args']['sbatch_args']
        self._pending = {}
        super(SLURMPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        #  subprocess.Popen requires taskid to be a string
        proc = subprocess.Popen(["showq", '-u'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        o, _ = proc.communicate()

        return o.find(str(taskid)) > -1

    def _submit_batchtask(self, scriptfile, node):
        """
        This is more or less the _submit_batchtask from sge.py with flipped variable
        names, different command line switches, and different output formatting/processing
        """
        cmd = CommandLine('sbatch', environ=os.environ.data,
                          terminal_output='allatonce')
        path = os.path.dirname(scriptfile)

        sbatch_args = ''
        if self._sbatch_args:
            sbatch_args = self._sbatch_args
        if 'sbatch_args' in node.plugin_args:
            if 'overwrite' in node.plugin_args and\
               node.plugin_args['overwrite']:
                sbatch_args = node.plugin_args['sbatch_args']
            else:
                sbatch_args += (" " + node.plugin_args['sbatch_args'])
        if '-o' not in sbatch_args:
            sbatch_args = '%s -o %s' % (sbatch_args, os.path.join(path, 'slurm-%j.out'))
        if '-e' not in sbatch_args:
            sbatch_args = '%s -e %s' % (sbatch_args, os.path.join(path, 'slurm-%j.out'))
        if '-p' not in sbatch_args:
            sbatch_args = '%s -p normal' % (sbatch_args)
        if '-n' not in sbatch_args:
            sbatch_args = '%s -n 16' % (sbatch_args)
        if '-t' not in sbatch_args:
            sbatch_args = '%s -t 1:00:00' % (sbatch_args)
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
        cmd.inputs.args = '%s -J %s %s' % (sbatch_args,
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
                    raise RuntimeError('\n'.join((('Could not submit sbatch task'
                                                   ' for node %s') % node._id,
                                                  str(e))))
            else:
                break
        logger.debug('Ran command ({0})'.format(cmd.cmdline))
        iflogger.setLevel(oldlevel)
        # retrieve taskid
        lines = [line for line in result.runtime.stdout.split('\n') if line]
        taskid = int(re.match("Submitted batch job ([0-9]*)",
                              lines[-1]).groups()[0])
        self._pending[taskid] = node.output_dir()
        logger.debug('submitted sbatch task: %d for node %s' % (taskid, node._id))
        return taskid
