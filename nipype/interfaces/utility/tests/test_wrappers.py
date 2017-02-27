# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
import os
import pytest

from nipype.interfaces import utility as niu
import nipype.pipeline.engine as pe
from nipype.interfaces.fsl import BET
from nipype.interfaces.base import TraitError

def test_function(tmpdir):
    os.chdir(str(tmpdir))

    def gen_random_array(size):
        import numpy as np
        return np.random.rand(size, size)

    f1 = pe.MapNode(niu.Function(input_names=['size'], output_names=['random_array'], function=gen_random_array), name='random_array', iterfield=['size'])
    f1.inputs.size = [2, 3, 5]

    wf = pe.Workflow(name="test_workflow")

    def increment_array(in_array):
        return in_array + 1

    f2 = pe.MapNode(niu.Function(input_names=['in_array'], output_names=['out_array'], function=increment_array), name='increment_array', iterfield=['in_array'])

    wf.connect(f1, 'random_array', f2, 'in_array')
    wf.run()


def make_random_array(size):
    return np.random.randn(size, size)


def should_fail(tmpdir):
    os.chdir(tmpdir)

    node = pe.Node(niu.Function(input_names=["size"],
                                    output_names=["random_array"],
                                    function=make_random_array),
                   name="should_fail")
    node.inputs.size = 10
    node.run()


def test_should_fail(tmpdir):
    with pytest.raises(NameError):
        should_fail(str(tmpdir))


