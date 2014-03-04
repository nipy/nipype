"""Parallel workflow execution via SGE
"""

import os
import re
import subprocess
import time

import xml.dom.minidom

import random

from .base import (SGELikeBatchManagerBase, logger, iflogger, logging)
from nipype.interfaces.base import CommandLine

DEBUGGING_PREFIX = str(int(random.uniform(100, 999)))


def sge_debug_print(message):
    """  Needed for debugging on big jobs.  Once this is fully vetted, it can be removed.
    """
    logger.debug(DEBUGGING_PREFIX + " " + "=!" * 3 + "  " + message)
    # print DEBUGGING_PREFIX + " " + "=!" * 3 + "  " + message


class QJobInfo:

    """Information about a single job created by OGE/SGE or similar
    Each job is responsible for knowing it's own refresh state
    :author Hans J. Johnson
    """

    def __init__(self, jobNum, jobQueueState, jobTime, jobQueueName, jobSlots, qsub_command_line):
        # self._jobName = None           # Ascii text name of job not unique
        self._jobNum = int(
            jobNum)      # The primary unique identifier for this job, must be an integer!
        # self._jobOwn  = None           # Who owns this job
        self._jobQueueState = str(
            jobQueueState)     # ["running","zombie",...??]
        # self._jobActionState = str(jobActionState)  # ['r','qw','S',...??]
        self._jobTime = jobTime               # The job start time
        self._jobInfoCreationTime = time.time(
        )  # When this job was created (for comparing against initalization)
        self._jobQueueName = jobQueueName  # Where the job is running
        self._jobSlots = jobSlots  # How many slots are being used
        self._qsub_command_line = qsub_command_line

    def __repr__(self):
        return str(self._jobNum).ljust(8) \
            + str(self._jobQueueState).ljust(12) \
            + str(self._jobSlots).ljust(3) \
            + time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self._jobTime)).ljust(20) \
            + str(self._jobQueueName).ljust(8) \
            + str(self._qsub_command_line)

    def is_initializing(self):
        return self._jobQueueState == "initializing"

    def is_zombie(self):
        return self._jobQueueState == "zombie"

    def is_running(self):
        return self._jobQueueState == "running"

    def is_pending(self):
        return self._jobQueueState == "pending"

    def is_job_state_pending(self):
        """ Return True, unless job is in the "zombie" status
        """
        time_diff = (time.time() - self._jobInfoCreationTime)
        if self.is_zombie():
            sge_debug_print(
                "DONE! QJobInfo.IsPending found in 'zombie' list, returning False so claiming done!\n{0}".format(self))
            isPendingStatus = False  # Job explicitly found as being completed!
        elif self.is_initializing() and (time_diff > 600):
            # if initializing for more than 5 minute, failure due to
            # initialization and completion before registration
            sge_debug_print(
                "FAILURE! QJobInfo.IsPending found long running at {1} seconds"
                "'initializing' returning False for to break loop!\n{0}".format(self, time_diff))
            isPendingStatus = True  # Job initialization took too long, so report!
        else:  # self.is_running() || self.is_pending():
            isPendingStatus = True  # Job cache last listed as running
        return isPendingStatus  # The job is in one of the hold states

    def update_info(self, jobQueueState, jobTime, jobQueueName, jobSlots):
        self._jobQueueState = jobQueueState
        self._jobTime = jobTime
        self._jobQueueName = jobQueueName
        self._jobSlots = jobSlots

    def set_state(self, new_state):
        self._jobQueueState = new_state


