import nipype.interfaces.base as nii
from nipype.testing import assert_equal, assert_not_equal, assert_raises, assert_true
import os

#test Bunch
def test_bunch():
    b = nii.Bunch()
    yield assert_equal, b.__dict__,{}
    b = nii.Bunch(a=1,b=[2,3])
    yield assert_equal, b.__dict__,{'a': 1, 'b': [2,3]}

def test_bunch_attribute():
    b = nii.Bunch(a=1,b=[2,3],c=None)
    yield assert_equal, b.a ,1
    yield assert_equal, b.b, [2,3]
    yield assert_equal, b.c, None

def test_bunch_repr():
    b = nii.Bunch(b=2,c=3,a=dict(n=1,m=2))
    yield assert_equal, repr(b), "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"

def test_bunch_methods():
    b = nii.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    yield assert_equal, b.a, 3
    yield assert_equal, b.get('a'), 3
    yield assert_equal, b.get('badkey', 'otherthing'), 'otherthing'
    yield assert_not_equal, b, newb
    yield assert_equal, type(dict()), type(newb)
    yield assert_equal, newb['a'], 3

def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    pth = os.path.split(os.path.abspath(__file__))[0]
    json_pth = os.path.join(pth, 'realign_json.json')
    b = nii.Bunch(infile = json_pth, 
                  otherthing = 'blue',
                  yat = True)
    newbdict, bhash = b._get_bunch_hash()
    yield assert_equal, bhash, 'ddcc7b4ec5675df8cf317a48bd1857fa'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nii.md5()
    fp = file(json_pth)
    jshash.update(fp.read())
    fp.close()
    yield assert_equal, newbdict['infile'][0][1], jshash.hexdigest()
    yield assert_equal, newbdict['yat'], True

#test CommandLine
def test_commandline():
    cl = nii.CommandLine('echo', 'foo')
    yield assert_equal, cl.inputs.args, ['echo', 'foo']
    yield assert_equal, cl.cmdline, 'echo foo'
    yield assert_not_equal, cl, cl.run()
    
    yield assert_equal, nii.CommandLine('echo foo').cmdline,\
        nii.CommandLine(args='echo foo').cmdline
    yield assert_equal, nii.CommandLine('ls','-l').cmdline,\
        nii.CommandLine('ls -l').cmdline
    clout = cl.run()
    yield assert_equal, clout.runtime.returncode, 0
    yield assert_equal, clout.runtime.stderr,  ''
    yield assert_equal, clout.runtime.stdout, 'foo\n'
    yield assert_equal, clout.interface.cmdline, cl.cmdline
    yield assert_not_equal, clout.interface, cl

"""
stuff =CommandLine('this is what I want to run')

better = Bet(frac=0.5, input='anotherfile', flags = ['-R', '-k'])

betted = better.run(input='filea', output='ssfilea')

def f(a='', *args, **kwargs):
    whateve

f(file1, file2, a=Something, b='this')


cl = COmmandLine('ls')

d1 = cl.run('/path/to/d1')

d2 = cl.run('/path/to/d2')

d3 = CommandLine().run('ls /path/to/d3')
or
d3 = CommandLine('ls /path/to/d3').run()
or
d3 = CommandLine('ls').run('/path/to/d3')


stuff = CommandLine(flags={'-f':0.5, 'otherthing': 2, '-c':[100,87,92], '-R':None})

stuff = CommandLine('ls',flags=['-R', '--thingy', '100 87 90'])


cmd1 = CommandLine('ls -l *')
cmd2 = CommandLine.update('-a -h').remove('-l')
"""

import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            assert_true, assert_false, with_setup)
import nipype.interfaces.base as nib
from nipype.interfaces.base import Undefined
from nipype.interfaces.base import InterfaceResult

tmp_infile = None
tmp_dir = None
def setup_file():
    global tmp_infile, tmp_dir
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo.txt')
    open(tmp_infile, 'w').writelines('123456789')

def teardown_file():
    shutil.rmtree(tmp_dir)

@with_setup(setup_file, teardown_file)
def test_TraitedSpec():
    yield assert_true, nib.TraitedSpec().hashval
    yield assert_equal, nib.TraitedSpec().__repr__(), ''
    
    class spec(nib.TraitedSpec):
        foo = nib.traits.Int
        goo = nib.traits.Float(usedefault=True)

    # This should fail currently and is consistent with traits, but
    # inconsistent with nipype interface api
    yield assert_equal, spec().foo, Undefined
    yield assert_equal, spec().goo, 0.0
    specfunc = lambda x : spec(hoo=x)
    yield assert_raises, nib.traits.TraitError, specfunc, 1
    infields = spec(foo=1)
    hashval = ({'goo': 0.0, 'foo': 1}, 'a83c1cb761df797f176bd23c7ca30a69')
    yield assert_equal, infields.hashval[0], hashval[0]
    yield assert_equal, infields.hashval[1], hashval[1]
    yield assert_equal, infields.__repr__(), 'foo = 1\ngoo = 0.0'

    global tmp_infile
    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec2(moo=tmp_infile,doo=[tmp_infile])
    yield assert_equal, infields.hashval[1], 'c687052171787b46d06ba55dbb74e6a3'

    
def test_NEW_Interface():
    yield assert_equal, nib.NEW_Interface.input_spec, None
    yield assert_equal, nib.NEW_Interface.output_spec, None
    yield assert_raises, NotImplementedError, nib.NEW_Interface
    yield assert_raises, NotImplementedError, nib.NEW_Interface.help
    yield assert_raises, NotImplementedError, nib.NEW_Interface._inputs_help
    yield assert_raises, NotImplementedError, nib.NEW_Interface._outputs_help
    yield assert_raises, NotImplementedError, nib.NEW_Interface._outputs

    class DerivedInterface(nib.NEW_Interface):
        def __init__(self):
            pass
        
    nif = DerivedInterface()
    yield assert_raises, NotImplementedError, nif.run
    yield assert_raises, NotImplementedError, nif.aggregate_outputs
    yield assert_raises, NotImplementedError, nif._list_outputs
    yield assert_raises, NotImplementedError, nif._get_filecopy_info

