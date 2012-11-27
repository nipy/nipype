# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""


import os
import warnings

from ...utils.filemanip import fname_presuffix
from ..base import (CommandLine, traits, CommandLineInputSpec, isdefined)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Info(object):
    """Handle afni output type and version information.
    """
    __outputtype = 'AFNI'
    ftypes = {'NIFTI':'.nii',
              'AFNI':'+orig.BRIK',
              'NIFTI_GZ':'.nii.gz',
              'AFNI_1D':'.1D'}

    @staticmethod
    def version():
        """Check for afni version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if AFNI not found

        """
        clout = CommandLine(command='afni_vcheck').run()
        out = clout.runtime.stdout
        return out.split('\n')[1]

    @classmethod
    def outputtype_to_ext(cls, outputtype):
        """Get the file extension for the given output type.

        Parameters
        ----------
        outputtype : {'NIFTI', 'NIFTI_GZ', 'AFNI'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.
        """

        try:
            return cls.ftypes[outputtype]
        except KeyError:
            msg = 'Invalid AFNIOUTPUTTYPE: ', outputtype
            raise KeyError(msg)

    @classmethod
    def outputtype(cls):
        """AFNI has no environment variables,
        Output filetypes get set in command line calls
        Nipype uses AFNI as default

        Returns
        -------
        None
        """
        #warn(('AFNI has no environment variable that sets filetype '
        #      'Nipype uses NIFTI_GZ as default'))
        return 'AFNI'

    @staticmethod
    def standard_image(img_name):
        """Grab an image from the standard location.  Could be made more fancy
        to allow for more relocatability
        """
        clout = CommandLine('which afni').run()
        if clout.runtime.returncode is not 0:
            return None
        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)


class AFNICommandInputSpec(CommandLineInputSpec):
    """
    Base input specification for AFNI
    """
    outputtype =  traits.Enum('AFNI', Info.ftypes.keys(), desc='AFNI output filetype')
    # prefix = traits.File(argstr='%s', mandatory=False, genfile=True, hash_file=False,
    #                      desc='Output file prefix')
    # suffix = traits.Str(argstr='%s', mandatory=False, desc='Output file suffix')


class AFNICommand(CommandLine):
    """
    General support for AFNI commands. Every AFNI command accepts 'outputtype' input.

    Example
    =======

    >>> afni.To3D(outputtype='NIFTI_GZ')

    """
    input_spec = AFNICommandInputSpec
    _outputtype = None
    _prefix = None
    _suffix = None

    def __init__(self, **inputs):
        super(AFNICommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._outputtype_update, 'outputtype')
        if self._outputtype is None:
            self._outputtype = Info.outputtype()
        if not isdefined(self.inputs.outputtype):
            self.inputs.outputtype = self._outputtype
        else:
            self._output_update()

    def _outputtype_update(self):
        self._outputtype = self.inputs.outputtype

    @classmethod
    def set_default_outputtype(cls, outputtype):
        """Set the default output type for AFNI classes.

        This method is used to set the default output type for all afni
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.outputtype.
        """

        if outputtype in Info.ftypes:
            cls._outputtype = outputtype
        else:
            raise AttributeError('Invalid AFNI outputtype: %s' % outputtype)

    @classmethod
    def set_default_prefix(cls, prefix):
        cls._prefix = prefix

    @classmethod
    def set_default_suffix(cls, suffix):
        cls._suffix = suffix

    def _gen_fname(self, basename, cwd=None, suffix='_afni', prefix='', change_ext=True):
        """
        Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extensions specified in
        <instance>inputs.outputtype.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (default is '_afni')
        change_ext : bool
            Flag to change the filename extension to the AFNI output type.
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
        ext = Info.outputtype_to_ext(self.inputs.outputtype)
        if change_ext:
            if not suffix is None:
                suffix = ''.join((suffix, ext))
            else:
                suffix = ext
        else:
            suffix = ext
            # raise IOError("change_ext flag MUST be true; False not yet implemented!")
        fname = fname_presuffix(basename, suffix = suffix, prefix=prefix,
                                use_ext = False, newpath = cwd)
        return fname



