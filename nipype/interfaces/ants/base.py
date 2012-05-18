# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ants module provides basic functions for interfacing with ANTS tools."""

# Local imports
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec, traits,
isdefined)

from ... import logging
logger = logging.getLogger('interface')


class ANTSCommandInputSpec(CommandLineInputSpec):
    """Base Input Specification for all ANTS Commands
    """

    num_threads = traits.Int(1, usedefault=True, nohash=True,
                             desc="Number of ITK threads to use")


class ANTSCommand(CommandLine):
    """Base class for ANTS interfaces
    """

    input_spec = ANTSCommandInputSpec
    _num_threads = 1

    def __init__(self, **inputs):
        super(ANTSCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, 'num_threads')

        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()

    def _num_threads_update(self):
        self._num_threads = self.inputs.num_threads
        self.inputs.environ.update({'ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS':
                                        '%s' % self.inputs.num_threads})

    @classmethod
    def set_default_num_threads(cls, num_threads):
        """Set the default number of threads for ITK calls

        This method is used to set the default number of ITK threads for all
        the ANTS interfaces. However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.num_threads
        """
        cls._num_threads = num_threads
