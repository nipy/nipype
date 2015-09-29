# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""

from multiprocessing import Process, Pool, cpu_count, pool
from traceback import format_exception
import sys

from .base import (DistributedPluginBase, report_crash)

def run_node(node, updatehash):
    result = dict(result=None, traceback=None)
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype,eval,etr)
        result['result'] = node.result
    return result

class NonDaemonProcess(Process):
    """A non-daemon process to support internal multiprocessing.
    """
    def _get_daemon(self):
        return False

    def _set_daemon(self, value):
        pass

    daemon = property(_get_daemon, _set_daemon)

class NonDaemonPool(pool.Pool):
    """A process pool with non-daemon processes.
    """
    Process = NonDaemonProcess

class MultiProcPlugin(DistributedPluginBase):
    """Execute workflow with multiprocessing

    The plugin_args input to run can be used to control the multiprocessing
    execution. Currently supported options are:

    - n_procs : number of processes to use
    - non_daemon : boolean flag to execute as non-daemon processes

    """

    def __init__(self, plugin_args=None):
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._taskid = 0
        non_daemon = True
        n_procs = cpu_count()
        if plugin_args:
            if 'n_procs' in plugin_args:
                n_procs = plugin_args['n_procs']
            if 'non_daemon' in plugin_args:
                non_daemon = plugin_args['non_daemon']
        if non_daemon:
            # run the execution using the non-daemon pool subclass
            self.pool = NonDaemonPool(processes=n_procs)
        else:
            self.pool = Pool(processes=n_procs)

    def _get_result(self, taskid):
        if taskid not in self._taskresult:
            raise RuntimeError('Multiproc task %d not found'%taskid)
        if not self._taskresult[taskid].ready():
            return None
        return self._taskresult[taskid].get()

    def _submit_job(self, node, updatehash=False):
        self._taskid += 1
        try:
            if node.inputs.terminal_output == 'stream':
                node.inputs.terminal_output = 'allatonce'
        except:
            pass
        self._taskresult[self._taskid] = self.pool.apply_async(run_node,
                                                               (node,
                                                                updatehash,))
        return self._taskid

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, taskid):
        del self._taskresult[taskid]





import numpy as np
from copy import deepcopy
from ..engine import (MapNode, str2bool)
import datetime
import psutil

