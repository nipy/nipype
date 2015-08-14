# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The BROCCOLI module provides classes for interfacing with the `BROCCOLI
<http://github.com/wanderine/BROCCOLI>`_ command line tools."""

import os
from glob import glob
import warnings
import tempfile

import numpy as np

from .base import BROCCOLICommand
from ..base import (traits, TraitedSpec, OutputMultiPath, File,
                    CommandLine, CommandLineInputSpec, isdefined)
from ...utils.filemanip import (load_json, save_json, split_filename,
                                fname_presuffix)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)



class GetOpenCLInfo(BROCCOLICommand):
    '''Print info about OpenCL platforms and devices
    '''

    input_spec = CommandLineInputSpec
    output_spec = None
    _cmd = 'GetOpenCLInfo'

class BandwidthCommandInputSpec(CommandLineInputSpec):
    """
    OpenCL platform and device only
    """

    platform = traits.Int(argstr='-platform %d', desc='OpenCL platform to use',mandatory=True)

    device = traits.Int(argstr='-device %d', desc='OpenCL device to use',mandatory=True)

class GetBandwidth(BROCCOLICommand):
    '''Print info about OpenCL platforms and devices
    '''

    input_spec = BandwidthCommandInputSpec
    output_spec = None
    _cmd = 'GetBandwidth'