def test_NEW_BaseInterface():
    yield assert_equal, nib.NEW_BaseInterface.help(), None
    yield assert_equal, nib.NEW_BaseInterface._outputs(), None
    yield assert_equal, nib.NEW_BaseInterface._get_filecopy_info(), []

    class InputSpec(nib.BaseInterfaceInputSpec):
        foo = nib.traits.Int(desc='a random int')
        goo = nib.traits.Int(desc='a random int', mandatory=True)
        hoo = nib.traits.Int(desc='a random int', usedefault=True)
        zoo = nib.File(desc='a file', copyfile=False)
        woo = nib.File(desc='a file', copyfile=True)
    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')
    class DerivedInterface(nib.NEW_BaseInterface):
        input_spec = InputSpec
        
    yield assert_equal, DerivedInterface.help(), None
    yield assert_equal, DerivedInterface._outputs(), None
    yield assert_equal, DerivedInterface._get_filecopy_info()[0]['key'], 'woo'
    yield assert_true, DerivedInterface._get_filecopy_info()[0]['copy']
    yield assert_equal, DerivedInterface._get_filecopy_info()[1]['key'], 'zoo'
    yield assert_false, DerivedInterface._get_filecopy_info()[1]['copy']
    yield assert_equal, DerivedInterface().inputs.foo, Undefined
    yield assert_raises, ValueError, DerivedInterface()._check_mandatory_inputs
    yield assert_equal, DerivedInterface(goo=1)._check_mandatory_inputs(), None
    yield assert_raises, ValueError, DerivedInterface().run
    yield assert_raises, NotImplementedError, DerivedInterface(goo=1).run
    
    class DerivedInterface2(DerivedInterface):
        output_spec = OutputSpec
        def _run_interface(self, runtime):
            return runtime

    yield assert_equal, DerivedInterface2.help(), None
    yield assert_equal, DerivedInterface2._outputs().foo, Undefined
    yield assert_raises, Exception, DerivedInterface2(goo=1).run

    class DerivedInterface3(DerivedInterface2):
        def _run_interface(self, runtime):
            runtime.returncode = 1
            return runtime

    yield assert_equal, DerivedInterface3(goo=1).run().outputs, None
    
    class DerivedInterface4(DerivedInterface):
        def _run_interface(self, runtime):
            runtime.returncode = 0
            return runtime
    yield assert_equal, DerivedInterface4(goo=1).run().outputs, None

    class DerivedInterface5(DerivedInterface2):
        def _run_interface(self, runtime):
            runtime.returncode = 0
            return runtime
    yield assert_raises, NotImplementedError, DerivedInterface5(goo=1).run

    nib.NEW_BaseInterface.input_spec = None
    yield assert_raises, Exception, nib.NEW_BaseInterface

def test_NEW_Commandline():
    yield assert_raises, Exception, nib.NEW_CommandLine
    ci = nib.NEW_CommandLine(command='which')
    yield assert_equal, ci.cmd, 'which'
    yield assert_equal, ci.inputs.args, Undefined
    ci2 = nib.NEW_CommandLine(command='which', args='ls')
    yield assert_equal, ci2.cmdline, 'which ls'
    ci3 = nib.NEW_CommandLine(command='echo')
    ci3.inputs.environ = {'MYENV' : 'foo'}
    res = ci3.run()
    yield assert_equal, res.runtime.environ['MYENV'], 'foo'
    yield assert_equal, res.outputs, None

    class CommandLineInputSpec(nib.TraitedSpec):
        foo = nib.traits.Str(argstr='%s', desc='a str')
        goo = nib.traits.Bool(argstr='-g', desc='a bool', position=0)
        hoo = nib.traits.List(argstr='-l %s', desc='a list')
        moo = nib.traits.List(argstr='-i %d...', desc='a repeated list',
                              position=-1)
        noo = nib.traits.Int(argstr='-x %d', desc='an int')
        roo = nib.traits.Str(desc='not on command line')
    nib.NEW_CommandLine.input_spec = CommandLineInputSpec
    ci4 = nib.NEW_CommandLine(command='cmd')
    ci4.inputs.foo = 'foo'
    ci4.inputs.goo = True
    ci4.inputs.hoo = ['a', 'b']
    ci4.inputs.moo = [1, 2, 3]
    ci4.inputs.noo = 0
    ci4.inputs.roo = 'hello'
    cmd = ci4._parse_inputs()
    yield assert_equal, cmd[0], '-g'
    yield assert_equal, cmd[-1], '-i 1 -i 2 -i 3'
    yield assert_true, 'hello' not in ' '.join(cmd)
    
    class CommandLineInputSpec2(nib.TraitedSpec):
        foo = nib.File(argstr='%s', desc='a str', genfile=True)
    nib.NEW_CommandLine.input_spec = CommandLineInputSpec2
    ci5 = nib.NEW_CommandLine(command='cmd')
    yield assert_raises, NotImplementedError, ci5._parse_inputs

    class DerivedClass(nib.NEW_CommandLine):
        input_spec = CommandLineInputSpec2
        def _gen_filename(self, name):
            return 'filename'
        
    ci6 = DerivedClass(command='cmd')
    yield assert_equal, ci6._parse_inputs()[0], 'filename'