class ResourceMultiProcPlugin(MultiProcPlugin):

    def __init__(self, plugin_args=None):
        super(ResourceMultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self.plugin_args = plugin_args
        self.current_time = datetime.datetime.now()
        self.log_nodes = []

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        executing_now = []
        processors = cpu_count()
        memory = psutil.virtual_memory()
        memory = memory.total
        if self.plugin_args:
            if 'n_procs' in self.plugin_args:
                processors = self.plugin_args['n_procs']
            if 'memory' in self.plugin_args:
                memory = self.plugin_args['memory']


        jobids = np.flatnonzero((self.proc_pending == True) & (self.depidx.sum(axis=0) == 0).__array__())
        print('START, pending_tasks:', jobids)

        #busy_processors = number of busy processors
        busy_memory = 0
        busy_processors = 0
        for jobid in jobids:
            print 'using memory:', jobid, self.procs[jobid]._interface.num_threads
            busy_memory+= self.procs[jobid]._interface.memory
            busy_processors+= self.procs[jobid]._interface.num_threads
                

        free_memory = memory - busy_memory
        free_processors = processors - busy_processors

        #jobids = all jobs without dependency not run
        jobids = np.flatnonzero((self.proc_done == False) & (self.depidx.sum(axis=0) == 0).__array__())


        #sort jobids first by memory and then by number of threads
        jobids = sorted(jobids, key=lambda item: (self.procs[item]._interface.memory, self.procs[item]._interface.num_threads))
        print('jobids ->', jobids)

        print 'free memory ->', free_memory, ', free processors ->', free_processors


        #while have enough memory and processors for first job
        #submit first job on the list
        for jobid in jobids:
            print 'next_job ->', jobid, 'memory:', self.procs[jobid]._interface.memory, 'threads:', self.procs[jobid]._interface.num_threads

            print 'can job execute?', self.procs[jobid]._interface.memory <= free_memory and self.procs[jobid]._interface.num_threads <= free_processors
            if self.procs[jobid]._interface.memory <= free_memory and self.procs[jobid]._interface.num_threads <= free_processors:
                print('Executing: %s ID: %d' %(self.procs[jobid]._id, jobid))
                executing_now.append(self.procs[jobid])
                
                if isinstance(self.procs[jobid], MapNode):
                    try:
                        num_subnodes = self.procs[jobid].num_subnodes()
                    except Exception:
                        self._clean_queue(jobid, graph)
                        self.proc_pending[jobid] = False
                        continue
                    if num_subnodes > 1:
                        submit = self._submit_mapnode(jobid)
                        if not submit:
                            continue


                self.proc_done[jobid] = True
                self.proc_pending[jobid] = True

                free_memory -= self.procs[jobid]._interface.memory
                free_processors -= self.procs[jobid]._interface.num_threads

                if self._status_callback:
                    self._status_callback(self.procs[jobid], 'start')
                    

                
                if str2bool(self.procs[jobid].config['execution']['local_hash_check']):
                    print('checking hash locally')
                    try:
                        hash_exists, _, _, _ = self.procs[
                            jobid].hash_exists()
                        print('Hash exists %s' % str(hash_exists))
                        if (hash_exists and (self.procs[jobid].overwrite == False or (self.procs[jobid].overwrite == None and not self.procs[jobid]._interface.always_run))):
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                            continue
                    except Exception:
                        self._clean_queue(jobid, graph)
                        self.proc_pending[jobid] = False
                        continue

                    
                print('Finished checking hash')


                if self.procs[jobid].run_without_submitting:
                    print('Running node %s on master thread' %self.procs[jobid])
                    try:
                        self.procs[jobid].run()
                    except Exception:
                        self._clean_queue(jobid, graph)
                    self._task_finished_cb(jobid)
                    self._remove_node_dirs()

                else:
                    print('submitting', jobid)
                    tid = self._submit_job(deepcopy(self.procs[jobid]), updatehash=updatehash)
                    if tid is None:
                        self.proc_done[jobid] = False
                        self.proc_pending[jobid] = False
                    else:
                        self.pending_tasks.insert(0, (tid, jobid))
            else:
                break

        #run this code when not running each node
        # max_node = datetime.datetime.min
        # for n in executing_now:
        #     name = n.name 
        #     start = self.current_time
        #     finish = self.current_time + n._interface.time
        #     duration = (finish - start).total_seconds()
        #     memory = n._interface.memory
        #     num_threads = n._interface.num_threads
            
        #     if finish > max_node:
        #         max_node = finish

        #     self.log_nodes.append({'name': name, 'start': str(start), 'finish': str(finish), 'duration': duration, 'memory':memory, 'num_threads': num_threads})


        # if len(executing_now) > 0:
        #     self.current_time = finish
        #     #write log
        #     self.log_nodes = sorted(self.log_nodes, key=lambda n: datetime.datetime.strptime(n['start'],"%Y-%m-%d %H:%M:%S.%f"))
        #     first_node = datetime.datetime.strptime(self.log_nodes[0]['start'],"%Y-%m-%d %H:%M:%S.%f")
        #     last_node = datetime.datetime.strptime(self.log_nodes[-1]['finish'],"%Y-%m-%d %H:%M:%S.%f")


        #     result = {"name": os.getcwd(), "start": str(first_node), "finish": str(last_node), "duration": (last_node - first_node).total_seconds() / 60, "nodes": self.log_nodes}

        #     log_content = json.dumps(result)
        #     log_file = open('log_anat_preproc.py', 'wb')
        #     log_file.write(log_content)
        #     log_file.close()

        print('- - - - - - - - - - - - - - - ', len(self.log_nodes), '- - - - - - - - - - - - - - - ')
        print('No jobs waiting to execute')
