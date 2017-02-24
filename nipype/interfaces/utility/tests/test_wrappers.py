# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import print_function, unicode_literals
import os
import pytest

from nipype.interfaces import utility
import nipype.pipeline.engine as pe


def test_function(tmpdir):
    os.chdir(str(tmpdir))

    def gen_random_array(size):
        import numpy as np
        return np.random.rand(size, size)

    f1 = pe.MapNode(utility.Function(input_names=['size'], output_names=['random_array'], function=gen_random_array), name='random_array', iterfield=['size'])
    f1.inputs.size = [2, 3, 5]

    wf = pe.Workflow(name="test_workflow")

    def increment_array(in_array):
        return in_array + 1

    f2 = pe.MapNode(utility.Function(input_names=['in_array'], output_names=['out_array'], function=increment_array), name='increment_array', iterfield=['in_array'])

    wf.connect(f1, 'random_array', f2, 'in_array')
    wf.run()


def make_random_array(size):
    return np.random.randn(size, size)


def should_fail(tmpdir):
    os.chdir(tmpdir)

    node = pe.Node(utility.Function(input_names=["size"],
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

    node = pe.Node(utility.Function(input_names=["size"],
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

    params = pe.Node(utility.IdentityInterface(fields=['size', 'num']), name='params')
    params.inputs.num  = 42
    params.inputs.size = 1

    gen_tuple = pe.Node(utility.Function(input_names=['size'],
                                         output_names=['tuple'],
                                         function=_gen_tuple),
                                         name='gen_tuple')

    ssm = pe.Node(utility.Function(input_names=['a', 'b', 'c'],
                                   output_names=['sum', 'sub'],
                                   function=_sum_and_sub_mul),
                                   name='sum_and_sub_mul')

    split = pe.Node(utility.Split(splits=[1, 1],
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
    with pytest.raises(RuntimeError):
        utility.WorkflowInterface(workflow=None)

def test_workflow_wrapper_fail_1():
    with pytest.raises(RuntimeError):
        utility.WorkflowInterface(workflow='generate_workflow')

def test_workflow_wrapper_fail_2(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    os.chdir(str(tmpdir))
    wfif = utility.WorkflowInterface(workflow=generate_workflow)
    wfif.inputs.num = 42
    wfif.inputs.size = 'a'

    with pytest.raises(TypeError):
        res = wfif.run()

def test_workflow_wrapper_fail_3():
    with pytest.raises(RuntimeError):
        utility.WorkflowInterface(workflow=pe.Workflow('some_failing_workflow'))


def test_workflow_wrapper_fail_4():
    from nipype.interfaces import utility as niu
    from nipype.pipeline import engine as pe
    from nipype.interfaces.fsl import BET

    wf = pe.Workflow('fail workflow')
    wf = pe.Workflow('failworkflow')
    node = pe.Node(BET(), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(fields=['out_file']), name='outputnode')
    wf.connect([
        (node, outputnode, [('out_file', 'out_file')])
    ])
    wi = niu.WorkflowInterface(workflow=wf)
    with pytest.raises(RuntimeError):
        wi.run()

def test_workflow_wrapper_fail_5():
    from nipype.interfaces import utility as niu
    from nipype.pipeline import engine as pe
    from nipype.interfaces.fsl import BET
    from nipype.interfaces.base import TraitError

    wf = pe.Workflow('fail workflow')
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
    def merge_workflow(name='MergeWorkflow'):
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



def test_workflow_wrapper_fail_4():
    wf = pe.Workflow('some_failing_workflow')

    # Add one inputnode to check how it fails when it does not find an outputnode
    wf.add_nodes([pe.Node(utility.IdentityInterface(fields=['a']), name='inputnode')])
    with pytest.raises(RuntimeError):
        utility.WorkflowInterface(workflow=wf)

def test_workflow_wrapper(tmpdir):
    """ This tests excution nodes with multiple inputs and auxiliary
    function inside the Workflow connect function.
    """
    os.chdir(str(tmpdir))
    wf = generate_workflow('test_workflow_1')
    wfif = utility.WorkflowInterface(workflow=wf)
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
    wfif = utility.WorkflowInterface(workflow=generate_workflow)
    wfif.inputs.num = 42
    wfif.inputs.size = 1

    res = wfif.run()
    assert res.outputs.sub == 43
    assert res.outputs.sum == 129


def generate_workflow(name='test_workflow'):

    def _gen_tuple(size):
        return [1, ] * size

    def _sum_and_sub_mul(a, b, c):
        return (a+b)*c, (a-b)*c

    def _inc(x):
        return x + 1

    wf = pe.Workflow(name=name)
    params = pe.Node(utility.IdentityInterface(fields=['size', 'num']), name='inputnode')
    gen_tuple = pe.Node(utility.Function(input_names=['size'],
                                         output_names=['tuple'],
                                         function=_gen_tuple),
                                         name='gen_tuple')

    ssm = pe.Node(utility.Function(input_names=['a', 'b', 'c'],
                                   output_names=['sum', 'sub'],
                                   function=_sum_and_sub_mul),
                                   name='sum_and_sub_mul')

    split = pe.Node(utility.Split(splits=[1, 1], squeeze=True),
                    name='split')

    outputnode = pe.Node(utility.IdentityInterface(fields=['sum', 'sub']), name='outputnode')
    wf.connect([
        (params,    gen_tuple,  [(("size", _inc),   "size")]),
        (params,    ssm,        [(("num", _inc),    "c")]),
        (gen_tuple, split,      [("tuple",          "inlist")]),
        (split,     ssm,        [(("out1", _inc),   "a"),
                                 ("out2",           "b")]),
        (ssm, outputnode,       [("sum", "sum"), ("sub", "sub")])
    ])
    return wf
