"""Parallel workflow execution via SGE
"""
from glob import glob

import os

from .base import (DistributedPluginBase, logger, report_crash, strftime)
from nipype.utils.filemanip import savepkl, loadpkl
from nipype.interfaces.base import CommandLine

class SGEPlugin(DistributedPluginBase):
    """Execute workflow with SGE/OGE

    The plugin_args input to run can be used to control the SGE execution.
    Currently supported options are:

    - template : template to use for SGE job submission
    - qsub_args : arguments to be prepended to the job execution script in the
                  qsub call

    """

    def __init__(self, plugin_args=None):
        self._template="""
#$$ -V
#$$ -S /bin/sh
"""
        self._qsub_args = None
        if plugin_args:
            if 'template' in plugin_args:
                self._template = plugin_args['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).readlines()
            if 'qsub_args' in plugin_args:
                self._qsub_args = plugin_args['qsub_args']
        self._pending = {}
        
    def _get_result(self, taskid):
        if taskid not in self._pending:
            raise Exception('SGE task %d not found'%taskid)
        cmd = CommandLine('qstat')
        cmd.inputs.args = '-j %d'%(taskid)
        # retrieve sge taskid
        result = cmd.run()
        if result.runtime.stdout.startswith('='):
            return None
        node_dir = self._pending[taskid]
        results_file = glob(os.path.join(node_dir,'result_*.pklz'))[0]
        result_data = loadpkl(results_file)
        result_out = dict(result=None, traceback=None)
        if isinstance(result_data, dict):
            result_out['result'] = result_data['result']
            result_out['traceback'] = result_data['traceback']
            os.remove(results_file)
        else:
            result_out['result'] = result_data
        return result_out

    def _submit_job(self, node, updatehash=False):
        # use qsub to submit job and return sgeid
        # pickle node
        timestamp = strftime('%Y%m%d_%H%M%S')
        suffix = '%s_%s'%(timestamp, node._id)
        sge_dir = os.path.join(node.base_dir, 'sge')
        if not os.path.exists(sge_dir):
            os.makedirs(sge_dir)
        pkl_file = os.path.join(sge_dir,'node_%s.pklz'%suffix)
        savepkl(pkl_file, dict(node=node, updatehash=updatehash))
        # create python script to load and trap exception
        cmdstr = """import os
import sys
from traceback import format_exception
from nipype.utils.filemanip import loadpkl, savepkl
traceback=None
print os.getcwd()
try:
    info = loadpkl('%s')
    result = info['node'].run(updatehash=info['updatehash'])
except:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    result = info['node'].result
    resultsfile = os.path.join(node.output_dir(), 'result_%%s.pklz'%%info['node'].name)
    savepkl(resultsfile,dict(result=result, traceback=traceback))
"""%pkl_file
        pyscript = os.path.join(sge_dir, 'pyscript_%s.py'%suffix)
        fp = open(pyscript, 'wt')
        fp.writelines(cmdstr)
        fp.close()
        sgescript = '\n'.join((self._template, 'python %s'%pyscript))
        sgescriptfile = os.path.join(sge_dir, 'sgescript_%s.sh'%suffix)
        fp = open(sgescriptfile, 'wt')
        fp.writelines(sgescript)
        fp.close()
        cmd = CommandLine('qsub', environ=os.environ.data)
        qsubargs = ''
        if self._qsub_args:
            qsubargs = self._qsub_args
        cmd.inputs.args = '%s %s'%(qsubargs, sgescriptfile)
        result = cmd.run()
        # retrieve sge taskid
        if not result.runtime.returncode:
            taskid = int(result.runtime.stdout.split(' ')[2])
            self._pending[taskid] = node.output_dir()
            logger.debug('submitted sge task: %d for node %s'%(taskid, node._id))
        else:
            raise RuntimeError('\n'.join(('Could not submit sge task for node %s'%node._id,
                                          result.runtime.stderr)))
        return taskid

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        del self._pending[taskid]
