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

import pytest, pdb
from nipype.testing import example_data

import nipype.interfaces.base as nib
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import config
import traitlets

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
    assert b.c is None

def test_bunch_set():
    b = nib.Bunch(a=1, b=[2, 3], c=None)
    b.set(c="str", a=3)
    assert b.a == 3
    assert b.b == [2, 3]
    assert b.c == "str"


def test_bunch_repr():
    b = nib.Bunch(b=2, c=3, a=dict(n=1, m=2))
    assert repr(b) == "Bunch(a={'m': 2, 'n': 1}, b=2, c=3)"


def test_bunch_methods():
    b = nib.Bunch(a=2)
    b.update(a=3)
    newb = b.dictcopy()
    assert b.a == 3
    assert b.get('a') == 3

    # dj TOASK: do we want to have an error or just None?
    assert b.get('badkey') is None
    assert b.get('badkey', 'otherthing') == 'otherthing' # changing default value 

    assert b is not newb
    assert type(newb) is dict
    assert newb == b.__dict__
    assert newb['a'] == 3


@pytest.mark.parametrize("infile_inp", ["json_pth", "[json_pth]"])
def test_bunch_hash(infile_inp):
    # NOTE: Since the path to the json file is included in the Bunch,
    # the hash will be unique to each machine.
    pth = os.path.split(os.path.abspath(__file__))[0]
    json_pth = os.path.join(pth, 'realign_json.json')
    b = nib.Bunch(infile=eval(infile_inp),
                  otherthing='blue',
                  yat=True)
    # newdict contains filename and its hash value for infile field
    # bhash is a hash value for the dictionary without filename (so can be compare)
    newbdict, bhash = b._get_bunch_hash()
    assert bhash == 'ddcc7b4ec5675df8cf317a48bd1857fa'
    # Make sure the hash stored in the json file for `infile` is correct.
    jshash = nib.md5()
    with open(json_pth, 'r') as fp:
        jshash.update(fp.read().encode('utf-8'))
    assert newbdict['infile'][0][1] == jshash.hexdigest()
    assert newbdict['yat'] == True
    assert newbdict['otherthing'] == 'blue'


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
        foo = nib.Int()
        goo = nib.Float()

    assert spec().foo is None
    assert spec().goo is None

    # dj NOTE/TODO: this will not give an error, don't have Disallow
    #specfunc = lambda x: spec(hoo=x)
    #with pytest.raises(nib.traits.TraitError): specfunc(1)

    infields = spec(foo=1, goo=0.)
    hashval = ([('foo', 1), ('goo', '0.0000000000')], 'e89433b8c9141aa0fda2f8f4d662c047')
    assert infields.get_hashval() == hashval
    assert infields.__repr__() == '\nfoo = 1\ngoo = 0.0\n'


# dj NOTE: this is new test, hope that the hash is correct
def test_TraitedSpec_1():
    class spec(nib.TraitedSpec):
        foo = nib.Dict()
        goo = nib.Int()
    
    infields = spec(foo={"d":2, "g":3}, goo=1)
    hashval = infields.get_hashval()
    assert hashval[1] == '54a882e072c067c1ea9fd656fd27a593'
    assert ('foo', [('d', 2), ('g', 3)]) in hashval[0]
    assert ('goo', 1) in hashval[0]


def test_TraitedSpec_logic():

    class spec3(nib.TraitedSpec):
        _xor_inputs = ('foo', 'bar')

        foo = nib.Int(help='foo or bar, not both').tag(xor=_xor_inputs)
        bar = nib.Int(help='bar or foo, not both', xor=_xor_inputs)
        kung = nib.Float(help='kung foo').tag(requires=('foo',), position=0)

    class out3(nib.TraitedSpec):
        output = nib.Int()

    class MyInterface(nib.BaseInterface):
        input_spec = spec3
        output_spec = out3

    myif = MyInterface()

    # testing help (xor)
    for str_help in ["bar or foo, not both\n\t\tmutually_exclusive: foo, bar",
                     "foo or bar, not both\n\t\tmutually_exclusive: foo, bar"]:
        assert str_help in myif.help(returnhelp=True)

    myif.inputs.foo = 1
    assert myif.inputs.foo == 1

    myif.inputs.kung = 2
    assert myif.inputs.kung == 2.0

    # dj NOTE: this test can't be earlier, since bar is set regardless the error
    set_bar = lambda: setattr(myif.inputs, 'bar', 1)    
    with pytest.raises(IOError): set_bar()


