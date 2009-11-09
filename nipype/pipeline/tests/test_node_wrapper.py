
import os
from copy import deepcopy
from tempfile import mkdtemp
from shutil import rmtree

from nipype.testing import assert_raises, assert_equal, assert_not_equal
import nipype.pipeline.node_wrapper as nw
from nipype.interfaces.base import (Interface, CommandLine, Bunch, 
                                    InterfaceResult)
from nipype.utils.filemanip import cleandir

# nosetests -sv --with-coverage --cover-package=nipype.pipeline.node_wrapper test_node_wrapper.py

class BasicInterface(Interface):
    """Basic interface class for testing nodewrapper
    """
    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.ran = None
        
    def _populate_inputs(self):
        self.inputs = Bunch(input1=None,
                            input2=None,
                            returncode=0)
    
    def get_input_info(self):
        return []
    
    def aggregate_outputs(self):
        outputs = Bunch(output1=None)
        if self.ran is not None:
            outputs.output1 = [self.ran,self.inputs.input1]
        return outputs
    
    def run(self, cwd=None):
        """Execute this module.
        """
        runtime = Bunch(returncode=self.inputs.returncode,
                        stdout=None,
                        stderr=None)
        self.ran = 'ran'
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

def rm_dir(d):
    # Remove the directory
    if os.path.exists(d):
        rmtree(d)
    
def test_init():
    # Test raising error with mandatory keyword arg interface absent
    yield assert_raises, Exception, nw.NodeWrapper

    bi = nw.NodeWrapper(interface=BasicInterface())
    yield assert_equal, bi.output_directory_base, None
    yield assert_equal, bi.name, 'BasicInterface.test_node_wrapper'
    yield assert_equal, bi.disk_based, False
    yield assert_equal, bi.result, None
    yield assert_equal, bi.overwrite, None
    yield assert_equal, bi.iterables, {}
    yield assert_equal, bi.iterfield, []
    yield assert_equal, bi.parameterization, None
    
    bi = nw.NodeWrapper(interface=BasicInterface(),diskbased=True)
    yield assert_equal, bi.output_directory_base, None
    yield assert_equal, bi.overwrite, False
    
    bi = nw.NodeWrapper(interface=BasicInterface(),diskbased=True,base_directory='.')
    yield assert_equal, bi.output_directory_base, '.'

    bi = lambda x: nw.NodeWrapper(interface=BasicInterface(),base_directory=x)
    yield assert_raises, Exception, bi, '.'

    bi = nw.NodeWrapper(interface=BasicInterface(),name='foo')
    yield assert_equal, bi.name, 'foo'
    

def test_interface():
    bi = nw.NodeWrapper(interface=BasicInterface())
    yield assert_equal, type(bi.interface),BasicInterface

def test_result():
    bi = nw.NodeWrapper(interface=BasicInterface())
    yield assert_equal, bi.result, None

def test_inputs():
    bi = nw.NodeWrapper(interface=BasicInterface())
    yield assert_equal, type(bi.inputs), Bunch
    yield assert_equal, bi.inputs.input1, None
    yield assert_equal, bi.inputs.input2, None

def test_set_input():
    bi = nw.NodeWrapper(interface=BasicInterface())
    bi.set_input('input1',1)
    yield assert_equal, bi.inputs.input1, 1

    def func():
        return 2
    bi.set_input('input2',func)
    yield assert_equal, bi.inputs.input2, 2

    def func(val1,val2):
        return [val1,val2]
    bi.set_input('input2',func,1,2)
    yield assert_equal, bi.inputs.input2, [1,2]

    def func(val1,val2,foo=None):
        return [val1,val2,foo]
    bi.set_input('input2',func,1,2,foo=3)
    yield assert_equal, bi.inputs.input2, [1,2,3]

def test_get_output():
    bi = nw.NodeWrapper(interface=BasicInterface())
    yield assert_equal, bi.get_output('output1'), None

    bi.run()
    yield assert_equal, bi.get_output('output1'), ['ran',None]

def test_run():
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True)
    bi.run()
    yield assert_equal, bi.get_output('output1'), ['ran',None]
    basedir = mkdtemp()
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True, 
                        base_directory=basedir)
    outdir = os.path.join(basedir, bi.name)
    rm_dir(outdir)
    bi.run()
    yield assert_equal, bi.get_output('output1'), ['ran',None]
    bi.run()
    yield assert_equal, bi.get_output('output1'), ['ran',None]
    rm_dir(outdir)
    bi.set_input('returncode',1)
    yield assert_raises, Exception, bi.run

    bi = nw.NodeWrapper(interface=BasicInterface())
    bi.iterfield = ['input1']
    bi.set_input('input1',[1,2,3,4])
    result = bi.run()
    yield assert_equal, len(result.outputs.output1), 4
    yield assert_equal, result.outputs.output1[3], ['ran',4]

def test_run_interface():
    bi = nw.NodeWrapper(interface=BasicInterface())
    bi.iterfield = ['input1']
    bi.set_input('input1',1)
    result = bi.run()
    yield assert_equal, len(result.outputs.output1), 1
    basedir = mkdtemp()
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True, 
                        base_directory=basedir)
    outdir = os.path.join(basedir, bi.name)
    rm_dir(outdir)
    bi.iterfield = ['input1']
    bi.set_input('input1',[1,2,3,4])
    result = bi.run()
    yield assert_equal, len(result.outputs.output1), 4
    result = bi.run()
    yield assert_equal, len(result.outputs.output1), 4
    rm_dir(outdir)

def test_update():
    bi = nw.NodeWrapper(interface=BasicInterface())
    bi.update(inputs1=2)
    yield assert_equal, bi.inputs.inputs1, 2

def test_hash_inputs():
    bi = nw.NodeWrapper(interface=BasicInterface())
    hashval = bi.hash_inputs()
    # this will fail if you change the input structure of the basic
    # interface class above. make sure to fix this in that case.
    yield assert_equal, hashval, 'd1cf3db3de3092e0de0b7f72fc78842c'

def test_output_directory():
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True)
    odir = bi._output_directory()
    outdir = bi.output_directory_base
    yield assert_equal, odir, os.path.join(outdir,bi.name)
    rm_dir(outdir)

def test_make_output_dir():
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True)
    outdir = mkdtemp()
    outdir1 = os.path.join(outdir, 'footestfoo')
    yield assert_equal, bi._make_output_dir(outdir1), os.path.abspath(outdir1)
    rm_dir(outdir)

def test_repr():
    bi = nw.NodeWrapper(interface=BasicInterface(), name='foo.goo')
    yield assert_equal, repr(bi), 'foo.goo'
    

def test_file_hashing():
    basedir = mkdtemp()
    bi = nw.NodeWrapper(interface=BasicInterface(), diskbased=True, 
                        name='hash.test', base_directory=basedir)
    bi.cmd = 'echo foo'
    res1 = bi.run()
    res2 = bi.run()
    yield assert_not_equal, res1.runtime, res2.runtime
    rm_dir(basedir)
