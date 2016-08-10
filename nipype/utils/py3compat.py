# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Compatibility for docstrings, inspired by IPython folks
https://github.com/ipython/ipython/blob/master/IPython/utils/py3compat.py#L261

"""
import functools
import sys
from six import string_types

def _modify_str_or_docstring(str_change_func):
    @functools.wraps(str_change_func)
    def wrapper(func_or_str):
        if isinstance(func_or_str, string_types):
            func = None
            doc = func_or_str
        else:
            func = func_or_str
            doc = func.__doc__

        # PYTHONOPTIMIZE=2 strips docstrings, so they can disappear unexpectedly
        if doc is not None:
            doc = str_change_func(doc)

        if func:
            func.__doc__ = doc
            return func
        return doc
    return wrapper


if sys.version_info[0] >= 3:
    # Abstract u'abc' syntax:
    @_modify_str_or_docstring
    def u_format(s):
        """"{u}'abc'" --> "'abc'" (Python 3)

        Accepts a string or a function, so it can be used as a decorator."""
        return s.format(u='')
else:
    # Abstract u'abc' syntax:
    @_modify_str_or_docstring
    def u_format(s):
        """"{u}'abc'" --> "u'abc'" (Python 2)

        Accepts a string or a function, so it can be used as a decorator."""
        return s.format(u='u')


def mymetaclass(cls, parents, attrs):
    attrs['__doc__'] = u_format(attrs['__doc__'])
    return type(cls, parents, attrs)
