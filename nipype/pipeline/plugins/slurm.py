'''
Created on Aug 2, 2013

@author: chadcumba

Parallel workflow execution with SLURM
'''

import os
import re
import subprocess
from time import sleep

from .base import (SLURMLikeBatchManagerBase, logger, iflogger, logging)

from nipype.interfaces.base import CommandLine




class SLURMPlugin(SLURMLikeBatchManagerBase):
    '''
    Execute using SLURM

    The plugin_args input to run can be used to control the SLURM execution.
    Currently supported options are:

    - template : template to use for batch job submission
    

    '''


    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        template="""
#!/bin/sh
        """
        self._retry_timeout = 2
        self._max_tries = 2
        if 'plugin_args' in kwargs and kwargs['plugin_args']:
            if 'retry_timeout' in kwargs['plugin_args']:
                self._retry_timeout = kwargs['plugin_args']['retry_timeout']
            if  'max_tries' in kwargs['plugin_args']:
                self._max_tries = kwargs['plugin_args']['max_tries']
        super(SLURMPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        #  subprocess.Popen requires taskid to be a string
        proc = subprocess.Popen(["showq", '-u'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        o, _ = proc.communicate()
        return o.find(taskid) > -1

    def _submit_batchtask(self, scriptfile, node):
        cmd = CommandLine('sbatch', environ=os.environ.data,
                          terminal_output='allatonce')
        path = os.path.dirname(scriptfile)
        
        slurmargs = ''
        if self._slurmargs:
            slurmargs = self._slurm_args
        if 'slurm_args' in node.plugin_args:
            if 'overwrite' in node.plugin_args and\
               node.plugin_args['overwrite']:
                slurmargs = node.plugin_args['slurm_args']
            else:
                slurmargs += (" " + node.plugin_args['slurm_args'])
        if '-o' not in slurmargs:
            slurmargs = '%s -o %s' % (slurmargs, path)
        if '-e' not in slurmargs:
            slurmargs = '%s -e %s' % (slurmargs, path)
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
        cmd.inputs.args = '%s -J %s %s' % (slurmargs,
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
                    raise RuntimeError('\n'.join((('Could not submit slurm task'
                                                   ' for node %s') % node._id,
                                                  str(e))))
            else:
                break
        iflogger.setLevel(oldlevel)
        # retrieve sge taskid
        lines = [line for line in result.runtime.stdout.split('\n') if line]
        taskid = int(re.match("Your job ([0-9]*) .* has been submitted",
                              lines[-1]).groups()[0])
        self._pending[taskid] = node.output_dir()
        logger.debug('submitted slurm task: %d for node %s' % (taskid, node._id))
        return taskid
