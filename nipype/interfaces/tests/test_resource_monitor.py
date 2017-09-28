# -*- coding: utf-8 -*-
# test_profiler.py
#
# Author: Daniel Clark, 2016

"""
Module to unit test the resource_monitor in nipype
"""

from __future__ import print_function, division, unicode_literals, absolute_import
import os
import pytest

# Import packages
from nipype.utils.profiler import resource_monitor as run_profile, _use_resources
from nipype.interfaces.base import traits, CommandLine, CommandLineInputSpec
from nipype.interfaces import utility as niu


# UseResources inputspec
class UseResourcesInputSpec(CommandLineInputSpec):
    mem_gb = traits.Float(desc='Number of GB of RAM to use',
                          argstr='-g %f', mandatory=True)
    n_procs = traits.Int(desc='Number of threads to use',
                         argstr='-p %d', mandatory=True)


# UseResources interface
class UseResources(CommandLine):
    '''
    use_resources cmd interface
    '''
    from nipype import __path__
    # Init attributes
    input_spec = UseResourcesInputSpec

    # Get path of executable
    exec_dir = os.path.realpath(__path__[0])
    exec_path = os.path.join(exec_dir, 'utils', 'tests', 'use_resources')

    # Init cmd
    _cmd = exec_path


# Test resources were used as expected in cmdline interface
# @pytest.mark.skipif(run_profile is False, reason='resources monitor is disabled')
@pytest.mark.skipif(True, reason='test disabled temporarily')
@pytest.mark.parametrize("mem_gb,n_procs", [(0.5, 3), (2.2, 2), (0.8, 4)])
def test_cmdline_profiling(tmpdir, mem_gb, n_procs):
    '''
    Test runtime profiler correctly records workflow RAM/CPUs consumption
    of a CommandLine-derived interface
    '''
    from nipype import config
    config.set('execution', 'resource_monitor_frequency', '0.2')  # Force sampling fast

    tmpdir.chdir()
    iface = UseResources(mem_gb=mem_gb, n_procs=n_procs)
    result = iface.run()

    assert abs(mem_gb - result.runtime.mem_peak_gb) < 0.3, 'estimated memory error above .3GB'
    assert result.runtime.nthreads_max == n_procs, 'wrong number of threads estimated'


# @pytest.mark.skipif(run_profile is False, reason='resources monitor is disabled')
@pytest.mark.skipif(True, reason='test disabled temporarily')
@pytest.mark.parametrize("mem_gb,n_procs", [(0.5, 3), (2.2, 2), (0.8, 4)])
def test_function_profiling(tmpdir, mem_gb, n_procs):
    '''
    Test runtime profiler correctly records workflow RAM/CPUs consumption
    of a Function interface
    '''
    from nipype import config
    config.set('execution', 'resource_monitor_frequency', '0.2')  # Force sampling fast

    tmpdir.chdir()
    iface = niu.Function(function=_use_resources)
    iface.inputs.mem_gb = mem_gb
    iface.inputs.n_procs = n_procs
    result = iface.run()

    assert abs(mem_gb - result.runtime.mem_peak_gb) < 0.3, 'estimated memory error above .3GB'
    assert result.runtime.nthreads_max == n_procs, 'wrong number of threads estimated'


# # Test case for the run function
# class TestRuntimeProfiler():
#     '''
#     This class is a test case for the runtime profiler
#     '''

#     # setup method for the necessary arguments to run cpac_pipeline.run
#     def setup_class(self):
#         '''
#         Method to instantiate TestRuntimeProfiler

#         Parameters
#         ----------
#         self : TestRuntimeProfile
#         '''

#         # Init parameters
#         # Input RAM GB to occupy
#         self.mem_gb = 1.0
#         # Input number of sub-threads (not including parent threads)
#         self.n_procs = 2
#         # Acceptable percent error for memory profiled against input
#         self.mem_err_gb = 0.3  # Increased to 30% for py2.7

#     # ! Only used for benchmarking the profiler over a range of
#     # ! RAM usage and number of threads
#     # ! Requires a LOT of RAM to be tested
#     def _collect_range_runtime_stats(self, n_procs):
#         '''
#         Function to collect a range of runtime stats
#         '''

#         # Import packages
#         import json
#         import numpy as np
#         import pandas as pd

#         # Init variables
#         ram_gb_range = 10.0
#         ram_gb_step = 0.25
#         dict_list = []

#         # Iterate through all combos
#         for mem_gb in np.arange(0.25, ram_gb_range+ram_gb_step, ram_gb_step):
#             # Cmd-level
#             cmd_node_str = self._run_cmdline_workflow(mem_gb, n_procs)
#             cmd_node_stats = json.loads(cmd_node_str)
#             cmd_start_ts = cmd_node_stats['start']
#             cmd_runtime_threads = int(cmd_node_stats['runtime_threads'])
#             cmd_runtime_gb = float(cmd_node_stats['runtime_memory_gb'])
#             cmd_finish_ts = cmd_node_stats['finish']

