# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The BROCCOLI module provides classes for interfacing with the `BROCCOLI
<http://github.com/wanderine/BROCCOLI>`_ command line tools."""

import os
from glob import glob
import warnings
import tempfile

import numpy as np

from .base import BROCCOLICommand, BROCCOLICommandInputSpec, BROCCOLICommandOutputSpec, Info
from ..base import (traits, TraitedSpec, OutputMultiPath, File,
                    CommandLine, CommandLineInputSpec, isdefined)
from ...utils.filemanip import (load_json, save_json, split_filename,
                                fname_presuffix)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)



class GetOpenCLInfoInputSpec(BROCCOLICommandInputSpec):

    platform = traits.Int(argstr='-platform %d', desc='OpenCL platform to use')

class GetOpenCLInfo(BROCCOLICommand):
    '''Print info about OpenCL platforms and devices
    '''

    input_spec = GetOpenCLInfoInputSpec
    output_spec = BROCCOLICommandOutputSpec
    _cmd = 'GetOpenCLInfo'




