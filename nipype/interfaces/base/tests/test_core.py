# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
from future import standard_library
from builtins import open
import os
import simplejson as json

import pytest

from .... import config
from ....testing import example_data
from ... import base as nib

standard_library.install_aliases()


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


def test_Interface():
    assert nib.Interface.input_spec is None
    assert nib.Interface.output_spec is None
    with pytest.raises(NotImplementedError):
        nib.Interface()
    with pytest.raises(NotImplementedError):
        nib.Interface.help()
    with pytest.raises(NotImplementedError):
        nib.Interface._inputs_help()
    with pytest.raises(NotImplementedError):
        nib.Interface._outputs_help()
    with pytest.raises(NotImplementedError):
        nib.Interface._outputs()

    class DerivedInterface(nib.Interface):
        def __init__(self):
            pass

    nif = DerivedInterface()
    with pytest.raises(NotImplementedError):
        nif.run()
    with pytest.raises(NotImplementedError):
        nif.aggregate_outputs()
    with pytest.raises(NotImplementedError):
        nif._list_outputs()
    with pytest.raises(NotImplementedError):
        nif._get_filecopy_info()


def test_BaseInterface():
    config.set('monitoring', 'enable', '0')

    assert nib.BaseInterface.help() is None
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
        resource_monitor = False

    assert DerivedInterface.help() is None
    assert 'moo' in ''.join(DerivedInterface._inputs_help())
    assert DerivedInterface()._outputs() is None
    assert DerivedInterface._get_filecopy_info()[0]['key'] == 'woo'
    assert DerivedInterface._get_filecopy_info()[0]['copy']
    assert DerivedInterface._get_filecopy_info()[1]['key'] == 'zoo'
    assert not DerivedInterface._get_filecopy_info()[1]['copy']
    assert DerivedInterface().inputs.foo == nib.Undefined
    with pytest.raises(ValueError):
        DerivedInterface()._check_mandatory_inputs()
    assert DerivedInterface(goo=1)._check_mandatory_inputs() is None
    with pytest.raises(ValueError):
        DerivedInterface().run()
    with pytest.raises(NotImplementedError):
        DerivedInterface(goo=1).run()

    class DerivedInterface2(DerivedInterface):
        output_spec = OutputSpec

        def _run_interface(self, runtime):
            return runtime

    assert DerivedInterface2.help() is None
    assert DerivedInterface2()._outputs().foo == nib.Undefined
    with pytest.raises(NotImplementedError):
        DerivedInterface2(goo=1).run()

    default_inpu_spec = nib.BaseInterface.input_spec
    nib.BaseInterface.input_spec = None
    with pytest.raises(Exception):
        nib.BaseInterface()
    nib.BaseInterface.input_spec = default_inpu_spec


def test_BaseInterface_load_save_inputs(tmpdir):
    tmp_json = tmpdir.join('settings.json').strpath

    class InputSpec(nib.TraitedSpec):
        input1 = nib.traits.Int()
        input2 = nib.traits.Float()
        input3 = nib.traits.Bool()
        input4 = nib.traits.Str()

    class DerivedInterface(nib.BaseInterface):
        input_spec = InputSpec

        def __init__(self, **inputs):
            super(DerivedInterface, self).__init__(**inputs)

    inputs_dict = {'input1': 12, 'input3': True, 'input4': 'some string'}
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
    settings = example_data(
        example_data('smri_ants_registration_settings.json'))
    with open(settings) as setf:
        data_dict = json.load(setf)

    tsthash = Registration()
    tsthash.load_inputs_from_json(settings)
    assert {} == check_dict(data_dict, tsthash.inputs.get_traitsfree())

    tsthash2 = Registration(from_file=settings)
    assert {} == check_dict(data_dict, tsthash2.inputs.get_traitsfree())

    _, hashvalue = tsthash.inputs.get_hashval(hash_method='timestamp')
    assert '8562a5623562a871115eb14822ee8d02' == hashvalue


class MinVerInputSpec(nib.TraitedSpec):
    foo = nib.traits.Int(desc='a random int', min_ver='0.9')

class MaxVerInputSpec(nib.TraitedSpec):
    foo = nib.traits.Int(desc='a random int', max_ver='0.7')


