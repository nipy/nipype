# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine utils module
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import range, open

import os, sys
from copy import deepcopy
from shutil import rmtree
import pytest

from ... import engine as pe
from ....interfaces import base as nib
from ....interfaces import utility as niu
from .... import config
from ..utils import merge_dict, clean_working_directory, write_workflow_prov


def test_identitynode_removal(tmpdir):

    def test_function(arg1, arg2, arg3):
        import numpy as np
        return (np.array(arg1) + arg2 + arg3).tolist()


    wf = pe.Workflow(name="testidentity", base_dir=tmpdir.strpath)

    n1 = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='src', base_dir=tmpdir.strpath)
    n1.iterables = ('b', [0, 1, 2, 3])
    n1.inputs.a = [0, 1, 2, 3]

    n2 = pe.Node(niu.Select(), name='selector', base_dir=tmpdir.strpath)
    wf.connect(n1, ('a', test_function, 1, -1), n2, 'inlist')
    wf.connect(n1, 'b', n2, 'index')

    n3 = pe.Node(niu.IdentityInterface(fields=['c', 'd']), name='passer', base_dir=tmpdir.strpath)
    n3.inputs.c = [1, 2, 3, 4]
    wf.connect(n2, 'out', n3, 'd')

    n4 = pe.Node(niu.Select(), name='selector2', base_dir=tmpdir.strpath)
    wf.connect(n3, ('c', test_function, 1, -1), n4, 'inlist')
    wf.connect(n3, 'd', n4, 'index')

    fg = wf._create_flat_graph()
    wf._set_needed_outputs(fg)
    eg = pe.generate_expanded_graph(deepcopy(fg))
    assert len(eg.nodes()) == 8


def test_clean_working_directory(tmpdir):
    class OutputSpec(nib.TraitedSpec):
        files = nib.traits.List(nib.File)
        others = nib.File()

    class InputSpec(nib.TraitedSpec):
        infile = nib.File()
    outputs = OutputSpec()
    inputs = InputSpec()

    filenames = ['file.hdr', 'file.img', 'file.BRIK', 'file.HEAD',
                 '_0x1234.json', 'foo.txt']
    outfiles = []
    for filename in filenames:
        outfile = tmpdir.join(filename)
        outfile.write('dummy')
        outfiles.append(outfile.strpath)
    outputs.files = outfiles[:4:2]
    outputs.others = outfiles[5]
    inputs.infile = outfiles[-1]
    needed_outputs = ['files']
    config.set_default_config()
    assert os.path.exists(outfiles[5])
    config.set_default_config()
    config.set('execution', 'remove_unnecessary_outputs', False)
    out = clean_working_directory(outputs, tmpdir.strpath, inputs, needed_outputs,
                                  deepcopy(config._sections))
    assert os.path.exists(outfiles[5])
    assert out.others == outfiles[5]
    config.set('execution', 'remove_unnecessary_outputs', True)
    out = clean_working_directory(outputs, tmpdir.strpath, inputs, needed_outputs,
                                  deepcopy(config._sections))
    assert os.path.exists(outfiles[1])
    assert os.path.exists(outfiles[3])
    assert os.path.exists(outfiles[4])
    assert not os.path.exists(outfiles[5])
    assert out.others == nib.Undefined
    assert len(out.files) == 2
    config.set_default_config()


