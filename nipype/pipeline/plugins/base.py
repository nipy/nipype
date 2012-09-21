# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Common graph operations for execution
"""

from copy import deepcopy
from glob import glob
import os
import pwd
import shutil
from socket import gethostname
import sys
from time import strftime, sleep, time
from traceback import format_exception, format_exc
from warnings import warn

import numpy as np
import scipy.sparse as ssp

from ..utils import (nx, dfs_preorder)
from ..engine import (MapNode, str2bool)

from nipype.utils.filemanip import savepkl, loadpkl
from nipype.interfaces.utility import Function


from ... import logging
logger = logging.getLogger('workflow')
iflogger = logging.getLogger('interface')


def report_crash(node, traceback=None, hostname=None):
    """Writes crash related information to a file
    """
    name = node._id
    if node.result and hasattr(node.result, 'runtime') and \
            node.result.runtime:
        if isinstance(node.result.runtime, list):
            host = node.result.runtime[0].hostname
        else:
            host = node.result.runtime.hostname
    else:
        if hostname:
            host = hostname
        else:
            host = gethostname()
    message = ['Node %s failed to run on host %s.' % (name,
                                                      host)]
    logger.error(message)
    if not traceback:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback = format_exception(exc_type,
                                     exc_value,
                                     exc_traceback)
    timeofcrash = strftime('%Y%m%d-%H%M%S')
    login_name = pwd.getpwuid(os.geteuid())[0]
    crashfile = 'crash-%s-%s-%s.npz' % (timeofcrash,
                                        login_name,
                                        name)
    crashdir = node.config['execution']['crashdump_dir']
    if crashdir is None:
        crashdir = os.getcwd()
    if not os.path.exists(crashdir):
        os.makedirs(crashdir)
    crashfile = os.path.join(crashdir, crashfile)
    logger.info('Saving crash info to %s' % crashfile)
    logger.info(''.join(traceback))
    np.savez(crashfile, node=node, traceback=traceback)
    return crashfile


def report_nodes_not_run(notrun):
    """List nodes that crashed with crashfile info

    Optionally displays dependent nodes that weren't executed as a result of
    the crash.
    """
    if notrun:
        logger.info("***********************************")
        for info in notrun:
            logger.error("could not run node: %s" %
                         '.'.join((info['node']._hierarchy,
                                   info['node']._id)))
            logger.info("crashfile: %s" % info['crashfile'])
            logger.debug("The following dependent nodes were not run")
            for subnode in info['dependents']:
                logger.debug(subnode._id)
        logger.info("***********************************")
        raise RuntimeError(('Workflow did not execute cleanly. '
                            'Check log for details'))


def create_pyscript(node, updatehash=False, store_exception=True):
    # pickle node
    timestamp = strftime('%Y%m%d_%H%M%S')
    if node._hierarchy:
        suffix = '%s_%s_%s' % (timestamp, node._hierarchy, node._id)
        batch_dir = os.path.join(node.base_dir,
                                 node._hierarchy.split('.')[0],
                                 'batch')
    else:
        suffix = '%s_%s' % (timestamp, node._id)
        batch_dir = os.path.join(node.base_dir, 'batch')
    if not os.path.exists(batch_dir):
        os.makedirs(batch_dir)
    pkl_file = os.path.join(batch_dir, 'node_%s.pklz' % suffix)
    savepkl(pkl_file, dict(node=node, updatehash=updatehash))
    # create python script to load and trap exception
    cmdstr = """import os
import sys
from socket import gethostname
from traceback import format_exception
info = None
pklfile = '%s'
batchdir = '%s'
try:
    from nipype import config, logging
    import sys
    if not sys.version_info < (2, 7):
        from ordereddict import OrderedDict
    config_dict=%s
    config.update_config(config_dict)
    config.update_matplotlib()
    logging.update_logging(config)
    from nipype.utils.filemanip import loadpkl, savepkl
    traceback=None
    cwd = os.getcwd()
    info = loadpkl(pklfile)
    result = info['node'].run(updatehash=info['updatehash'])
except Exception, e:
    etype, eval, etr = sys.exc_info()
    traceback = format_exception(etype,eval,etr)
    if info is None:
        result = None
        resultsfile = os.path.join(batchdir, 'crashdump_%s.pklz')
    else:
        result = info['node'].result
        resultsfile = os.path.join(info['node'].output_dir(),
                               'result_%%s.pklz'%%info['node'].name)
"""
    if store_exception:
        cmdstr += """
    savepkl(resultsfile, dict(result=result, hostname=gethostname(),
                              traceback=traceback))
"""
    else:
        cmdstr += """
    if info is None:
        savepkl(resultsfile, dict(result=result, hostname=gethostname(),
                              traceback=traceback))
    else:
        from nipype.pipeline.plugins.base import report_crash
        report_crash(info['node'], traceback, gethostname())
    raise Exception(e)
