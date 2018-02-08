# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()

import os
from shutil import rmtree
from builtins import next

import pytest

from nipype.utils.misc import (container_to_string, str2bool, flatten,
                               unflatten)


def test_cont_to_str():
    # list
    x = ['a', 'b']
    assert container_to_string(x) == 'a b'
    # tuple
    x = tuple(x)
    assert container_to_string(x) == 'a b'
    # set
    x = set(x)
    y = container_to_string(x)
    assert (y == 'a b') or (y == 'b a')
    # dict
    x = dict(a='a', b='b')
    y = container_to_string(x)
    assert (y == 'a b') or (y == 'b a')
    # string
    assert container_to_string('foobar') == 'foobar'
    # int.  Integers are not the main intent of this function, but see
    # no reason why they shouldn't work.
    assert (container_to_string(123) == '123')


@pytest.mark.parametrize("string, expected",
                         [("yes", True), ("true", True), ("t", True),
                          ("1", True), ("no", False), ("false", False),
                          ("n", False), ("f", False), ("0", False)])
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

    monkeypatch.setenv('PWD', oldpath)
    assert rgetcwd(error=False) == oldpath

    # Test when error should be raised
    with pytest.raises(OSError):
        rgetcwd()

    # Deleted env variable
    monkeypatch.delenv('PWD')
    with pytest.raises(OSError):
        rgetcwd(error=False)