class DeprecationSpec1(nib.TraitedSpec):
    foo = nib.Int().tag(deprecated='0.1')

class DeprecationSpec2(nib.TraitedSpec):
    foo = nib.Int().tag(deprecated='100', new_name='bar')

class DeprecationSpec3(nib.TraitedSpec):
    foo = nib.Int().tag(deprecated='1000', new_name='bar')
    bar = nib.Int()


#dj TOASK: some of those tests check ONLY if there are no warnings??
@pytest.mark.parametrize("DeprecationClass, excinfo_secondpart", [
        (DeprecationSpec1, 'Will be removed or raise an error'),
        (DeprecationSpec2, 'Replacement trait bar not found')
        ])
def test_deprecation_1(DeprecationClass, excinfo_secondpart):
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        spec_instance = DeprecationClass()
        set_foo = lambda: setattr(spec_instance, 'foo', 1)
        with pytest.raises(traitlets.TraitError) as excinfo: 
            set_foo()
        assert 'Input foo in interface %s is deprecated.' % DeprecationClass.__name__ in str(excinfo.value)
        assert excinfo_secondpart in str(excinfo.value)
        assert len(w) == 0, 'no warnings, just errors'


def test_deprecation_2():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        spec_instance = DeprecationSpec3()
        # dj NOTE: din't understand the try/except block, removed
        spec_instance.foo = 1
        assert len(w) == 1, 'deprecated warning 1 %s' % [w1.message for w1 in w]
        assert "Unsetting old value foo; setting new value bar" in str(w[0].message)

def test_deprecation_3():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings('always', '', UserWarning)

        spec_instance = DeprecationSpec3()
        # dj NOTE: din't understand the try/except block, removed
        spec_instance.foo = 1
        assert spec_instance.foo is None
        assert spec_instance.bar == 1
        assert len(w) == 1, 'deprecated warning 2 %s' % [w1.message for w1 in w]
        assert "Unsetting old value foo; setting new value bar" in str(w[0].message)


# dj TODO: just testing a single class, remove at the end (?)
def test_temp_namesource():
    class spec2(nib.CommandLineInputSpec):
        goo = nib.Int()
    ms = spec2(goo=0)
    assert ms.goo == 0


