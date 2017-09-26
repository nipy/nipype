# -*- coding: utf-8 -*-
# @Author: oesteban
# @Date:   2017-09-21 15:50:37
# @Last Modified by:   oesteban
# @Last Modified time: 2017-09-26 15:05:24
"""
Utilities to keep track of performance
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import threading
from time import time
try:
    import psutil
except ImportError as exc:
    psutil = None

from .. import config, logging
from .misc import str2bool
from builtins import open

proflogger = logging.getLogger('utils')

resource_monitor = str2bool(config.get('execution', 'resource_monitor'))
if resource_monitor and psutil is None:
    proflogger.warn('Switching "resource_monitor" off: the option was on, but the '
                    'necessary package "psutil" could not be imported.')
    resource_monitor = False

# Init variables
_MB = 1024.0**2


class ResourceMonitor(threading.Thread):
    def __init__(self, pid, freq=5, fname=None):
        if freq <= 0:
            raise RuntimeError('Frequency (%0.2fs) cannot be lower than zero' % freq)

        if fname is None:
            fname = '.nipype.prof'

        self._pid = pid
        self._fname = fname
        self._freq = freq

        self._log = open(self._fname, 'w')
        print('%s,0.0,0' % time(), file=self._log)
        self._log.flush()
        threading.Thread.__init__(self)
        self._event = threading.Event()

    def stop(self):
        if not self._event.is_set():
            self._event.set()
            self.join()
            self._log.flush()
            self._log.close()

    def run(self):
        while not self._event.is_set():
            ram = _get_ram_mb(self._pid)
            cpus = _get_num_threads(self._pid)
            if ram is not None and cpus is not None:
                print('%s,%f,%d' % (time(), ram, cpus),
                      file=self._log)
                self._log.flush()
            self._event.wait(self._freq)


# Log node stats function
def log_nodes_cb(node, status):
    """Function to record node run statistics to a log file as json
    dictionaries

    Parameters
    ----------
    node : nipype.pipeline.engine.Node
        the node being logged
    status : string
        acceptable values are 'start', 'end'; otherwise it is
        considered and error

    Returns
    -------
    None
        this function does not return any values, it logs the node
        status info to the callback logger
    """

    if status != 'end':
        return

    # Import packages
    import logging
    import json

    status_dict = {
        'name': node.name,
        'id': node._id,
        'start': getattr(node.result.runtime, 'startTime'),
        'finish': getattr(node.result.runtime, 'endTime'),
        'duration': getattr(node.result.runtime, 'duration'),
        'runtime_threads': getattr(
            node.result.runtime, 'nthreads_max', 'N/A'),
        'runtime_memory_gb': getattr(
            node.result.runtime, 'mem_peak_gb', 'N/A'),
        'estimated_memory_gb': node._interface.estimated_memory_gb,
        'num_threads': node._interface.num_threads,
    }

    if status_dict['start'] is None or status_dict['finish'] is None:
        status_dict['error'] = True

    # Dump string to log
    logging.getLogger('callback').debug(json.dumps(status_dict))


# Get total system RAM
def get_system_total_memory_gb():
    """
    Function to get the total RAM of the running system in GB
    """

    # Import packages
    import os
    import sys

    # Get memory
    if 'linux' in sys.platform:
        with open('/proc/meminfo', 'r') as f_in:
            meminfo_lines = f_in.readlines()
            mem_total_line = [line for line in meminfo_lines
                              if 'MemTotal' in line][0]
            mem_total = float(mem_total_line.split()[1])
            memory_gb = mem_total / (1024.0**2)
    elif 'darwin' in sys.platform:
        mem_str = os.popen('sysctl hw.memsize').read().strip().split(' ')[-1]
        memory_gb = float(mem_str) / (1024.0**3)
    else:
        err_msg = 'System platform: %s is not supported'
        raise Exception(err_msg)

    # Return memory
    return memory_gb


# Get max resources used for process
def get_max_resources_used(pid, mem_mb, num_threads, pyfunc=False):
    """
    Function to get the RAM and threads utilized by a given process

    Parameters
    ----------
    pid : integer
        the process ID of process to profile
    mem_mb : float
        the high memory watermark so far during process execution (in MB)
    num_threads: int
        the high thread watermark so far during process execution

    Returns
    -------
    mem_mb : float
        the new high memory watermark of process (MB)
    num_threads : float
        the new high thread watermark of process
    """

    if not resource_monitor:
        raise RuntimeError('Attempted to measure resources with '
                           '"resource_monitor" set off.')

    try:
        mem_mb = max(mem_mb, _get_ram_mb(pid, pyfunc=pyfunc))
        num_threads = max(num_threads, _get_num_threads(pid))
    except Exception as exc:
        proflogger = logging.getLogger('profiler')
        proflogger.info('Could not get resources used by process. Error: %s', exc)

    return mem_mb, num_threads


# Get number of threads for process
def _get_num_threads(pid):
    """
    Function to get the number of threads a process is using

    Parameters
    ----------
    pid : integer
        the process ID of process to profile

    Returns
    -------
    num_threads : int
        the number of threads that the process is using

    """

    try:
        proc = psutil.Process(pid)
        # If process is running
        if proc.status() == psutil.STATUS_RUNNING:
            num_threads = proc.num_threads()
        elif proc.num_threads() > 1:
            tprocs = [psutil.Process(thr.id) for thr in proc.threads()]
            alive_tprocs = [tproc for tproc in tprocs if tproc.status() == psutil.STATUS_RUNNING]
            num_threads = len(alive_tprocs)
        else:
            num_threads = 1

        child_threads = 0
        # Iterate through child processes and get number of their threads
        for child in proc.children(recursive=True):
            # Leaf process
            if len(child.children()) == 0:
                # If process is running, get its number of threads
                if child.status() == psutil.STATUS_RUNNING:
                    child_thr = child.num_threads()
                # If its not necessarily running, but still multi-threaded
                elif child.num_threads() > 1:
                    # Cast each thread as a process and check for only running
                    tprocs = [psutil.Process(thr.id) for thr in child.threads()]
                    alive_tprocs = [tproc for tproc in tprocs
                                    if tproc.status() == psutil.STATUS_RUNNING]
                    child_thr = len(alive_tprocs)
                # Otherwise, no threads are running
                else:
                    child_thr = 0
                # Increment child threads
                child_threads += child_thr
    except psutil.NoSuchProcess:
        return None

    # Number of threads is max between found active children and parent
    num_threads = max(child_threads, num_threads)

    # Return number of threads found
    return num_threads


# Get ram usage of process
def _get_ram_mb(pid, pyfunc=False):
    """
    Function to get the RAM usage of a process and its children
    Reference: http://ftp.dev411.com/t/python/python-list/095thexx8g/\
multiprocessing-forking-memory-usage

    Parameters
    ----------
    pid : integer
        the PID of the process to get RAM usage of
    pyfunc : boolean (optional); default=False
        a flag to indicate if the process is a python function;
        when Pythons are multithreaded via multiprocess or threading,
        children functions include their own memory + parents. if this
        is set, the parent memory will removed from children memories


    Returns
    -------
    mem_mb : float
        the memory RAM in MB utilized by the process PID

    """
    try:
        # Init parent
        parent = psutil.Process(pid)
        # Get memory of parent
        parent_mem = parent.memory_info().rss
        mem_mb = parent_mem / _MB
        # Iterate through child processes
        for child in parent.children(recursive=True):
            child_mem = child.memory_info().rss
            if pyfunc:
                child_mem -= parent_mem
            mem_mb += child_mem / _MB
    except psutil.NoSuchProcess:
        return None

    # Return memory
    return mem_mb
