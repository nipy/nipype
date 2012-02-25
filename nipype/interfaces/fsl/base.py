# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

These are the base tools for working with FSL.
Preprocessing tools are found in fsl/preprocess.py
Model tools are found in fsl/model.py
DTI tools are found in fsl/dti.py

XXX Make this doc current!

Currently these tools are supported:

* BET v2.1: brain extraction
* FAST v4.1: segmentation and bias correction
* FLIRT v5.5: linear registration
* MCFLIRT: motion correction
* FNIRT v1.0: non-linear warp

Examples
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import (CommandLine, traits, CommandLineInputSpec,
                                    isdefined)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Info(object):
    """Handle fsl output type and version information.

    version refers to the version of fsl on the system

    output type refers to the type of file fsl defaults to writing
    eg, NIFTI, NIFTI_GZ

    """

    ftypes = {'NIFTI': '.nii',
              'NIFTI_PAIR': '.img',
              'NIFTI_GZ': '.nii.gz',
              'NIFTI_PAIR_GZ': '.img.gz'}

    @staticmethod
    def version():
        """Check for fsl version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if FSL not found

        """
        # find which fsl being used....and get version from
        # /path/to/fsl/etc/fslversion
        try:
            basedir = os.environ['FSLDIR']
        except KeyError:
            return None
        clout = CommandLine(command='cat',
                            args='%s/etc/fslversion' % (basedir)).run()
        out = clout.runtime.stdout
        return out.strip('\n')

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
            msg = 'Invalid FSLOUTPUTTYPE: ', output_type
            raise KeyError(msg)

    @classmethod
    def output_type(cls):
        """Get the global FSL output file type FSLOUTPUTTYPE.

        This returns the value of the environment variable
        FSLOUTPUTTYPE.  An exception is raised if it is not defined.

        Returns
        -------
        fsl_ftype : string
            Represents the current environment setting of FSLOUTPUTTYPE
        """
        try:
            return os.environ['FSLOUTPUTTYPE']
        except KeyError:
            warnings.warn('FSL environment variables not set. setting output type to NIFTI')
            return 'NIFTI'

    @staticmethod
    def standard_image(img_name=None):
        '''Grab an image from the standard location.

        Returns a list of standard images if called without arguments.

        Could be made more fancy to allow for more relocatability'''
        try:
            fsldir = os.environ['FSLDIR']
        except KeyError:
            raise Exception('FSL environment variables not set')
        stdpath = os.path.join(fsldir, 'data', 'standard')
        if img_name is None:
            return [filename.replace(stdpath + '/', '')
                    for filename in glob(os.path.join(stdpath, '*nii*'))]
        return os.path.join(stdpath, img_name)


class FSLCommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all FSL Commands

    All command support specifying FSLOUTPUTTYPE dynamically
    via output_type.

    Example
    -------
    fsl.ExtractRoi(tmin=42, tsize=1, output_type='NIFTI')
    """
    output_type = traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='FSL output type')


class FSLCommand(CommandLine):
    """Base support for FSL commands.

    """

    input_spec = FSLCommandInputSpec
    _output_type = None

    def __init__(self, **inputs):
        super(FSLCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, 'output_type')

        if self._output_type is None:
            self._output_type = Info.output_type()

        if not isdefined(self.inputs.output_type):
            self.inputs.output_type = self._output_type
        else:
            self._output_update()

    def _output_update(self):
        self._output_type = self.inputs.output_type
        self.inputs.environ.update({'FSLOUTPUTTYPE': self.inputs.output_type})

    @classmethod
    def set_default_output_type(cls, output_type):
        """Set the default output type for FSL classes.

        This method is used to set the default output type for all fSL
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.output_type.
        """

        if output_type in Info.ftypes:
            cls._output_type = output_type
        else:
            raise AttributeError('Invalid FSL output_type: %s' % output_type)

    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True,
                   ext=None):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extentions specified in
        <instance>intputs.output_type.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )
        change_ext : bool
            Flag to change the filename extension to the FSL output type.
            (default True)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """

        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        if ext is None:
            ext = Info.output_type_to_ext(self.inputs.output_type)
        if change_ext:
            if suffix:
                suffix = ''.join((suffix, ext))
            else:
                suffix = ext
        if suffix is None:
            suffix = ''
        fname = fname_presuffix(basename, suffix=suffix,
                                use_ext=False, newpath=cwd)
        return fname


def check_fsl():
    ver = Info.version()
    if ver:
        return 0
    else:
        return 1


def no_fsl():
    """Checks if FSL is NOT installed
    used with skipif to skip tests that will
    fail if FSL is not installed"""

    if Info.version() == None:
        return True
    else:
        return False


def no_fsl_course_data():
    """check if fsl_course data is present"""

    return not (os.path.isdir(os.path.abspath('fsl_course_data')))
