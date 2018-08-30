# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Testing module for functions and classes from multiproc.py
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, open

# Import packages
import os
import sys
from tempfile import mkdtemp
from shutil import rmtree
import pytest

import nipype.pipeline.engine as pe
from nipype.interfaces.utility import Function


def mytestFunction(insum=0):
    '''
    Run a multiprocessing job and spawn child processes.
    '''

    # need to import here since this is executed as an external process
    import multiprocessing
    import os
    import tempfile
    import time

    numberOfThreads = 2

    # list of processes
    t = [None] * numberOfThreads

    # list of alive flags
    a = [None] * numberOfThreads

    # list of tempFiles
    f = [None] * numberOfThreads

    def dummyFunction(filename):
        '''
        This function writes the value 45 to the given filename.
        '''
        j = 0
        for i in range(0, 10):
            j += i

        # j is now 45 (0+1+2+3+4+5+6+7+8+9)

        with open(filename, 'w') as f:
            f.write(str(j))

    for n in range(numberOfThreads):

        # mark thread as alive
        a[n] = True

        # create a temp file to use as the data exchange container
        tmpFile = tempfile.mkstemp('.txt', 'test_engine_')[1]
        f[n] = tmpFile  # keep track of the temp file
        t[n] = multiprocessing.Process(target=dummyFunction, args=(tmpFile, ))
        # fire up the job
        t[n].start()

    # block until all processes are done
    allDone = False
    while not allDone:

        time.sleep(1)

        for n in range(numberOfThreads):

            a[n] = t[n].is_alive()

        if not any(a):
            # if no thread is alive
            allDone = True

    # here, all processes are done

    # read in all temp files and sum them up
    total = insum
    for ff in f:
        with open(ff) as fd:
            total += int(fd.read())
        os.remove(ff)

    return total


def run_multiproc_nondaemon_with_flag(nondaemon_flag):
    '''
    Start a pipe with two nodes using the resource multiproc plugin and
    passing the nondaemon_flag.
    '''

    cur_dir = os.getcwd()
    temp_dir = mkdtemp(prefix='test_engine_')
    os.chdir(temp_dir)

    pipe = pe.Workflow(name='pipe')

    f1 = pe.Node(
        interface=Function(
            function=mytestFunction,
            input_names=['insum'],
            output_names=['sum_out']),
        name='f1')
    f2 = pe.Node(
        interface=Function(
            function=mytestFunction,
            input_names=['insum'],
            output_names=['sum_out']),
        name='f2')

    pipe.connect([(f1, f2, [('sum_out', 'insum')])])
    pipe.base_dir = os.getcwd()
    f1.inputs.insum = 0

    pipe.config['execution']['stop_on_first_crash'] = True

    # execute the pipe using the LegacyMultiProc plugin with 2 processes and the
    # non_daemon flag to enable child processes which start other
    # multiprocessing jobs
    execgraph = pipe.run(
        plugin="LegacyMultiProc",
        plugin_args={
            'n_procs': 2,
            'non_daemon': nondaemon_flag
        })

    names = [
        '.'.join((node._hierarchy, node.name)) for node in execgraph.nodes()
    ]
    node = list(execgraph.nodes())[names.index('pipe.f2')]
    result = node.get_output('sum_out')
    os.chdir(cur_dir)
    rmtree(temp_dir)
    return result


def test_run_multiproc_nondaemon_false():
    '''
    This is the entry point for the test. Two times a pipe of several
    multiprocessing jobs gets executed. First, without the nondaemon flag.
    Second, with the nondaemon flag.

    Since the processes of the pipe start child processes, the execution only
    succeeds when the non_daemon flag is on.
    '''
    shouldHaveFailed = False
    try:
        # with nondaemon_flag = False, the execution should fail
        run_multiproc_nondaemon_with_flag(False)
    except:
        shouldHaveFailed = True
    assert shouldHaveFailed


def test_run_multiproc_nondaemon_true():
    # with nondaemon_flag = True, the execution should succeed
    result = run_multiproc_nondaemon_with_flag(True)
    assert result == 180  # n_procs (2) * numberOfThreads (2) * 45 == 180
