# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
from future import standard_library
standard_library.install_aliases()

from builtins import open, str, bytes
import os
import warnings
import simplejson as json

import pytest
from nipype.testing import example_data

import nipype.interfaces.base as nib
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import Undefined, config
import traits.api as traits

@pytest.mark.parametrize("args", [
        {},
        {'a' : 1, 'b' : [2, 3]}
])
def test_bunch(args):
    b = nib.Bunch(**args)
    assert b.__dict__ == args


def test_bunch_attribute():
    b = nib.Bunch(a=1, b=[2, 3], c=None)
    assert b.a == 1
    assert b.b == [2, 3]
    assert b.c == None


def test_bunch_repr():
    b = nib.Bunch(b=2, c=3, a=dict(n=1, m=2))
    assert repr(b) == "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"


def test_bunch_methods():
    b = nib.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    assert b.a == 3
    assert b.get('a') == 3
    assert b.get('badkey', 'otherthing') == 'otherthing'
    assert b != newb
    assert type(dict()) == type(newb)
    assert newb['a'] == 3


def test_bunch_hash():
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    pth = os.path.split(os.path.abspath(__file__))[0]
    json_pth = os.path.join(pth, 'realign_json.json')
    b = nib.Bunch(infile=json_pth,
                  otherthing='blue',
                  yat=True)
    newbdict, bhash = b._get_bunch_hash()
    assert bhash == 'ddcc7b4ec5675df8cf317a48bd1857fa'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nib.md5()
    with open(json_pth, 'r') as fp:
        jshash.update(fp.read().encode('utf-8'))
    assert newbdict['infile'][0][1] == jshash.hexdigest()
    assert newbdict['yat'] == True


@pytest.fixture(scope="module")
def setup_file(request, tmpdir_factory):
    tmp_dir = str(tmpdir_factory.mktemp('files'))
    tmp_infile = os.path.join(tmp_dir, 'foo.txt')
    with open(tmp_infile, 'w') as fp:
        fp.writelines([u'123456789'])

    os.chdir(tmp_dir)

    return tmp_infile


def test_TraitedSpec():
    assert nib.TraitedSpec().get_hashval()
    assert nib.TraitedSpec().__repr__() == '\n\n'

    class spec(nib.TraitedSpec):
        foo = nib.traits.Int
        goo = nib.traits.Float(usedefault=True)

    assert spec().foo == Undefined
    assert spec().goo == 0.0
    specfunc = lambda x: spec(hoo=x)
    with pytest.raises(nib.traits.TraitError): specfunc(1)
    infields = spec(foo=1)
    hashval = ([('foo', 1), ('goo', '0.0000000000')], 'e89433b8c9141aa0fda2f8f4d662c047')
    assert infields.get_hashval() == hashval
    assert infields.__repr__() == '\nfoo = 1\ngoo = 0.0\n'


@pytest.mark.skip
def test_TraitedSpec_dynamic():
    from pickle import dumps, loads
    a = nib.BaseTraitedSpec()
    a.add_trait('foo', nib.traits.Int)
    a.foo = 1
    assign_a = lambda: setattr(a, 'foo', 'a')
    with pytest.raises(Exception): assign_a
    pkld_a = dumps(a)
    unpkld_a = loads(pkld_a)
    assign_a_again = lambda: setattr(unpkld_a, 'foo', 'a')
    with pytest.raises(Exception): assign_a_again


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
    # NOTE_dj, FAIL: I don't get a TypeError, only a UserWarning
    #with pytest.raises(TypeError):
    #    setattr(myif.inputs, 'kung', 10.0)
    myif.inputs.foo = 1
    assert myif.inputs.foo == 1
    set_bar = lambda: setattr(myif.inputs, 'bar', 1)
    with pytest.raises(IOError): set_bar()
    assert myif.inputs.foo == 1
    myif.inputs.kung = 2
    assert myif.inputs.kung == 2.0


def test_deprecation():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec1(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='0.1')
        spec_instance = DeprecationSpec1()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        with pytest.raises(nib.TraitError): set_foo()
        assert len(w) == 0, 'no warnings, just errors'


    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        class DeprecationSpec2(nib.TraitedSpec):
            foo = nib.traits.Int(deprecated='100', new_name='bar')
        spec_instance = DeprecationSpec2()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        with pytest.raises(nib.TraitError): set_foo()
        assert len(w) == 0, 'no warnings, just errors'

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
        assert not_raised
        assert len(w) == 1, 'deprecated warning 1 %s' % [w1.message for w1 in w]

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
        assert not_raised
        assert spec_instance.foo == Undefined
        assert spec_instance.bar == 1
        assert len(w) == 1, 'deprecated warning 2 %s' % [w1.message for w1 in w]


