"""Parallel workflow execution via SGE
"""
import os
from .base import (DistributedPluginBase, logger, report_crash)
from nipype.utils.filemanip import savepkl

class sge_runner(DistributedPluginBase):
    """Execute workflow with ipython
    """

    def _get_result(self, taskid):
        #get results from sge taskid
        pass

    def _submit_job(self, node, updatehash=False):
        # use qsub to submit job and return sgeid
        # pickle node
        node_dir = node.output_dir()
        if not os.path.exists(node_dir):
            os.makedirs(node_dir)
        pkl_file = ''
        # create python script to load and trap exception
        cmdstr = """import sys
from traceback import format_exception
from nipype.utils.filemanip import loadpkl
traceback=None
try:
task = loadpkl('%s')
result = task.run(updatehash=updatehash)
except:
etype, eval, etr = sys.exc_info()
traceback = format_exception(etype,eval,etr)
result = task.result
"""%pkl_file
        # retrieve sge taskid
        pass

    def _report_crash(self, node, result=None):
        if result and result['traceback']
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=res['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        # clear sge script
