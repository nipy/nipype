# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Utilities to keep track of performance
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import threading
from time import time
try:
    import psutil
except ImportError as exc:
    psutil = None

from builtins import open, range
from .. import config, logging

proflogger = logging.getLogger('nipype.utils')
resource_monitor = config.resource_monitor

# Init variables
_MB = 1024.0**2


class ResourceMonitor(threading.Thread):
    """
    A ``Thread`` to monitor a specific PID with a certain frequence
    to a file
    """

    def __init__(self, pid, freq=5, fname=None, python=True):
        # Make sure psutil is imported
        import psutil

        if freq < 0.2:
            raise RuntimeError(
                'Frequency (%0.2fs) cannot be lower than 0.2s' % freq)

        if fname is None:
            fname = '.proc-%d_time-%s_freq-%0.2f' % (pid, time(), freq)
        self._fname = fname
        self._logfile = open(self._fname, 'w')
        self._freq = freq
        self._python = python

        # Leave process initialized and make first sample
        self._process = psutil.Process(pid)
        self._sample(cpu_interval=0.2)

        # Start thread
        threading.Thread.__init__(self)
        self._event = threading.Event()

    @property
    def fname(self):
        """Get/set the internal filename"""
        return self._fname

    def stop(self):
        """Stop monitoring"""
        if not self._event.is_set():
            self._event.set()
            self.join()
            self._sample()
            self._logfile.flush()
            self._logfile.close()

    def _sample(self, cpu_interval=None):
        cpu = 0.0
        rss = 0.0
        vms = 0.0
        try:
            with self._process.oneshot():
                cpu += self._process.cpu_percent(interval=cpu_interval)
                mem_info = self._process.memory_info()
                rss += mem_info.rss
                vms += mem_info.vms
        except psutil.NoSuchProcess:
            pass

        # Iterate through child processes and get number of their threads
        try:
            children = self._process.children(recursive=True)
        except psutil.NoSuchProcess:
            children = []

        for child in children:
            try:
                with child.oneshot():
                    cpu += child.cpu_percent()
                    mem_info = child.memory_info()
                    rss += mem_info.rss
                    vms += mem_info.vms
            except psutil.NoSuchProcess:
                pass

        print(
            '%f,%f,%f,%f' % (time(), cpu, rss / _MB, vms / _MB),
            file=self._logfile)
        self._logfile.flush()

    def run(self):
        """Core monitoring function, called by start()"""
        start_time = time()
        wait_til = start_time
        while not self._event.is_set():
            self._sample()
            wait_til += self._freq
            self._event.wait(max(0, wait_til - time()))


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
        'runtime_threads': getattr(node.result.runtime, 'cpu_percent', 'N/A'),
        'runtime_memory_gb': getattr(node.result.runtime, 'mem_peak_gb',
                                     'N/A'),
        'estimated_memory_gb': node.mem_gb,
        'num_threads': node.n_procs,
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
            mem_total_line = [
                line for line in meminfo_lines if 'MemTotal' in line
            ][0]
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
        raise RuntimeError('Attempted to measure resources with option '
                           '"monitoring.enabled" set off.')

    try:
        mem_mb = max(mem_mb, _get_ram_mb(pid, pyfunc=pyfunc))
        num_threads = max(num_threads, _get_num_threads(pid))
    except Exception as exc:
        proflogger.info('Could not get resources used by process.\n%s', exc)

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
            alive_tprocs = [
                tproc for tproc in tprocs
                if tproc.status() == psutil.STATUS_RUNNING
            ]
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
                    tprocs = [
                        psutil.Process(thr.id) for thr in child.threads()
                    ]
                    alive_tprocs = [
                        tproc for tproc in tprocs
                        if tproc.status() == psutil.STATUS_RUNNING
                    ]
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


def _use_cpu(x):
    ctr = 0
    while ctr < 1e7:
        ctr += 1
        x * x


# Spin multiple threads
def _use_resources(n_procs, mem_gb):
    """
    Function to execute multiple use_gb_ram functions in parallel
    """
    import os
    import sys
    import psutil
    from multiprocessing import Pool
    from nipype import logging
    from nipype.utils.profiler import _use_cpu

    iflogger = logging.getLogger('nipype.interface')

    # Getsize of one character string
    BSIZE = sys.getsizeof('  ') - sys.getsizeof(' ')
    BOFFSET = sys.getsizeof('')
    _GB = 1024.0**3

    def _use_gb_ram(mem_gb):
        """A test function to consume mem_gb GB of RAM"""
        num_bytes = int(mem_gb * _GB)
        # Eat mem_gb GB of memory for 1 second
        gb_str = ' ' * ((num_bytes - BOFFSET) // BSIZE)
        assert sys.getsizeof(gb_str) == num_bytes
        return gb_str

    # Measure the amount of memory this process already holds
    p = psutil.Process(os.getpid())
    mem_offset = p.memory_info().rss / _GB
    big_str = _use_gb_ram(mem_gb - mem_offset)
    _use_cpu(5)
    mem_total = p.memory_info().rss / _GB
    del big_str
    iflogger.info('[%d] Memory offset %0.2fGB, total %0.2fGB', os.getpid(),
                  mem_offset, mem_total)

    if n_procs > 1:
        pool = Pool(n_procs)
        pool.map(_use_cpu, range(n_procs))
    return True
