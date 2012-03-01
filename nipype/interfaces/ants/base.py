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


