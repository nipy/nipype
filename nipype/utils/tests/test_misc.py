# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()

from builtins import next

from nipype.testing import (assert_equal, assert_true, assert_false,
                            assert_raises)

from nipype.utils.misc import (container_to_string, getsource,
                               create_function_from_source, str2bool, flatten,
                               unflatten)


def test_cont_to_str():
    # list
    x = ['a', 'b']
    yield assert_true, container_to_string(x) == 'a b'
    # tuple
    x = tuple(x)
    yield assert_true, container_to_string(x) == 'a b'
    # set
    x = set(x)
    y = container_to_string(x)
    yield assert_true, (y == 'a b') or (y == 'b a')
    # dict
    x = dict(a='a', b='b')
    y = container_to_string(x)
    yield assert_true, (y == 'a b') or (y == 'b a')
    # string
    yield assert_true, container_to_string('foobar') == 'foobar'
    # int.  Integers are not the main intent of this function, but see
    # no reason why they shouldn't work.
    yield assert_true, (container_to_string(123) == '123')


def _func1(x):
    return x**3


def test_func_to_str():

    def func1(x):
        return x**2

    # Should be ok with both functions!
    for f in _func1, func1:
        f_src = getsource(f)
        f_recreated = create_function_from_source(f_src)
        yield assert_equal, f(2.3), f_recreated(2.3)

def test_func_to_str_err():
    bad_src = "obbledygobbledygook"
    yield assert_raises, RuntimeError, create_function_from_source, bad_src

def test_str2bool():
    yield assert_true, str2bool("yes")
    yield assert_true, str2bool("true")
    yield assert_true, str2bool("t")
    yield assert_true, str2bool("1")
    yield assert_false, str2bool("no")
    yield assert_false, str2bool("false")
    yield assert_false, str2bool("n")
    yield assert_false, str2bool("f")
    yield assert_false, str2bool("0")


def test_flatten():
    in_list = [[1, 2, 3], [4], [[5, 6], 7], 8]

    flat = flatten(in_list)
    yield assert_equal, flat, [1, 2, 3, 4, 5, 6, 7, 8]

    back = unflatten(flat, in_list)
    yield assert_equal, in_list, back

    new_list = [2, 3, 4, 5, 6, 7, 8, 9]
    back = unflatten(new_list, in_list)
    yield assert_equal, back, [[2, 3, 4], [5], [[6, 7], 8], 9]

    flat = flatten([])
    yield assert_equal, flat, []

    back = unflatten([], [])
    yield assert_equal, back, []