#             # Func-level
#             func_node_str = self._run_function_workflow(mem_gb, n_procs)
#             func_node_stats = json.loads(func_node_str)
#             func_start_ts = func_node_stats['start']
#             func_runtime_threads = int(func_node_stats['runtime_threads'])
#             func_runtime_gb = float(func_node_stats['runtime_memory_gb'])
#             func_finish_ts = func_node_stats['finish']

#             # Calc errors
#             cmd_threads_err = cmd_runtime_threads - n_procs
#             cmd_gb_err = cmd_runtime_gb - mem_gb
#             func_threads_err = func_runtime_threads - n_procs
#             func_gb_err = func_runtime_gb - mem_gb

#             # Node dictionary
#             results_dict = {'input_threads': n_procs,
#                             'input_gb': mem_gb,
#                             'cmd_runtime_threads': cmd_runtime_threads,
#                             'cmd_runtime_gb': cmd_runtime_gb,
#                             'func_runtime_threads': func_runtime_threads,
#                             'func_runtime_gb': func_runtime_gb,
#                             'cmd_threads_err': cmd_threads_err,
#                             'cmd_gb_err': cmd_gb_err,
#                             'func_threads_err': func_threads_err,
#                             'func_gb_err': func_gb_err,
#                             'cmd_start_ts': cmd_start_ts,
#                             'cmd_finish_ts': cmd_finish_ts,
#                             'func_start_ts': func_start_ts,
#                             'func_finish_ts': func_finish_ts}
#             # Append to list
#             dict_list.append(results_dict)

#         # Create dataframe
#         runtime_results_df = pd.DataFrame(dict_list)

#         # Return dataframe
#         return runtime_results_df

#     # Test node
#     def _run_cmdline_workflow(self, mem_gb, n_procs):
#         '''
#         Function to run the use_resources cmdline script in a nipype workflow
#         and return the runtime stats recorded by the profiler

#         Parameters
#         ----------
#         self : TestRuntimeProfile

#         Returns
#         -------
#         finish_str : string
#             a json-compatible dictionary string containing the runtime
#             statistics of the nipype node that used system resources
#         '''

#         # Import packages
#         import logging
#         import os
#         import shutil
#         import tempfile

#         import nipype.pipeline.engine as pe
#         import nipype.interfaces.utility as util
#         from nipype.utils.profiler import log_nodes_cb

#         # Init variables
#         base_dir = tempfile.mkdtemp()
#         log_file = os.path.join(base_dir, 'callback.log')

#         # Init logger
#         logger = logging.getLogger('callback')
#         logger.propagate = False
#         logger.setLevel(logging.DEBUG)
#         handler = logging.FileHandler(log_file)
#         logger.addHandler(handler)

#         # Declare workflow
#         wf = pe.Workflow(name='test_runtime_prof_cmd')
#         wf.base_dir = base_dir

#         # Input node
#         input_node = pe.Node(util.IdentityInterface(fields=['mem_gb',
#                                                             'n_procs']),
#                              name='input_node')

#         # Resources used node
#         resource_node = pe.Node(UseResources(), name='resource_node', mem_gb=mem_gb,
#                                 n_procs=n_procs)

#         # Connect workflow
#         wf.connect(input_node, 'mem_gb', resource_node, 'mem_gb')
#         wf.connect(input_node, 'n_procs', resource_node, 'n_procs')

#         # Run workflow
#         plugin_args = {'n_procs': n_procs,
#                        'memory_gb': mem_gb,
#                        'status_callback': log_nodes_cb}
#         wf.run(plugin='MultiProc', plugin_args=plugin_args)

#         # Get runtime stats from log file
#         with open(log_file, 'r') as log_handle:
#             lines = log_handle.readlines()

#         node_str = lines[0].rstrip('\n')

#         # Delete wf base dir
#         shutil.rmtree(base_dir)

#         # Return runtime stats
#         return node_str

#     # Test node
#     def _run_function_workflow(self, mem_gb, n_procs):
#         '''
#         Function to run the use_resources() function in a nipype workflow
#         and return the runtime stats recorded by the profiler

#         Parameters
#         ----------
#         self : TestRuntimeProfile

#         Returns
#         -------
#         finish_str : string
#             a json-compatible dictionary string containing the runtime
#             statistics of the nipype node that used system resources
#         '''

#         # Import packages
#         import logging
#         import os
#         import shutil
#         import tempfile

#         import nipype.pipeline.engine as pe
#         import nipype.interfaces.utility as util
#         from nipype.utils.profiler import log_nodes_cb

#         # Init variables
#         base_dir = tempfile.mkdtemp()
#         log_file = os.path.join(base_dir, 'callback.log')

