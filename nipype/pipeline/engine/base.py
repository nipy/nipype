#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `EngineBase` class implements the more general view of a task.

  .. testsetup::
     # Change directory to provide relative paths for doctests
     import os
     filepath = os.path.dirname(os.path.realpath( __file__ ))
     datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
     os.chdir(datadir)

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import object

from copy import deepcopy
import re
import numpy as np

from ... import config
from ...interfaces.base import DynamicTraitedSpec
from ...utils.filemanip import loadpkl, savepkl


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
        self._hierarchy = None
        self._name = None

        self.base_dir = base_dir
        self.config = deepcopy(config._sections)
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if not name or not re.match(r'^[\w-]+$', name):
            raise ValueError('[Workflow|Node] name "%s" is not valid.' % name)
        self._name = name

    @property
    def fullname(self):
        if self._hierarchy:
            return '%s.%s' % (self._hierarchy, self.name)
        return self.name

    @property
    def inputs(self):
        raise NotImplementedError

    @property
    def outputs(self):
        raise NotImplementedError

    def clone(self, name):
        """Clone an EngineBase object

        Parameters
        ----------

        name : string (mandatory)
            A clone of node or workflow must have a new name
        """
        if name == self.name:
            raise ValueError('Cloning requires a new name, "%s" is in use.' % name)
        clone = deepcopy(self)
        clone.name = name
        return clone

    def _check_outputs(self, parameter):
        return hasattr(self.outputs, parameter)

    def _check_inputs(self, parameter):
        if isinstance(self.inputs, DynamicTraitedSpec):
            return True
        return hasattr(self.inputs, parameter)

    def __str__(self):
        return self.fullname

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
