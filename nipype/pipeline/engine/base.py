#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Workflow` class provides core functionality for batch processing.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)

"""

from future import standard_library
standard_library.install_aliases()
from builtins import object

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from copy import deepcopy
import re
import numpy as np
from nipype.interfaces.traits_extension import traits, Undefined
from nipype.interfaces.base import DynamicTraitedSpec
from nipype.utils.filemanip import loadpkl, savepkl

from nipype import logging
logger = logging.getLogger('workflow')


class EngineBase(object):
    """Defines common attributes and functions for workflows and nodes."""

    def __init__(self, name=None, base_dir=None):
        """ Initialize base parameters of a workflow or node

        Parameters
        ----------
        name : string (mandatory)
            Name of this node. Name must be alphanumeric and not contain any
            special characters (e.g., '.', '@').
        base_dir : string
            base output directory (will be hashed before creations)
            default=None, which results in the use of mkdtemp

        """
        self.base_dir = base_dir
        self.config = None
        self._verify_name(name)
        self.name = name
        # for compatibility with node expansion using iterables
        self._id = self.name
        self._hierarchy = None

    @property
    def inputs(self):
        raise NotImplementedError

    @property
    def outputs(self):
        raise NotImplementedError

    @property
    def fullname(self):
        fullname = self.name
        if self._hierarchy:
            fullname = self._hierarchy + '.' + self.name
        return fullname

    def clone(self, name):
        """Clone a workflowbase object

        Parameters
        ----------

        name : string (mandatory)
            A clone of node or workflow must have a new name
        """
        if (name is None) or (name == self.name):
            raise Exception('Cloning requires a new name')
        self._verify_name(name)
        clone = deepcopy(self)
        clone.name = name
        clone._id = name
        clone._hierarchy = None
        return clone

    def _check_outputs(self, parameter):
        return hasattr(self.outputs, parameter)

    def _check_inputs(self, parameter):
        if isinstance(self.inputs, DynamicTraitedSpec):
            return True
        return hasattr(self.inputs, parameter)

    def _verify_name(self, name):
        valid_name = bool(re.match('^[\w-]+$', name))
        if not valid_name:
            raise ValueError('[Workflow|Node] name \'%s\' contains'
                             ' special characters' % name)

    def __repr__(self):
        if self._hierarchy:
            return '.'.join((self._hierarchy, self._id))
        else:
            return self._id

    def save(self, filename=None):
        if filename is None:
            filename = 'temp.pklz'
        savepkl(filename, self)

    def load(self, filename):
        if '.npz' in filename:
            DeprecationWarning(('npz files will be deprecated in the next '
                                'release. you can use numpy to open them.'))
            return np.load(filename)
        return loadpkl(filename)


class WorkflowSignalTraits(traits.HasTraits):
    def __init__(self, **kwargs):
        """ Initialize handlers and inputs"""
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        # super(TraitedSpec, self).__init__(*args, **kwargs)
        super(WorkflowSignalTraits, self).__init__(**kwargs)
        traits.push_exception_handler(reraise_exceptions=True)
        undefined_traits = {}
        for trait in self.copyable_trait_names():
            if not self.traits()[trait].usedefault:
                undefined_traits[trait] = Undefined
        self.trait_set(trait_change_notify=False, **undefined_traits)
        self.set(**kwargs)


class BaseSignals(WorkflowSignalTraits):
    disable = traits.Bool(False, usedefault=True)


class NodeBase(EngineBase):
    def __init__(self, name, base_dir=None, control=True):
        """Create a workflow object.

        Parameters
        ----------
        name : alphanumeric string
            unique identifier for the workflow
        base_dir : string, optional
            path to workflow storage

        """
        super(NodeBase, self).__init__(name, base_dir)
        # Initialize signals
        self._signals = None
        if control:
            self._signals = BaseSignals()
            for elem in self._signals.copyable_trait_names():
                self._signals.on_trait_change(self._update_disable, elem)

    @property
    def signals(self):
        return self._signals

    def _update_disable(self):
        pass
