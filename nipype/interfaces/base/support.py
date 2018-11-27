# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""

Miscellaneous tools to support Interface functionality
......................................................

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import object

from ... import __version__


class NipypeInterfaceError(RuntimeError):
    """Custom error for interfaces"""
    pass


class InterfaceRuntime(object):
    """A class to store runtime details of interfaces

    Elements can be set at initialization:

    >>> rt = InterfaceRuntime(cmdline='/bin/echo', returncode=0)
    >>> rt.returncode == 0
    True

    Unset elements are initialized to ``None``:

    >>> rt.cwd is None
    True

    And any element can be set by attribute:

    >>> rt.cwd = '/scratch/workflow'
    >>> rt.cwd
    '/scratch/workflow'

    The structure raises ``AttributeError`` if trying to accessing
    an invalid attribute:

    >>> rt.nonruntime
    Traceback (most recent call last):
        ...
    AttributeError: 'InterfaceRuntime' object has no attribute 'nonruntime'


    For Nipype to work, it is fundamental that runtime objects
    can be pickled/unpickled:

    >>> import pickle
    >>> pickleds = pickle.dumps(rt)
    >>> newrt = pickle.loads(pickleds)
    >>> newrt == rt
    True

    >>> newrt != rt
    False

    >>> newrt
    Bunch(cmdline='/bin/echo', cwd='/scratch/workflow', returncode=0)

    """

    __slots__ = sorted([
        'cwd',
        'prevcwd',
        'returncode',
        'duration',
        'environ',
        'startTime',
        'endTime',
        'platform',
        'hostname',
        'version',
        'traceback',
        'traceback_args',
        'mem_peak_gb',
        'cpu_percent',
        'prof_dict',
        'cmdline',
        'stdout',
        'stderr',
        'merged',
        'command_path',
        'dependencies',
    ])

    def __init__(self, **inputs):
        self.__setstate__(inputs)

    def __setstate__(self, state):
        """Necessary for un-pickling"""
        for key in self.__class__.__slots__:
            setattr(self, key, state.get(key, None))

    def __getstate__(self):
        """Necessary for pickling"""
        outdict = {}
        for key in self.__class__.__slots__:
            value = getattr(self, key, None)
            if value is not None:
                outdict[key] = value
        return outdict

    def dictcopy(self):
        """
        Returns a dictionary of set attributes (backward compatibility)

        >>> rt = InterfaceRuntime()
        >>> rt.dictcopy()
        {}

        >>> rt = InterfaceRuntime(cmdline='/bin/echo', returncode=0)
        >>> rt.dictcopy()
        {'cmdline': '/bin/echo', 'returncode': 0}

        """
        return self.__getstate__()

    def items(self):
        """Provide an interface for items

        >>> rt = InterfaceRuntime()
        >>> list(rt.items())
        []

        >>> rt = InterfaceRuntime(cmdline='/bin/echo', returncode=0)
        >>> list(rt.items())
        [('cmdline', '/bin/echo'), ('returncode', 0)]


        """
        for key in self.__class__.__slots__:
            value = getattr(self, key, None)
            if value is not None:
                yield (key, value)

    def __repr__(self):
        """representation of the runtime object"""
        outstr = ['Bunch(']
        first = True
        for k, v in sorted(self.items()):
            if not first:
                outstr.append(', ')
            if isinstance(v, dict):
                pairs = []
                for key, value in sorted(v.items()):
                    pairs.append("'%s': %s" % (key, value))
                v = '{' + ', '.join(pairs) + '}'
                outstr.append('%s=%s' % (k, v))
            else:
                outstr.append('%s=%r' % (k, v))
            first = False
        outstr.append(')')
        return ''.join(outstr)

    def __str__(self):
        return '%s' % self.__getstate__()

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, InterfaceRuntime):
            return self.__getstate__() == other.__getstate__()
        return NotImplemented

    def __ne__(self, other):
        """Overrides the default implementation (Python 2)"""
        x = self.__eq__(other)
        if x is not NotImplemented:
            return not x
        return NotImplemented


class InterfaceResult(object):
    """Object that contains the results of running a particular Interface.

    Attributes
    ----------
    version : version of this Interface result object (a readonly property)
    interface : class type
        A copy of the `Interface` class that was run to generate this result.
    inputs :  a traits free representation of the inputs
    outputs : Bunch
        An `Interface` specific Bunch that contains all possible files
        that are generated by the interface.  The `outputs` are used
        as the `inputs` to another node when interfaces are used in
        the pipeline.
    runtime : Bunch

        Contains attributes that describe the runtime environment when
        the `Interface` was run.  Contains the attributes:

        * cmdline : The command line string that was executed
        * cwd : The directory the ``cmdline`` was executed in.
        * stdout : The output of running the ``cmdline``.
        * stderr : Any error messages output from running ``cmdline``.
        * returncode : The code returned from running the ``cmdline``.

    """
    __slots__ = ['interface', 'runtime', 'inputs', 'outputs', 'provenance']
    version = __version__

    def __init__(self,
                 interface,
                 runtime,
                 inputs=None,
                 outputs=None,
                 provenance=None):
        self.interface = interface
        self.runtime = runtime
        self.inputs = inputs
        self.outputs = outputs
        self.provenance = provenance
