#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Wrapper to run setup.py using setuptools."""
from __future__ import print_function, division, unicode_literals, absolute_import
from io import open
import os.path

################################################################################
# Call the setup.py script, injecting the setuptools-specific arguments.

extra_setuptools_args = dict(tests_require=['nose'],
                             test_suite='nose.collector',
                             zip_safe=False,
                             )


if __name__ == '__main__':
    setup_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'setup.py')
    with open(setup_file) as f:
        code = compile(f.read(), setup_file, 'exec')
        exec(code, dict(__name__='__main__',
                        extra_setuptools_args=extra_setuptools_args))