class QstatSubstitute:

    """A wrapper for Qstat to avoid overloading the
    SGE/OGS server with rapid continuous qstat requests"""

    def __init__(self, qstatInstantExecutable='qstat', qstatCachedExecutable='qstat'):
        """
        :param qstatInstantExecutable:
        :param qstatCachedExecutable:
        """
        self._qstatInstantExecutable = qstatInstantExecutable
        self._qstatCachedExecutable = qstatCachedExecutable
        self._OutOfScopeJobs = list()  # Initialize first
        self._task_dictionary = dict(
        )  # {'taskid': QJobInfo(), .... }  The dictionaryObject
        self._remove_old_jobs()

    def _remove_old_jobs(self):
        """ This is only called during initialization of the function for the purpose
        of identifying jobs that are not part of this run of nipype.  They
        are jobs that existed prior to starting a new jobs, so they are irrelevant.
        """
        self._run_qstat("QstatInitialization", True)
                        # If qstat does not exist on this system, then quietly
                        # fail during init

    def add_startup_job(self, taskid, qsub_command_line):
        """
        :param taskid: The job id
        :param scriptFile: When initializing, re-use the jobQueue name
        :return: NONE
        """
        taskid = int(taskid)  # Ensure that it is an integer
        self._task_dictionary[taskid] = QJobInfo(
            taskid, "initializing", time.time(), "noQueue", 1, qsub_command_line)

    def _qacct_verified_complete(self, taskid):
        """ request definitive job completion information for the current job
            from the qacct report
        """
        sge_debug_print(
            "WARNING:  CONTACTING qacct for finished jobs, {0}: {1}".format(time.time(), "Verifying Completion"))

        thisCommand = 'qacct'
        qacct_retries = 10
        isComplete = False
        while qacct_retries > 0:
            qacct_retries -= 1
            try:
                proc = subprocess.Popen(
                    [thisCommand, '-o', os.getlogin(), '-j', str(taskid)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                qacct_result, _ = proc.communicate()
                if qacct_result.find(str(taskid)):
                    isComplete = True
                sge_debug_print(
                    "NOTE: qacct for jobs\n{0}".format(qacct_result))
                break
            except:
                sge_debug_print("NOTE: qacct call failed")
                time.sleep(5)
                pass
        return isComplete

    def _parse_qstat_job_list(self, xml_job_list):
        current_jobs_parsed = list()
        for current_job_element in xml_job_list:
            # jobname = current_job_element.getElementsByTagName('JB_name')[0].childNodes[0].data
            # jobown =
            # current_job_element.getElementsByTagName('JB_owner')[0].childNodes[0].data
            try:
                jobQueueName = current_job_element.getElementsByTagName(
                    'queue_name')[0].childNodes[0].data
            except:
                jobQueueName = "unknown"
            try:
                jobSlots = current_job_element.getElementsByTagName(
                    'slots')[0].childNodes[0].data
            except:
                jobSlots = "uknown"
            jobQueueState = current_job_element.getAttribute('state')
            jobNum = int(current_job_element.getElementsByTagName(
                'JB_job_number')[0].childNodes[0].data)
            try:
                jobtimeText = current_job_element.getElementsByTagName(
                    'JAT_start_time')[0].childNodes[0].data
                jobTime = float(time.mktime(time.strptime(
                    jobtimeText, "%Y-%m-%dT%H:%M:%S")))
            except:
                jobTime = float(0.0)
                # Make job entry

            taskId = int(jobNum)
            if taskId in self._task_dictionary:
                self._task_dictionary[taskId].update_info(
                    jobQueueState, jobTime, jobQueueName, jobSlots)
                sge_debug_print("Updating job:  {0}".format(
                    self._task_dictionary[taskId]))
                current_jobs_parsed.append(jobNum)
            else:
                # Any Job that was not explicitly added with qsub command is
                # out of scope
                self._OutOfScopeJobs.append(int(taskId))

        # To ensure that every job is in the dictionary has a state reported
        # by the SGE environment, it is necessary to explicitly check jobs
        # that are not reported by the qstat command to determine if they
        # were started and finished, and pushed out of the window of review
        # before their state being recorded.  The qacct command is slower, but
        # much more robust for ensuring that a job has completed.
        for dictionary_job in self._task_dictionary.keys():
            if dictionary_job not in current_jobs_parsed:
                is_completed = self._qacct_verified_complete(dictionary_job)
                if is_completed:
                    self._task_dictionary[dictionary_job].set_state("zombie")
                else:
                    sge_debug_print(
                        "ERROR:  Job not in current parselist, and not in done list {0}: {1}".format(
                        dictionary_job, self._task_dictionary[dictionary_job]))
                    pass
            if self._task_dictionary[dictionary_job].is_initializing():
                is_completed = self._qacct_verified_complete(dictionary_job)
                if is_completed:
                    self._task_dictionary[dictionary_job].set_state("zombie")
                else:
                    sge_debug_print(
                        "ERROR:  Job not in still in intializing mode, and not in done list {0}: {1}".format(
                        dictionary_job, self._task_dictionary[dictionary_job]))
                    pass

    def _run_qstat(self, reasonForQstat, forceInstant=True):
        """ request all job information for the current user in xmlformat.
            See documentation from java documentation:
            http://arc.liv.ac.uk/SGE/javadocs/jgdi/com/sun/grid/jgdi/monitoring/filter/JobStateFilter.html
            -s r gives running jobs
            -s z gives recently completed jobs (**recently** is very ambiguous)
            -s s suspended jobs
        """
        sge_debug_print(
            "WARNING:  CONTACTING qmaster for jobs, {0}: {1}".format(time.time(), reasonForQstat))
        if forceInstant:
            thisCommand = self._qstatInstantExecutable
        else:
            thisCommand = self._qstatCachedExecutable

        qstat_retries = 10
        while qstat_retries > 0:
            qstat_retries -= 1
            try:
                proc = subprocess.Popen(
                    [thisCommand, '-u', os.getlogin(), '-xml', '-s', 'psrz'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                qstat_xml_result, _ = proc.communicate()
                dom = xml.dom.minidom.parseString(qstat_xml_result)
                jobs = dom.getElementsByTagName('job_info')
                run = jobs[0]
                runjobs = run.getElementsByTagName('job_list')
                self._parse_qstat_job_list(runjobs)
                break
            except Exception as inst:
                exceptionMessage = "QstatParsingError:\n\t{0}\n\t{1}\n".format(
                    type(
                        inst),     # the exception instance
                    inst           # __str__ allows args to printed directly
                )
                sge_debug_print(exceptionMessage)
                time.sleep(5)
                pass

    def print_dictionary(self):
        """For debugging"""
        for vv in self._task_dictionary.values():
            sge_debug_print(str(vv))

    def is_job_pending(self, taskId, recursionNumber=12):
        taskId = int(taskId)  # Ensure that it is an integer
        self._run_qstat(
            "checking job pending status {0}".format(taskId), False)
        if taskId in self._task_dictionary:
            # Trust the cache, only False if state='zombie'
            jobIsPending = self._task_dictionary[taskId].is_job_state_pending()
        else:
            self._run_qstat(
                "checking job pending status {0}".format(taskId), True)
            if taskId in self._task_dictionary:
                # Trust the cache, only False if state='zombie'
                jobIsPending = self._task_dictionary[
                    taskId].is_job_state_pending()
            else:
                sge_debug_print(
                    "ERROR: Job {0} not in task list, even after forced qstat!".format(taskId))
                jobIsPending = False
        if not jobIsPending:
            sge_debug_print(
                "DONE! Returning for {0} claiming done!".format(taskId))
            if taskId in self._task_dictionary:
                sge_debug_print(
                    "NOTE: Adding {0} to OutOfScopeJobs list!".format(taskId))
                self._OutOfScopeJobs.append(int(taskId))
                self._task_dictionary.pop(taskId)
            else:
                sge_debug_print(
                    "ERROR: Job {0} not in task list, but attempted to be removed!".format(taskId))
        return jobIsPending


def qsub_sanitize_job_name(testjobname):
    """ Ensure that qsub job names must begin with a letter.

    Numbers and punctuation are  not allowed.

    >>> qsub_sanitize_job_name('01')
    'J01'
    >>> qsub_sanitize_job_name('a01')
    'a01'
    """
    if testjobname[0].isalpha():
        return testjobname
    else:
        return 'J' + testjobname


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
        instantQstat = 'qstat'
        cachedQstat = 'qstat'

        if 'plugin_args' in kwargs and kwargs['plugin_args']:
            if 'retry_timeout' in kwargs['plugin_args']:
                self._retry_timeout = kwargs['plugin_args']['retry_timeout']
            if 'max_tries' in kwargs['plugin_args']:
                self._max_tries = kwargs['plugin_args']['max_tries']
            if 'qstatProgramPath' in kwargs['plugin_args']:
                instantQstat = kwargs['plugin_args']['qstatProgramPath']
            if 'qstatCachedProgramPath' in kwargs['plugin_args']:
                cachedQstat = kwargs['plugin_args']['qstatCachedProgramPath']
            self._refQstatSubstitute = QstatSubstitute(
                instantQstat, cachedQstat)

        super(SGEPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        return self._refQstatSubstitute.is_job_pending(int(taskid))

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
        jobname = qsub_sanitize_job_name(jobname)
        cmd.inputs.args = '%s -N %s %s' % (qsubargs,
                                           jobname,
                                           scriptfile)
        oldlevel = iflogger.level
        iflogger.setLevel(logging.getLevelName('CRITICAL'))
        tries = 0
        result = list()
        while True:
            try:
                result = cmd.run()
            except Exception, e:
                if tries < self._max_tries:
                    tries += 1
                    time.sleep(
                        self._retry_timeout)  # sleep 2 seconds and try again.
                else:
                    iflogger.setLevel(oldlevel)
                    raise RuntimeError('\n'.join((('Could not submit sge task'
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
        self._refQstatSubstitute.add_startup_job(taskid, cmd.cmdline)
        logger.debug('submitted sge task: %d for node %s with %s' %
                     (taskid, node._id, cmd.cmdline))
        return taskid
