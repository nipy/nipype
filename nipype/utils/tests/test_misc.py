# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from shutil import rmtree

import pytest

from nipype.utils.misc import (
    container_to_string,
    str2bool,
    flatten,
    unflatten,
    dict_diff,
)


def test_cont_to_str():
    # list
    x = ["a", "b"]
    assert container_to_string(x) == "a b"
    # tuple
    x = tuple(x)
    assert container_to_string(x) == "a b"
    # set
    x = set(x)
    y = container_to_string(x)
    assert (y == "a b") or (y == "b a")
    # dict
    x = dict(a="a", b="b")
    y = container_to_string(x)
    assert (y == "a b") or (y == "b a")
    # string
    assert container_to_string("foobar") == "foobar"
    # int.  Integers are not the main intent of this function, but see
    # no reason why they shouldn't work.
    assert container_to_string(123) == "123"


@pytest.mark.parametrize(
    "string, expected",
    [
        ("yes", True),
        ("true", True),
        ("t", True),
        ("1", True),
        ("no", False),
        ("false", False),
        ("n", False),
        ("f", False),
        ("0", False),
    ],
)
def test_str2bool(string, expected):
    assert str2bool(string) == expected


def test_flatten():
    in_list = [[1, 2, 3], [4], [[5, 6], 7], 8]

    flat = flatten(in_list)
    assert flat == [1, 2, 3, 4, 5, 6, 7, 8]

    back = unflatten(flat, in_list)
    assert in_list == back

    new_list = [2, 3, 4, 5, 6, 7, 8, 9]
    back = unflatten(new_list, in_list)
    assert back == [[2, 3, 4], [5], [[6, 7], 8], 9]

    flat = flatten([])
    assert flat == []

    back = unflatten([], [])
    assert back == []


def test_rgetcwd(monkeypatch, tmpdir):
    from ..misc import rgetcwd

    oldpath = tmpdir.strpath
    tmpdir.mkdir("sub").chdir()
    newpath = os.getcwd()

    # Path still there
    assert rgetcwd() == newpath

    # Remove path
    rmtree(newpath, ignore_errors=True)
    with pytest.raises(OSError):
        os.getcwd()

    monkeypatch.setenv("PWD", oldpath)
    assert rgetcwd(error=False) == oldpath

    # Test when error should be raised
    with pytest.raises(OSError):
        rgetcwd()

    # Deleted env variable
    monkeypatch.delenv("PWD")
    with pytest.raises(OSError):
        rgetcwd(error=False)


def test_dict_diff():
    abtuple = [("a", "b")]
    abdict = dict(abtuple)

    # Unchanged
    assert dict_diff(abdict, abdict) == ""
    assert dict_diff(abdict, abtuple) == ""
    assert dict_diff(abtuple, abdict) == ""
    assert dict_diff(abtuple, abtuple) == ""

    # Changed keys
    diff = dict_diff({"a": "b"}, {"b": "a"})
    assert "Dictionaries had differing keys" in diff
    assert "keys not previously seen: {'b'}" in diff
    assert "keys not presently seen: {'a'}" in diff

    # Trigger recursive uniformization
    complicated_val1 = [{"a": ["b"], "c": ("d", "e")}]
    complicated_val2 = [{"a": ["x"], "c": ("d", "e")}]
    uniformized_val1 = ({"a": ("b",), "c": ("d", "e")},)
    uniformized_val2 = ({"a": ("x",), "c": ("d", "e")},)

    diff = dict_diff({"a": complicated_val1}, {"a": complicated_val2})
    assert "Some dictionary entries had differing values:" in diff
    assert f"a: {uniformized_val2!r} != {uniformized_val1!r}" in diff

    # Trigger shortening
    diff = dict_diff({"a": "b" * 60}, {"a": "c" * 70})
    assert "Some dictionary entries had differing values:" in diff
    assert "a: 'cccccccccc...cccccccccc' != 'bbbbbbbbbb...bbbbbbbbbb'" in diff

    # Fail the dict conversion
    diff = dict_diff({}, "not a dict")
    assert diff == (
        "Diff between nipype inputs failed:\n"
        "* Cached inputs: {}\n"
        "* New inputs: not a dict"
    )
