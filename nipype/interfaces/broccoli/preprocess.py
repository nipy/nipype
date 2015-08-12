# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The BROCCOLI module provides classes for interfacing with the `BROCCOLI
<http://github.com/wanderine/BROCCOLI>`_ command line tools.  

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os
import os.path as op
import warnings

import numpy as np

from nipype.interfaces.fsl.base import BROCCOLICommand, BROCCOLICommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    isdefined, OutputMultiPath)
from nipype.utils.filemanip import split_filename

from nibabel import load


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)



class RegisterTwoVolumesInputSpec(BROCCOLICommandInputSpec):
    in_file = File(desc='input volume to align',
                   argstr='%s',
                   position=0,
                   mandatory=True,
                   exists=True,
                   copyfile=False)

    reference = File(desc='reference volume to align to',
                   argstr='%s',
                   position=1,
                   mandatory=True,
                   exists=True,
                   copyfile=False)


    platform = traits.Int(argstr='-platform %d', desc='OpenCL platform to use')

    device = traits.Int(argstr='-device %d', desc='OpenCL device to use')

    iterationslinear = traits.Int(argstr='-iterationslinear %d', desc='Number of iterations for linear registration')

    iterationsnonlinear = traits.Int(argstr='-iterationsnonlinear %d', desc='Number of iterations for non-linear registration')

class RegisterTwoVolumes(BROCCOLICommand):
    """This program performs linear and non-linear registration of two volumes

    Examples
    ========

    >>> from nipype.interfaces import broccoli
    >>> from nipype.testing import example_data
    >>> reg = broccoli.RegisterTwoVolumes()
    >>> reg.inputs.in_file = 'structural.nii'
    >>> reg.inputs.reference = 'mni.nii'
    >>> reg.platform = 1
    >>> reg.device = 2
    >>> reg.cmdline
    'RegisterTwoVolumes structural.nii mni.nii -platform 1 -device 2'
    >>> res = reg.run() # doctest: +SKIP

    """

    _cmd = 'RegisterTwoVolumes'
    input_spec = RegisterTwoVolumesInputSpec
    output_spec = BROCCOLICommandOutputSpec