def test_input_version_1():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec

    obj = DerivedInterface1()
    obj._check_version_requirements(obj.inputs)

    config.set('execution', 'stop_on_unknown_version', True)

    with pytest.raises(ValueError) as excinfo:
        obj._check_version_requirements(obj.inputs)
    assert "no version information" in str(excinfo.value)

    config.set_default_config()


def test_input_version_2():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec
        _version = '0.8'

    obj = DerivedInterface1()
    obj.inputs.foo = 1
    with pytest.raises(Exception) as excinfo:
        obj._check_version_requirements(obj.inputs)
    assert "version 0.8 < required 0.9" in str(excinfo.value)


def test_input_version_3():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec
        _version = '0.10'

    obj = DerivedInterface1()
    obj._check_version_requirements(obj.inputs)


def test_input_version_4():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec
        _version = '0.9'

    obj = DerivedInterface1()
    obj.inputs.foo = 1
    obj._check_version_requirements(obj.inputs)


def test_input_version_5():
    class DerivedInterface2(nib.BaseInterface):
        input_spec = MaxVerInputSpec
        _version = '0.8'

    obj = DerivedInterface2()
    obj.inputs.foo = 1
    with pytest.raises(Exception) as excinfo:
        obj._check_version_requirements(obj.inputs)
    assert "version 0.8 > required 0.7" in str(excinfo.value)


def test_input_version_6():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MaxVerInputSpec
        _version = '0.7'

    obj = DerivedInterface1()
    obj.inputs.foo = 1
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
        resource_monitor = False

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
        resource_monitor = False

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
        resource_monitor = False

        def _run_interface(self, runtime):
            return runtime

        def _list_outputs(self):
            return {'foo': 1}

    obj = DerivedInterface1()
    with pytest.raises(KeyError):
        obj.run()


def test_Commandline():
    with pytest.raises(Exception):
        nib.CommandLine()
    ci = nib.CommandLine(command='which')
    assert ci.cmd == 'which'
    assert ci.inputs.args == nib.Undefined
    ci2 = nib.CommandLine(command='which', args='ls')
    assert ci2.cmdline == 'which ls'
    ci3 = nib.CommandLine(command='echo')
    ci3.resource_monitor = False
    ci3.inputs.environ = {'MYENV': 'foo'}
    res = ci3.run()
    assert res.runtime.environ['MYENV'] == 'foo'
    assert res.outputs is None

    class CommandLineInputSpec1(nib.CommandLineInputSpec):
        foo = nib.Str(argstr='%s', desc='a str')
        goo = nib.traits.Bool(argstr='-g', desc='a bool', position=0)
        hoo = nib.traits.List(argstr='-l %s', desc='a list')
        moo = nib.traits.List(
            argstr='-i %d...', desc='a repeated list', position=-1)
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
    with pytest.raises(NotImplementedError):
        ci5._parse_inputs()

    class DerivedClass(nib.CommandLine):
        input_spec = CommandLineInputSpec2

        def _gen_filename(self, name):
            return 'filename'

    ci6 = DerivedClass(command='cmd')
    assert ci6._parse_inputs()[0] == 'filename'
    nib.CommandLine.input_spec = nib.CommandLineInputSpec


def test_Commandline_environ(monkeypatch, tmpdir):
    from nipype import config
    config.set_default_config()

    tmpdir.chdir()
    monkeypatch.setitem(os.environ, 'DISPLAY', ':1')
    # Test environment
    ci3 = nib.CommandLine(command='echo')
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':1'

    # Test display_variable option
    monkeypatch.delitem(os.environ, 'DISPLAY', raising=False)
    config.set('execution', 'display_variable', ':3')
    res = ci3.run()
    assert 'DISPLAY' not in ci3.inputs.environ
    assert 'DISPLAY' not in res.runtime.environ

    # If the interface has _redirect_x then yes, it should be set
    ci3._redirect_x = True
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':3'

    # Test overwrite
    monkeypatch.setitem(os.environ, 'DISPLAY', ':1')
    ci3.inputs.environ = {'DISPLAY': ':2'}
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':2'


