import os
import multiprocessing
from tempfile import mkdtemp
from tempfile import mkstemp
from shutil import rmtree

from inspect import *

from nipype.testing import assert_equal, assert_true
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import Function

class TestInterface():

    def testFunction(sum=0):
        '''
        Run a multiprocessing job and spawn child processes.
        '''
        
        # need to import here since this is executed as an external process
        import multiprocessing
        import tempfile
        import time
        import os
        import test_multiproc_nondaemon_dummy as d
      
        numberOfThreads = 2
            
        # list of processes
        t = [None] * numberOfThreads
      
        # list of alive flags
        a = [None] * numberOfThreads
      
        # list of tempFiles
        f = [None] * numberOfThreads
        
        for n in xrange( numberOfThreads ):
          
          # mark thread as alive
          a[n] = True
          
          # create a temp file to use as the data exchange container
          tmpFile = tempfile.mkstemp('.txt','test_engine_')[1]
          f[n] = tmpFile # keep track of the temp file
          t[n] = multiprocessing.Process(target=d.dummyFunction, args=(tmpFile,))
          # fire up the job
          t[n].start()
        
        
        # block until all processes are done
        allDone = False
        while not allDone:
      
          time.sleep(1)
      
          for n in xrange(numberOfThreads):
      
            a[n] = t[n].is_alive()
      
          if not any(a):
            # if no thread is alive
            allDone = True
            
        # here, all processes are done
        
        # read in all temp files and sum them up
        for file in f:
          with open(file) as fd:
            sum += int(fd.read())
          os.remove(file)
            
        return sum


def test_run_multiproc_nondaemon_with_flag(nondaemon_flag):
    '''
    Start a pipe with two nodes using the multiproc plugin and passing the nondaemon_flag.
    '''
    
    cur_dir = os.getcwd()
    temp_dir = mkdtemp(prefix='test_engine_')
    os.chdir(temp_dir)
    
    pipe = pe.Workflow(name='pipe')
    
    f1 = pe.Node(interface=Function(function=TestInterface.testFunction, input_names=['sum'], output_names=['sum_out']), name='f1')
    f2 = pe.Node(interface=Function(function=TestInterface.testFunction, input_names=['sum'], output_names=['sum_out']), name='f2')

    pipe.connect([(f1,f2,[('sum_out','sum')])])
    pipe.base_dir = os.getcwd()
    f1.inputs.sum = 0
    
    # execute the pipe using the MultiProc plugin with 2 processes and the non_daemon flag
    # to enable child processes which start other multiprocessing jobs
    execgraph = pipe.run(plugin="MultiProc", plugin_args={'n_procs':2, 'non_daemon':nondaemon_flag})
    
    names = ['.'.join((node._hierarchy,node.name)) for node in execgraph.nodes()]
    node = execgraph.nodes()[names.index('pipe.f2')]
    result = node.get_output('sum_out')
    yield assert_equal, result, 180 # n_procs (2) * numberOfThreads (2) * 45 == 180
    os.chdir(cur_dir)
    rmtree(temp_dir)
    
    
def test_run_multiproc_nondaemon():
    '''
    This is the entry point for the test. Two times a pipe of several multiprocessing jobs gets
    executed. First, without the nondaemon flag. Second, with the nondaemon flag.
    
    Since the processes of the pipe start child processes, the execution only succeeds when the
    non_daemon flag is on.
    '''
    shouldHaveFailed = False
    
    try:
      # with nondaemon_flag = False, the execution should fail
      test_run_multiproc_nondaemon_with_flag(False)
    except:
      shouldHaveFailed = True
    
    # with nondaemon_flag = True, the execution should succeed
    test_run_multiproc_nondaemon_with_flag(True)
  
    yield assert_true, shouldHaveFailed
    