def test_outputs_removal(tmpdir):

    def test_function(arg1):
        import os
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        fp = open(file1, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        fp = open(file2, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        return file1, file2

    n1 = pe.Node(niu.Function(input_names=['arg1'],
                              output_names=['file1', 'file2'],
                              function=test_function),
                 base_dir=tmpdir.strpath,
                 name='testoutputs')
    n1.inputs.arg1 = 1
    n1.config = {'execution': {'remove_unnecessary_outputs': True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    assert tmpdir.join(n1.name,'file1.txt').check()
    assert tmpdir.join(n1.name,'file1.txt').check()
    n1.needed_outputs = ['file2']
    n1.run()
    assert not tmpdir.join(n1.name,'file1.txt').check()
    assert tmpdir.join(n1.name,'file2.txt').check()


class InputSpec(nib.TraitedSpec):
    in_file = nib.File(exists=True, copyfile=True)


class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')


class UtilsTestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1]
        return outputs


def test_inputs_removal(tmpdir):
    file1 = tmpdir.join('file1.txt')
    file1.write('dummy_file')
    n1 = pe.Node(UtilsTestInterface(),
                 base_dir=tmpdir.strpath,
                 name='testinputs')
    n1.inputs.in_file = file1.strpath
    n1.config = {'execution': {'keep_inputs': True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    assert tmpdir.join(n1.name,'file1.txt').check()
    n1.inputs.in_file = file1.strpath
    n1.config = {'execution': {'keep_inputs': False}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.overwrite = True
    n1.run()
    assert not tmpdir.join(n1.name,'file1.txt').check()


def test_outputs_removal_wf(tmpdir):

    def test_function(arg1):
        import os
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        file3 = os.path.join(os.getcwd(), 'file3.txt')
        file4 = os.path.join(os.getcwd(), 'subdir', 'file1.txt')
        files = [file1, file2, file3, file4]
        os.mkdir("subdir")
        for filename in files:
            with open(filename, 'wt') as fp:
                fp.write('%d' % arg1)
        return file1, file2, os.path.join(os.getcwd(), "subdir")

    def test_function2(in_file, arg):
        import os
        in_arg = open(in_file).read()
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        file3 = os.path.join(os.getcwd(), 'file3.txt')
        files = [file1, file2, file3]
        for filename in files:
            with open(filename, 'wt') as fp:
                fp.write('%d' % arg + in_arg)
        return file1, file2, 1

    def test_function3(arg):
        import os
        return arg


    for plugin in ('Linear',):  # , 'MultiProc'):
        n1 = pe.Node(niu.Function(input_names=['arg1'],
                                  output_names=['out_file1', 'out_file2', 'dir'],
                                  function=test_function),
                     name='n1', base_dir=tmpdir.strpath)
        n1.inputs.arg1 = 1

        n2 = pe.Node(niu.Function(input_names=['in_file', 'arg'],
                                  output_names=['out_file1', 'out_file2', 'n'],
                                  function=test_function2),
                     name='n2', base_dir=tmpdir.strpath)
        n2.inputs.arg = 2

        n3 = pe.Node(niu.Function(input_names=['arg'],
                                  output_names=['n'],
                                  function=test_function3),
                     name='n3', base_dir=tmpdir.strpath)

        wf = pe.Workflow(name="node_rem_test" + plugin, base_dir=tmpdir.strpath)
        wf.connect(n1, "out_file1", n2, "in_file")

        wf.run(plugin='Linear')

        for remove_unnecessary_outputs in [True, False]:
            config.set_default_config()
            wf.config = {'execution': {'remove_unnecessary_outputs': remove_unnecessary_outputs}}
            rmtree(os.path.join(wf.base_dir, wf.name))
            wf.run(plugin=plugin)

            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n1.name,
                                               'file2.txt')) != remove_unnecessary_outputs
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n1.name,
                                               "subdir",
                                               'file1.txt')) != remove_unnecessary_outputs
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n1.name,
                                               'file1.txt'))
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n1.name,
                                               'file3.txt')) != remove_unnecessary_outputs
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n2.name,
                                               'file1.txt'))
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n2.name,
                                               'file2.txt'))
            assert os.path.exists(os.path.join(wf.base_dir,
                                               wf.name,
                                               n2.name,
                                               'file3.txt')) != remove_unnecessary_outputs

        n4 = pe.Node(UtilsTestInterface(), name='n4', base_dir=tmpdir.strpath)
        wf.connect(n2, "out_file1", n4, "in_file")

        def pick_first(l):
            return l[0]

        wf.connect(n4, ("output1", pick_first), n3, "arg")
        for remove_unnecessary_outputs in [True, False]:
            for keep_inputs in [True, False]:
                config.set_default_config()
                wf.config = {'execution': {'keep_inputs': keep_inputs, 'remove_unnecessary_outputs': remove_unnecessary_outputs}}
                rmtree(os.path.join(wf.base_dir, wf.name))
                wf.run(plugin=plugin)
                assert os.path.exists(os.path.join(wf.base_dir,
                                                   wf.name,
                                                   n2.name,
                                                   'file1.txt'))
                assert os.path.exists(os.path.join(wf.base_dir,
                                                   wf.name,
                                                   n2.name,
                                                   'file2.txt')) != remove_unnecessary_outputs
                assert os.path.exists(os.path.join(wf.base_dir,
                                                   wf.name,
                                                   n4.name,
                                                   'file1.txt')) == keep_inputs


