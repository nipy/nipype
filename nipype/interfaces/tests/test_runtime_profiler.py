# test_runtime_profiler.py
#
# Author: Daniel Clark, 2016

'''
Module to unit test the runtime_profiler in nipype
'''

# Import packages
import unittest
from nipype.interfaces.base import traits, CommandLine, CommandLineInputSpec

try:
    import psutil
    import memory_profiler
    run_profiler = True
    skip_profile_msg = 'Run profiler tests'
except ImportError as exc:
    skip_profile_msg = 'Missing python packages for runtime profiling, skipping...\n'\
                       'Error: %s' % exc
    run_profiler = False

# UseResources inputspec
class UseResourcesInputSpec(CommandLineInputSpec):
    '''
    use_resources cmd interface inputspec
    '''

    # Init attributes
    num_gb = traits.Float(desc='Number of GB of RAM to use',
                          argstr = "-g %f")
    num_procs = traits.Int(desc='Number of processors to use',
                          argstr = "-p %d")


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


# Spin multiple processors
def use_resources(num_procs, num_gb):
    '''
    Function to execute multiple use_gb_ram functions in parallel
    '''

    # Function to occupy GB of memory
    def _use_gb_ram(num_gb):
        '''
        Function to consume GB of memory
        '''
    
        # Eat 1 GB of memory for 1 second
        gb_str = ' ' * int(num_gb*1024.0**3)
    
        # Spin CPU
        ctr = 0
        while ctr < 50e6:
            ctr += 1
    
        # Clear memory
        del ctr
        del gb_str

    # Import packages
    import logging
    from multiprocessing import Process

    from threading import Thread

    # Init variables
    num_gb = float(num_gb)
    # Init variables
    #num_threads = proc.num_threads()
    from CPAC.utils.utils import setup_logger
    # Build proc list
    proc_list = []
    for idx in range(num_procs):
        #proc = Thread(target=_use_gb_ram, args=(num_gb/num_procs,), name=str(idx))
        proc = Process(target=_use_gb_ram, args=(num_gb/num_procs,), name=str(idx))
        proc_list.append(proc)

    logger = setup_logger('memory_profiler', '/home/dclark/memory_profiler.log',
                          logging.DEBUG, to_screen=False)
    # Run multi-threaded
    print 'Using %.3f GB of memory over %d processors...' % (num_gb, num_procs)
    for idx, proc in enumerate(proc_list):
        proc.start()
        #logger.debug('Starting PID: %d' % proc.pid)

    for proc in proc_list:
        proc.join()


