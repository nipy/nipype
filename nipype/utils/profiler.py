# -*- coding: utf-8 -*-
# @Author: oesteban
# @Date:   2017-09-21 15:50:37
# @Last Modified by:   oesteban
# @Last Modified time: 2017-09-21 16:43:42

try:
    import psutil
except ImportError as exc:
    psutil = None

from .. import config, logging
from .misc import str2bool

proflogger = logging.getLogger('utils')

runtime_profile = str2bool(config.get('execution', 'profile_runtime'))
if runtime_profile and psutil is None:
    proflogger.warn('Switching "profile_runtime" off: the option was on, but the '
                    'necessary package "psutil" could not be imported.')
    runtime_profile = False


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

    try:
        mem_mb = max(mem_mb, _get_ram_mb(pid, pyfunc=pyfunc))
        num_threads = max(num_threads, _get_num_threads(psutil.Process(pid)))
    except Exception as exc:
        proflogger = logging.getLogger('profiler')
        proflogger.info('Could not get resources used by process. Error: %s', exc)

    return mem_mb, num_threads


# Get number of threads for process
def _get_num_threads(proc):
    """
    Function to get the number of threads a process is using

    Parameters
    ----------
    proc : psutil.Process instance
        the process to evaluate thead usage of

    Returns
    -------
    num_threads : int
        the number of threads that the process is using

    """

    # If process is running
    if proc.status() == psutil.STATUS_RUNNING:
        num_threads = proc.num_threads()
    elif proc.num_threads() > 1:
        tprocs = [psutil.Process(thr.id) for thr in proc.threads()]
        alive_tprocs = [tproc for tproc in tprocs if tproc.status() == psutil.STATUS_RUNNING]
        num_threads = len(alive_tprocs)
    else:
        num_threads = 1

    # Try-block for errors
    try:
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
    # Catch any NoSuchProcess errors
    except psutil.NoSuchProcess:
        pass

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

    # Init variables
    _MB = 1024.0**2

    # Try block to protect against any dying processes in the interim
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

    # Catch if process dies, return gracefully
    except psutil.NoSuchProcess:
        pass

    # Return memory
    return mem_mb
