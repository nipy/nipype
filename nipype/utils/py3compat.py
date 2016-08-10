# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Compatibility for docstrings, inspired by IPython folks
https://github.com/ipython/ipython/blob/master/IPython/utils/py3compat.py#L261

"""


import sys
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