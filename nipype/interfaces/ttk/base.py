# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ttk module provides classes for interfacing with the Tensor ToolKit 
<https://gforge.inria.fr/projects/ttk/> _ command line tools.

These are the base tools for working with TTK.

Examples
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from ...utils.filemanip import fname_presuffix
from ..base import (CommandLine, traits, CommandLineInputSpec, isdefined)

from nipype.interfaces.fsl.base import FSLCommand as TTKCommand

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class Info(object):
    """Handle ttk output type and version information.

    version refers to the version of ttk on the system

    output type refers to the type of file ttk defaults to writing
    eg, NIFTI, NIFTI_GZ

    """

    ftypes = {'NIFTI': '.nii',
              'NIFTI_PAIR': '.img',
              'NIFTI_GZ': '.nii.gz',
              'NIFTI_PAIR_GZ': '.img.gz'}

    @staticmethod
    def version():
        """Check for ttk version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if TTK not found

        """
        # find which ttk being used....and get version from
        # /path/to/ttk/etc/ttkversion
        try:
            basedir = os.environ['TTKDIR']
        except KeyError:
            return None
#        clout = CommandLine(command='cat',
#                            args='%s/etc/ttkversion' % (basedir),
#                            terminal_output='allatonce').run()
#        out = clout.runtime.stdout
        return '1.4.0'

    @classmethod
    def output_type_to_ext(cls, output_type):
        """Get the file extension for the given output type.

        Parameters
        ----------
        output_type : {'NIFTI', 'NIFTI_GZ', 'NIFTI_PAIR', 'NIFTI_PAIR_GZ'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.
        """

        try:
            return cls.ftypes[output_type]
        except KeyError:
            msg = 'Invalid TTKOUTPUTTYPE: ', output_type
            raise KeyError(msg)

    @classmethod
    def output_type(cls):
        """Get the global TTK output file type TTKOUTPUTTYPE.

        This returns the value of the environment variable
        TTKOUTPUTTYPE.  An exception is raised if it is not defined.

        Returns
        -------
        ttk_ftype : string
            Represents the current environment setting of TTKOUTPUTTYPE
        """
        try:
            return os.environ['TTKOUTPUTTYPE']
        except KeyError:
            warnings.warn(('TTK environment variables not set. setting output type to NIFTI'))
            return 'NIFTI'

    @staticmethod
    def standard_image(img_name=None):
        '''Grab an image from the standard location.

        Returns a list of standard images if called without arguments.

        Could be made more fancy to allow for more relocatability'''
        try:
            ttkdir = os.environ['TTKDIR']
        except KeyError:
            raise Exception('TTK environment variables not set')
        stdpath = os.path.join(ttkdir, 'data', 'standard')
        if img_name is None:
            return [filename.replace(stdpath + '/', '')
                    for filename in glob(os.path.join(stdpath, '*nii*'))]
        return os.path.join(stdpath, img_name)


class TTKCommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all TTK Commands

    All command support specifying TTKOUTPUTTYPE dynamically
    via output_type.

    Example
    -------
    ttk.ExtractRoi(tmin=42, tsize=1, output_type='NIFTI')
    """
    output_type = traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='TTK output type')


def no_ttk():
    """Checks if TTK is NOT installed
    used with skipif to skip tests that will
    fail if TTK is not installed"""

    if Info.version() is None:
        return True
    else:
        return False