#         # Init logger
#         logger = logging.getLogger('callback')
#         logger.propagate = False
#         logger.setLevel(logging.DEBUG)
#         handler = logging.FileHandler(log_file)
#         logger.addHandler(handler)

#         # Declare workflow
#         wf = pe.Workflow(name='test_runtime_prof_func')
#         wf.base_dir = base_dir

#         # Input node
#         input_node = pe.Node(util.IdentityInterface(fields=['mem_gb',
#                                                             'n_procs']),
#                              name='input_node')
#         input_node.inputs.mem_gb = mem_gb
#         input_node.inputs.n_procs = n_procs

#         # Resources used node
#         resource_node = pe.Node(util.Function(input_names=['n_procs',
#                                                            'mem_gb'],
#                                               output_names=[],
#                                               function=use_resources),
#                                 name='resource_node',
#                                 mem_gb=mem_gb,
#                                 n_procs=n_procs)

#         # Connect workflow
#         wf.connect(input_node, 'mem_gb', resource_node, 'mem_gb')
#         wf.connect(input_node, 'n_procs', resource_node, 'n_procs')

#         # Run workflow
#         plugin_args = {'n_procs': n_procs,
#                        'memory_gb': mem_gb,
#                        'status_callback': log_nodes_cb}
#         wf.run(plugin='MultiProc', plugin_args=plugin_args)

#         # Get runtime stats from log file
#         with open(log_file, 'r') as log_handle:
#             lines = log_handle.readlines()

#         # Delete wf base dir
#         shutil.rmtree(base_dir)

#         # Return runtime stats
#         return lines[0].rstrip('\n')

#     # Test resources were used as expected in cmdline interface
#     @pytest.mark.skipif(run_profile is False, reason='resources monitor is disabled')
#     def test_cmdline_profiling(self):
#         '''
#         Test runtime profiler correctly records workflow RAM/CPUs consumption
#         from a cmdline function
#         '''

#         # Import packages
#         import json
#         import numpy as np

#         # Init variables
#         mem_gb = self.mem_gb
#         n_procs = self.n_procs

#         # Run workflow and get stats
#         node_str = self._run_cmdline_workflow(mem_gb, n_procs)
#         # Get runtime stats as dictionary
#         node_stats = json.loads(node_str)

#         # Read out runtime stats
#         runtime_gb = float(node_stats['runtime_memory_gb'])
#         runtime_threads = int(node_stats['runtime_threads'])

#         # Get margin of error for RAM GB
#         allowed_gb_err = self.mem_err_gb
#         runtime_gb_err = np.abs(runtime_gb-mem_gb)
#         #
#         expected_runtime_threads = n_procs

#         # Error message formatting
#         mem_err = 'Input memory: %f is not within %.3f GB of runtime '\
#                   'memory: %f' % (mem_gb, self.mem_err_gb, runtime_gb)
#         threads_err = 'Input threads: %d is not equal to runtime threads: %d' \
#                     % (expected_runtime_threads, runtime_threads)

#         # Assert runtime stats are what was input
#         assert runtime_gb_err <= allowed_gb_err, mem_err
#         assert abs(expected_runtime_threads - runtime_threads) <= 1, threads_err

#     # Test resources were used as expected
#     # @pytest.mark.skipif(True, reason="https://github.com/nipy/nipype/issues/1663")
#     @pytest.mark.skipif(run_profile is False, reason='resources monitor is disabled')
#     def test_function_profiling(self):
#         '''
#         Test runtime profiler correctly records workflow RAM/CPUs consumption
#         from a python function
#         '''

#         # Import packages
#         import json
#         import numpy as np

#         # Init variables
#         mem_gb = self.mem_gb
#         n_procs = self.n_procs

#         # Run workflow and get stats
#         node_str = self._run_function_workflow(mem_gb, n_procs)
#         # Get runtime stats as dictionary
#         node_stats = json.loads(node_str)

#         # Read out runtime stats
#         runtime_gb = float(node_stats['runtime_memory_gb'])
#         runtime_threads = int(node_stats['runtime_threads'])

#         # Get margin of error for RAM GB
#         allowed_gb_err = self.mem_err_gb
#         runtime_gb_err = np.abs(runtime_gb - mem_gb)
#         #
#         expected_runtime_threads = n_procs

#         # Error message formatting
#         mem_err = 'Input memory: %f is not within %.3f GB of runtime '\
#                   'memory: %f' % (mem_gb, self.mem_err_gb, runtime_gb)
#         threads_err = 'Input threads: %d is not equal to runtime threads: %d' \
#                     % (expected_runtime_threads, runtime_threads)

#         # Assert runtime stats are what was input
#         assert runtime_gb_err <= allowed_gb_err, mem_err
#         assert abs(expected_runtime_threads - runtime_threads) <= 1, threads_err
