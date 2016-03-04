# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

import os
import tempfile
import shutil
import warnings

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            assert_true, assert_false, with_setup, package_check,
                            skipif)
import nipype.interfaces.base as nib
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import Undefined, config, text_type
from traits.testing.nose_tools import skip
import traits.api as traits


def test_bunch():
    b = nib.Bunch()
    yield assert_equal, b.__dict__, {}
    b = nib.Bunch(a=1, b=[2, 3])
    yield assert_equal, b.__dict__, {'a': 1, 'b': [2, 3]}


def test_bunch_attribute():
    b = nib.Bunch(a=1, b=[2, 3], c=None)
    yield assert_equal, b.a, 1
    yield assert_equal, b.b, [2, 3]
    yield assert_equal, b.c, None


def test_bunch_repr():
    b = nib.Bunch(b=2, c=3, a=dict(n=1, m=2))
    yield assert_equal, repr(b), "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"


def test_bunch_methods():
    b = nib.Bunch(a=2)
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
    b = nib.Bunch(infile=json_pth,
                  otherthing='blue',
                  yat=True)
    newbdict, bhash = b._get_bunch_hash()
    yield assert_equal, bhash, 'ddcc7b4ec5675df8cf317a48bd1857fa'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nib.md5()
    with open(json_pth) as fp:
        jshash.update(fp.read().encode('utf-8'))
    yield assert_equal, newbdict['infile'][0][1], jshash.hexdigest()
    yield assert_equal, newbdict['yat'], True


# create a temp file
# global tmp_infile, tmp_dir
# tmp_infile = None
# tmp_dir = None
def setup_file():
    # global tmp_infile, tmp_dir
    tmp_dir = tempfile.mkdtemp()
    tmp_infile = os.path.join(tmp_dir, 'foo.txt')
    with open(tmp_infile, 'w') as fp:
        fp.writelines(['123456789'])
    return tmp_infile


def teardown_file(tmp_dir):
    shutil.rmtree(tmp_dir)


def test_TraitedSpec():
    yield assert_true, nib.TraitedSpec().get_hashval()
    yield assert_equal, nib.TraitedSpec().__repr__(), '\n\n'

    class spec(nib.TraitedSpec):
        foo = nib.traits.Int
        goo = nib.traits.Float(usedefault=True)

    yield assert_equal, spec().foo, Undefined
    yield assert_equal, spec().goo, 0.0
    specfunc = lambda x: spec(hoo=x)
    yield assert_raises, nib.traits.TraitError, specfunc, 1
    infields = spec(foo=1)
    hashval = ([('foo', 1), ('goo', '0.0000000000')], 'e89433b8c9141aa0fda2f8f4d662c047')
    yield assert_equal, infields.get_hashval(), hashval
    # yield assert_equal, infields.hashval[1], hashval[1]
    yield assert_equal, infields.__repr__(), '\nfoo = 1\ngoo = 0.0\n'


@skip
def test_TraitedSpec_dynamic():
    from pickle import dumps, loads
    a = nib.BaseTraitedSpec()
    a.add_trait('foo', nib.traits.Int)
    a.foo = 1
    assign_a = lambda: setattr(a, 'foo', 'a')
    yield assert_raises, Exception, assign_a
    pkld_a = dumps(a)
    unpkld_a = loads(pkld_a)
    assign_a_again = lambda: setattr(unpkld_a, 'foo', 'a')
    yield assert_raises, Exception, assign_a_again


