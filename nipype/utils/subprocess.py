# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous utility functions
"""
from __future__ import (print_function, unicode_literals, division,
                        absolute_import)
import os
import sys
import gc
import errno
import threading
from time import time, sleep
from subprocess import Popen
from .filemanip import canonicalize_env

from .. import logging

iflogger = logging.getLogger('nipype.interface')


def run_command(runtime, background=False, output=None, period=0.01,
                callback_fn=None, callback_args=None, callback_kwargs=None):
    r"""
    Run a command in a subprocess, handling output and allowing for
    background processes.

    Parameters
    ----------
    runtime: :class:`~nipype.interfaces.support.Bunch`
        runtime object encapsulating the command line, current working
        directory, environment, etc.
    background: bool
        whether the command line should be waited for, or run in background
        otherwise.
    output: str or None
        accepts the keyword ``stream`` when the command's outputs should
        be also printed out to the terminal.
    period: float
        process polling period (in seconds).
    callback_fn: callable
        a function to be called when the process has terminated.
    callback_args: tuple or None
        positional arguments to be passed over to ``callback_fn()``.
    callback_kwargs: dict or None
        keyword arguments to be passed over to ``callback_fn()``.

    Returns
    -------

    rtmon: :class:`.RuntimeMonitor`
        the runtime monitor thread


    >>> from time import sleep
    >>> from nipype.interfaces.base.support import Bunch
    >>> from nipype.utils.subprocess import run_command
    >>> rt = run_command(Bunch(cmdline='echo hello!',
    ...                  shell=True)).runtime
    >>> rt.returncode
    0
    >>> with open(rt.stdout) as stdout:
    ...     data = stdout.read()
    >>> data
    'hello!\n'
    >>> rt = run_command(Bunch(cmdline='sleep 2', shell=True),
    ...                  background=True).runtime
    >>> rt.returncode is None
    True
    >>> sleep(5)
    >>> rt.returncode
    0

    """

    rtmon = RuntimeMonitor(runtime, output,
                           period=period,
                           callback_fn=callback_fn,
                           callback_args=callback_args,
                           callback_kwargs=callback_kwargs)
    rtmon.start()

    if not background:
        rtmon.join()

    return rtmon


class RuntimeMonitor(threading.Thread):
    """
    A ``Thread`` to monitor a subprocess with a certain polling
    period
    """
    __slots__ = ['_proc', '_output', '_stdoutfh', '_stderrfh', '_runtime',
                 '_callback_fn', '_calback_args', '_callback_kwargs']

    def __init__(self, runtime, output=None, period=0.1,
                 callback_fn=None, callback_args=None, callback_kwargs=None):
        """
        Initialize a self-monitored process.


        Parameters
        ----------
        runtime: :class:`~nipype.interfaces.support.Bunch`
            runtime object encapsulating the command line, current working
            directory, environment, etc.
        output: str or None
            accepts the keyword ``stream`` when the command's outputs should
            be also printed out to the terminal.
        period: float
            process polling period (in seconds).
        callback_fn: callable
            a function to be called when the process has terminated.
        callback_args: tuple or None
            positional arguments to be passed over to ``callback_fn()``.
        callback_kwargs: dict or None
            keyword arguments to be passed over to ``callback_fn()``.


        """
        self._proc = None
        self._output = output
        self._period = period
        self._stdoutfh = None
        self._stderrfh = None
        self._runtime = runtime
        self._runtime.returncode = None
        self._callback_fn = callback_fn
        self._callback_args = callback_args or tuple()
        self._callback_kwargs = callback_kwargs or {}

        cwd = getattr(self._runtime, 'cwd', os.getcwd())
        self._runtime.cwd = cwd
        self._runtime.stdout = getattr(
            self._runtime, 'stdout', os.path.join(cwd, '.nipype.out'))
        self._runtime.stderr = getattr(
            self._runtime, 'stderr', os.path.join(cwd, '.nipype.err'))

        # Open file descriptors and get number
        self._stdoutfh = open(self._runtime.stdout, 'wb')
        self._stderrfh = open(self._runtime.stderr, 'wb')

        # Start thread
        threading.Thread.__init__(self)

    @property
    def runtime(self):
        return self._runtime

    def _update_output(self, tracker=None):
        """When the ``stream`` output is selected, just keeps
        track of the logs backing up the process' outputs and
        sends them to the standard i/o streams"""
        if self._output == 'stream':
            self._stdoutfh.flush()
            self._stderrfh.flush()
            if tracker is None:
                tracker = (0, 0)

            out_size = os.stat(self._runtime.stdout).st_size
            err_size = os.stat(self._runtime.stderr).st_size

            if out_size > tracker[0]:
                data = None
                with open(self._runtime.stdout) as out:
                    out.seek(tracker[0])
                    data = out.read()
                tracker = (out_size, tracker[1])
                if data:
                    print(data)

            if err_size > tracker[1]:
                data = None
                with open(self._runtime.stderr) as err:
                    err.seek(tracker[1])
                    data = err.read()
                tracker = (tracker[0], err_size)
                if data:
                    print(data, file=sys.stderr)
        return tracker

    def run(self):
        """Monitor the process and fill in the runtime object"""

        # Init variables
        cmdline = self._runtime.cmdline
        env = canonicalize_env(
            getattr(self._runtime, 'environ', os.environ))

        tracker = None
        start_time = time()
        self._proc = Popen(
            cmdline,
            stdout=self._stdoutfh.fileno(),
            stderr=self._stderrfh.fileno(),
            shell=getattr(self._runtime, 'shell', False),
            cwd=self._runtime.cwd,
            env=env,
            close_fds=False,
        )
        wait_til = start_time
        while self._proc.returncode is None:
            self._proc.poll()
            tracker = self._update_output(tracker)
            wait_til += self._period
            sleep(max(0, wait_til - time()))
        self._runtime.returncode = self._proc.returncode

        try:
            self._proc.terminate()  # Ensure we are done
        except OSError as error:
            # Python 2 raises when the process is already gone
            if error.errno != errno.ESRCH:
                raise

        # Close open file descriptors
        self._stdoutfh.flush()
        self._stdoutfh.close()
        self._stderrfh.flush()
        self._stderrfh.close()

        # Run callback
        if self._callback_fn and hasattr(self._callback_fn, '__call__'):
            self._callback_fn(*self._callback_args,
                              **self._callback_kwargs)

        # Dereference & force GC for a cleanup
        del self._proc
        gc.collect()
