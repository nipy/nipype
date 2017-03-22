# -*- coding: utf-8 -*-
# test_runtime_profiler.py
#
# Author: Daniel Clark, 2016

"""
Module to unit test the runtime_profiler in nipype
"""

from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import open, str

# Import packages
from nipype.interfaces.base import (traits, CommandLine, CommandLineInputSpec,
                                    runtime_profile)
import pytest
import sys

run_profile = runtime_profile

if run_profile:
    try:
        import psutil
        skip_profile_msg = 'Run profiler tests'
    except ImportError as exc:
        skip_profile_msg = 'Missing python packages for runtime profiling, skipping...\n'\
                           'Error: %s' % exc
        run_profile = False
else:
    skip_profile_msg = 'Not running profiler'

# UseResources inputspec
class UseResourcesInputSpec(CommandLineInputSpec):
    '''
    use_resources cmd interface inputspec
    '''

    # Init attributes
    num_gb = traits.Float(desc='Number of GB of RAM to use',
                          argstr='-g %f')
    num_threads = traits.Int(desc='Number of threads to use',
                          argstr='-p %d')


# UseResources interface
class UseResources(CommandLine):
    '''
    use_resources cmd interface
    '''

    # Import packages
    import os

    # Init attributes
    input_spec = UseResourcesInputSpec

    # Get path of executable
    exec_dir = os.path.dirname(os.path.realpath(__file__))
    exec_path = os.path.join(exec_dir, 'use_resources')

    # Init cmd
    _cmd = exec_path