def test_namesource(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)


    class spec2(nib.CommandLineInputSpec):
        moo = nib.Unicode().tag(name_source=['doo'], argstr="%s", position=2)
        doo = nib.File(exists=True).tag(argstr="%s", position=1)
        goo = nib.Int().tag(argstr="%d", position=4)
        poo = nib.Unicode().tag(name_source=['goo'], argstr="%s", position=3)

    class TestName(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec2

    testobj = TestName()
    # testing help (args)
    for str_help in ["flag: %s\n", "flag: %d, position: 4"]:
        assert str_help in testobj.help(returnhelp=True)
    testobj.inputs.doo = tmp_infile 
    testobj.inputs.goo = 99
    assert '%s_generated' % nme in testobj.cmdline
    assert '%d_generated' % testobj.inputs.goo in testobj.cmdline
    testobj.inputs.moo = "my_%s_template"
    assert 'my_%s_template' % nme in testobj.cmdline

    #dj TOASK: if this how moo should be represented in list_withhash and list_nofilename?
    assert ('moo', 'my_%s_template')  in testobj.inputs.get_hashval()[0]


def test_chained_namesource(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

    class spec2(nib.CommandLineInputSpec):
        doo = nib.File(exists=True).tag(argstr="%s", position=1)
        moo = nib.Unicode().tag(name_source=['doo'], 
                             argstr="%s", position=2, name_template='%s_mootpl')
        poo = nib.Unicode().tag(name_source=['moo'], argstr="%s", position=3)

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
        moo = nib.Unicode().tag(name_source=['doo'],
                                argstr="%s", position=1, name_template='%s_mootpl')
        poo = nib.Unicode().tag(name_source=['moo'], argstr="%s", position=2)
        doo = nib.Unicode().tag(name_source=['poo'], argstr="%s", position=3)

    class TestCycle(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec3

    # Check that an exception is raised
    to0 = TestCycle()

    with pytest.raises(nib.NipypeInterfaceError):
        to0.cmdline


def test_cycle_namesource2(setup_file):
    tmp_infile = setup_file
    tmpd, nme, ext = split_filename(tmp_infile)

    class spec3(nib.CommandLineInputSpec):
        moo = nib.Unicode().tag(name_source=['doo'],
                                argstr="%s", position=1, name_template='%s_mootpl')
        poo = nib.Unicode().tag(name_source=['moo'],
                                argstr="%s", position=2)
        doo = nib.Unicode().tag(name_source=['poo'],
                                argstr="%s", position=3)

    class TestCycle(nib.CommandLine):
        _cmd = "mycommand"
        input_spec = spec3

    # Check that loop can be broken by setting one of the inputs
    to1 = TestCycle()
    to1.inputs.poo = tmp_infile

    #dj NOTE: not sure if I understood the try/except block, but removed
    res = to1.cmdline

    assert '%s' % tmp_infile in res
    assert '%s_generated' % nme in res
    assert '%s_generated_mootpl' % nme in res


def test_TraitedSpec_withFile(setup_file):
    tmp_infile = setup_file
    tmpd, nme = os.path.split(tmp_infile)
    assert os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.List(nib.File(exists=True))

    infields = spec2(moo=tmp_infile, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    assert hashval[1] == 'a00e9ee24f5bfa9545a515b7a759886b'

    # should give the same hash
    infields = spec2(moo=tmp_infile, doo=[None])
    infields.doo = [tmp_infile]
    hashval = infields.get_hashval(hash_method='content')
    assert hashval[1] == 'a00e9ee24f5bfa9545a515b7a759886b'



@pytest.mark.parametrize("class_name, name", 
                         [(nib.File, "file"), (nib.Directory, "directory")])
def test_TraitedSpec_withFileOrDirectory_traiterror(class_name, name):

    class spec(nib.TraitedSpec):
        moo = class_name()
        doo = class_name(exists=True)

    with pytest.raises(traitlets.TraitError) as excinfo:
        infields = spec(moo=3)
    assert "instance expected a {} name".format(name) in str(excinfo.value)
    spec(moo="some_string")

    with pytest.raises(traitlets.TraitError) as excinfo:
        infields = spec(doo="some_string")
    assert "instance expected an existing {} name".format(name) in str(excinfo.value)


def test_TraitedSpec_withNoFileHashing(setup_file):
    tmp_infile = setup_file
    tmpd, nme = os.path.split(tmp_infile)
    assert os.path.exists(tmp_infile)

    class spec2(nib.TraitedSpec):
        moo = nib.Unicode()
        doo = nib.List(nib.File(exists=True))
    infields = spec2(moo=nme, doo=[tmp_infile])
    hashval = infields.get_hashval(hash_method='content')
    # dj NOTE: i've changed the hash, since the list_withhash contains now
    # dj NOTE: the name of the file and hash value (since moo is unicode now)
    # dj NOTE: see the second assert for hashval[0][1]
    # dj TOASK: is that how it should be?
    assert hashval[1] == 'a00e9ee24f5bfa9545a515b7a759886b'
    assert hashval[0][1] == ('moo', ('foo.txt', '25f9e794323b453885f5181f1b624d0b'))

    class spec3(nib.TraitedSpec):
        moo = nib.File(exists=True).tag(name_source="doo")
        doo = nib.List(nib.File(exists=True))
    infields = spec3(moo=nme, doo=[tmp_infile])
    hashval1 = infields.get_hashval(hash_method='content')

    class spec4(nib.TraitedSpec):
        moo = nib.File(exists=True)
        doo = nib.List(nib.File(exists=True))
    infields = spec4(moo=nme, doo=[tmp_infile])
    hashval2 = infields.get_hashval(hash_method='content')
    assert hashval1[1] != hashval2[1]


def test_Interface_notimplemented_1():
    assert nib.Interface.input_spec is None
    assert nib.Interface.output_spec is None
    with pytest.raises(NotImplementedError): nib.Interface()
    with pytest.raises(NotImplementedError): nib.Interface.help()
    with pytest.raises(NotImplementedError): nib.Interface._inputs_help()
    with pytest.raises(NotImplementedError): nib.Interface._outputs_help()
    with pytest.raises(NotImplementedError): nib.Interface._outputs()


def test_Interface_notimplemented_2():
    class DerivedInterface(nib.Interface):
        def __init__(self):
            pass

    nif = DerivedInterface()
    with pytest.raises(NotImplementedError): nif.run()
    with pytest.raises(NotImplementedError): nif.aggregate_outputs()
    with pytest.raises(NotImplementedError): nif._list_outputs()
    with pytest.raises(NotImplementedError): nif._get_filecopy_info()



class BaseInterfaceInputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int')
    goo = nib.Int(help='a random int').tag(mandatory=True)
    moo = nib.Int(help='a random int', mandatory=False)
    zoo = nib.File(help='a file').tag(copyfile=False)
    woo = nib.File(help='a file', copyfile=True)


class BaseInterfaceOutputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int')


def test_BaseInterface_1():
    assert nib.BaseInterface.help() is None
    assert nib.BaseInterface._get_filecopy_info() == []


def test_BaseInterface_2():
    class DerivedInterface(nib.BaseInterface):
        input_spec = BaseInterfaceInputSpec

    assert DerivedInterface.help() is None
    #testing help
    for str_help in ["[Mandatory]\n\tgoo: (an int with default_value = None, nipype default value: None)",
                     "[Optional]\n\tfoo: (an int with default_value = None, nipype default value: None)",
                     "Outputs::\n\n\tNone"]:
        assert str_help in DerivedInterface.help(returnhelp=True)

    assert 'moo' in ''.join(DerivedInterface._inputs_help())
    assert DerivedInterface()._outputs() is None
    assert DerivedInterface._get_filecopy_info()[0]['key'] == 'woo'
    assert DerivedInterface._get_filecopy_info()[0]['copy']
    assert DerivedInterface._get_filecopy_info()[1]['key'] == 'zoo'
    assert not DerivedInterface._get_filecopy_info()[1]['copy']
    assert DerivedInterface().inputs.foo is None
    with pytest.raises(ValueError): 
        DerivedInterface()._check_mandatory_inputs()
    assert DerivedInterface(goo=1)._check_mandatory_inputs() is None
    with pytest.raises(ValueError): 
        DerivedInterface().run()
    with pytest.raises(NotImplementedError): 
        DerivedInterface(goo=1).run()


def test_BaseInterface_3():
    class DerivedInterface(nib.BaseInterface):
        input_spec = BaseInterfaceInputSpec

    class DerivedInterface2(DerivedInterface):
        output_spec = BaseInterfaceOutputSpec

        def _run_interface(self, runtime):
            return runtime

    assert DerivedInterface2.help() is None
    assert DerivedInterface2()._outputs().foo is None 
    with pytest.raises(NotImplementedError): 
        DerivedInterface2(goo=1).run()

    default_inpu_spec = nib.BaseInterface.input_spec
    nib.BaseInterface.input_spec = None
    with pytest.raises(Exception): 
        nib.BaseInterface()
    nib.BaseInterface.input_spec = default_inpu_spec


@pytest.mark.parametrize("inp, get_skip_output, get_full_output", [
        ({}, {}, 
         {'inp_int1': None, 'inp_str': None, 'inp_lst1': None}),
        ({'inp_int1': 0}, {'inp_int1': 0},
         {'inp_int1': 0, 'inp_str': None, 'inp_lst1': None}),
        ({'inp_int1': 2, 'inp_str': "text"}, {'inp_int1': 2, 'inp_str': "text"},
         {'inp_int1': 2, 'inp_str': "text", 'inp_lst1': None}),
        ({'inp_int1': 2, 'inp_lst1': [1,2,3]}, {'inp_int1': 2, 'inp_lst1': [1,2,3]},
         {'inp_int1': 2, 'inp_str': None, 'inp_lst1': [1,2,3]}),
        ])
def test_BaseInterface_get(inp, get_skip_output, get_full_output):
    class BaseInterfaceInputSpec(nib.TraitedSpec):
        inp_int1 = nib.Int()
        inp_str = nib.Unicode()
        inp_lst1 = nib.List()

    class DerivedInterface(nib.BaseInterface):
        input_spec = BaseInterfaceInputSpec

    di = DerivedInterface(**inp)
    assert di.inputs.get() == get_full_output
    assert di.inputs.get_skipundefined() == get_skip_output


def test_BaseInterface_load_save_inputs(tmpdir):
    tmp_json = os.path.join(str(tmpdir), 'settings.json')

    class InputSpec(nib.TraitedSpec):
        input1 = nib.Int()
        input2 = nib.Float()
        input3 = nib.Bool()
        input4 = nib.Unicode()

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
    assert bif2.inputs.get_skipundefined() == inputs_dict

    bif3 = DerivedInterface(from_file=tmp_json)
    assert bif3.inputs.get_skipundefined() == inputs_dict

    inputs_dict2 = inputs_dict.copy()
    inputs_dict2.update({'input4': 'some other string'})
    bif4 = DerivedInterface(from_file=tmp_json, input4=inputs_dict2['input4'])
    assert bif4.inputs.get_skipundefined() == inputs_dict2

    bif5 = DerivedInterface(input4=inputs_dict2['input4'])
    bif5.load_inputs_from_json(tmp_json, overwrite=False)
    assert bif5.inputs.get_skipundefined() == inputs_dict2

    bif6 = DerivedInterface(input4=inputs_dict2['input4'])
    bif6.load_inputs_from_json(tmp_json)
    assert bif6.inputs.get_skipundefined() == inputs_dict


@pytest.mark.xfail(reason="dj: WIP; check ants")
def test_BaseInterface_load_save_inputs_ants():
    # test get hashval in a complex interface
    from nipype.interfaces.ants import Registration
    settings = example_data(example_data('smri_ants_registration_settings.json'))
    with open(settings) as setf:
        data_dict = json.load(setf)

    tsthash = Registration()
    # dj TODO: tsthash.inputs has no all list; check the test after changing ants!
    tsthash.load_inputs_from_json(settings)
    assert {} == check_dict(data_dict, tsthash.inputs.get_skipundefined())

#    tsthash2 = Registration(from_file=settings)
#    assert {} == check_dict(data_dict, tsthash2.inputs.get_traitsfree())

#    _, hashvalue = tsthash.inputs.get_hashval(hash_method='timestamp')
#    assert 'ec5755e07287e04a4b409e03b77a517c' == hashvalue


class MinVerInputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int', min_ver='0.9')

class MaxVerInputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int').tag(max_ver='0.7')


def test_input_version_1():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec

    obj = DerivedInterface1()
    obj._check_version_requirements(obj.inputs)

    config.set('execution', 'stop_on_unknown_version', True)

    #dj TOASK: is this the expected error: ValueError: Interface DerivedInterface1 has no version information
    #dj TODO: change Exception to the error
    with pytest.raises(Exception): 
        obj._check_version_requirements(obj.inputs)

    config.set_default_config()

def test_input_version_2():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MinVerInputSpec
        _version = '0.8'

    obj = DerivedInterface1()
    obj.inputs.foo = 1
    with pytest.raises(Exception) as excinfo:
        # dj NOTE: this was giving an error because it was no argument
        obj._check_version_requirements(obj.inputs)
    assert "required 0.9" in str(excinfo.value)


#dj TOASK: this part doesn check the version at all, is that right?
# dj TOASK: can add obj.inputs.foo = 1, but that would be the same as test_input_version_4
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
        # dj NOTE: this was giving an error only because it was no argument
        obj._check_version_requirements(obj.inputs)
    assert "required 0.7" in str(excinfo.value)


def test_input_version_6():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = MaxVerInputSpec
        _version = '0.7'
    obj = DerivedInterface1()
    obj.inputs.foo = 1
    obj._check_version_requirements(obj.inputs)



class VerInputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int')

class MinVerOutputSpec(nib.TraitedSpec):
    foo = nib.Int(help='a random int').tag(min_ver='0.9')
def test_output_version_1():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = VerInputSpec
        output_spec = MinVerOutputSpec
        _version = '0.10'

    obj = DerivedInterface1()
    assert obj._check_version_requirements(obj._outputs()) == []


def test_output_version_2():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = VerInputSpec
        output_spec = MinVerOutputSpec
        _version = '0.08'

    obj = DerivedInterface1()
    assert obj._check_version_requirements(obj._outputs()) == ['foo']


def test_output_version_3():
    class DerivedInterface1(nib.BaseInterface):
        input_spec = VerInputSpec
        output_spec = MinVerOutputSpec
        _version = '0.08'

        def _run_interface(self, runtime):
            return runtime

        def _list_outputs(self):
            return {'foo': 1}

    obj = DerivedInterface1()
    with pytest.raises(KeyError): 
        obj.run()


def test_Commandline_1():
    with pytest.raises(Exception) as excinfo:
        nib.CommandLine()
    assert str(excinfo.value) == "Missing command"

#dj TODO: pytes.param
def test_Commandline_2():
    ci = nib.CommandLine(command='which')
    assert ci.cmd == 'which'
    assert ci.inputs.args is None

    ci2 = nib.CommandLine(command='which', args='ls')
    assert ci2.cmdline == 'which ls'
    ci3 = nib.CommandLine(command='echo')
    ci3.inputs.environ = {'MYENV': 'foo'}
    res = ci3.run()
    assert res.runtime.environ['MYENV'] == 'foo'
    assert res.outputs is None


def test_Commandline_3():
    class CommandLineInputSpec1(nib.CommandLineInputSpec):
        foo = nib.Unicode(help='a str').tag(argstr='%s')
        goo = nib.Bool(help='a bool').tag(argstr='-g', position=0)
        # dj NOTE: nib.List has default_value is None, not [] as in trailets.List
        hoo = nib.List(help='a list').tag(argstr='-l %s') 
        moo = nib.List(help='a repeated list').tag(argstr='-i %d...', position=-1)
        mooo = nib.List(help='a repeated list').tag(argstr='-i %d...', position=-2, sep=" AND ")
        noo = nib.Int(help='an int').tag(argstr='-x %d')
        roo = nib.Unicode(help='not on command line')
        soo = nib.Bool().tag(argstr="-soo")

    nib.CommandLine.input_spec = CommandLineInputSpec1
    ci4 = nib.CommandLine(command='which')
    ci4.inputs.foo = 'foo'
    ci4.inputs.goo = True
    ci4.inputs.hoo = ['a', 'b']
    ci4.inputs.moo = [1, 2, 3]
    ci4.inputs.mooo = [1, 2, 3]
    ci4.inputs.noo = 0
    ci4.inputs.roo = 'hello'
    ci4.inputs.soo = False
    cmd = ci4._parse_inputs()
    assert cmd[0] == '-g'
    assert cmd[-1] == '-i 1 -i 2 -i 3'
    assert cmd[-2] == '-i 1 AND -i 2 AND -i 3'
    assert 'hello' not in ' '.join(cmd)
    assert '-soo' not in ' '.join(cmd)
    ci4.inputs.soo = True
    cmd = ci4._parse_inputs()
    assert '-soo' in ' '.join(cmd)


def test_Commandline_4():
    class CommandLineInputSpec2(nib.CommandLineInputSpec):
        foo = nib.File().tag(argstr='%s', genfile=True)
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


class SpecTag(nib.CommandLineInputSpec):
    bar = nib.Int()
    kung_bar = nib.Float().tag(requires=('bar',))

class SpecNoTag(nib.CommandLineInputSpec):
    bar = nib.Int()
    kung_bar = nib.Float(requires=('bar',))

@pytest.mark.parametrize("spec", [SpecTag, SpecNoTag])
def test_Commandline_checkreq(spec):

    class DerivedClass(nib.CommandLine):
        input_spec = spec

    with pytest.raises(ValueError) as excinfo:
        ci2 = DerivedClass(command='cmd', kung_bar=3.4)
        ci2.cmdline
    assert "DerivedClass requires a value for input 'bar' because one of kung_bar is set." \
        in str(excinfo.value)


class SpecTag(nib.CommandLineInputSpec):
    bar = nib.Int().tag(mandatory=True, xor=("bar", "goo"))
    goo = nib.Int().tag(mandatory=True, xor=("bar", "goo"))

class SpecNoTag(nib.CommandLineInputSpec):
    bar = nib.Int(mandatory=True, xor=("bar", "goo"))
    goo = nib.Int(mandatory=True, xor=("bar", "goo"))

@pytest.mark.parametrize("spec", [SpecTag, SpecNoTag])
def test_Commandline_checkmandxor(spec):

    class DerivedClass(nib.CommandLine):
        input_spec = spec

    with pytest.raises(ValueError) as excinfo:
        ci2 = DerivedClass(command='cmd')
        ci2.cmdline
    assert "DerivedClass requires a value for one of the inputs 'bar, goo'." \
        in str(excinfo.value)


def test_Commandline_environ():
    from nipype import config
    config.set_default_config()
    ci3 = nib.CommandLine(command='echo')
    res = ci3.run()
    assert res.runtime.environ['DISPLAY'] == ':1'
    config.set('execution', 'display_variable', ':3')
    res = ci3.run()
    assert ci3.inputs.environ is None
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
    with pytest.raises(AttributeError) as excinfo:
        nib.CommandLine.set_default_terminal_output('wrong_terminal')
    assert "Invalid terminal output_type" in str(excinfo.value)
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



def image_inputs():
    class ImSpec(nib.TraitedSpec):
        nifti = nib.ImageFile(types=['nifti1', 'dicom'])
        anytype = nib.ImageFile()
        newtype = nib.ImageFile(types=['nifti10'])
        nocompress = nib.ImageFile(types=['mgh'], allow_compressed=False)

    class ImInterface(nib.BaseInterface):
        input_spec = ImSpec
        
    return ImInterface().inputs

def image_inputs_dynam():
    inp = nib.BaseInterface().inputs
    # setup traits
    inp.add_traits(nifti=nib.ImageFile(types=['nifti1', 'dicom']))
    inp.add_traits(anytype=nib.ImageFile())
    inp.add_traits(newtype=nib.ImageFile(types=['nifti10']))
    inp.add_traits(nocompress=nib.ImageFile(types=['mgh'],
                                          allow_compressed=False))
    return inp

#dj NOTE: testing for dynamical and non-dynamical version 
@pytest.mark.parametrize("inp_fun", [image_inputs, image_inputs_dynam])
def test_ImageFile(inp_fun):

    x = inp_fun()

    with pytest.raises(traitlets.TraitError) as excinfo:
        x.nifti = 3
    assert "instance expected a file name" in str(excinfo.value)

    with pytest.raises(traitlets.TraitError) as excinfo: 
        x.nifti = 'test.mgz'
    assert "test.mgz is not included in allowed types" in str(excinfo.value)
    x.nifti = 'test.nii'

    x.anytype = 'test.xml'

    with pytest.raises(AttributeError) as excinfo:
        x.newtype = 'test.nii'
    assert "Information has not been added for format" in str(excinfo.value)

    with pytest.raises(traitlets.TraitError) as excinfo: 
        x.nocompress = 'test.nii.gz'
    assert "test.nii.gz is not included in allowed types" in str(excinfo.value)
    x.nocompress = 'test.mgh'


# dj TODO: the simplest test for StdOutCommandLine, any suggestions??
def test_StdOutCommandLine():

    class spec(nib.StdOutCommandLineInputSpec):
        doo = nib.Int()


    class TestName(nib.StdOutCommandLine):
        _cmd = "mycommand"
        input_spec = spec

    testobj = TestName(doo=3)

    assert testobj.inputs.doo == 3
    assert "out_file" in testobj.inputs.traits() 
    
    assert testobj.cmd == "mycommand"
    with pytest.raises(NotImplementedError):
        testobj.cmdline



# dj TOASK: a new tests for SEMLikeCommandLine - 
# dj TOASK: are these the expected results?? traits version gave similar results
# dj TOASK: other tests suggestions? 

def test_SEMLikeCommandLine_1():
    
    class SEMLikeInpSpec(nib.CommandLineInputSpec):
        foo = nib.Unicode()
        doo = nib.Unicode()

    class SEMLikeOutSpec(nib.TraitedSpec):
        foo = nib.Unicode()

    class TestName(nib.SEMLikeCommandLine):
        _cmd = "mycommand"
        input_spec = SEMLikeInpSpec
        output_spec = SEMLikeOutSpec

    testobj = TestName()
    testobj.cmdline
    assert "foo" in testobj._list_outputs()


def test_SEMLikeCommandLine_2():

    class SEMLikeInpSpec(nib.CommandLineInputSpec):
        doo = nib.Int()

    class SEMLikeOutSpec(nib.TraitedSpec):
        foo = nib.Int()

    class TestName(nib.SEMLikeCommandLine):
        _cmd = "mycommand"
        input_spec = SEMLikeInpSpec
        output_spec = SEMLikeOutSpec

    testobj = TestName()

    with pytest.raises(AttributeError) as excinfo:
        testobj._list_outputs()
    assert "'SEMLikeInpSpec' object has no attribute 'foo'" == str(excinfo.value)


@pytest.mark.xfail(reason="this is a new test for _format_arg, don't know how it should be changed")
def test_SEMLikeCommandline_3():
    class SEMLikeInpSpec(nib.CommandLineInputSpec):
        foo = nib.Unicode(help='a str').tag(argstr='%s')
        goo = nib.Bool(help='a bool').tag(argstr='-g', position=0)

    class TestName(nib.SEMLikeCommandLine):
        _cmd = "mycommand"
        input_spec = SEMLikeInpSpec
        
    testobj = TestName()
    testobj.inputs.foo = 'foo'
    testobj.inputs.goo = True

    testobj.cmdline
    #dj TODO: add asserts once it works



# dj TOASK: any suggestion about tests? 
# dj TOASK: are those are expected outpus??
def test_MultiObject():

    class spec(nib.TraitedSpec):
        goo = nib.MultiObject()

    mp = spec()
 
    assert mp.goo is None

    mp.goo = None
    assert mp.goo is None

    # dj TOASK: this is now treated as a perfectly fine list (shoudl it stay?)
    mp.goo = []
    assert mp.goo == []

    mp.goo = 4
    assert mp.goo == [4]

    mp.goo = "text"
    assert mp.goo == ["text"]

    mp.goo = ["text"]
    assert mp.goo == ["text"]

    mp.goo = ["text1", "text2"]
    assert mp.goo == ["text1", "text2"]

    # dj TOASK: is this really expected?
    mp.goo = {}
    assert mp.goo == [{}]

    mp.goo = ()
    assert mp.goo == [()]


# dj TOASK: any suggestion about tests?
# dj TOASK: are those are expected outpus??
def test_OutputMultiObject():

    class spec(nib.TraitedSpec):
        goo = nib.OutputMultiObject()

    mp = spec()

    assert mp.goo is None

    mp.goo = None
    assert mp.goo is None

    mp.goo = []
    assert mp.goo is None

    mp.goo = "text"
    assert mp.goo == "text"

    mp.goo = ["text"]
    assert mp.goo == "text"

    mp.goo = ["text1", "text2"]
    assert mp.goo == ["text1", "text2"]
