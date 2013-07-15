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
    if False:
        print DEBUGGING_PREFIX + " " + "=!" * 3 + "  " + message
        pass
    else:
        pass


class QJobInfo:
    """Information about a single job created by OGE/SGE or similar
    Each job is responsible for knowing it's own refresh state
    :author Hans J. Johnson
    """

    def __init__(self, jobNum, jobQueueState, jobTime, jobQueueName, jobSlots):
        #self._jobName = None           # Ascii text name of job not unique
        self._jobNum = int(jobNum)      # The primary unique identifier for this job, must be an integer!
        #self._jobOwn  = None           # Who owns this job
        self._jobQueueState = str(jobQueueState)     # ["running","zombie",...??]
        #self._jobActionState = str(jobActionState)  # ['r','qw','S',...??]
        self._jobTime = float(jobTime)               # The job start time
        self._currentRefreshTime = 1                 # How much time should elaspe before refreshing state?
        self._jobLastCheckTime = time.time()   # When was this job last checked by qstat
        #self._jobSubmissionTime = None # When the job was submitted
        self._jobQueueName = jobQueueName  ## Where the job is running
        self._jobSlots = jobSlots          ## How many slots are being used

    def isInitializing(self):
        return ( self._jobQueueState == "initializing" )

    def isZombie(self):
        return ( self._jobQueueState == "zombie" )

    def getJobLastCheckTime(self):
        return self._jobLastCheckTime

    def updateLastCheckTime(self):
        self._jobLastCheckTime = time.time()

    def NeedsRefreshCheck(self):
        timeSinceCheck = time.time() - self.getJobLastCheckTime()
        if timeSinceCheck < self._currentRefreshTime:
            #sge_debug_print("Job {0} last checked {1} < {2} seconds ago".format(self._jobNum , timeSinceCheck,self._currentRefreshTime) )
            return False
        else:
            self._currentRefreshTime = min(self._currentRefreshTime * 2,
                                           30) # Never wait more than 30 seconds to refresh
            return True

    def isJobStateFinished(self):
        """ Return True, unless job is in the "zombie" status
        """
        if self._jobQueueState == "running":
            #Job is not pending!
            return True  # Job cache last listed as running
        if self._jobQueueState == "zombie":
            sge_debug_print(
                "DONE! QJobInfo.IsPending found in 'zombie' list, returning False for {0}claiming done!".format(self))
            return False # Job explicitly found as being completed!
        if self._jobQueueState == "initializing" and (time.time() - self._jobTime > 300):
            ## if initializing for more than 5 minute, failure
            sge_debug_print(
                "FAILURE! QJobInfo.IsPending found long running 'initializing' returning False for {0} to break loop!".format(
                    self))
            return False # Job initialization took too long, so failing!
        return True## The job is in one of the hold states

    def updateInfo(self, jobQueueState, jobTime, jobQueueName, jobSlots):
        self._jobQueueState = jobQueueState
        self._jobTime = jobTime
        self._jobQueueName = jobQueueName
        self._jobSlots = jobSlots

    def __repr__(self):
        return str(self._jobNum).ljust(12) \
               + str(self._jobQueueState).ljust(12) \
               + time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self._jobTime)).ljust(20) \
               + str(self._jobSlots).ljust(3) \
               + str(self._jobQueueName).ljust(40)


