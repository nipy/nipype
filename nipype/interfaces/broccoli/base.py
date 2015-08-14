# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The BROCCOLI module provides classes for interfacing with the `BROCCOLI
<http://github.com/wanderine/BROCCOLI>`_ command line tools.  

These are the base tools for working with BROCCOLI.
Preprocessing tools are found in broccoli/preprocess.py

Currently these tools are supported:

* MotionCorrection
* Smoothing
* RegisterTwoVolumes

Examples
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from ...utils.filemanip import fname_presuffix, split_filename, copyfile
from ..base import (traits, isdefined,
                    CommandLine, CommandLineInputSpec, TraitedSpec,
                    File, Directory, InputMultiPath, OutputMultiPath)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Info(object):
    """Handle broccoli output type and version information.

    version refers to the version of broccoli on the system

    output type refers to the type of file broccoli defaults to writing
    eg, NIFTI, NIFTI_GZ

    """

    __outputtype = 'NIFTI_GZ'

    ftypes = {'NIFTI': '.nii',
              'NIFTI_GZ': '.nii.gz'}

    @classmethod
    def output_type_to_ext(cls, output_type):
        """Get the file extension for the given output type.

    #    Parameters
    #    ----------
    #    output_type : {'NIFTI', 'NIFTI_GZ'}
    #        String specifying the output type.

    #    Returns
    #    -------
    #    extension : str
    #        The file extension for the output type.
    #    """

        try:
            return cls.ftypes[output_type]
        except KeyError:
            msg = 'Invalid BROCCOLIOUTPUTTYPE: ', output_type
            raise KeyError(msg)





class BROCCOLICommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all BROCCOLI Commands

    All commands support specifying OpenCL platform and device,
    as well as verbose and quiet
    """
    output_type = traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='BROCCOLI output type')

    output = traits.Str(argstr='-output %s', desc='Set output filename')

    platform = traits.Int(argstr='-platform %d', desc='OpenCL platform to use')

    device = traits.Int(argstr='-device %d', desc='OpenCL device to use')

    quiet = traits.Bool(argstr='-quiet', desc='Dont print anything')

    verbose = traits.Bool(argstr='-verbose', desc='Print extra stuff')


class BROCCOLICommandOutputSpec(TraitedSpec):
    out_file = File(desc='output file', exists=True)

class BROCCOLICommand(CommandLine):
    """Base support for BROCCOLI commands."""

    input_spec = BROCCOLICommandInputSpec
    _output_type = None

    def __init__(self, **inputs):
        super(BROCCOLICommand, self).__init__(**inputs)


