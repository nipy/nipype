# -*- coding: utf-8 -*-
import pytest
from nipype.utils.functions import getsource, create_function_from_source


def _func1(x):
    return x**3


def test_func_to_str():
    def func1(x):
        return x**2

    # Should be ok with both functions!
    for f in _func1, func1:
        f_src = getsource(f)
        f_recreated = create_function_from_source(f_src)
        assert f(2.3) == f_recreated(2.3)


def test_func_to_str_err():
    bad_src = "obbledygobbledygook"
    with pytest.raises(RuntimeError):
        create_function_from_source(bad_src)


def _print_statement():
    try:
        exec('print("")')
        return True
    except SyntaxError:
        return False


def test_func_string():
    def is_string():
        return isinstance("string", str)

    wrapped_func = create_function_from_source(getsource(is_string))
    assert is_string() == wrapped_func()


def test_func_print():
    wrapped_func = create_function_from_source(getsource(_print_statement))
    assert wrapped_func()
