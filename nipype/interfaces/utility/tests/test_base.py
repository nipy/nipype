# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import pytest

from nipype.interfaces import utility
from nipype.interfaces.base import isdefined
import nipype.pipeline.engine as pe


def test_rename(tmpdir):
    tmpdir.chdir()

    # Test very simple rename
    _ = open("file.txt", "w").close()
    rn = utility.Rename(in_file="file.txt", format_string="test_file1.txt")
    res = rn.run()
    outfile = tmpdir.join("test_file1.txt").strpath
    assert res.outputs.out_file == outfile
    assert os.path.exists(outfile)

    # Now a string-formatting version
    rn = utility.Rename(
        in_file="file.txt", format_string="%(field1)s_file%(field2)d", keep_ext=True
    )
    # Test .input field creation
    assert hasattr(rn.inputs, "field1")
    assert hasattr(rn.inputs, "field2")

    # Set the inputs
    rn.inputs.field1 = "test"
    rn.inputs.field2 = 2
    res = rn.run()
    outfile = tmpdir.join("test_file2.txt").strpath
    assert res.outputs.out_file == outfile
    assert os.path.exists(outfile)


@pytest.mark.parametrize(
    "args, expected", [({}, ([0], [1, 2, 3])), ({"squeeze": True}, (0, [1, 2, 3]))]
)
def test_split(tmpdir, args, expected):
    tmpdir.chdir()

    node = pe.Node(
        utility.Split(inlist=list(range(4)), splits=[1, 3], **args),
        name="split_squeeze",
    )
    res = node.run()
    assert res.outputs.out1 == expected[0]
    assert res.outputs.out2 == expected[1]


@pytest.mark.parametrize(
    "args, kwargs, in_lists, expected",
    [
        ([3], {}, [0, [1, 2], [3, 4, 5]], [0, 1, 2, 3, 4, 5]),
        ([0], {}, None, None),
        ([], {}, [], []),
        ([], {}, [0, [1, 2], [3, 4, 5]], [0, [1, 2], [3, 4, 5]]),
        ([3], {"axis": "hstack"}, [[0], [1, 2], [3, 4, 5]], [[0, 1, 3]]),
        ([3], {"axis": "hstack"}, [[0, 1], [2, 3], [4, 5]], [[0, 2, 4], [1, 3, 5]]),
        ([3], {"axis": "hstack"}, [[0, 1], [2, 3], [4, 5]], [[0, 2, 4], [1, 3, 5]]),
    ],
)
def test_merge(tmpdir, args, kwargs, in_lists, expected):
    tmpdir.chdir()

    node = pe.Node(utility.Merge(*args, **kwargs), name="merge")

    numinputs = args[0] if args else 0
    if numinputs >= 1:
        for i in range(1, numinputs + 1):
            setattr(node.inputs, "in{:d}".format(i), in_lists[i - 1])

    res = node.run()
    if numinputs < 1:
        assert not isdefined(res.outputs.out)
    else:
        assert res.outputs.out == expected
