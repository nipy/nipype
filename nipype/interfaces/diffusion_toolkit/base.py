# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The dtk module provides basic functions for interfacing with
Diffusion Toolkit tools.

Currently these tools are supported:

    * TODO

Examples
--------
See the docstrings for the individual classes for 'working' examples.

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import object
import re
from ..base import CommandLine

__docformat__ = 'restructuredtext'


class Info(object):
    """ Handle dtk output type and version information.

    Examples
    --------

    >>> from nipype.interfaces.diffusion_toolkit import Info
    >>> Info.version()  # doctest: +SKIP
    >>> Info.subjectsdir()  # doctest: +SKIP

    """

    @staticmethod
    def version():
        """Check for dtk version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if FSL not found

        """
        clout = CommandLine(
            command='dti_recon', terminal_output='allatonce').run()

        if clout.runtime.returncode is not 0:
            return None

        dtirecon = clout.runtime.stdout
        result = re.search('dti_recon (.*)\n', dtirecon)
        version = result.group(0).split()[1]
        return version