def test_TraitedSpec_logic():
    class spec3(nib.TraitedSpec):
        _xor_inputs = ('foo', 'bar')

        foo = nib.traits.Int(xor=_xor_inputs,
                             desc='foo or bar, not both')
        bar = nib.traits.Int(xor=_xor_inputs,
                             desc='bar or foo, not both')
        kung = nib.traits.Float(requires=('foo',),
                                position=0,
                                desc='kung foo')

    class out3(nib.TraitedSpec):
        output = nib.traits.Int

    class MyInterface(nib.BaseInterface):
        input_spec = spec3
        output_spec = out3

    myif = MyInterface()
    yield assert_raises, TypeError, setattr(myif.inputs, 'kung', 10.0)
    myif.inputs.foo = 1
    yield assert_equal, myif.inputs.foo, 1
    set_bar = lambda: setattr(myif.inputs, 'bar', 1)
    yield assert_raises, IOError, set_bar
    yield assert_equal, myif.inputs.foo, 1
    myif.inputs.kung = 2
    yield assert_equal, myif.inputs.kung, 2.0


def test_deprecation():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec1(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='0.1')
        spec_instance = DeprecationSpec1()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        yield assert_raises, nib.TraitError, set_foo
        yield assert_equal, len(w), 0, 'no warnings, just errors'

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec1numeric(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='0.1')
        spec_instance = DeprecationSpec1numeric()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        yield assert_raises, nib.TraitError, set_foo
        yield assert_equal, len(w), 0, 'no warnings, just errors'

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec2(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='100', new_name='bar')
        spec_instance = DeprecationSpec2()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        yield assert_raises, nib.TraitError, set_foo
        yield assert_equal, len(w), 0, 'no warnings, just errors'

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec3(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='1000', new_name='bar')
            bar = nib.traits.Int()
        spec_instance = DeprecationSpec3()
        not_raised = True
        try:
            spec_instance.foo = 1
        except nib.TraitError:
            not_raised = False
        yield assert_true, not_raised
        yield assert_equal, len(w), 1, 'deprecated warning 1 %s' % [w1.message for w1 in w]

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec3(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='1000', new_name='bar')
            bar = nib.traits.Int()
        spec_instance = DeprecationSpec3()
        not_raised = True
        try:
            spec_instance.foo = 1
        except nib.TraitError:
            not_raised = False
        yield assert_true, not_raised
        yield assert_equal, spec_instance.foo, Undefined
        yield assert_equal, spec_instance.bar, 1
        yield assert_equal, len(w), 1, 'deprecated warning 2 %s' % [w1.message for w1 in w]