class QstatSubstitute:
    """A wrapper for Qstat to avoid overloading the
    SGE/OGS server with rapid continuous qstat requests"""

    def __init__(self, qstatInstantExecutable='qstat', qstatCachedExecutable='qstat'):
        self._qstatInstantExecutable = qstatInstantExecutable
        self._qstatCachedExecutable = qstatCachedExecutable
        self._taskDictionary = dict() # {'taskid': QJobInfo(), .... }  The dictionaryObject can be a m
        self._NonZombieJobs = 0
        self._OutOfScopeJobs = list() # Initialize first
        try:
            self._runQstat("QstatInitialization",True) #If qstat does not exist on this system, then quietly fail during init
        except:
            pass
        self._RemoveOldJobs() # _OutOfScopeJobs are created by different processes, and are not relevant here

    def _RemoveOldJobs(self):
        """ This is only called during initialization of the function for the purpose
        of identifying jobs that are not part of this run of nipype.  They
        are jobs that existed prior to starting a new jobs, so they are irrelevant.
        """
        self._OutOfScopeJobs = list()
        for item in self._taskDictionary.items():
            if not item[1].isInitializing():
                self._taskDictionary.pop(item[0])
                #sge_debug_print("---Removing {0}: TotalSize {1}".format(item, len(self._taskDictionary)))
                self._OutOfScopeJobs.append(item[0])
            else:
                #sge_debug_print("+++Keeping {0}: TotalSize {1}".format(item,len(self._taskDictionary)))
                pass

    def AddStartupJob(self, taskid, scriptFile, jobs):
        """
        :param taskid: The job id
        :param scriptFile: When initializing, re-use the jobQueue name
        :param jobs: Just set to 1 for this case since it is initializing.
        :return: NONE
        """
        taskid = int(taskid) ## Ensure that it is an integer
        self._taskDictionary[taskid] = QJobInfo(taskid, "initializing", time.time(), scriptFile, jobs)

    def AddJob(self, jobNum, jobQueueState, jobTime, jobQueueName, jobSlots):
        taskId = int(jobNum)
        if taskId in self._taskDictionary:
            self._taskDictionary[taskId].updateInfo(jobQueueState, jobTime, jobQueueName, jobSlots)
            #sge_debug_print("Updating job:  {0}".format(self._taskDictionary[taskId]) )
        else:
            qjb = QJobInfo(taskId, jobQueueState, jobTime, jobQueueName, jobSlots)
            sge_debug_print("Adding job:  {0}".format(qjb))
            self._taskDictionary[taskId] = qjb

    def _parseQstatJobList(self, xml_job_list):
        self._NonZombieJobs = 0
        for current_job_element in xml_job_list:
            #jobname = current_job_element.getElementsByTagName('JB_name')[0].childNodes[0].data
            #jobown = current_job_element.getElementsByTagName('JB_owner')[0].childNodes[0].data
            try:
                jobQueueName = current_job_element.getElementsByTagName('queue_name')[0].childNodes[0].data
            except:
                jobQueueName = "unknown"
            try:
                jobSlots = current_job_element.getElementsByTagName('slots')[0].childNodes[0].data
            except:
                jobSlots = "uknown"
            jobQueueState = current_job_element.getAttribute('state')
            if jobQueueState != 'zombie':
                self._NonZombieJobs += 1
                #jobActionState = current_job_element.getElementsByTagName('state')[0].childNodes[0].data
            jobNum = int(current_job_element.getElementsByTagName('JB_job_number')[0].childNodes[0].data)
            try:
                jobtimeText = current_job_element.getElementsByTagName('JAT_start_time')[0].childNodes[0].data
                jobTime = float(time.mktime(time.strptime(jobtimeText, "%Y-%m-%dT%H:%M:%S")))
            except:
                jobTime = float(0.0)
                ## Make job entry
            if jobNum not in self._OutOfScopeJobs:
                self.AddJob(jobNum, jobQueueState, jobTime, jobQueueName, jobSlots)
            else:
                #sge_debug_print("Skipping out of scope job {0}".format(jobNum))
                pass

    def _runQstat(self, reasonForQstat, forceInstant = True):
        """ request all job information for the current user in xmlformat.
            See documentation from java documentation:
            http://arc.liv.ac.uk/SGE/javadocs/jgdi/com/sun/grid/jgdi/monitoring/filter/JobStateFilter.html
            -s r gives running jobs
            -s z gives recently completed jobs (**recently** is very ambiguous)
            -s s suspended jobs
        """
        sge_debug_print(
            "WARNING:  CONTACTING qmaster for jobs, SPAMMING SYSTEM {0}: {1}".format(time.time(), reasonForQstat))
        if forceInstant:
            thisCommand = self._qstatInstantExecutable
        else:
            thisCommand = self._qstatCachedExecutable

        proc = subprocess.Popen([thisCommand, '-u', os.getlogin(), '-xml', '-s', 'hazr'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        qstat_xml_result, _ = proc.communicate()
        dom = xml.dom.minidom.parseString(qstat_xml_result)
        jobs = dom.getElementsByTagName('job_info')
        run = jobs[0]
        runjobs = run.getElementsByTagName('job_list')
        self._parseQstatJobList(runjobs)

    def printDictionary(self):
        """For debugging"""
        for vv in self._taskDictionary.values():
            sge_debug_print(str(vv))


    def isJobPending(self, taskId, recursionNumber=12):
        taskId = int(taskId) ## Ensure that it is an integer
        if taskId in self._taskDictionary and not self._taskDictionary[taskId].NeedsRefreshCheck():
            return True
        self._runQstat("checking job pending status {0}".format(taskId),False)
        if taskId in self._taskDictionary:
            jobIsPending = self._taskDictionary[
                taskId].isJobStateFinished() # Trust the cache, only False if state='zombie'
            self._taskDictionary[taskId].updateLastCheckTime()
        else:
            self._runQstat("checking job pending status {0}".format(taskId),True)
            sge_debug_print(
                "Job {0} not in task list, sleeping 10 seconds, then double checking completion {1} more times".format(
                    taskId, recursionNumber))
            if recursionNumber > 0:
                time.sleep(15)
                # NOTE: qstat may have a delay between when a job is submitted, and when it is visible, and this
                #       results in a race condition, if a job finishes so fast, and it also does not persist as a zombie
                #       because of too many completed tasks, then wait 'awhile' and check again.
                jobIsPending = self.isJobPending(taskId, recursionNumber - 1)
                # NOTE: if not in cache list, then force re-reading cache several times before giving up done
            else:
                sge_debug_print("ERROR: Job {0} not in task list, even after 100 seconds!".format(taskId))
                jobIsPending = False
        if jobIsPending == False:
            sge_debug_print("DONE! Returning False for {0} claiming done!".format(taskId))
            if taskId in self._taskDictionary:
                if self._taskDictionary[taskId].isZombie():
                    sge_debug_print("NOTE: Adding {0} to OutOfScopeJobs list!".format(taskId))
                    self._OutOfScopeJobs.append(taskId)
                self._taskDictionary.pop(taskId)
            else:
                sge_debug_print("ERROR: Job {0} not in task list, but attempted to be removed!".format(taskId))
        return jobIsPending


def qsubSanitizeJobName(testjobname):
    """ Ensure that qsub job names must begin with a letter.

    Numbers and punctuation are  not allowed.

    >>> qsubSanitizeJobName('01')
    'J01'
    >>> qsubSanitizeJobName('a01')
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
                cachedQstat=kwargs['plugin_args']['qstatCachedProgramPath']
            self._refQstatSubstitute = QstatSubstitute(instantQstat,cachedQstat)
            
        super(SGEPlugin, self).__init__(template, **kwargs)

    def _is_pending(self, taskid):
        return self._refQstatSubstitute.isJobPending(int(taskid))

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
        jobname = qsubSanitizeJobName(jobname)
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
                    time.sleep(self._retry_timeout)  # sleep 2 seconds and try again.
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
        self._refQstatSubstitute.AddStartupJob(taskid, scriptfile, 1)
        logger.debug('submitted sge task: %d for node %s with %s' % (taskid, node._id, cmd.cmdline))
        return taskid
