# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine utils module
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, open

import os
import sys
from copy import deepcopy
import pytest

from ... import engine as pe
from ....interfaces import base as nib
from ....interfaces import utility as niu
from .... import config
from ..utils import clean_working_directory, write_workflow_prov, modify_paths


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


def test_identitynode_removal(tmpdir):
    def test_function(arg1, arg2, arg3):
        import numpy as np
        return (np.array(arg1) + arg2 + arg3).tolist()

    wf = pe.Workflow(name="testidentity", base_dir=tmpdir.strpath)

    n1 = pe.Node(
        niu.IdentityInterface(fields=['a', 'b']),
        name='src',
        base_dir=tmpdir.strpath)
    n1.iterables = ('b', [0, 1, 2, 3])
    n1.inputs.a = [0, 1, 2, 3]

    n2 = pe.Node(niu.Select(), name='selector', base_dir=tmpdir.strpath)
    wf.connect(n1, ('a', test_function, 1, -1), n2, 'inlist')
    wf.connect(n1, 'b', n2, 'index')

    n3 = pe.Node(
        niu.IdentityInterface(fields=['c', 'd']),
        name='passer',
        base_dir=tmpdir.strpath)
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

    filenames = [
        'file.hdr', 'file.img', 'file.BRIK', 'file.HEAD', '_0x1234.json',
        'foo.txt'
    ]
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
    out = clean_working_directory(outputs, tmpdir.strpath, inputs,
                                  needed_outputs, deepcopy(config._sections))
    assert os.path.exists(outfiles[5])
    assert out.others == outfiles[5]
    config.set('execution', 'remove_unnecessary_outputs', True)
    out = clean_working_directory(outputs, tmpdir.strpath, inputs,
                                  needed_outputs, deepcopy(config._sections))
    assert os.path.exists(outfiles[1])
    assert os.path.exists(outfiles[3])
    assert os.path.exists(outfiles[4])
    assert not os.path.exists(outfiles[5])
    assert out.others == nib.Undefined
    assert len(out.files) == 2
    config.set_default_config()


def create_wf(name):
    """Creates a workflow for the following tests"""
    def fwhm(fwhm):
        return fwhm

    pipe = pe.Workflow(name=name)
    process = pe.Node(
        niu.Function(
            input_names=['fwhm'], output_names=['fwhm'], function=fwhm),
        name='proc')
    process.iterables = ('fwhm', [0])
    process2 = pe.Node(
        niu.Function(
            input_names=['fwhm'], output_names=['fwhm'], function=fwhm),
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


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="the famous segfault #1788")
def test_mapnode_crash(tmpdir):
    """Test mapnode crash when stop_on_first_crash is True"""
    cwd = os.getcwd()
    node = pe.MapNode(
        niu.Function(
            input_names=['WRONG'],
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


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="the famous segfault #1788")
def test_mapnode_crash2(tmpdir):
    """Test mapnode crash when stop_on_first_crash is False"""
    cwd = os.getcwd()
    node = pe.MapNode(
        niu.Function(
            input_names=['WRONG'],
            output_names=['newstring'],
            function=dummy_func),
        iterfield=['WRONG'],
        name='myfunc')
    node.inputs.WRONG = ['string{}'.format(i) for i in range(3)]
    node.base_dir = tmpdir.strpath

    with pytest.raises(Exception):
        node.run()
    os.chdir(cwd)


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="the famous segfault #1788")
def test_mapnode_crash3(tmpdir):
    """Test mapnode crash when mapnode is embedded in a workflow"""
    tmpdir.chdir()
    node = pe.MapNode(
        niu.Function(
            input_names=['WRONG'],
            output_names=['newstring'],
            function=dummy_func),
        iterfield=['WRONG'],
        name='myfunc')
    node.inputs.WRONG = ['string{}'.format(i) for i in range(3)]
    wf = pe.Workflow('testmapnodecrash')
    wf.add_nodes([node])
    wf.base_dir = tmpdir.strpath
    # changing crashdump dir to current working directory (to avoid problems with read-only systems)
    wf.config["execution"]["crashdump_dir"] = os.getcwd()
    with pytest.raises(RuntimeError):
        wf.run(plugin='Linear')


class StrPathConfuser(nib.SimpleInterface):
    class input_spec(nib.TraitedSpec):
        in_str = nib.traits.String()

    class output_spec(nib.TraitedSpec):
        out_tuple = nib.traits.Tuple(nib.File, nib.traits.String)
        out_dict_path = nib.traits.Dict(nib.traits.String, nib.File(exists=True))
        out_dict_str = nib.traits.DictStrStr()
        out_list = nib.traits.List(nib.traits.String)
        out_str = nib.traits.String()
        out_path = nib.File(exists=True)

    def _run_interface(self, runtime):
        out_path = os.path.abspath(os.path.basename(self.inputs.in_str) + '_path')
        open(out_path, 'w').close()

        self._results['out_str'] = self.inputs.in_str
        self._results['out_path'] = out_path
        self._results['out_tuple'] = (out_path, self.inputs.in_str)
        self._results['out_dict_path'] = {self.inputs.in_str: out_path}
        self._results['out_dict_str'] = {self.inputs.in_str: self.inputs.in_str}
        self._results['out_list'] = [self.inputs.in_str] * 2
        return runtime


def test_modify_paths_bug(tmpdir):
    """
    There was a bug in which, if the current working directory contained a file with the name
    of an output String, the string would get transformed into a path, and generally wreak havoc.

    This attempts to replicate that condition, using an object with strings and paths in various
    trait configurations, to ensure that the guards added resolve the issue.

    Please see https://github.com/nipy/nipype/issues/2944 for more details.
    """
    tmpdir.chdir()

    spc = pe.Node(StrPathConfuser(in_str='2'), name='spc')

    open('2', 'w').close()

    results = spc.run()

    # Basic check that string was not manipulated and path exists
    out_path = results.outputs.out_path
    out_str = results.outputs.out_str
    assert out_str == '2'
    assert os.path.basename(out_path) == '2_path'
    assert os.path.isfile(out_path)

    # Assert data structures pass through correctly
    assert results.outputs.out_tuple == (out_path, out_str)
    assert results.outputs.out_dict_path == {out_str: out_path}
    assert results.outputs.out_dict_str == {out_str: out_str}
    assert results.outputs.out_list == [out_str] * 2