def test_namesource():
    tmp_infile = setup_file()
    tmpd, nme, ext = split_filename(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)

    class spec2(nib.CommandLineInputSpec):
        moo = nib.File(name_source=['doo'], hash_files=False, argstr="%s",
                       position=2)
        doo = nib.File(exists=True, argstr="%s", position=1)
        goo = traits.Int(argstr="%d", position=4)
        poo = nib.File(name_source=['goo'], hash_files=False, argstr="%s", position=3)

    class TestName(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec2
    testobj = TestName()
    testobj.inputs.doo = tmp_infile
    testobj.inputs.goo = 99
    yield assert_true, '%s_generated' % nme in testobj.cmdline
    testobj.inputs.moo = "my_%s_template"
    yield assert_true, 'my_%s_template' % nme in testobj.cmdline
    os.chdir(pwd)
    teardown_file(tmpd)


def test_chained_namesource():
    tmp_infile = setup_file()
    tmpd, nme, ext = split_filename(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)

    class spec2(nib.CommandLineInputSpec):
        doo = nib.File(exists=True, argstr="%s", position=1)
        moo = nib.File(name_source=['doo'], hash_files=False, argstr="%s",
                       position=2, name_template='%s_mootpl')
        poo = nib.File(name_source=['moo'], hash_files=False,
                       argstr="%s", position=3)

    class TestName(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec2

    testobj = TestName()
    testobj.inputs.doo = tmp_infile
    res = testobj.cmdline
    yield assert_true, '%s' % tmp_infile in res
    yield assert_true, '%s_mootpl ' % nme in res
    yield assert_true, '%s_mootpl_generated' % nme in res

    os.chdir(pwd)
    teardown_file(tmpd)


def test_cycle_namesource1():
    tmp_infile = setup_file()
    tmpd, nme, ext = split_filename(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)

    class spec3(nib.CommandLineInputSpec):
        moo = nib.File(name_source=['doo'], hash_files=False, argstr="%s",
                       position=1, name_template='%s_mootpl')
        poo = nib.File(name_source=['moo'], hash_files=False,
                       argstr="%s", position=2)
        doo = nib.File(name_source=['poo'], hash_files=False,
                       argstr="%s", position=3)

    class TestCycle(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec3

    # Check that an exception is raised
    to0 = TestCycle()
    not_raised = True
    try:
        to0.cmdline
    except nib.NipypeInterfaceError:
        not_raised = False
    yield assert_false, not_raised

    os.chdir(pwd)
    teardown_file(tmpd)


def test_cycle_namesource2():
    tmp_infile = setup_file()
    tmpd, nme, ext = split_filename(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)

    class spec3(nib.CommandLineInputSpec):
        moo = nib.File(name_source=['doo'], hash_files=False, argstr="%s",
                       position=1, name_template='%s_mootpl')
        poo = nib.File(name_source=['moo'], hash_files=False,
                       argstr="%s", position=2)
        doo = nib.File(name_source=['poo'], hash_files=False,
                       argstr="%s", position=3)

    class TestCycle(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec3

    # Check that loop can be broken by setting one of the inputs
    to1 = TestCycle()
    to1.inputs.poo = tmp_infile

    not_raised = True
    try:
        res = to1.cmdline
    except nib.NipypeInterfaceError:
        not_raised = False
    print(res)

    yield assert_true, not_raised
    yield assert_true, '%s' % tmp_infile in res
    yield assert_true, '%s_generated' % nme in res
    yield assert_true, '%s_generated_mootpl' % nme in res

    os.chdir(pwd)
    teardown_file(tmpd)


def checknose():
    """check version of nose for known incompatability"""
    mod = __import__('nose')
    if mod.__versioninfo__[1] <= 11:
        return 0
    else:
        return 1


@skipif(checknose)
def test_TraitedSpec_withFile():
    tmp_infile = setup_file()
    tmpd, nme = os.path.split(tmp_infile)
    yield assert_true, os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec2(moo=tmp_infile, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    yield assert_equal, hashval[1], 'a00e9ee24f5bfa9545a515b7a759886b'
    teardown_file(tmpd)


@skipif(checknose)
def test_TraitedSpec_withNoFileHashing():
    tmp_infile = setup_file()
    tmpd, nme = os.path.split(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)
    yield assert_true, os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True, hash_files=False)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec2(moo=nme, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    yield assert_equal, hashval[1], '8da4669ff5d72f670a46ea3e7a203215'

    class spec3(nib.TraitedSpec):
        moo = nib.File(exists=True, name_source="doo")
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec3(moo=nme, doo=[tmp_infile])
    hashval1 = infields.get_hashval(hash_method='content')

    class spec4(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec4(moo=nme, doo=[tmp_infile])
    hashval2 = infields.get_hashval(hash_method='content')

    yield assert_not_equal, hashval1[1], hashval2[1]
    os.chdir(pwd)
    teardown_file(tmpd)


def test_Interface():
    yield assert_equal, nib.Interface.input_spec, None
    yield assert_equal, nib.Interface.output_spec, None
    yield assert_raises, NotImplementedError, nib.Interface
    yield assert_raises, NotImplementedError, nib.Interface.help
    yield assert_raises, NotImplementedError, nib.Interface._inputs_help
    yield assert_raises, NotImplementedError, nib.Interface._outputs_help
    yield assert_raises, NotImplementedError, nib.Interface._outputs

    class DerivedInterface(nib.Interface):
        def __init__(self):
            pass

    nif = DerivedInterface()
    yield assert_raises, NotImplementedError, nif.run
    yield assert_raises, NotImplementedError, nif.aggregate_outputs
    yield assert_raises, NotImplementedError, nif._list_outputs
    yield assert_raises, NotImplementedError, nif._get_filecopy_info


def test_BaseInterface():
    yield assert_equal, nib.BaseInterface.help(), None
    yield assert_equal, nib.BaseInterface._get_filecopy_info(), []

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')
        goo = nib.traits.Int(desc='a random int', mandatory=True)
        moo = nib.traits.Int(desc='a random int', mandatory=False)
        hoo = nib.traits.Int(desc='a random int', usedefault=True)
        zoo = nib.File(desc='a file', copyfile=False)
        woo = nib.File(desc='a file', copyfile=True)

    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')

    class DerivedInterface(nib.BaseInterface):
        input_spec = InputSpec

    yield assert_equal, DerivedInterface.help(), None
    yield assert_true, 'moo' in ''.join(DerivedInterface._inputs_help())
    yield assert_equal, DerivedInterface()._outputs(), None
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
    yield assert_equal, DerivedInterface2()._outputs().foo, Undefined
    yield assert_raises, NotImplementedError, DerivedInterface2(goo=1).run

    nib.BaseInterface.input_spec = None
    yield assert_raises, Exception, nib.BaseInterface


def assert_not_raises(fn, *args, **kwargs):
    fn(*args, **kwargs)
    return True


def test_input_version():
    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
    obj = DerivedInterface1()
    yield assert_not_raises, obj._check_version_requirements, obj.inputs

    config.set('execution', 'stop_on_unknown_version', True)
    yield assert_raises, Exception, obj._check_version_requirements, obj.inputs

    config.set_default_config()

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.8'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    yield assert_raises, Exception, obj._check_version_requirements

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.10'
    obj = DerivedInterface1()
    yield assert_not_raises, obj._check_version_requirements, obj.inputs

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.9'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    not_raised = True
    yield assert_not_raises, obj._check_version_requirements, obj.inputs

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', max_ver='0.7')

    class DerivedInterface2(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.8'
    obj = DerivedInterface2()
    obj.inputs.foo = 1
    yield assert_raises, Exception, obj._check_version_requirements

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', max_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.9'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    not_raised = True
    yield assert_not_raises, obj._check_version_requirements, obj.inputs


def test_output_version():
    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')

    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        output_spec = OutputSpec
        _version = '0.10'
    obj = DerivedInterface1()
    yield assert_equal, obj._check_version_requirements(obj._outputs()), []

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')

    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.11')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        output_spec = OutputSpec
        _version = '0.10'
    obj = DerivedInterface1()
    yield assert_equal, obj._check_version_requirements(obj._outputs()), ['foo']

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')

    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.11')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        output_spec = OutputSpec
        _version = '0.10'

        def _run_interface(self, runtime):
            return runtime

        def _list_outputs(self):
            return {'foo': 1}
    obj = DerivedInterface1()
    yield assert_raises, KeyError, obj.run


def test_Commandline():
    yield assert_raises, Exception, nib.CommandLine
    ci = nib.CommandLine(command='which')
    yield assert_equal, ci.cmd, 'which'
    yield assert_equal, ci.inputs.args, Undefined
    ci2 = nib.CommandLine(command='which', args='ls')
    yield assert_equal, ci2.cmdline, 'which ls'
    ci3 = nib.CommandLine(command='echo')
    ci3.inputs.environ = {'MYENV': 'foo'}
    res = ci3.run()
    yield assert_equal, res.runtime.environ['MYENV'], 'foo'
    yield assert_equal, res.outputs, None

    class CommandLineInputSpec1(nib.CommandLineInputSpec):
        foo = nib.traits.Str(argstr='%s', desc='a str')
        goo = nib.traits.Bool(argstr='-g', desc='a bool', position=0)
        hoo = nib.traits.List(argstr='-l %s', desc='a list')
        moo = nib.traits.List(argstr='-i %d...', desc='a repeated list',
                              position=-1)
        noo = nib.traits.Int(argstr='-x %d', desc='an int')
        roo = nib.traits.Str(desc='not on command line')
        soo = nib.traits.Bool(argstr="-soo")
    nib.CommandLine.input_spec = CommandLineInputSpec1
    ci4 = nib.CommandLine(command='cmd')
    ci4.inputs.foo = 'foo'
    ci4.inputs.goo = True
    ci4.inputs.hoo = ['a', 'b']
    ci4.inputs.moo = [1, 2, 3]
    ci4.inputs.noo = 0
    ci4.inputs.roo = 'hello'
    ci4.inputs.soo = False
    cmd = ci4._parse_inputs()
    yield assert_equal, cmd[0], '-g'
    yield assert_equal, cmd[-1], '-i 1 -i 2 -i 3'
    yield assert_true, 'hello' not in ' '.join(cmd)
    yield assert_true, '-soo' not in ' '.join(cmd)
    ci4.inputs.soo = True
    cmd = ci4._parse_inputs()
    yield assert_true, '-soo' in ' '.join(cmd)

    class CommandLineInputSpec2(nib.CommandLineInputSpec):
        foo = nib.File(argstr='%s', desc='a str', genfile=True)
    nib.CommandLine.input_spec = CommandLineInputSpec2
    ci5 = nib.CommandLine(command='cmd')
    yield assert_raises, NotImplementedError, ci5._parse_inputs

    class DerivedClass(nib.CommandLine):
        input_spec = CommandLineInputSpec2

        def _gen_filename(self, name):
            return 'filename'

    ci6 = DerivedClass(command='cmd')
    yield assert_equal, ci6._parse_inputs()[0], 'filename'
    nib.CommandLine.input_spec = nib.CommandLineInputSpec


def test_Commandline_environ():
    from nipype import config
    config.set_default_config()
    ci3 = nib.CommandLine(command='echo')
    res = ci3.run()
    yield assert_equal, res.runtime.environ['DISPLAY'], ':1'
    config.set('execution', 'display_variable', ':3')
    res = ci3.run()
    yield assert_false, 'DISPLAY' in ci3.inputs.environ
    yield assert_equal, res.runtime.environ['DISPLAY'], ':3'
    ci3.inputs.environ = {'DISPLAY': ':2'}
    res = ci3.run()
    yield assert_equal, res.runtime.environ['DISPLAY'], ':2'


def test_CommandLine_output():
    tmp_infile = setup_file()
    tmpd, name = os.path.split(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)
    yield assert_true, os.path.exists(tmp_infile)
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'allatonce'
    res = ci.run()
    yield assert_equal, res.runtime.merged, ''
    yield assert_true, name in res.runtime.stdout
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'file'
    res = ci.run()
    yield assert_true, 'stdout.nipype' in res.runtime.stdout
    yield assert_equal, type(res.runtime.stdout), text_type
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'none'
    res = ci.run()
    yield assert_equal, res.runtime.stdout, ''
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    yield assert_true, 'stdout.nipype' in res.runtime.stdout
    os.chdir(pwd)
    teardown_file(tmpd)


def test_global_CommandLine_output():
    tmp_infile = setup_file()
    tmpd, name = os.path.split(tmp_infile)
    pwd = os.getcwd()
    os.chdir(tmpd)
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    yield assert_true, name in res.runtime.stdout
    yield assert_true, os.path.exists(tmp_infile)
    nib.CommandLine.set_default_terminal_output('allatonce')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    yield assert_equal, res.runtime.merged, ''
    yield assert_true, name in res.runtime.stdout
    nib.CommandLine.set_default_terminal_output('file')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    yield assert_true, 'stdout.nipype' in res.runtime.stdout
    nib.CommandLine.set_default_terminal_output('none')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    yield assert_equal, res.runtime.stdout, ''
    os.chdir(pwd)
    teardown_file(tmpd)