def test_CommandLine_output(tmpdir):
    # Create one file
    tmpdir.chdir()
    file = tmpdir.join('foo.txt')
    file.write('123456\n')
    name = os.path.basename(file.strpath)

    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'allatonce'
    res = ci.run()
    assert res.runtime.merged == ''
    assert name in res.runtime.stdout

    # Check stdout is written
    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'file_stdout'
    res = ci.run()
    assert os.path.isfile('stdout.nipype')
    assert name in res.runtime.stdout
    tmpdir.join('stdout.nipype').remove(ignore_errors=True)

    # Check stderr is written
    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'file_stderr'
    res = ci.run()
    assert os.path.isfile('stderr.nipype')
    tmpdir.join('stderr.nipype').remove(ignore_errors=True)

    # Check outputs are thrown away
    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'none'
    res = ci.run()
    assert res.runtime.stdout == '' and \
        res.runtime.stderr == '' and \
        res.runtime.merged == ''

    # Check that new interfaces are set to default 'stream'
    ci = nib.CommandLine(command='ls -l')
    res = ci.run()
    assert ci.terminal_output == 'stream'
    assert name in res.runtime.stdout and \
        res.runtime.stderr == ''

    # Check only one file is generated
    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'file'
    res = ci.run()
    assert os.path.isfile('output.nipype')
    assert name in res.runtime.merged and \
        res.runtime.stdout == '' and \
        res.runtime.stderr == ''
    tmpdir.join('output.nipype').remove(ignore_errors=True)

    # Check split files are generated
    ci = nib.CommandLine(command='ls -l')
    ci.terminal_output = 'file_split'
    res = ci.run()
    assert os.path.isfile('stdout.nipype')
    assert os.path.isfile('stderr.nipype')
    assert name in res.runtime.stdout


def test_global_CommandLine_output(tmpdir):
    """Ensures CommandLine.set_default_terminal_output works"""
    from nipype.interfaces.fsl import BET

    ci = nib.CommandLine(command='ls -l')
    assert ci.terminal_output == 'stream'  # default case

    ci = BET()
    assert ci.terminal_output == 'stream'  # default case

    nib.CommandLine.set_default_terminal_output('allatonce')
    ci = nib.CommandLine(command='ls -l')
    assert ci.terminal_output == 'allatonce'

    nib.CommandLine.set_default_terminal_output('file')
    ci = nib.CommandLine(command='ls -l')
    assert ci.terminal_output == 'file'

    # Check default affects derived interfaces
    ci = BET()
    assert ci.terminal_output == 'file'


def test_CommandLine_prefix(tmpdir):
    tmpdir.chdir()
    oop = 'out/of/path'
    os.makedirs(oop)

    script_name = 'test_script.sh'
    script_path = os.path.join(oop, script_name)
    with open(script_path, 'w') as script_f:
        script_f.write('#!/usr/bin/env bash\necho Success!')
    os.chmod(script_path, 0o755)

    ci = nib.CommandLine(command=script_name)
    with pytest.raises(IOError):
        ci.run()

    class OOPCLI(nib.CommandLine):
        _cmd_prefix = oop + '/'

    ci = OOPCLI(command=script_name)
    ci.run()

    class OOPShell(nib.CommandLine):
        _cmd_prefix = 'bash {}/'.format(oop)

    ci = OOPShell(command=script_name)
    ci.run()

    class OOPBadShell(nib.CommandLine):
        _cmd_prefix = 'shell_dne {}/'.format(oop)

    ci = OOPBadShell(command=script_name)
    with pytest.raises(IOError):
        ci.run()


def test_runtime_checks():
    class TestInterface(nib.BaseInterface):
        class input_spec(nib.TraitedSpec):
            a = nib.traits.Any()
        class output_spec(nib.TraitedSpec):
            b = nib.traits.Any()

        def _run_interface(self, runtime):
            return runtime

    class NoRuntime(TestInterface):
        def _run_interface(self, runtime):
            return None

    class BrokenRuntime(TestInterface):
        def _run_interface(self, runtime):
            del runtime.__dict__['cwd']
            return runtime

    with pytest.raises(RuntimeError):
        NoRuntime().run()

    with pytest.raises(RuntimeError):
        BrokenRuntime().run()