def fwhm(fwhm):
    return fwhm


def create_wf(name):
    pipe = pe.Workflow(name=name)
    process = pe.Node(niu.Function(input_names=['fwhm'],
                                   output_names=['fwhm'],
                                   function=fwhm),
                      name='proc')
    process.iterables = ('fwhm', [0])
    process2 = pe.Node(niu.Function(input_names=['fwhm'],
                                    output_names=['fwhm'],
                                    function=fwhm),
                       name='proc2')
    process2.iterables = ('fwhm', [0])
    pipe.connect(process, 'fwhm', process2, 'fwhm')
    return pipe


def test_multi_disconnected_iterable(tmpdir):
    metawf = pe.Workflow(name='meta')
    metawf.base_dir = tmpdir.strpath
    metawf.add_nodes([create_wf('wf%d' % i) for i in range(30)])
    eg = metawf.run(plugin='Linear')
    assert len(eg.nodes()) == 60


def test_provenance(tmpdir):
    metawf = pe.Workflow(name='meta')
    metawf.base_dir = tmpdir.strpath
    metawf.add_nodes([create_wf('wf%d' % i) for i in range(1)])
    eg = metawf.run(plugin='Linear')
    prov_base = tmpdir.join('workflow_provenance_test').strpath
    psg = write_workflow_prov(eg, prov_base, format='all')
    assert len(psg.bundles) == 2
    assert len(psg.get_records()) == 7


def dummy_func(value):
    return value + 1


@pytest.mark.skipif(sys.version_info < (3,0),
                   reason="the famous segfault #1788")
def test_mapnode_crash(tmpdir):
    """Test mapnode crash when stop_on_first_crash is True"""
    cwd = os.getcwd()
    node = pe.MapNode(niu.Function(input_names=['WRONG'],
                                   output_names=['newstring'],
                                   function=dummy_func),
                      iterfield=['WRONG'],
                      name='myfunc')
    node.inputs.WRONG = ['string{}'.format(i) for i in range(3)]
    node.config = deepcopy(config._sections)
    node.config['execution']['stop_on_first_crash'] = True
    node.base_dir = tmpdir.strpath
    with pytest.raises(TypeError):
        node.run()
    os.chdir(cwd)


@pytest.mark.skipif(sys.version_info < (3,0),
                   reason="the famous segfault #1788")
def test_mapnode_crash2(tmpdir):
    """Test mapnode crash when stop_on_first_crash is False"""
    cwd = os.getcwd()
    node = pe.MapNode(niu.Function(input_names=['WRONG'],
                                   output_names=['newstring'],
                                   function=dummy_func),
                      iterfield=['WRONG'],
                      name='myfunc')
    node.inputs.WRONG = ['string{}'.format(i) for i in range(3)]
    node.base_dir = tmpdir.strpath

    with pytest.raises(Exception):
        node.run()
    os.chdir(cwd)


@pytest.mark.skipif(sys.version_info < (3,0),
                   reason="the famous segfault #1788")
def test_mapnode_crash3(tmpdir):
    """Test mapnode crash when mapnode is embedded in a workflow"""
    tmpdir.chdir()
    node = pe.MapNode(niu.Function(input_names=['WRONG'],
                                   output_names=['newstring'],
                                   function=dummy_func),
                      iterfield=['WRONG'],
                      name='myfunc')
    node.inputs.WRONG = ['string{}'.format(i) for i in range(3)]
    wf = pe.Workflow('testmapnodecrash')
    wf.add_nodes([node])
    wf.base_dir = tmpdir.strpath
    #changing crashdump dir to cwl (to avoid problems with read-only systems)
    wf.config["execution"]["crashdump_dir"] = os.getcwd()
    with pytest.raises(RuntimeError):
        wf.run(plugin='Linear')
