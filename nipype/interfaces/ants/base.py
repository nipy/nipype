# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ants module provides basic functions for interfacing with ANTS tools."""

__docformat__ = 'restructuredtext'

# Standard library imports
import os
from copy import deepcopy

# Third-party imports
import numpy as np

# Local imports
from nipype.interfaces.base import (TraitedSpec, File, traits,
                                    Directory, InputMultiPath,
                                    OutputMultiPath, CommandLine,
                                    CommandLineInputSpec, isdefined)
import logging
logger = logging.getLogger('iflogger')


class ANTSCommandInputSpec(CommandLineInputSpec):

    def _test():
        return True

class ANTSCommand(CommandLine):

    def _run_interface(self,runtime):
        if (not os.environ.has_key('LD_LIBRARY_PATH')) or (os.environ.get('LD_LIBRARY_PATH').find(':/software/ANTS/versions/120222/lib') == -1):
            os.environ['LD_LIBRARY_PATH']=os.environ['LD_LIBRARY_PATH']+':/software/ANTS/versions/120222/lib'
        if (not os.environ.has_key('PATH')) or (os.environ.get('PATH').find('/software/ANTS/versions/120222/bin') == -1):
            os.environ['PATH']=os.environ['PATH']+':/software/ANTS/versions/120222/bin'
        if (not os.environ.has_key('ANTSPATH') )or (os.environ.get('ANTSPATH').find('/software/ANTS/versions/120222/bin/') == -1):
            os.environ['ANTSPATH']='/software/ANTS/versions/120222/bin/'
        self.inputs.environ=dict(os.environ)
        return super(ANTSCommand, self)._run_interface(runtime)