# Test case for the run function
class RuntimeProfilerTestCase(unittest.TestCase):
    '''
    This class is a test case for the runtime profiler

    Inherits
    --------
    unittest.TestCase class

    Attributes (class):
    ------------------
    see unittest.TestCase documentation

    Attributes (instance):
    ----------------------
    '''

    # setUp method for the necessary arguments to run cpac_pipeline.run
    def setUp(self):
        '''
        Method to instantiate TestCase

        Parameters
        ----------
        self : RuntimeProfileTestCase
            a unittest.TestCase-inherited class
        '''

        # Init parameters
        # Input RAM GB to occupy
        self.num_gb= 4
        # Input number of processors
        self.num_procs = 1
        # Acceptable percent error for memory profiled against input
        self.mem_err_percent = 5

    # ! Only used for benchmarking the profiler over a range of
    # ! processors and RAM usage
    # ! Requires a LOT of RAM and PROCS to be tested
    def _collect_range_runtime_stats(self):
        '''
        Function to collect a range of runtime stats
        '''

        # Import packages
        import json
        import numpy as np
        import pandas as pd

        # Init variables
        num_procs_range = 8
        ram_gb_range = 10.0
        ram_gb_step = 0.25
        dict_list = []

        # Iterate through all combos
        for num_procs in np.arange(1, num_procs_range+1, 1):
            for num_gb in np.arange(0.25, ram_gb_range+ram_gb_step, ram_gb_step):
                # Cmd-level
                cmd_fin_str = self._run_cmdline_workflow(num_gb, num_procs)
                cmd_node_stats = json.loads(cmd_fin_str)
                cmd_runtime_procs = int(cmd_node_stats['runtime_threads'])
                cmd_runtime_gb = float(cmd_node_stats['runtime_memory_gb'])

                # Func-level
                func_fin_str = self._run_function_workflow(num_gb, num_procs)
                func_node_stats = json.loads(func_fin_str)
                func_runtime_procs = int(func_node_stats['runtime_threads'])
                func_runtime_gb = float(func_node_stats['runtime_memory_gb'])

                # Calc errors
                cmd_procs_err = cmd_runtime_procs - num_procs
                cmd_gb_err = cmd_runtime_gb - num_gb
                func_procs_err = func_runtime_procs - num_procs
                func_gb_err = func_runtime_gb - num_gb

                # Node dictionary
                results_dict = {'input_procs' : num_procs,
                                'input_gb' : num_gb,
                                'cmd_runtime_procs' : cmd_runtime_procs,
                                'cmd_runtime_gb' : cmd_runtime_gb,
                                'func_runtime_procs' : func_runtime_procs,
                                'func_runtime_gb' : func_runtime_gb,
                                'cmd_procs_err' : cmd_procs_err,
                                'cmd_gb_err' : cmd_gb_err,
                                'func_procs_err' : func_procs_err,
                                'func_gb_err' : func_gb_err}
                # Append to list
                dict_list.append(results_dict)

        # Create dataframe
        runtime_results_df = pd.DataFrame(dict_list)

        # Return dataframe
        return runtime_results_df

    # Test node
    def _run_cmdline_workflow(self, num_gb, num_procs):
        '''
        Function to run the use_resources cmdline script in a nipype workflow
        and return the runtime stats recorded by the profiler

        Parameters
        ----------
        self : RuntimeProfileTestCase
            a unittest.TestCase-inherited class

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
                                                            'num_procs']),
                             name='input_node')
        input_node.inputs.num_gb = num_gb
        input_node.inputs.num_procs = num_procs

        # Resources used node
        resource_node = pe.Node(UseResources(), name='resource_node')
        resource_node.interface.estimated_memory_gb = num_gb
        resource_node.interface.num_threads = num_procs

        # Connect workflow
        wf.connect(input_node, 'num_gb', resource_node, 'num_gb')
        wf.connect(input_node, 'num_procs', resource_node, 'num_procs')

        # Run workflow
        plugin_args = {'n_procs' : num_procs,
                       'memory' : num_gb,
                       'status_callback' : log_nodes_cb}
        wf.run(plugin='MultiProc', plugin_args=plugin_args)

        # Get runtime stats from log file
        finish_str = open(log_file, 'r').readlines()[1].rstrip('\n')

        # Delete wf base dir
        shutil.rmtree(base_dir)

        # Return runtime stats
        return finish_str

    # Test node
    def _run_function_workflow(self, num_gb, num_procs):
        '''
        Function to run the use_resources() function in a nipype workflow
        and return the runtime stats recorded by the profiler

        Parameters
        ----------
        self : RuntimeProfileTestCase
            a unittest.TestCase-inherited class

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
                                                            'num_procs']),
                             name='input_node')
        input_node.inputs.num_gb = num_gb
        input_node.inputs.num_procs = num_procs

        # Resources used node
        resource_node = pe.Node(util.Function(input_names=['num_procs',
                                                           'num_gb'],
                                              output_names=[],
                                              function=use_resources),
                                name='resource_node')
        resource_node.interface.estimated_memory_gb = num_gb
        resource_node.interface.num_threads = num_procs

        # Connect workflow
        wf.connect(input_node, 'num_gb', resource_node, 'num_gb')
        wf.connect(input_node, 'num_procs', resource_node, 'num_procs')

        # Run workflow
        plugin_args = {'n_procs' : num_procs,
                       'memory' : num_gb,
                       'status_callback' : log_nodes_cb}
        wf.run(plugin='MultiProc', plugin_args=plugin_args)

        # Get runtime stats from log file
        finish_str = open(log_file, 'r').readlines()[1].rstrip('\n')

        # Delete wf base dir
        shutil.rmtree(base_dir)

        # Return runtime stats
        return finish_str

    # Test resources were used as expected in cmdline interface
    @unittest.skipIf(run_profiler == False, skip_profile_msg)
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
        num_procs = self.num_procs

        # Run workflow and get stats
        finish_str = self._run_cmdline_workflow(num_gb, num_procs)
        # Get runtime stats as dictionary
        node_stats = json.loads(finish_str)

        # Read out runtime stats
        runtime_gb = float(node_stats['runtime_memory_gb'])
        runtime_procs = int(node_stats['runtime_threads'])

        # Get margin of error for RAM GB
        allowed_gb_err = (self.mem_err_percent/100.0)*num_gb
        runtime_gb_err = np.abs(runtime_gb-num_gb)

        # Error message formatting
        mem_err = 'Input memory: %f is not within %.1f%% of runtime '\
                  'memory: %f' % (num_gb, self.mem_err_percent, runtime_gb)
        procs_err = 'Input procs: %d is not equal to runtime procs: %d' \
                    % (num_procs, runtime_procs)

        # Assert runtime stats are what was input
        self.assertLessEqual(runtime_gb_err, allowed_gb_err, msg=mem_err)
        self.assertEqual(num_procs, runtime_procs, msg=procs_err)

    # Test resources were used as expected
    @unittest.skipIf(run_profiler == False, skip_profile_msg)
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
        num_procs = self.num_procs

        # Run workflow and get stats
        finish_str = self._run_function_workflow(num_gb, num_procs)
        # Get runtime stats as dictionary
        node_stats = json.loads(finish_str)

        # Read out runtime stats
        runtime_gb = float(node_stats['runtime_memory_gb'])
        runtime_procs = int(node_stats['runtime_threads'])

        # Get margin of error for RAM GB
        allowed_gb_err = (self.mem_err_percent/100.0)*num_gb
        runtime_gb_err = np.abs(runtime_gb-num_gb)

        # Error message formatting
        mem_err = 'Input memory: %f is not within %.1f%% of runtime '\
                  'memory: %f' % (num_gb, self.mem_err_percent, runtime_gb)
        procs_err = 'Input procs: %d is not equal to runtime procs: %d' \
                    % (num_procs, runtime_procs)

        # Assert runtime stats are what was input
        self.assertLessEqual(runtime_gb_err, allowed_gb_err, msg=mem_err)
        self.assertEqual(num_procs, runtime_procs, msg=procs_err)


# Command-line run-able unittest module
if __name__ == '__main__':
    unittest.main()
