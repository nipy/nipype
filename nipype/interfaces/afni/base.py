# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""


import os
import warnings

from ...utils.filemanip import fname_presuffix
from ..base import (CommandLine, traits, CommandLineInputSpec, isdefined)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

###################################
#
# NEW_AFNI base class
#
###################################

class Info(object):
    """Handle afni output type and version information.
    """
    __outputtype = 'NIFTI_GZ'
    ftypes = {'NIFTI': '.nii',
              'AFNI': '.BRIK',
              'NIFTI_GZ': '.nii.gz'}

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
        Nipype uses NIFTI_GZ as default


        Returns
        -------
        None
        """
        #warn(('AFNI has no environment variable that sets filetype '
        #      'Nipype uses NIFTI_GZ as default'))
        return 'NIFTI_GZ'


    @staticmethod
    def standard_image(img_name):
        '''Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability'''
        clout = CommandLine('which afni').run()
        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)


class AFNITraitedSpec(CommandLineInputSpec):
    outputtype =  traits.Enum('NIFTI_GZ', Info.ftypes.keys(),
                              desc = 'AFNI output filetype')


class AFNICommand(CommandLine):
    """General support for AFNI commands. Every AFNI command accepts 'outputtype' input. For example:
    afni.Threedsetup(outputtype='NIFTI_GZ')
    """

    input_spec = AFNITraitedSpec
    _outputtype = None

    def __init__(self, **inputs):
        super(AFNICommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, 'outputtype')

        if self._outputtype is None:
            self._outputtype = Info.outputtype()

        if not isdefined(self.inputs.outputtype):
            self.inputs.outputtype = self._outputtype
        else:
            self._output_update()

    def _output_update(self):
        """ i think? updates class private attribute based on instance input
         in fsl also updates ENVIRON variable....not valid in afni
         as it uses no environment variables
        """
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

    def _gen_fname(self, basename, cwd=None, suffix='_afni', change_ext=True):
        """Generate a filename based on the given parameters.

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
            Suffix to add to the `basename`.  (default is '_fsl')
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
        ext = Info.outputtype_to_ext(self.inputs.outputtype)
        if change_ext:
            if suffix:
                suffix = ''.join((suffix, ext))
            else:
                suffix = ext
        fname = fname_presuffix(basename, suffix = suffix,
                                use_ext = False, newpath = cwd)
        return fname



