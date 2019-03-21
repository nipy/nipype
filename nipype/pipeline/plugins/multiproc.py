# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Parallel workflow execution via multiprocessing

Support for child processes running as non-daemons based on
http://stackoverflow.com/a/8963618/1183453
"""
from __future__ import print_function, division, unicode_literals, absolute_import

# Import packages
from multiprocessing import Process, Pool, cpu_count, pool
from traceback import format_exception
import sys

from copy import deepcopy
import numpy as np

from ... import logging
from ...utils.profiler import get_system_total_memory_gb
from ..engine import MapNode
from .base import DistributedPluginBase

# Init logger
logger = logging.getLogger('workflow')

# GPU stuff
import json
import os


# Run node
def run_node(node, updatehash, taskid, devno=None):
    """Function to execute node.run(), catch and log any errors and
    return the result dictionary

    Parameters
    ----------
    node : nipype Node instance
        the node to run
    updatehash : boolean
        flag for updating hash

    devno: the device id of the GPU to make it  the only visible device before 
           submitting a job to it
    Returns
    -------
    result : dictionary
        dictionary containing the node runtime results and stats
    """

    # Init variables
    result = dict(result=None, traceback=None, taskid=taskid)

    # Try and execute the node via node.run()
    try:
        #set dev visible if not none
        if devno is not None:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(devno)
            logger.info('CUDA_VISIBLE_DEVICE=%d',devno)
            
        result['result'] = node.run(updatehash=updatehash)
    except:
        if devno is not None:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(devno)
            logger.info('EXC: CUDA_VISIBLE_DEVICE=%d',devno)

        result['traceback'] = format_exception(*sys.exc_info())
        result['result'] = node.result

    # Return the result dictionary
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
    """
    Execute workflow with multiprocessing, not sending more jobs at once
    than the system can support.

    The plugin_args input to run can be used to control the multiprocessing
    execution and defining the maximum amount of memory and threads that
    should be used. When those parameters are not specified,
    the number of threads and memory of the system is used.

    System consuming nodes should be tagged::

      memory_consuming_node.mem_gb = 8
      thread_consuming_node.n_procs = 16

    The default number of threads and memory are set at node
    creation, and are 1 and 0.25GB respectively.

    Currently supported options are:

    - non_daemon : boolean flag to execute as non-daemon processes
    - n_procs: maximum number of threads to be executed in parallel
    - memory_gb: maximum memory (in GB) that can be used at once.
    - raise_insufficient: raise error if the requested resources for
        a node over the maximum `n_procs` and/or `memory_gb`
        (default is ``True``).
    - scheduler: sort jobs topologically (``'tsort'``, default value)
        or prioritize jobs by, first, memory consumption and, second,
        number of threads (``'mem_thread'`` option).
    - maxtasksperchild: number of nodes to run on each process before
        refreshing the worker (default: 10).

    """

    def __init__(self, plugin_args=None):
        # Init variables and instance attributes
        super(MultiProcPlugin, self).__init__(plugin_args=plugin_args)
        self._taskresult = {}
        self._task_obj = {}
        self._taskid = 0

        # Read in options or set defaults.
        non_daemon = self.plugin_args.get('non_daemon', True)
        maxtasks = self.plugin_args.get('maxtasksperchild', 10)
        self.processors = self.plugin_args.get('n_procs', cpu_count())
        self.memory_gb = self.plugin_args.get('memory_gb',  # Allocate 90% of system memory
                                              get_system_total_memory_gb() * 0.9)
        self.raise_insufficient = self.plugin_args.get('raise_insufficient', True)
        
        self.n_gpus_visible = self.gpu_count()
        self.n_gpus = self.plugin_args.get('n_gpus', self.n_gpus_visible)
        self.n_gpu_proc = self.plugin_args.get('ngpuproc', 1)
        
        # Check plugin args
        if self.plugin_args:
            if 'non_daemon' in self.plugin_args:
                non_daemon = plugin_args['non_daemon']
            if 'n_procs' in self.plugin_args:
                self.processors = self.plugin_args['n_procs']
            if 'memory_gb' in self.plugin_args:
                self.memory_gb = self.plugin_args['memory_gb']
            if 'n_gpus' in self.plugin_args:
                self.n_gpus = self.plugin_args['n_gpus']
            if 'ngpuproc' in self.plugin_args:
                self.n_gpu_proc = self.plugin_args['ngpuproc']
                
                
        #total no. of processes allowed on all gpus
        if self.n_gpus > self.n_gpus_visible:
            logger.info('Total number of GPUs (%d) requested exceeds the available number of GPUs (%d) on the system. Using requested %d GPU(s) (!!!at your own risk!!!).'%(self.n_gpus,self.n_gpus_visible, self.n_gpus))
            #self.n_gpus = self.n_gpus_visible
            self.total_gpu_processors = self.n_gpus * self.n_gpu_proc
        else:
            #total gpu_processors = no.of GPUs * no.of threads per single GPU
            self.total_gpu_processors = self.n_gpus * self.n_gpu_proc
            

        #form a GPU queue first
        gpus=[]
        try:
            import GPUtil
            ngpus=GPUtil.getGPUs()
            gpus=list(range(len(ngpus)))
        except ImportError:
            gpus=list(range(self.n_gpus))

        self.gpu_q={}
        
        #initialize the queue, set all slots free
        slotno=0
        for gpu in range(len(gpus)):
            temp={}
            for ngp in range(self.n_gpu_proc):
                slotno +=1
                temp.update({slotno:'free'})
            self.gpu_q.update({ gpu: temp })
            
            
        # Instantiate different thread pools for non-daemon processes
        logger.debug('MultiProcPlugin starting in "%sdaemon" mode (n_procs=%d, mem_gb=%0.2f', 
                                                                   ' ngpus=%d)',
                     'non' if non_daemon else '', self.processors, self.memory_gb, self.n_gpus)

        NipypePool = NonDaemonPool if non_daemon else Pool
        try:
            self.pool = NipypePool(processes=self.processors,
                                   maxtasksperchild=maxtasks)
        except TypeError:
            self.pool = NipypePool(processes=self.processors)

        self._stats = None


    
    def _async_callback(self, args):
        self._taskresult[args['taskid']] = args

    def _get_result(self, taskid):
        return self._taskresult.get(taskid)

    def _clear_task(self, taskid):
        del self._task_obj[taskid]
        
    
    def gpu_count(self):
        ngpus=1
        try:
           import GPUtil
           return len(GPUtil.getGPUs())
        except ImportError:
           return ngpus

    def gpu_has_free_slots(self,nproc):
        #if a single GPU has enough slots for nproc
        free=False
        devno=None
        slotnos=None

        for dk in self.gpu_q.keys():
            devno=dk
            slotnos=[]
            for sdk in self.gpu_q[dk].keys():
                if self.gpu_q[dk][sdk]=='free':
                    slotnos.append(sdk) 
                    if len(slotnos) == nproc:
                        free=True
                        break
            if free:
                break

        return free,devno,slotnos

    def gpu_has_free_slot(self):
        #if a GPU has free slot, return True,its device-ID and the slot no.
        free=False
        devno=None
        slotno=None
        for dk in self.gpu_q.keys():
            devno=dk
            for sdk in self.gpu_q[dk].keys():
                    if self.gpu_q[dk][sdk]=='free':
                        free=True
                        slotno=sdk
                        break
            if free:
                break

        return free,devno,slotno
       

    def set_gpu_slots_busy(self,slotnos,jobid): 
        #if a GPU has free slots, book all for that single jobid
        devno=None
        
        for dk in self.gpu_q.keys():
            for sk in self.gpu_q[dk].keys():
                for slotno in slotnos:
                    if sk==slotno:
                        devno=dk
                        self.gpu_q[dk][sk]= {'state':'busy','jobid':jobid}
        return devno

    def set_gpu_slot_busy(self,slotno,jobid):
        #if a GPU has free slot, book it for a jobid,modify the queue and set its slotno busy
        devno=None
        for dk in self.gpu_q.keys():
            for sk in self.gpu_q[dk].keys():
                if sk==slotno:
                    devno=dk
                    self.gpu_q[dk][sk]= {'state':'busy','jobid':jobid}
        return devno


    def set_gpu_slot_free(self,jobid):
        #if a GPU task is finished, then set the slotno free in the queue
        devno=None
        for dk in self.gpu_q.keys():
            for sdk in self.gpu_q[dk].keys():
                if isinstance(self.gpu_q[dk][sdk],dict):
                    if self.gpu_q[dk][sdk]['jobid'] == jobid:
                        devno=dk
                        self.gpu_q[dk][sdk]='free'
        return devno

    def set_gpu_slots_free(self,jobid):
        #if a GPU task is finished, then set the slots free in the queue
        devno=None
        for dk in self.gpu_q.keys():
            for sdk in self.gpu_q[dk].keys():
                if isinstance(self.gpu_q[dk][sdk],dict):
                    if self.gpu_q[dk][sdk]['jobid'] == jobid:
                        devno=dk
                        self.gpu_q[dk][sdk]='free'
        return devno

 
    #override, to set gpu slot free, if the job was a gpu job
    def _task_finished_cb(self, jobid, cached=False):
        """ Extract outputs and assign to inputs of dependent tasks

        This is called when a job is completed.
        """
        logger.info('[Job %d] %s (%s).', jobid, 'Cached'
                    if cached else 'Completed', self.procs[jobid])

        if self._status_callback:
            self._status_callback(self.procs[jobid], 'end')
        # Update job and worker queues
        self.proc_pending[jobid] = False
        # update the job dependency structure
        rowview = self.depidx.getrowview(jobid)
        rowview[rowview.nonzero()] = 0
        if jobid not in self.mapnodesubids:
            self.refidx[self.refidx[:, jobid].nonzero()[0], jobid] = 0

        #update queue status
        was_gpu_job = (hasattr(self.procs[jobid]._interface.inputs, 'use_cuda') or \
                          hasattr(self.procs[jobid]._interface.inputs, 'use_gpu'))
        if was_gpu_job:
            if self.procs[jobid].n_procs > 1:
                devid=self.set_gpu_slots_free(jobid)
                if devid is not None:
                    logger.info('GPU Device no %d slots set free from jobid %d' % (devid,jobid) )
            else:
                devid=self.set_gpu_slot_free(jobid)
                if devid is not None:
                    logger.info('GPU Device no %d slot set free from jobid %d' % (devid, jobid) )
                

    def _submit_job(self, node, devno=None, updatehash=False):
        self._taskid += 1

        # Don't allow streaming outputs
        if getattr(node.interface, 'terminal_output', '') == 'stream':
            node.interface.terminal_output = 'allatonce'

        self._task_obj[self._taskid] = self.pool.apply_async(
            run_node, (node, updatehash, self._taskid, devno),
            callback=self._async_callback)

        logger.debug('MultiProc submitted task %s (taskid=%d).',
                     node.fullname, self._taskid)
        return self._taskid

    def _prerun_check(self, graph):
        """Check if any node exeeds the available resources"""
        tasks_mem_gb = []
        tasks_num_th = []
        tasks_gpu_th = []
        
        for node in graph.nodes():
            tasks_mem_gb.append(node.mem_gb)
            tasks_num_th.append(node.n_procs)
            is_gpu_job = (hasattr(node.interface.inputs, 'use_cuda') or \
                          hasattr(node.interface.inputs, 'use_gpu'))
            if is_gpu_job:
                tasks_gpu_th.append(node.n_procs)

        if np.any(np.array(tasks_mem_gb) > self.memory_gb):
            logger.warning(
                'Some nodes exceed the total amount of memory available '
                '(%0.2fGB).', self.memory_gb)
            if self.raise_insufficient:
                raise RuntimeError('Insufficient resources available for job')

        if np.any(np.array(tasks_num_th) > self.processors):
            logger.warning(
                'Some nodes demand for more threads than available (%d).',
                self.processors)
            if self.raise_insufficient:
                raise RuntimeError('Insufficient resources available for job')
                
        if np.any(np.array(tasks_gpu_th) > self.total_gpu_processors):
            logger.warning(
                    'Nodes demand more processes than allowed (%d).',
                    self.total_gpu_processors)
            if self.raise_insufficient:
                raise RuntimeError('Insufficient GPU resources available for job')

    def _postrun_check(self):
        self.pool.close()

    def _check_resources(self, running_tasks):
        """
        Make sure there are resources available
        """
        free_memory_gb = self.memory_gb
        free_processors = self.processors
        free_gpu_slots = self.total_gpu_processors
        
       
        for _, jobid in running_tasks:
            is_gpu_job = (hasattr(self.procs[jobid]._interface.inputs, 'use_cuda') or \
                      hasattr(self.procs[jobid]._interface.inputs, 'use_gpu'))
            if is_gpu_job:
                free_gpu_slots -= min(self.procs[jobid].n_procs, free_gpu_slots)
                
            free_memory_gb -= min(self.procs[jobid].mem_gb, free_memory_gb)
            free_processors -= min(self.procs[jobid].n_procs, free_processors)

        return free_memory_gb, free_processors, free_gpu_slots

    def _send_procs_to_workers(self, updatehash=False, graph=None):
        """
        Sends jobs to workers when system resources are available.
        """

        # Check to see if a job is available (jobs without dependencies not run)
        # See https://github.com/nipy/nipype/pull/2200#discussion_r141605722
        jobids = np.nonzero(~self.proc_done & (self.depidx.sum(0) == 0))[1]

        # Check available system resources by summing all threads and memory used
        free_memory_gb, free_processors, free_gpu_slots = self._check_resources(self.pending_tasks)

        stats = (len(self.pending_tasks), len(jobids), free_memory_gb,
                 self.memory_gb, free_processors, self.processors, free_gpu_slots, self.total_gpu_processors)
        
        if self._stats != stats:
            logger.info('Currently running %d tasks, and %d jobs ready. Free '
                        'memory (GB): %0.2f/%0.2f, Free processors: %d/%d Free GPU slots %d/%d',
                        *stats)
            self._stats = stats

        if free_memory_gb < 0.01 or free_processors == 0:
            logger.debug('No resources available')
            return

        if len(jobids) + len(self.pending_tasks) == 0:
            logger.info('**** ATTENTION ****: No tasks are being run, and no jobs can '
                         'be submitted to the queue. Potential deadlock')
            return

        jobids = self._sort_jobs(jobids, scheduler=self.plugin_args.get('scheduler'))

        # Submit jobs
        for jobid in jobids:
            # First expand mapnodes
            if isinstance(self.procs[jobid], MapNode):
                try:
                    num_subnodes = self.procs[jobid].num_subnodes()
                    logger.info('\n***ATTENTION:%d is a MapNode with %d sub-nodes:%d' % (jobid,num_subnodes))
                except Exception:
                    traceback = format_exception(*sys.exc_info())
                    self._report_crash(self.procs[jobid], traceback=traceback)
                    self._clean_queue(jobid, graph)
                    self.proc_pending[jobid] = False
                    continue
                if num_subnodes > 1:
                    submit = self._submit_mapnode(jobid)
                    if not submit:
                        continue
                
            is_gpu_job = (hasattr(self.procs[jobid]._interface.inputs, 'use_cuda') or \
                          hasattr(self.procs[jobid]._interface.inputs, 'use_gpu'))


            # Check requirements of this job
            next_job_gb = min(self.procs[jobid].mem_gb, self.memory_gb)
            next_job_th = min(self.procs[jobid].n_procs, self.processors)
            next_job_gpu_th = min(self.procs[jobid].n_procs, self.total_gpu_processors)

            is_gpu_free,devno,slotnos = self.gpu_has_free_slots(next_job_gpu_th)

            if is_gpu_job and next_job_gpu_th > len(slotnos):
                logger.debug('Can not allocate slots, insufficient slots for this job %d', jobid)
                continue

            if is_gpu_job and next_job_gpu_th > free_gpu_slots:
                
                logger.debug('Cannot allocate job %d on GPU (%d slots).',
                             jobid, next_job_gpu_th)
                continue
            
            elif not is_gpu_job and next_job_th > free_processors or next_job_gb > free_memory_gb:
                # If node does not fit, skip at this moment
                logger.debug('Cannot allocate job %d (%0.2fGB, %d threads, %d slots).',
                             jobid, next_job_gb, next_job_th, next_job_gpu_th)
                continue

            free_memory_gb -= next_job_gb
            free_processors -= next_job_th
            
            if is_gpu_job:
                
                free_gpu_slots -= next_job_gpu_th
                if next_job_gpu_th > 1:
                    is_gpu_free,devno,slotnos = self.gpu_has_free_slots(next_job_gpu_th)
                    if is_gpu_free and next_job_gpu_th <= len(slotnos):
                        self.set_gpu_slots_busy(slotnos,jobid)
                        logger.info('[*** GPU ID: %d  Running Job: %s Job-ID: %d on multiple slots:%s' %
                           (devno, self.procs[jobid]._id, jobid, slotnos))
                        logger.debug('[*** GPU ID: %d  Running Job: %s Job-ID: %d on multiple slots:%s, Queue State:%s' %
                           (devno, self.procs[jobid]._id, jobid, slotnos, json.dumps(self.gpu_q)))
                else:
                    is_gpu_free,devno,slotno = self.gpu_has_free_slot()
                    if is_gpu_free and slotno is not None:
                        self.set_gpu_slot_busy(slotno,jobid)
                        logger.info('[*** GPU ID: %d  Running Job: %s Job-ID: %d on single slot-ID:%d' %
                            (devno, self.procs[jobid]._id, jobid, slotno))
                        logger.debug('[*** GPU ID: %d  Running Job: %s Job-ID: %d on single slot-ID:%d, Queue State:%s' %
                            (devno, self.procs[jobid]._id, jobid, slotno, json.dumps(self.gpu_q)))
                
                # change job status in appropriate queues
                self.proc_done[jobid] = True
                self.proc_pending[jobid] = True
                
                # If cached just retrieve it, don't run
                if self._local_hash_check(jobid, graph):
                    continue
                
                if self.procs[jobid].run_without_submitting:
                    logger.debug('Running node %s on master thread', self.procs[jobid])
                    try:
                        self.procs[jobid].run()
                    except Exception:
                        traceback = format_exception(*sys.exc_info())
                        self._report_crash(self.procs[jobid], traceback=traceback)
                        
                    # Release resources
                    self._task_finished_cb(jobid)
                    self._remove_node_dirs()
                    free_memory_gb += next_job_gb
                    free_processors += next_job_th
                    free_gpu_slots += next_job_gpu_th
                    
                    # Display stats next loop
                    self._stats = None
                    continue
                
                # Task should be submitted to workers
                # Send job to task manager and add to pending tasks
                if self._status_callback:
                    self._status_callback(self.procs[jobid], 'start')
                tid = self._submit_job(deepcopy(self.procs[jobid]),devno,
                                   updatehash=updatehash)
                    
                if tid is None:
                    self.proc_done[jobid] = False
                    self.proc_pending[jobid] = False
                else:
                    self.pending_tasks.insert(0, (tid, jobid))
                # Display stats next loop
                self._stats = None
            else:
                logger.info('Allocating %s ID=%d (%0.2fGB, %d threads). Free: %0.2fGB, %d threads.',
                         self.procs[jobid].fullname, jobid, next_job_gb, next_job_th,
                         free_memory_gb, free_processors)
                # change job status in appropriate queues
                self.proc_done[jobid] = True
                self.proc_pending[jobid] = True
                
                # If cached just retrieve it, don't run
                if self._local_hash_check(jobid, graph):
                    continue
                
                if self.procs[jobid].run_without_submitting:
                    logger.debug('Running node %s on master thread', self.procs[jobid])
                    try:
                        self.procs[jobid].run()
                    except Exception:
                        traceback = format_exception(*sys.exc_info())
                        self._report_crash(self.procs[jobid], traceback=traceback)
                        
                    # Release resources
                    self._task_finished_cb(jobid)
                    self._remove_node_dirs()
                    free_memory_gb += next_job_gb
                    free_processors += next_job_th
                    free_gpu_slots += next_job_gpu_th
                    
                    # Display stats next loop
                    self._stats = None
                    continue
                
                # Task should be submitted to workers
                # Send job to task manager and add to pending tasks
                if self._status_callback:
                    self._status_callback(self.procs[jobid], 'start')
                tid = self._submit_job(deepcopy(self.procs[jobid]),None,
                                   updatehash=updatehash)
                    
                if tid is None:
                    self.proc_done[jobid] = False
                    self.proc_pending[jobid] = False
                else:
                    self.pending_tasks.insert(0, (tid, jobid))
                # Display stats next loop
                self._stats = None

    def _sort_jobs(self, jobids, scheduler='tsort'):
        if scheduler == 'mem_thread':
            return sorted(jobids, key=lambda item: (
                self.procs[item].mem_gb, self.procs[item].n_procs))
        return jobids
