#!/usr/bin/env python
"""Wrapper to run setup.py using setuptools."""

from setuptools import setup 

################################################################################
# Call the setup.py script, injecting the setuptools-specific arguments.

extra_setuptools_args = dict(
                            tests_require=['nose'],
                            test_suite='nose.collector',
                            zip_safe=False,
                            )


if __name__ == '__main__':
    execfile('setup.py', dict(__name__='__main__', 
                          extra_setuptools_args=extra_setuptools_args))



