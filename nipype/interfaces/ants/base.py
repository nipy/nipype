# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ants module provides basic functions for interfacing with ANTS tools."""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str

import os

# Local imports
from ... import logging, LooseVersion
from ..base import (CommandLine, CommandLineInputSpec, traits, isdefined,
                    PackageInfo)
iflogger = logging.getLogger('nipype.interface')

# -Using -1 gives primary responsibilty to ITKv4 to do the correct
#  thread limitings.
# -Using 1 takes a very conservative approach to avoid overloading
#  the computer (when running MultiProc) by forcing everything to
#  single threaded.  This can be a severe penalty for registration
#  performance.
LOCAL_DEFAULT_NUMBER_OF_THREADS = 1
# -Using NSLOTS has the same behavior as ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS
#  as long as ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS is not set.  Otherwise
#  ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS takes precidence.
#  This behavior states that you the user explicitly specifies
#  num_threads, then respect that no matter what SGE tries to limit.
PREFERED_ITKv4_THREAD_LIMIT_VARIABLE = 'NSLOTS'
ALT_ITKv4_THREAD_LIMIT_VARIABLE = 'ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS'


class Info(PackageInfo):
    version_cmd = os.path.join(os.getenv('ANTSPATH', ''),
                               'antsRegistration') + ' --version'

    @staticmethod
    def parse_version(raw_info):
        for line in raw_info.splitlines():
            if line.startswith('ANTs Version: '):
                v_string = line.split()[2]
                break
        else:
            return None

        # -githash may or may not be appended
        v_string = v_string.split('-')[0]

        # 2.2.0-equivalent version string
        if 'post' in v_string and \
                LooseVersion(v_string) >= LooseVersion('2.1.0.post789'):
            return '2.2.0'
        else:
            return '.'.join(v_string.split('.')[:3])


class ANTSCommandInputSpec(CommandLineInputSpec):
    """Base Input Specification for all ANTS Commands
    """

    num_threads = traits.Int(
        LOCAL_DEFAULT_NUMBER_OF_THREADS,
        usedefault=True,
        nohash=True,
        desc="Number of ITK threads to use")


class ANTSCommand(CommandLine):
    """Base class for ANTS interfaces
    """

    input_spec = ANTSCommandInputSpec
    _num_threads = LOCAL_DEFAULT_NUMBER_OF_THREADS

    def __init__(self, **inputs):
        super(ANTSCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._num_threads_update, 'num_threads')

        if not isdefined(self.inputs.num_threads):
            self.inputs.num_threads = self._num_threads
        else:
            self._num_threads_update()

    def _num_threads_update(self):
        self._num_threads = self.inputs.num_threads
        # ONLY SET THE ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS if requested
        # by the end user.  The default setting did not allow for
        # overwriting the default values.
        # In ITKv4 (the version used for all ANTS programs), ITK respects
        # the SGE controlled $NSLOTS environmental variable.
        # If user specifies -1, then that indicates that the system
        # default behavior should be the one specified by ITKv4 rules
        # (i.e. respect SGE $NSLOTS or environmental variables of threads, or
        # user environmental settings)
        if (self.inputs.num_threads == -1):
            if (ALT_ITKv4_THREAD_LIMIT_VARIABLE in self.inputs.environ):
                del self.inputs.environ[ALT_ITKv4_THREAD_LIMIT_VARIABLE]
            if (PREFERED_ITKv4_THREAD_LIMIT_VARIABLE in self.inputs.environ):
                del self.inputs.environ[PREFERED_ITKv4_THREAD_LIMIT_VARIABLE]
        else:
            self.inputs.environ.update({
                PREFERED_ITKv4_THREAD_LIMIT_VARIABLE:
                '%s' % self.inputs.num_threads
            })

    @staticmethod
    def _format_xarray(val):
        """ Convenience method for converting input arrays [1,2,3] to
        commandline format '1x2x3' """
        return 'x'.join([str(x) for x in val])

    @classmethod
    def set_default_num_threads(cls, num_threads):
        """Set the default number of threads for ITK calls

        This method is used to set the default number of ITK threads for all
        the ANTS interfaces. However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.num_threads
        """
        cls._num_threads = num_threads

    @property
    def version(self):
        return Info.version()