# Spin multiple threads
def use_resources(num_threads, num_gb):
    '''
    Function to execute multiple use_gb_ram functions in parallel
    '''

    # Function to occupy GB of memory
    def _use_gb_ram(num_gb):
        '''
        Function to consume GB of memory
        '''
        import sys

        # Getsize of one character string
        bsize = sys.getsizeof('  ') - sys.getsizeof(' ')
        boffset = sys.getsizeof('')

        num_bytes = int(num_gb * (1024**3))
        # Eat num_gb GB of memory for 1 second
        gb_str = ' ' * ((num_bytes - boffset) // bsize)

        assert sys.getsizeof(gb_str) == num_bytes

        # Spin CPU
        ctr = 0
        while ctr < 30e6:
            ctr += 1

        # Clear memory
        del ctr
        del gb_str

    # Import packages
    from multiprocessing import Process
    from threading import Thread

    # Init variables
    num_gb = float(num_gb)

    # Build thread list
    thread_list = []
    for idx in range(num_threads):
        thread = Thread(target=_use_gb_ram, args=(num_gb/num_threads,),
                        name=str(idx))
        thread_list.append(thread)

    # Run multi-threaded
    print('Using %.3f GB of memory over %d sub-threads...' % \
          (num_gb, num_threads))
    for idx, thread in enumerate(thread_list):
        thread.start()

    for thread in thread_list:
        thread.join()


# Test case for the run function
class TestRuntimeProfiler():
    '''
    This class is a test case for the runtime profiler
    '''

    # setup method for the necessary arguments to run cpac_pipeline.run
    def setup_class(self):
        '''
        Method to instantiate TestRuntimeProfiler

        Parameters
        ----------
        self : TestRuntimeProfile
        '''

        # Init parameters
        # Input RAM GB to occupy
        self.num_gb = 1.0
        # Input number of sub-threads (not including parent threads)
        self.num_threads = 2
        # Acceptable percent error for memory profiled against input
        self.mem_err_gb = 0.3  # Increased to 30% for py2.7

    # ! Only used for benchmarking the profiler over a range of
    # ! RAM usage and number of threads
    # ! Requires a LOT of RAM to be tested
    def _collect_range_runtime_stats(self, num_threads):
        '''
        Function to collect a range of runtime stats
        '''

        # Import packages
        import json
        import numpy as np
        import pandas as pd

        # Init variables
        ram_gb_range = 10.0
        ram_gb_step = 0.25
        dict_list = []

        # Iterate through all combos
        for num_gb in np.arange(0.25, ram_gb_range+ram_gb_step, ram_gb_step):
            # Cmd-level
            cmd_start_str, cmd_fin_str = self._run_cmdline_workflow(num_gb, num_threads)
            cmd_start_ts = json.loads(cmd_start_str)['start']
            cmd_node_stats = json.loads(cmd_fin_str)
            cmd_runtime_threads = int(cmd_node_stats['runtime_threads'])
            cmd_runtime_gb = float(cmd_node_stats['runtime_memory_gb'])
            cmd_finish_ts = cmd_node_stats['finish']

            # Func-level
            func_start_str, func_fin_str = self._run_function_workflow(num_gb, num_threads)
            func_start_ts = json.loads(func_start_str)['start']
            func_node_stats = json.loads(func_fin_str)
            func_runtime_threads = int(func_node_stats['runtime_threads'])
            func_runtime_gb = float(func_node_stats['runtime_memory_gb'])
            func_finish_ts = func_node_stats['finish']

            # Calc errors
            cmd_threads_err = cmd_runtime_threads - num_threads
            cmd_gb_err = cmd_runtime_gb - num_gb
            func_threads_err = func_runtime_threads - num_threads
            func_gb_err = func_runtime_gb - num_gb

            # Node dictionary
            results_dict = {'input_threads' : num_threads,
                            'input_gb' : num_gb,
                            'cmd_runtime_threads' : cmd_runtime_threads,
                            'cmd_runtime_gb' : cmd_runtime_gb,
                            'func_runtime_threads' : func_runtime_threads,
                            'func_runtime_gb' : func_runtime_gb,
                            'cmd_threads_err' : cmd_threads_err,
                            'cmd_gb_err' : cmd_gb_err,
                            'func_threads_err' : func_threads_err,
                            'func_gb_err' : func_gb_err,
                            'cmd_start_ts' : cmd_start_ts,
                            'cmd_finish_ts' : cmd_finish_ts,
                            'func_start_ts' : func_start_ts,
                            'func_finish_ts' : func_finish_ts}
            # Append to list
            dict_list.append(results_dict)

        # Create dataframe
        runtime_results_df = pd.DataFrame(dict_list)

        # Return dataframe
        return runtime_results_df

    # Test node
    def _run_cmdline_workflow(self, num_gb, num_threads):
        '''
        Function to run the use_resources cmdline script in a nipype workflow
        and return the runtime stats recorded by the profiler

        Parameters
        ----------
        self : TestRuntimeProfile

        Returns
        -------
        finish_str : string
            a json-compatible dictionary string containing the runtime
            statistics of the nipype node that used system resources
        '''

        # Import packages
        import logging
        import os
        import shutil
        import tempfile

        import nipype.pipeline.engine as pe
        import nipype.interfaces.utility as util
        from nipype.pipeline.plugins.callback_log import log_nodes_cb

        # Init variables
        base_dir = tempfile.mkdtemp()
        log_file = os.path.join(base_dir, 'callback.log')

        # Init logger
        logger = logging.getLogger('callback')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)

        # Declare workflow
        wf = pe.Workflow(name='test_runtime_prof_cmd')
        wf.base_dir = base_dir

        # Input node
        input_node = pe.Node(util.IdentityInterface(fields=['num_gb',
                                                            'num_threads']),
                             name='input_node')
        input_node.inputs.num_gb = num_gb
        input_node.inputs.num_threads = num_threads

        # Resources used node
        resource_node = pe.Node(UseResources(), name='resource_node')
        resource_node.interface.estimated_memory_gb = num_gb
        resource_node.interface.num_threads = num_threads

        # Connect workflow
        wf.connect(input_node, 'num_gb', resource_node, 'num_gb')
        wf.connect(input_node, 'num_threads', resource_node, 'num_threads')

        # Run workflow
        plugin_args = {'n_procs' : num_threads,
                       'memory_gb' : num_gb,
                       'status_callback' : log_nodes_cb}
        wf.run(plugin='MultiProc', plugin_args=plugin_args)

        # Get runtime stats from log file
        with open(log_file, 'r') as log_handle:
            lines = log_handle.readlines()
            start_str = lines[0].rstrip('\n')
            finish_str = lines[1].rstrip('\n')

        # Delete wf base dir
        shutil.rmtree(base_dir)

        # Return runtime stats
        return start_str, finish_str

    # Test node
    def _run_function_workflow(self, num_gb, num_threads):
        '''
        Function to run the use_resources() function in a nipype workflow
        and return the runtime stats recorded by the profiler

        Parameters
        ----------
        self : TestRuntimeProfile

        Returns
        -------
        finish_str : string
            a json-compatible dictionary string containing the runtime
            statistics of the nipype node that used system resources
        '''

        # Import packages
        import logging
        import os
        import shutil
        import tempfile

        import nipype.pipeline.engine as pe
        import nipype.interfaces.utility as util
        from nipype.pipeline.plugins.callback_log import log_nodes_cb

        # Init variables
        base_dir = tempfile.mkdtemp()
        log_file = os.path.join(base_dir, 'callback.log')

        # Init logger
        logger = logging.getLogger('callback')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)

        # Declare workflow
        wf = pe.Workflow(name='test_runtime_prof_func')
        wf.base_dir = base_dir

        # Input node
        input_node = pe.Node(util.IdentityInterface(fields=['num_gb',
                                                            'num_threads']),
                             name='input_node')
        input_node.inputs.num_gb = num_gb
        input_node.inputs.num_threads = num_threads

        # Resources used node
        resource_node = pe.Node(util.Function(input_names=['num_threads',
                                                           'num_gb'],
                                              output_names=[],
                                              function=use_resources),
                                name='resource_node')
        resource_node.interface.estimated_memory_gb = num_gb
        resource_node.interface.num_threads = num_threads

        # Connect workflow
        wf.connect(input_node, 'num_gb', resource_node, 'num_gb')
        wf.connect(input_node, 'num_threads', resource_node, 'num_threads')

        # Run workflow
        plugin_args = {'n_procs' : num_threads,
                       'memory_gb' : num_gb,
                       'status_callback' : log_nodes_cb}
        wf.run(plugin='MultiProc', plugin_args=plugin_args)

        # Get runtime stats from log file
        with open(log_file, 'r') as log_handle:
            lines = log_handle.readlines()
            start_str = lines[0].rstrip('\n')
            finish_str = lines[1].rstrip('\n')

        # Delete wf base dir
        shutil.rmtree(base_dir)

        # Return runtime stats
        return start_str, finish_str

    # Test resources were used as expected in cmdline interface
    @pytest.mark.skipif(run_profile == False, reason=skip_profile_msg)
    def test_cmdline_profiling(self):
        '''
        Test runtime profiler correctly records workflow RAM/CPUs consumption
        from a cmdline function
        '''

        # Import packages
        import json
        import numpy as np

        # Init variables
        num_gb = self.num_gb
        num_threads = self.num_threads

        # Run workflow and get stats
        start_str, finish_str = self._run_cmdline_workflow(num_gb, num_threads)
        # Get runtime stats as dictionary
        node_stats = json.loads(finish_str)

        # Read out runtime stats
        runtime_gb = float(node_stats['runtime_memory_gb'])
        runtime_threads = int(node_stats['runtime_threads'])

        # Get margin of error for RAM GB
        allowed_gb_err = self.mem_err_gb
        runtime_gb_err = np.abs(runtime_gb-num_gb)
        #
        expected_runtime_threads = num_threads

        # Error message formatting
        mem_err = 'Input memory: %f is not within %.3f GB of runtime '\
                  'memory: %f' % (num_gb, self.mem_err_gb, runtime_gb)
        threads_err = 'Input threads: %d is not equal to runtime threads: %d' \
                    % (expected_runtime_threads, runtime_threads)

        # Assert runtime stats are what was input
        assert runtime_gb_err <= allowed_gb_err, mem_err
        assert abs(expected_runtime_threads - runtime_threads) <= 1, threads_err

    # Test resources were used as expected
    @pytest.mark.skipif(True, reason="https://github.com/nipy/nipype/issues/1663")
    @pytest.mark.skipif(run_profile == False, reason=skip_profile_msg)
    def test_function_profiling(self):
        '''
        Test runtime profiler correctly records workflow RAM/CPUs consumption
        from a python function
        '''

        # Import packages
        import json
        import numpy as np

        # Init variables
        num_gb = self.num_gb
        num_threads = self.num_threads

        # Run workflow and get stats
        start_str, finish_str = self._run_function_workflow(num_gb, num_threads)
        # Get runtime stats as dictionary
        node_stats = json.loads(finish_str)

        # Read out runtime stats
        runtime_gb = float(node_stats['runtime_memory_gb'])
        runtime_threads = int(node_stats['runtime_threads'])

        # Get margin of error for RAM GB
        allowed_gb_err = self.mem_err_gb
        runtime_gb_err = np.abs(runtime_gb-num_gb)
        #
        expected_runtime_threads = num_threads

        # Error message formatting
        mem_err = 'Input memory: %f is not within %.3f GB of runtime '\
                  'memory: %f' % (num_gb, self.mem_err_gb, runtime_gb)
        threads_err = 'Input threads: %d is not equal to runtime threads: %d' \
                    % (expected_runtime_threads, runtime_threads)

        # Assert runtime stats are what was input
        assert runtime_gb_err <= allowed_gb_err, mem_err
        assert abs(expected_runtime_threads - runtime_threads) <= 1, threads_err