"""
    cmdstr = cmdstr % (pkl_file, batch_dir, node.config, suffix)
    pyscript = os.path.join(batch_dir, 'pyscript_%s.py' % suffix)
    fp = open(pyscript, 'wt')
    fp.writelines(cmdstr)
    fp.close()
    return pyscript


class PluginBase(object):
    """Base class for plugins"""

    def __init__(self, plugin_args=None):
        if plugin_args and 'status_callback' in plugin_args:
            self._status_callback = plugin_args['status_callback']
        else:
            self._status_callback = None
        return

    def run(self, graph, config, updatehash=False):
        raise NotImplementedError


class DistributedPluginBase(PluginBase):
    """Execute workflow with a distribution engine
    """

    def __init__(self, plugin_args=None):
        """Initialize runtime attributes to none

        procs: list (N) of underlying interface elements to be processed
        proc_done: a boolean vector (N) signifying whether a process has been
            executed
        proc_pending: a boolean vector (N) signifying whether a
            process is currently running. Note: A process is finished only when
            both proc_done==True and
        proc_pending==False
        depidx: a boolean matrix (NxN) storing the dependency structure accross
            processes. Process dependencies are derived from each column.
        """
        super(DistributedPluginBase, self).__init__(plugin_args=plugin_args)
        self.procs = None
        self.depidx = None
        self.refidx = None
        self.mapnodes = None
        self.mapnodesubids = None
        self.proc_done = None
        self.proc_pending = None
        self.max_jobs = np.inf
        if plugin_args and 'max_jobs' in plugin_args:
            self.max_jobs = plugin_args['max_jobs']

    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline using distributed approaches
        """
        logger.info("Running in parallel.")
        self._config = config
        # Generate appropriate structures for worker-manager model
        self._generate_dependency_list(graph)
        self.pending_tasks = []
        self.readytorun = []
        self.mapnodes = []
        self.mapnodesubids = {}
        # setup polling - TODO: change to threaded model
        notrun = []
        while np.any(self.proc_done == False) | \
              np.any(self.proc_pending == True):
            toappend = []
            # trigger callbacks for any pending results
            while self.pending_tasks:
                taskid, jobid = self.pending_tasks.pop()
                try:
                    result = self._get_result(taskid)
                    if result:
                        if result['traceback']:
                            notrun.append(self._clean_queue(jobid, graph,
                                                            result=result))
                        else:
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                        self._clear_task(taskid)
                    else:
                        toappend.insert(0, (taskid, jobid))
                except Exception:
                    result = {'result': None,
                              'traceback': format_exc()}
                    notrun.append(self._clean_queue(jobid, graph,
                                                    result=result))
            if toappend:
                self.pending_tasks.extend(toappend)
            num_jobs = len(self.pending_tasks)
            if num_jobs < self.max_jobs:
                if np.isinf(self.max_jobs):
                    slots = None
                else:
                    slots = self.max_jobs - num_jobs
                self._send_procs_to_workers(updatehash=updatehash,
                                            slots=slots, graph=graph)
            sleep(2)
        self._remove_node_dirs()
        report_nodes_not_run(notrun)

    def _get_result(self, taskid):
        raise NotImplementedError

    def _submit_job(self, node, updatehash=False):
        raise NotImplementedError

    def _report_crash(self, node, result=None):
        raise NotImplementedError

    def _clear_task(self, taskid):
        raise NotImplementedError

    def _clean_queue(self, jobid, graph, result=None):
        if str2bool(self._config['execution']['stop_on_first_crash']):
            raise RuntimeError("".join(result['traceback']))
        crashfile = self._report_crash(self.procs[jobid],
                                       result=result)
        if self._status_callback:
            self._status_callback(self.procs[jobid], 'exception')
        if jobid in self.mapnodesubids:
            # remove current jobid
            self.proc_pending[jobid] = False
            self.proc_done[jobid] = True
            # remove parent mapnode
            jobid = self.mapnodesubids[jobid]
            self.proc_pending[jobid] = False
            self.proc_done[jobid] = True
        # remove dependencies from queue
        return self._remove_node_deps(jobid, crashfile, graph)

    def _submit_mapnode(self, jobid):
        if jobid in self.mapnodes:
            return True
        self.mapnodes.append(jobid)
        mapnodesubids = self.procs[jobid].get_subnodes()
        numnodes = len(mapnodesubids)
        logger.info('Adding %d jobs for mapnode %s' % (numnodes,
                                                       self.procs[jobid]._id))
        for i in range(numnodes):
            self.mapnodesubids[self.depidx.shape[0] + i] = jobid
        self.procs.extend(mapnodesubids)
        self.depidx = ssp.vstack((self.depidx,
                                  ssp.lil_matrix(np.zeros((numnodes,
                                                    self.depidx.shape[1])))),
                                 'lil')
        self.depidx = ssp.hstack((self.depidx,
                                  ssp.lil_matrix(np.zeros((self.depidx.shape[0],
                                                           numnodes)))),
                                 'lil')
        self.depidx[-numnodes:, jobid] = 1
        self.proc_done = np.concatenate((self.proc_done,
                                         np.zeros(numnodes, dtype=bool)))
        self.proc_pending = np.concatenate((self.proc_pending,
                                            np.zeros(numnodes, dtype=bool)))
        return False

    def _send_procs_to_workers(self, updatehash=False, slots=None, graph=None):
        """ Sends jobs to workers using ipython's taskclient interface
        """
        while np.any(self.proc_done == False):
            # Check to see if a job is available
            jobids = np.flatnonzero((self.proc_done == False) & \
                                    (self.depidx.sum(axis=0) == 0).__array__())
            if len(jobids) > 0:
                # send all available jobs
                logger.info('Submitting %d jobs' % len(jobids))
                for jobid in jobids[:slots]:
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
                    # change job status in appropriate queues
                    self.proc_done[jobid] = True
                    self.proc_pending[jobid] = True
                    # Send job to task manager and add to pending tasks
                    logger.info('Executing: %s ID: %d' % \
                                    (self.procs[jobid]._id, jobid))
                    if self._status_callback:
                        self._status_callback(self.procs[jobid], 'start')
                    continue_with_submission = True
                    if str2bool(self.procs[jobid].config['execution']['local_hash_check']):
                        logger.debug('checking hash locally')
                        try:
                            hash_exists, _, _, _ = self.procs[jobid].hash_exists()
                            logger.debug('Hash exists %s' % str(hash_exists))
                            if (hash_exists and
                            (self.procs[jobid].overwrite == False or
                             (self.procs[jobid].overwrite == None and
                              not self.procs[jobid]._interface.always_run))):
                                continue_with_submission = False
                                self._task_finished_cb(jobid)
                                self._remove_node_dirs()
                        except Exception:
                            self._clean_queue(jobid, graph)
                            self.proc_pending[jobid] = False
                            continue_with_submission = False
                    logger.debug('Finished checking hash %s' %
                                 str(continue_with_submission))
                    if continue_with_submission:
                        if self.procs[jobid].run_without_submitting:
                            logger.debug('Running node %s on master thread' %
                                         self.procs[jobid])
                            try:
                                self.procs[jobid].run()
                            except Exception:
                                self._clean_queue(jobid, graph)
                            self._task_finished_cb(jobid)
                            self._remove_node_dirs()
                        else:
                            tid = self._submit_job(deepcopy(self.procs[jobid]),
                                                   updatehash=updatehash)
                            if tid is None:
                                self.proc_done[jobid] = False
                                self.proc_pending[jobid] = False
                            else:
                                self.pending_tasks.insert(0, (tid, jobid))
            else:
                break

    def _task_finished_cb(self, jobid):
        """ Extract outputs and assign to inputs of dependent tasks

        This is called when a job is completed.
        """
        logger.info('[Job finished] jobname: %s jobid: %d' % \
                    (self.procs[jobid]._id, jobid))
        if self._status_callback:
            self._status_callback(self.procs[jobid], 'end')
        # Update job and worker queues
        self.proc_pending[jobid] = False
        # update the job dependency structure
        rowview = self.depidx.getrowview(jobid)
        rowview[rowview.nonzero()] = 0
        if jobid not in self.mapnodesubids:
            self.refidx[self.refidx[:, jobid].nonzero()[0], jobid] = 0

    def _generate_dependency_list(self, graph):
        """ Generates a dependency list for a list of graphs.
        """
        self.procs = graph.nodes()
        try:
            self.depidx = nx.to_scipy_sparse_matrix(graph, format='lil')
        except:
            self.depidx = nx.to_scipy_sparse_matrix(graph)
        self.refidx = deepcopy(self.depidx)
        self.refidx.astype = np.int
        self.proc_done = np.zeros(len(self.procs), dtype=bool)
        self.proc_pending = np.zeros(len(self.procs), dtype=bool)

    def _remove_node_deps(self, jobid, crashfile, graph):
        subnodes = [s for s in dfs_preorder(graph, self.procs[jobid])]
        for node in subnodes:
            idx = self.procs.index(node)
            self.proc_done[idx] = True
            self.proc_pending[idx] = False
        return dict(node=self.procs[jobid],
                    dependents=subnodes,
                    crashfile=crashfile)

    def _remove_node_dirs(self):
        """Removes directories whose outputs have already been used up
        """
        if str2bool(self._config['execution']['remove_node_directories']):
            for idx in np.nonzero((self.refidx.sum(axis=1) == 0).__array__())[0]:
                if idx in self.mapnodesubids:
                    continue
                if self.proc_done[idx] and (not self.proc_pending[idx]):
                    self.refidx[idx, idx] = -1
                    outdir = self.procs[idx]._output_directory()
                    logger.info(('[node dependencies finished] '
                                 'removing node: %s from directory %s') % \
                                (self.procs[idx]._id, outdir))
                    shutil.rmtree(outdir)