def test_function_with_imports(tmpdir):
    os.chdir(str(tmpdir))

    node = pe.Node(niu.Function(input_names=["size"],
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
    os.chdir(str(tmpdir))

    wf = pe.Workflow(name="test_workflow")

    def _gen_tuple(size):
        return [1, ] * size

    def _sum_and_sub_mul(a, b, c):
        return (a+b)*c, (a-b)*c

    def _inc(x):
        return x + 1

    params = pe.Node(niu.IdentityInterface(fields=['size', 'num']), name='params')
    params.inputs.num  = 42
    params.inputs.size = 1

    gen_tuple = pe.Node(niu.Function(input_names=['size'],
                                         output_names=['tuple'],
                                         function=_gen_tuple),
                                         name='gen_tuple')

    ssm = pe.Node(niu.Function(input_names=['a', 'b', 'c'],
                                   output_names=['sum', 'sub'],
                                   function=_sum_and_sub_mul),
                                   name='sum_and_sub_mul')

    split = pe.Node(niu.Split(splits=[1, 1],
                                  squeeze=True),
                    name='split')

    wf.connect([
                (params,    gen_tuple,  [(("size", _inc),   "size")]),
                (params,    ssm,        [(("num", _inc),    "c")]),
                (gen_tuple, split,      [("tuple",          "inlist")]),
                (split,     ssm,        [(("out1", _inc),   "a"),
                                         ("out2",           "b"),
                                        ]),
                ])

    wf.run()

def test_workflow_wrapper_fail_0():
    """ Test the WorkflowInterface constructor without workflow """
    with pytest.raises(RuntimeError):
        niu.WorkflowInterface(workflow=None)

def test_workflow_wrapper_fail_1():
    """ Test the WorkflowInterface constructor without workflow """
    with pytest.raises(RuntimeError):
        niu.WorkflowInterface(workflow='generate_workflow')

def test_workflow_wrapper_fail_2(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    os.chdir(str(tmpdir))
    wfif = niu.WorkflowInterface(workflow=generate_workflow)
    wfif.inputs.num = 42
    wfif.inputs.size = 'a'

    with pytest.raises(TypeError):
        wfif.run()

def test_workflow_wrapper_fail_3():
    """ Test the WorkflowInterface with an empty workflow """
    with pytest.raises(RuntimeError):
        niu.WorkflowInterface(workflow=pe.Workflow('WorkflowWithoutInputnode'))

def test_workflow_wrapper_fail_4():
    """ Test the WorkflowInterface constructor when there is no outputnode """
    wf = pe.Workflow('WorkflowWithoutOutputnode')

    # Add one inputnode to check how it fails when it does not find an outputnode
    wf.add_nodes([pe.Node(niu.IdentityInterface(fields=['a']), name='inputnode')])
    with pytest.raises(RuntimeError):
        niu.WorkflowInterface(workflow=wf)

def test_workflow_wrapper_fail_5():
    """ Test the WorkflowInterface when inputs are not set """

    wf = pe.Workflow('WorkflowNoInputsSet')
    node = pe.Node(BET(), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')
    wf.connect([
        (node, outputnode, [('out_file', 'out_file')])
    ])
    wi = niu.WorkflowInterface(workflow=wf)
    with pytest.raises(RuntimeError):
        wi.run()

def test_workflow_wrapper_fail_6():
    """ Test the WorkflowInterface setting an inproper input trait """
    wf = pe.Workflow('failworkflow')
    node = pe.Node(BET(), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')
    wf.connect([
        (node, outputnode, [('out_file', 'out_file')])
    ])
    wi = niu.WorkflowInterface(workflow=wf)
    wi.inputs.in_file = 'idonotexist.nii.gz'
    with pytest.raises(TraitError):
        wi.run()

def test_workflow_wrapper_mapnode():
    """ Test the WorkflowInterface in a MapNode """
    outerworkflow = pe.Workflow(name='OuterWorkflow')
    outerinput = pe.Node(niu.IdentityInterface(
                         fields=['a', 'b']), name='outerinput')
    wrapped = pe.MapNode(niu.WorkflowInterface(workflow=merge_workflow),
                         iterfield=['a', 'b'], name='dyniterable')
    outeroutput = pe.Node(niu.IdentityInterface(
                          fields=['c']), name='outeroutput')

    outerworkflow.connect([
        (outerinput, wrapped, [('a', 'a'), ('b', 'b')]),
        (wrapped, outeroutput, [('out', 'c')])
    ])
    outerworkflow.inputs.outerinput.a = [10, 12, 14]
    outerworkflow.inputs.outerinput.b = [9, -1, 10]

    outerworkflow.run()


def test_workflow_wrapper_iterables_1():
    """ Test the WorkflowInterface with iterables """
    wrapped = pe.Node(niu.WorkflowInterface(workflow=merge_workflow),
                      name='dyniterable')
    wrapped.iterables = ('a', [10, 12, 14])
    wrapped.inputs.b = 9
    res = wrapped.run()

    assert res.outputs == [[10, 9], [12, 9], [14, 9]]


def test_workflow_wrapper_iterables_2():
    """ Test the WorkflowInterface with iterables """
    wrapped = pe.Node(niu.WorkflowInterface(workflow=merge_workflow),
                      name='dyniterable')

    wrapped.iterables = [('a', [10, 12]),
                         ('b', [9, -1])]
    res = wrapped.run()
    assert res.outputs == [[10, 9], [10, -1], [12, 9], [12, -1]]

def test_workflow_wrapper_iterables_3():
    """ Test the WorkflowInterface with iterables """
    wrapped = pe.Node(niu.WorkflowInterface(workflow=merge_workflow),
                      name='dyniterable')

    wrapped.iterables = [('a', [10, 12]),
                         ('b', [9, -1])]

    wrapped.synchronize = True
    res = wrapped.run()
    assert res.outputs == [[10, 9], [12, -1]]

def test_workflow_wrapper(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    os.chdir(str(tmpdir))
    wf = generate_workflow('test_workflow_1')
    wfif = niu.WorkflowInterface(workflow=wf)
    wfif.inputs.num = 42
    wfif.inputs.size = 1

    res = wfif.run()
    assert res.outputs.sub == 43
    assert res.outputs.sum == 129

def test_workflow_wrapper_callable(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    os.chdir(str(tmpdir))
    wfif = niu.WorkflowInterface(workflow=generate_workflow)
    wfif.inputs.num = 42
    wfif.inputs.size = 1

    res = wfif.run()
    assert res.outputs.sub == 43
    assert res.outputs.sum == 129


def merge_workflow(name='MergeWorkflow'):
    """ Generates a simple workflow with only a merge node """
    inputnode = pe.Node(niu.IdentityInterface(
        fields=['a', 'b']), name='inputnode')

    mergenode = pe.Node(niu.Merge(2), name='mergenode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['c']), name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, mergenode, [('a', 'in1'), ('b', 'in2')]),
        (mergenode, outputnode, [('out', 'c')])
    ])
    return wf

def generate_workflow(name='TestWorkflow'):
    """ Generate a testing workflow """
    def _gen_tuple(size):
        return [1, ] * size

    def _sum_and_sub_mul(a, b, c):
        return (a+b)*c, (a-b)*c

    def _inc(x):
        return x + 1

    wf = pe.Workflow(name=name)
    params = pe.Node(niu.IdentityInterface(fields=['size', 'num']), name='inputnode')
    gen_tuple = pe.Node(niu.Function(
        input_names=['size'], output_names=['tuple'],
        function=_gen_tuple), name='gen_tuple')

    ssm = pe.Node(niu.Function(
        input_names=['a', 'b', 'c'], output_names=['sum', 'sub'],
        function=_sum_and_sub_mul), name='sum_and_sub_mul')

    split = pe.Node(niu.Split(splits=[1, 1], squeeze=True),
                    name='split')

    outputnode = pe.Node(niu.IdentityInterface(fields=['sum', 'sub']), name='outputnode')
    wf.connect([
        (params, gen_tuple, [(("size", _inc), "size")]),
        (params, ssm, [(("num", _inc), "c")]),
        (gen_tuple, split, [("tuple", "inlist")]),
        (split, ssm, [(("out1", _inc), "a"), ("out2", "b")]),
        (ssm, outputnode, [("sum", "sum"), ("sub", "sub")])
    ])
    return wf
