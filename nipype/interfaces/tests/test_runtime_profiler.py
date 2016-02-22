# test_runtime_profiler.py
#
# Author: Daniel Clark, 2016

'''
Module to unit test the runtime_profiler in nipype
'''

# Import packages
import unittest
from nipype.interfaces.base import traits, CommandLine, CommandLineInputSpec


# UseResources inputspec
class UseResourcesInputSpec(CommandLineInputSpec):
    '''
    '''

    # Init attributes
    num_gb = traits.Float(desc='Number of GB of RAM to use',
                          argstr = "-g %f")
    num_procs = traits.Int(desc='Number of processors to use',
                          argstr = "-p %d")


# UseResources interface
class UseResources(CommandLine):
    '''
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


# Test case for the run function
class RuntimeProfilerTestCase(unittest.TestCase):
    '''
    This class is a test case for the ResourceMultiProc plugin runtime
    profiler

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

        self.num_gb = 1
        self.num_procs = 2

    # Test node
    def _run_workflow(self):
        '''
        Function to run the use_resources script in a nipype workflow
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
        num_gb = self.num_gb
        num_procs = self.num_procs
        base_dir = tempfile.mkdtemp()
        log_file = os.path.join(base_dir, 'callback.log')

        # Init logger
        logger = logging.getLogger('callback')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)

        # Declare workflow
        wf = pe.Workflow(name='test_runtime_prof')
        wf.base_dir = base_dir

        # Input node
        input_node = pe.Node(util.IdentityInterface(fields=['num_gb',
                                                            'num_procs']),
                             name='input_node')
        input_node.inputs.num_gb = num_gb
        input_node.inputs.num_procs = num_procs

        # Resources used node
        resource_node = pe.Node(UseResources(), name='resource_node')
        resource_node.interface.estimated_memory = num_gb
        resource_node.interface.num_threads = num_procs

        # Connect workflow
        wf.connect(input_node, 'num_gb', resource_node, 'num_gb')
        wf.connect(input_node, 'num_procs', resource_node, 'num_procs')

        # Run workflow
        plugin_args = {'n_procs' : num_procs,
                       'memory' : num_gb,
                       'runtime_profile' : True,
                       'status_callback' : log_nodes_cb}
        wf.run(plugin='ResourceMultiProc', plugin_args=plugin_args)

        # Get runtime stats from log file
        finish_str = open(log_file, 'r').readlines()[1].rstrip('\n')

        # Delete wf base dir
        shutil.rmtree(base_dir)

        # Return runtime stats
        return finish_str

    # Test resources were used as expected
    def test_wf_logfile(self):
        '''
        Test runtime profiler correctly records workflow RAM/CPUs consumption
        '''

        # Import packages
        import json

        # Init variables
        places = 1

        # Run workflow and get stats
        finish_str = self._run_workflow()
        # Get runtime stats as dictionary
        node_stats = json.loads(finish_str)

        # Read out runtime stats
        runtime_gb = float(node_stats['runtime_memory'])
        runtime_procs = int(node_stats['runtime_threads'])

        # Error message formatting
        mem_err = 'Input memory: %.5f is not within %d places of runtime '\
                  'memory: %.5f' % (self.num_gb, places, runtime_gb)
        procs_err = 'Input procs: %d is not equal to runtime procs: %d' \
                    % (self.num_procs, runtime_procs)

        # Assert runtime stats are what was input
        self.assertAlmostEqual(self.num_gb, runtime_gb, places=places,
                               msg=mem_err)
        self.assertEqual(self.num_procs, runtime_procs, msg=procs_err)


# Command-line run-able unittest module
if __name__ == '__main__':
    unittest.main()
