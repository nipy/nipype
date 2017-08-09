# -*- coding: utf-8 -*-
import sys
import pytest
from nipype.utils.functions import (getsource, create_function_from_source)

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
    with pytest.raises(RuntimeError): create_function_from_source(bad_src)

@pytest.mark.skipif(sys.version_info[0] > 2, reason="breaks python 3")
def test_func_py2():
    def is_string():
        return isinstance('string', str)

    def print_statement():
        # test python 2 compatibility
        exec('print ""')

    wrapped_func = create_function_from_source(getsource(is_string))
    assert is_string() == wrapped_func()

    wrapped_func2 = create_function_from_source(getsource(print_statement))
    wrapped_func2()
