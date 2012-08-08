# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine utils module
"""
import os
from copy import deepcopy
from tempfile import mkdtemp
from shutil import rmtree

from ...testing import (assert_equal, assert_true,
                            assert_false)
import nipype.pipeline.engine as pe
import nipype.interfaces.base as nib
import nipype.interfaces.utility as niu
from ... import config
from ..utils import merge_dict


def test_identitynode_removal():

    def test_function(arg1, arg2, arg3):
        import numpy as np
        return (np.array(arg1) + arg2 + arg3).tolist()

    wf = pe.Workflow(name="testidentity")

    n1 = pe.Node(niu.IdentityInterface(fields=['a', 'b']), name='src')
    n1.iterables = ('b', [0, 1, 2, 3])
    n1.inputs.a = [0, 1, 2, 3]

    n2 = pe.Node(niu.Select(), name='selector')
    wf.connect(n1, ('a', test_function, 1, -1), n2, 'inlist')
    wf.connect(n1, 'b', n2, 'index')

    n3 = pe.Node(niu.IdentityInterface(fields=['c', 'd']), name='passer')
    n3.inputs.c = [1, 2, 3, 4]
    wf.connect(n2, 'out', n3, 'd')

    n4 = pe.Node(niu.Select(), name='selector2')
    wf.connect(n3, ('c', test_function, 1, -1), n4, 'inlist')
    wf.connect(n3, 'd', n4, 'index')

    fg = wf._create_flat_graph()
    wf._set_needed_outputs(fg)
    eg = pe.generate_expanded_graph(deepcopy(fg))
    yield assert_equal, len(eg.nodes()), 8


def test_outputs_removal():

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

    out_dir = mkdtemp()
    n1 = pe.Node(niu.Function(input_names=['arg1'],
                              output_names=['file1', 'file2'],
                              function=test_function),
                 base_dir=out_dir,
                 name='testoutputs')
    n1.inputs.arg1 = 1
    n1.config = {'execution': {'remove_unnecessary_outputs': True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file2.txt'))
    n1.needed_outputs = ['file2']
    n1.run()
    yield assert_false, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file2.txt'))
    rmtree(out_dir)


class InputSpec(nib.TraitedSpec):
    in_file = nib.File(exists=True, copyfile=True)

class OutputSpec(nib.TraitedSpec):
    output1 = nib.traits.List(nib.traits.Int, desc='outputs')

class TestInterface(nib.BaseInterface):
    input_spec = InputSpec
    output_spec = OutputSpec

    def _run_interface(self, runtime):
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output1'] = [1]
        return outputs

def test_inputs_removal():
    out_dir = mkdtemp()
    file1 = os.path.join(out_dir, 'file1.txt')
    fp = open(file1, 'wt')
    fp.write('dummy_file')
    fp.close()
    n1 = pe.Node(TestInterface(),
                 base_dir=out_dir,
                 name='testinputs')
    n1.inputs.in_file = file1
    n1.config = {'execution': {'keep_inputs': True}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.run()
    yield assert_true, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    n1.inputs.in_file = file1
    n1.config = {'execution': {'keep_inputs': False}}
    n1.config = merge_dict(deepcopy(config._sections), n1.config)
    n1.overwrite = True
    n1.run()
    yield assert_false, os.path.exists(os.path.join(out_dir,
                                                   n1.name,
                                                   'file1.txt'))
    rmtree(out_dir)


def test_outputs_removal_wf():

    def test_function(arg1):
        import os
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        file3 = os.path.join(os.getcwd(), 'file3.txt')
        fp = open(file1, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        fp = open(file2, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        fp = open(file3, 'wt')
        fp.write('%d' % arg1)
        fp.close()
        os.mkdir("subdir")
        fp = open("subdir/file1.txt", 'wt')
        fp.write('%d' % arg1)
        fp.close()
        return file1, file2, os.path.join(os.getcwd(),"subdir")

    def test_function2(in_file, arg):
        import os
        in_arg = open(in_file).read()
        file1 = os.path.join(os.getcwd(), 'file1.txt')
        file2 = os.path.join(os.getcwd(), 'file2.txt')
        file3 = os.path.join(os.getcwd(), 'file3.txt')
        fp = open(file1, 'wt')
        fp.write('%d' % arg + in_arg)
        fp.close()
        fp = open(file2, 'wt')
        fp.write('%d' % arg + in_arg)
        fp.close()
        fp = open(file3, 'wt')
        fp.write('%d' % arg + in_arg)
        fp.close()
        return file1, file2, 1

    def test_function3(arg):
        import os
        return arg

    out_dir = mkdtemp()

    for plugin in ('Linear',):#, 'MultiProc'):
        n1 = pe.Node(niu.Function(input_names=['arg1'],
                              output_names=['out_file1', 'out_file2', 'dir'],
                              function=test_function),
                 name='n1')
        n1.inputs.arg1 = 1

        n2 = pe.Node(niu.Function(input_names=['in_file', 'arg'],
                              output_names=['out_file1', 'out_file2', 'n'],
                              function=test_function2),
                 name='n2')
        n2.inputs.arg = 2

        n3 = pe.Node(niu.Function(input_names=['arg'],
                              output_names=['n'],
                              function=test_function3),
                 name='n3')

        wf = pe.Workflow(name="node_rem_test" + plugin, base_dir=out_dir)
        wf.connect(n1, "out_file1", n2, "in_file")

        wf.run(plugin='Linear')

        for remove_unnecessary_outputs in [True, False]:
            config.set_default_config()
            wf.config = {'execution': {'remove_unnecessary_outputs': remove_unnecessary_outputs}}
            rmtree(os.path.join(wf.base_dir, wf.name))
            wf.run(plugin=plugin)

            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                            wf.name,
                                                            n1.name,
                                                            'file2.txt')) != remove_unnecessary_outputs
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                            wf.name,
                                                            n1.name,
                                                            "subdir",
                                                            'file1.txt')) != remove_unnecessary_outputs
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                           wf.name,
                                                           n1.name,
                                                           'file1.txt'))
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                           wf.name,
                                                           n1.name,
                                                           'file3.txt')) != remove_unnecessary_outputs
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                           wf.name,
                                                           n2.name,
                                                           'file1.txt'))
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                           wf.name,
                                                           n2.name,
                                                           'file2.txt'))
            yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                           wf.name,
                                                           n2.name,
                                                           'file3.txt')) != remove_unnecessary_outputs

        n4 = pe.Node(TestInterface(), name='n4')
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
                yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                                   wf.name,
                                                                   n2.name,
                                                                   'file1.txt'))
                yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                                   wf.name,
                                                                   n2.name,
                                                                   'file2.txt')) != remove_unnecessary_outputs
                yield assert_true, os.path.exists(os.path.join(wf.base_dir,
                                                                   wf.name,
                                                                   n4.name,
                                                                   'file1.txt')) == keep_inputs

    rmtree(out_dir)

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

def test_multi_disconnected_iterable():
    out_dir = mkdtemp()
    metawf = pe.Workflow(name='meta')
    metawf.base_dir = out_dir
    metawf.add_nodes([create_wf('wf%d' % i) for i in range(30)])
    eg = metawf.run(plugin='Linear')
    yield assert_equal, len(eg.nodes()), 60
    rmtree(out_dir)
