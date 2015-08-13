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

    ftypes = {'NIFTI': '.nii',
              'NIFTI_GZ': '.nii.gz'}

    @classmethod
    def output_type_to_ext(cls, output_type):
        """Get the file extension for the given output type.

        Parameters
        ----------
        output_type : {'NIFTI', 'NIFTI_GZ'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.
        """

        try:
            return cls.ftypes[output_type]
        except KeyError:
            msg = 'Invalid BROCCOLIOUTPUTTYPE: ', output_type
            raise KeyError(msg)

    @classmethod
    def output_type(cls):
        """Get the global BROCCOLI output file type BROCCOLIOUTPUTTYPE.

        This returns the value of the environment variable
        BROCCOLIOUTPUTTYPE.  An exception is raised if it is not defined.

        Returns
        -------
        broccoli_ftype : string
            Represents the current environment setting of BROCCOLIOUTPUTTYPE
        """
        try:
            return os.environ['BROCCOLIOUTPUTTYPE']
        except KeyError:
            warnings.warn(('BROCCOLI environment variables not set. setting output type to NIFTI'))
            return 'NIFTI'



class BROCCOLICommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all BROCCOLI Commands

    All command support specifying BROCCOLIOUTPUTTYPE dynamically
    via output_type.

    Example
    -------
    broccoli.MotionCorrection(tmin=42, tsize=1, output_type='NIFTI')
    """
    output_type = traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='BROCCOLI output type')


class BROCCOLICommandOutputSpec(TraitedSpec):
    out_file = File(desc='output file',
                    exists=True)

class BROCCOLICommand(CommandLine):
    """Base support for BROCCOLI commands.

    """

    input_spec = BROCCOLICommandInputSpec
    _output_type = None

    def __init__(self, **inputs):
        super(BROCCOLICommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, 'output_type')

        if self._output_type is None:
            self._output_type = Info.output_type()

        if not isdefined(self.inputs.output_type):
            self.inputs.output_type = self._output_type
        else:
            self._output_update()

    def _output_update(self):
        self._output_type = self.inputs.output_type
        self.inputs.environ.update({'BROCCOLIOUTPUTTYPE': self.inputs.output_type})

    @classmethod
    def set_default_output_type(cls, output_type):
        """Set the default output type for BROCCOLI classes.

        This method is used to set the default output type for all BROCCOLI
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.output_type.
        """

        if output_type in Info.ftypes:
            cls._output_type = output_type
        else:
            raise AttributeError('Invalid BROCCOLI output_type: %s' % output_type)