class SGELikeBatchManagerBase(DistributedPluginBase):
    """Execute workflow with SGE/OGE/PBS like batch system
    """

    def __init__(self, template, plugin_args=None):
        super(SGELikeBatchManagerBase, self).__init__(plugin_args=plugin_args)
        self._template = template
        self._qsub_args = None
        if plugin_args:
            if 'template' in plugin_args:
                self._template = plugin_args['template']
                if os.path.isfile(self._template):
                    self._template = open(self._template).read()
            if 'qsub_args' in plugin_args:
                self._qsub_args = plugin_args['qsub_args']
        self._pending = {}

    def _is_pending(self, taskid):
        """Check if a task is pending in the batch system
        """
        raise NotImplementedError

    def _submit_batchtask(self, scriptfile, node):
        """Submit a task to the batch system
        """
        raise NotImplementedError

    def _get_result(self, taskid):
        if taskid not in self._pending:
            raise Exception('Task %d not found' % taskid)
        if self._is_pending(taskid):
            return None
        node_dir = self._pending[taskid]
        # MIT HACK
        # on the pbs system at mit the parent node directory needs to be
        # accessed before internal directories become available. there
        # is a disconnect when the queueing engine knows a job is
        # finished to when the directories become statable.
        t = time()
        timeout = float(self._config['execution']['job_finished_timeout'])
        timed_out = True
        while (time() - t) < timeout:
            try:
                logger.debug(os.listdir(os.path.realpath(os.path.join(node_dir,
                                                                      '..'))))
                logger.debug(os.listdir(node_dir))
                glob(os.path.join(node_dir, 'result_*.pklz')).pop()
                timed_out = False
                break
            except Exception, e:
                logger.debug(e)
            sleep(2)
        if timed_out:
            result_data = {'hostname': 'unknown',
                           'result': None,
                           'traceback': None}
            results_file = None
            try:
                raise IOError(('Job (%s) finished or terminated, but results file '
                               'does not exist. Batch dir contains crashdump '
                               'file if node raised an exception' % node_dir))
            except IOError, e:
                result_data['traceback'] = format_exc()
        else:
            results_file = glob(os.path.join(node_dir, 'result_*.pklz'))[0]
            result_data = loadpkl(results_file)
        result_out = dict(result=None, traceback=None)
        if isinstance(result_data, dict):
            result_out['result'] = result_data['result']
            result_out['traceback'] = result_data['traceback']
            result_out['hostname'] = result_data['hostname']
            if results_file:
                crash_file = os.path.join(node_dir, 'crashstore.pklz')
                os.rename(results_file, crash_file)
        else:
            result_out['result'] = result_data
        return result_out

    def _submit_job(self, node, updatehash=False):
        """submit job and return taskid
        """
        pyscript = create_pyscript(node, updatehash=updatehash)
        batch_dir, name = os.path.split(pyscript)
        name = '.'.join(name.split('.')[:-1])
        batchscript = '\n'.join((self._template,
                                 '%s %s' % (sys.executable, pyscript)))
        batchscriptfile = os.path.join(batch_dir, 'batchscript_%s.sh' % name)
        fp = open(batchscriptfile, 'wt')
        fp.writelines(batchscript)
        fp.close()
        return self._submit_batchtask(batchscriptfile, node)

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


class GraphPluginBase(PluginBase):
    """Base class for plugins that distribute graphs to workflows
    """

    def __init__(self, plugin_args=None):
        if plugin_args and 'status_callback' in plugin_args:
            warn('status_callback not supported for Graph submission plugins')
        super(GraphPluginBase, self).__init__(plugin_args=plugin_args)

    def run(self, graph, config, updatehash=False):
        pyfiles = []
        dependencies = {}
        self._config = config
        nodes = nx.topological_sort(graph)
        logger.debug('Creating executable python files for each node')
        for idx, node in enumerate(nodes):
            pyfiles.append(create_pyscript(node,
                                           updatehash=updatehash,
                                           store_exception=False))
            dependencies[idx] = [nodes.index(prevnode) for prevnode in
                                 graph.predecessors(node)]
        self._submit_graph(pyfiles, dependencies)

    def _submit_graph(self, pyfiles, dependencies):
        """
        pyfiles: list of files corresponding to a topological sort
        dependencies: dictionary of dependencies based on the toplogical sort
        """
        raise NotImplementedError
