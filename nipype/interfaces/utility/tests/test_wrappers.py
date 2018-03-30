# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
import os
import pytest

from nipype.interfaces import utility
from nipype.interfaces.base import traits
import nipype.pipeline.engine as pe
from nipype.utils.functions import getsource

concat_sort = """\
def concat_sort(in_arrays):
    import numpy as np
    all_vals = np.concatenate([arr.flatten() for arr in in_arrays])
    return np.sort(all_vals)
"""


def test_function(tmpdir):
    tmpdir.chdir()

    def gen_random_array(size):
        import numpy as np
        return np.random.rand(size, size)

    f1 = pe.MapNode(
        utility.Function(
            input_names=['size'],
            output_names=['random_array'],
            function=gen_random_array),
        name='random_array',
        iterfield=['size'])
    f1.inputs.size = [2, 3, 5]

    wf = pe.Workflow(name="test_workflow")

    def increment_array(in_array):
        return in_array + 1

    f2 = pe.MapNode(
        utility.Function(function=increment_array),
        name='increment_array',
        iterfield=['in_array'])

    wf.connect(f1, 'random_array', f2, 'in_array')

    f3 = pe.Node(utility.Function(function=concat_sort), name="concat_sort")

    wf.connect(f2, 'out', f3, 'in_arrays')
    wf.run()


def test_function_inputs():
    def f(a, b=2):
        return a + b

    def g(a, b=3):
        return a + b

    fun1 = utility.Function(function=f)
    fun2 = utility.Function(function=f, input_names=['a', 'b'])
    fun3 = utility.Function(function=f, input_names=['a'])

    fun1.inputs.a = 1
    fun2.inputs.a = 1
    fun3.inputs.a = 1

    assert fun1.run().outputs.out == 3
    assert fun2.run().outputs.out == 3
    assert fun3.run().outputs.out == 3

    fun1.inputs.b = 1
    fun2.inputs.b = 1

    assert fun1.run().outputs.out == 2
    assert fun2.run().outputs.out == 2

    with pytest.raises(traits.TraitError):
        fun3.inputs.b = 1

    # Non-hidden parameters are unaffected
    fun1.inputs.c = 1
    fun2.inputs.c = 1
    fun3.inputs.c = 1

    # Updating the function string adds all parameters
    fun3.inputs.function_str = getsource(g)
    # Check we're using the new function with default b=3
    assert fun3.run().outputs.out == 4
    # Verify we can now set this parameter
    fun3.inputs.b = 1
    assert fun3.run().outputs.out == 2


def make_random_array(size):
    return np.random.randn(size, size)


def should_fail(tmp):
    tmp.chdir()

    node = pe.Node(
        utility.Function(
            input_names=["size"],
            output_names=["random_array"],
            function=make_random_array),
        name="should_fail")
    node.inputs.size = 10
    node.run()


def test_should_fail(tmpdir):
    with pytest.raises(NameError):
        should_fail(tmpdir)


def test_function_with_imports(tmpdir):
    tmpdir.chdir()

    node = pe.Node(
        utility.Function(
            input_names=["size"],
            output_names=["random_array"],
            function=make_random_array,
            imports=["import numpy as np"]),
        name="should_not_fail")
    print(node.inputs.function_str)
    node.inputs.size = 10
    node.run()


def test_aux_connect_function(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    tmpdir.chdir()

    wf = pe.Workflow(name="test_workflow")

    def _gen_tuple(size):
        return [
            1,
        ] * size

    def _sum_and_sub_mul(a, b, c):
        return (a + b) * c, (a - b) * c

    def _inc(x):
        return x + 1

    params = pe.Node(
        utility.IdentityInterface(fields=['size', 'num']), name='params')
    params.inputs.num = 42
    params.inputs.size = 1

    gen_tuple = pe.Node(
        utility.Function(
            input_names=['size'], output_names=['tuple'], function=_gen_tuple),
        name='gen_tuple')

    ssm = pe.Node(
        utility.Function(
            input_names=['a', 'b', 'c'],
            output_names=['sum', 'sub'],
            function=_sum_and_sub_mul),
        name='sum_and_sub_mul')

    split = pe.Node(utility.Split(splits=[1, 1], squeeze=True), name='split')

    wf.connect([
        (params, gen_tuple, [(("size", _inc), "size")]),
        (params, ssm, [(("num", _inc), "c")]),
        (gen_tuple, split, [("tuple", "inlist")]),
        (split, ssm, [
            (("out1", _inc), "a"),
            ("out2", "b"),
        ]),
    ])

    wf.run()
