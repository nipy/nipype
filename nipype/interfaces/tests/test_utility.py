# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import pytest

from nipype.interfaces import utility
import nipype.pipeline.engine as pe


def test_rename(tmpdir):
    os.chdir(str(tmpdir))

    # Test very simple rename
    _ = open("file.txt", "w").close()
    rn = utility.Rename(in_file="file.txt", format_string="test_file1.txt")
    res = rn.run()
    outfile = str(tmpdir.join("test_file1.txt"))
    assert res.outputs.out_file == outfile
    assert os.path.exists(outfile)

    # Now a string-formatting version
    rn = utility.Rename(in_file="file.txt", format_string="%(field1)s_file%(field2)d", keep_ext=True)
    # Test .input field creation
    assert hasattr(rn.inputs, "field1")
    assert hasattr(rn.inputs, "field2")

    # Set the inputs
    rn.inputs.field1 = "test"
    rn.inputs.field2 = 2
    res = rn.run()
    outfile = str(tmpdir.join("test_file2.txt"))
    assert res.outputs.out_file == outfile
    assert os.path.exists(outfile)


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


@pytest.mark.parametrize("args, expected", [
        ({}                ,  ([0], [1,2,3])),
        ({"squeeze" : True},  (0  , [1,2,3]))
        ])
def test_split(tmpdir, args, expected):
    os.chdir(str(tmpdir))

    node = pe.Node(utility.Split(inlist=list(range(4)),
                                 splits=[1, 3],
                                 **args),
                   name='split_squeeze')
    res = node.run()
    assert res.outputs.out1 == expected[0]
    assert res.outputs.out2 == expected[1]


def test_csvReader(tmpdir):
    header = "files,labels,erosion\n"
    lines = ["foo,hello,300.1\n",
             "bar,world,5\n",
             "baz,goodbye,0.3\n"]
    for x in range(2):
        name = str(tmpdir.join("testfile.csv"))
        with open(name, 'w') as fid:
            reader = utility.CSVReader()
            if x % 2 == 0:
                fid.write(header)
                reader.inputs.header = True
            fid.writelines(lines)
            fid.flush()
            reader.inputs.in_file = name
            out = reader.run()
            if x % 2 == 0:
                assert out.outputs.files == ['foo', 'bar', 'baz']
                assert out.outputs.labels == ['hello', 'world', 'goodbye']
                assert out.outputs.erosion == ['300.1', '5', '0.3']
            else:
                assert out.outputs.column_0 == ['foo', 'bar', 'baz']
                assert out.outputs.column_1 == ['hello', 'world', 'goodbye']
                assert out.outputs.column_2 == ['300.1', '5', '0.3']


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