def test_namesource(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

    class spec2(nib.CommandLineInputSpec):
        moo = nib.File(name_source=['doo'], hash_files=False, argstr="%s",
                       position=2)
        doo = nib.File(exists=True, argstr="%s", position=1)
        goo = traits.Int(argstr="%d", position=4)
        poo = nib.File(name_source=['goo'], hash_files=False, argstr="%s",
                       position=3)

    class TestName(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec2
    testobj = TestName()
    testobj.inputs.doo = tmp_infile
    testobj.inputs.goo = 99
    assert '%s_generated' % nme in testobj.cmdline
    assert '%d_generated' % testobj.inputs.goo in testobj.cmdline
    testobj.inputs.moo = "my_%s_template"
    assert 'my_%s_template' % nme in testobj.cmdline


def test_chained_namesource(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

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
    assert '%s' % tmp_infile in res
    assert '%s_mootpl ' % nme in res
    assert '%s_mootpl_generated' % nme in res


def test_cycle_namesource1(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

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
    assert not not_raised


def test_cycle_namesource2(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

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

    assert not_raised
    assert '%s' % tmp_infile in res
    assert '%s_generated' % nme in res
    assert '%s_generated_mootpl' % nme in res


def test_TraitedSpec_withFile(setup_file):
    tmp_infile = setup_file
    tmpd, nme = os.path.split(tmp_infile)
    assert os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec2(moo=tmp_infile, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    assert hashval[1] == 'a00e9ee24f5bfa9545a515b7a759886b'


def test_TraitedSpec_withNoFileHashing(setup_file):
    tmp_infile = setup_file
    tmpd, nme = os.path.split(tmp_infile)
    assert os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True, hash_files=False)
        doo = nib.traits.List(nib.File(exists=True))
    infields = spec2(moo=nme, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    assert hashval[1] == '8da4669ff5d72f670a46ea3e7a203215'

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
    assert hashval1[1] != hashval2[1]


def test_Interface():
    assert nib.Interface.input_spec == None
    assert nib.Interface.output_spec == None
    with pytest.raises(NotImplementedError): nib.Interface()
    with pytest.raises(NotImplementedError): nib.Interface.help()
    with pytest.raises(NotImplementedError): nib.Interface._inputs_help()
    with pytest.raises(NotImplementedError): nib.Interface._outputs_help()
    with pytest.raises(NotImplementedError): nib.Interface._outputs()

    class DerivedInterface(nib.Interface):
        def __init__(self):
            pass

    nif = DerivedInterface()
    with pytest.raises(NotImplementedError): nif.run()
    with pytest.raises(NotImplementedError): nif.aggregate_outputs()
    with pytest.raises(NotImplementedError): nif._list_outputs()
    with pytest.raises(NotImplementedError): nif._get_filecopy_info()


def test_BaseInterface():
    assert nib.BaseInterface.help() == None
    assert nib.BaseInterface._get_filecopy_info() == []

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

    assert DerivedInterface.help() == None
    assert 'moo' in ''.join(DerivedInterface._inputs_help())
    assert DerivedInterface()._outputs() == None
    assert DerivedInterface._get_filecopy_info()[0]['key'] == 'woo'
    assert DerivedInterface._get_filecopy_info()[0]['copy']
    assert DerivedInterface._get_filecopy_info()[1]['key'] == 'zoo'
    assert not DerivedInterface._get_filecopy_info()[1]['copy']
    assert DerivedInterface().inputs.foo == Undefined
    with pytest.raises(ValueError): DerivedInterface()._check_mandatory_inputs()
    assert DerivedInterface(goo=1)._check_mandatory_inputs() == None
    with pytest.raises(ValueError): DerivedInterface().run()
    with pytest.raises(NotImplementedError): DerivedInterface(goo=1).run()

    class DerivedInterface2(DerivedInterface):
        output_spec = OutputSpec

        def _run_interface(self, runtime):
            return runtime

    assert DerivedInterface2.help() == None
    assert DerivedInterface2()._outputs().foo == Undefined
    with pytest.raises(NotImplementedError): DerivedInterface2(goo=1).run()

    default_inpu_spec = nib.BaseInterface.input_spec
    nib.BaseInterface.input_spec = None
    with pytest.raises(Exception): nib.BaseInterface()
    nib.BaseInterface.input_spec = default_inpu_spec


def test_BaseInterface_load_save_inputs(tmpdir):
    tmp_json = os.path.join(str(tmpdir), 'settings.json')

    class InputSpec(nib.TraitedSpec):
        input1 = nib.traits.Int()
        input2 = nib.traits.Float()
        input3 = nib.traits.Bool()
        input4 = nib.traits.Str()

    class DerivedInterface(nib.BaseInterface):
        input_spec = InputSpec

        def __init__(self, **inputs):
            super(DerivedInterface, self).__init__(**inputs)

    inputs_dict = {'input1': 12, 'input3': True,
                   'input4': 'some string'}
    bif = DerivedInterface(**inputs_dict)
    bif.save_inputs_to_json(tmp_json)
    bif2 = DerivedInterface()
    bif2.load_inputs_from_json(tmp_json)
    assert bif2.inputs.get_traitsfree() == inputs_dict

    bif3 = DerivedInterface(from_file=tmp_json)
    assert bif3.inputs.get_traitsfree() == inputs_dict

    inputs_dict2 = inputs_dict.copy()
    inputs_dict2.update({'input4': 'some other string'})
    bif4 = DerivedInterface(from_file=tmp_json, input4=inputs_dict2['input4'])
    assert bif4.inputs.get_traitsfree() == inputs_dict2

    bif5 = DerivedInterface(input4=inputs_dict2['input4'])
    bif5.load_inputs_from_json(tmp_json, overwrite=False)
    assert bif5.inputs.get_traitsfree() == inputs_dict2

    bif6 = DerivedInterface(input4=inputs_dict2['input4'])
    bif6.load_inputs_from_json(tmp_json)
    assert bif6.inputs.get_traitsfree() == inputs_dict

    # test get hashval in a complex interface
    from nipype.interfaces.ants import Registration
    settings = example_data(example_data('smri_ants_registration_settings.json'))
    with open(settings) as setf:
        data_dict = json.load(setf)

    tsthash = Registration()
    tsthash.load_inputs_from_json(settings)
    assert {} == check_dict(data_dict, tsthash.inputs.get_traitsfree())

    tsthash2 = Registration(from_file=settings)
    assert {} == check_dict(data_dict, tsthash2.inputs.get_traitsfree())

    _, hashvalue = tsthash.inputs.get_hashval(hash_method='timestamp')
    assert 'ec5755e07287e04a4b409e03b77a517c' == hashvalue


def test_input_version():
    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
    obj = DerivedInterface1()
    obj._check_version_requirements(obj.inputs)

    config.set('execution', 'stop_on_unknown_version', True)

    with pytest.raises(Exception): obj._check_version_requirements(obj.inputs)

    config.set_default_config()

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.8'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    with pytest.raises(Exception): obj._check_version_requirements()

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.10'
    obj = DerivedInterface1()
    obj._check_version_requirements(obj.inputs)

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.9'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    not_raised = True
    obj._check_version_requirements(obj.inputs)

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', max_ver='0.7')

    class DerivedInterface2(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.8'
    obj = DerivedInterface2()
    obj.inputs.foo = 1
    with pytest.raises(Exception): obj._check_version_requirements()

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', max_ver='0.9')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        _version = '0.9'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    not_raised = True
    obj._check_version_requirements(obj.inputs)


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
    assert obj._check_version_requirements(obj._outputs()) == []

    class InputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int')

    class OutputSpec(nib.TraitedSpec):
        foo = nib.traits.Int(desc='a random int', min_ver='0.11')

    class DerivedInterface1(nib.BaseInterface):
        input_spec = InputSpec
        output_spec = OutputSpec
        _version = '0.10'
    obj = DerivedInterface1()
    assert obj._check_version_requirements(obj._outputs()) == ['foo']

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
    with pytest.raises(KeyError): obj.run()


def test_Commandline():
    with pytest.raises(Exception): nib.CommandLine()
    ci = nib.CommandLine(command='which')
    assert ci.cmd == 'which'
    assert ci.inputs.args == Undefined
    ci2 = nib.CommandLine(command='which', args='ls')
    assert ci2.cmdline == 'which ls'
    ci3 = nib.CommandLine(command='echo')
    ci3.inputs.environ = {'MYENV': 'foo'}
    res = ci3.run()
    assert res.runtime.environ['MYENV'] == 'foo'
    assert res.outputs == None

    class CommandLineInputSpec1(nib.CommandLineInputSpec):
        foo = nib.Str(argstr='%s', desc='a str')
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
    assert cmd[0] == '-g'
    assert cmd[-1] == '-i 1 -i 2 -i 3'
    assert 'hello' not in ' '.join(cmd)
    assert '-soo' not in ' '.join(cmd)
    ci4.inputs.soo = True
    cmd = ci4._parse_inputs()
    assert '-soo' in ' '.join(cmd)

    class CommandLineInputSpec2(nib.CommandLineInputSpec):
        foo = nib.File(argstr='%s', desc='a str', genfile=True)
    nib.CommandLine.input_spec = CommandLineInputSpec2
    ci5 = nib.CommandLine(command='cmd')
    with pytest.raises(NotImplementedError): ci5._parse_inputs()

    class DerivedClass(nib.CommandLine):
        input_spec = CommandLineInputSpec2

        def _gen_filename(self, name):
            return 'filename'

    ci6 = DerivedClass(command='cmd')
    assert ci6._parse_inputs()[0] == 'filename'
    nib.CommandLine.input_spec = nib.CommandLineInputSpec


def test_Commandline_environ():
    from nipype import config
    config.set_default_config()
    ci3 = nib.CommandLine(command='echo')
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':1'
    config.set('execution', 'display_variable', ':3')
    res = ci3.run()
    assert not 'DISPLAY' in ci3.inputs.environ
    assert res.runtime.environ['DISPLAY'] == ':3'
    ci3.inputs.environ = {'DISPLAY': ':2'}
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':2'


def test_CommandLine_output(setup_file):
    tmp_infile = setup_file
    tmpd, name = os.path.split(tmp_infile)
    assert os.path.exists(tmp_infile)
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'allatonce'
    res = ci.run()
    assert res.runtime.merged == ''
    assert name in res.runtime.stdout
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'file'
    res = ci.run()
    assert 'stdout.nipype' in res.runtime.stdout
    assert isinstance(res.runtime.stdout, (str, bytes))
    ci = nib.CommandLine(command='ls -l')
    ci.inputs.terminal_output = 'none'
    res = ci.run()
    assert res.runtime.stdout == ''
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert 'stdout.nipype' in res.runtime.stdout


def test_global_CommandLine_output(setup_file):
    tmp_infile = setup_file
    tmpd, name = os.path.split(tmp_infile)
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert name in res.runtime.stdout
    assert os.path.exists(tmp_infile)
    nib.CommandLine.set_default_terminal_output('allatonce')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert res.runtime.merged == ''
    assert name in res.runtime.stdout
    nib.CommandLine.set_default_terminal_output('file')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert 'stdout.nipype' in res.runtime.stdout
    nib.CommandLine.set_default_terminal_output('none')
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert res.runtime.stdout == ''


def check_dict(ref_dict, tst_dict):
    """Compare dictionaries of inputs and and those loaded from json files"""
    def to_list(x):
        if isinstance(x, tuple):
            x = list(x)

        if isinstance(x, list):
            for i, xel in enumerate(x):
                x[i] = to_list(xel)

        return x

    failed_dict = {}
    for key, value in list(ref_dict.items()):
        newval = to_list(tst_dict[key])
        if newval != value:
            failed_dict[key] = (value, newval)
    return failed_dict

def test_ImageFile():
    x = nib.BaseInterface().inputs

    # setup traits
    x.add_trait('nifti', nib.ImageFile(types=['nifti1', 'dicom']))
    x.add_trait('anytype', nib.ImageFile())
    x.add_trait('newtype', nib.ImageFile(types=['nifti10']))
    x.add_trait('nocompress', nib.ImageFile(types=['mgh'],
                                            allow_compressed=False))

    with pytest.raises(nib.TraitError): x.nifti = 'test.mgz'
    x.nifti = 'test.nii'
    x.anytype = 'test.xml'
    with pytest.raises(AttributeError): x.newtype = 'test.nii'
    with pytest.raises(nib.TraitError): x.nocompress = 'test.nii.gz'
    x.nocompress = 'test.mgh'
