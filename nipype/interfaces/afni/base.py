# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""

"""old
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import Bunch, CommandLine
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string

import warnings
warn = warnings.warn
"""

import os
from glob import glob
import warnings

from nipype.utils.filemanip import fname_presuffix, list_to_filename, FileNotFoundError
from nipype.interfaces.base import CommandLine, traits, TraitedSpec, CommandLineInputSpec
from nipype.utils.misc import isdefined

from copy import deepcopy

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

''' Old AFNIInfo
class AFNIInfo(object):
    """Handle afni output type and version information.
    """

    __outputtype = 'NIFTI_GZ'
    ftypes = {'NIFTI': '.nii',
              'NIFTI_PAIR': '.img',
              'NIFTI_GZ': '.nii.gz',
              'NIFTI_PAIR_GZ': '.img.gz',
              'ANALYZE_GZ': '.hdr.gz',
              'ANALYZE': '.hdr'}

    @staticmethod
    def version():
        """Check for afni version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Output of afni_vcheck as string or None if AFNI not found

        """
        # find which afni is being used....and get version from
        # /path/to/afni/afni_vcheck
        clout = CommandLine('which afni').run()
        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]

        clout = CommandLine('%s/afni_vcheck' % (basedir)).run()
        out = clout.runtime.stdout
        return out.split('\n')

    @classmethod
    def outputtype_to_ext(cls, outputtype):
        """Get the file extension for the given output type.

        Parameters
        ----------
        outputtype : {'ANALYZE_GZ', 'NIFTI_PAIR_GZ', 'NIFTI',
                      'NIFTI_PAIR', 'NIFTI_GZ', 'ANALYZE'}
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
    def outputtype(cls, ftype=None):
        """Check and or set the global AFNI output file type AFNIOUTPUTTYPE

        Parameters
        ----------
        ftype :  string
            Represents the file type to set based on string of valid AFNI
            file types ftype == None to get current setting/ options

        Returns
        -------
        afni_ftype : string
            Represents the current environment setting of AFNIOUTPUTTYPE
        ext : string
            The extension associated with the AFNIOUTPUTTYPE

        """
        if ftype is not None:
            try:
                # Grabbing extension only to confirm given ftype is a
                # valid key
                ext = cls.ftypes[ftype]
                cls.__outputtype = ftype
            except KeyError:
                msg = 'Invalid AFNIOUTPUTTYPE: ', ftype
                raise KeyError(msg)
        return cls.__outputtype, cls.outputtype_to_ext(cls.__outputtype)

    @staticmethod
    def standard_image(img_name):
	"""Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability

	DTE: this seems to only be creating a string pointing to a file,
	but not verifying its existence nor doing anything with it.
        what is the intention of this def?"""

        clout = CommandLine('which afni').run()
        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)
'''

''' Old AFNICommand
class AFNICommand(OptMapCommand):
    """General support for AFNI commands. Every AFNI command accepts 'outputtype'
    input. For example:
    afni.Threedbucket(outputtype='NIFTI_GZ')
    """

    def __init__(self, *args, **inputs):
        super(AFNICommand, self).__init__(**inputs)

        if 'outputtype' not in inputs or inputs['outputtype'] == None:
            outputtype, _ = AFNIInfo.outputtype()
        else:
            outputtype = inputs['outputtype']
        self._outputtype = outputtype

    def run(self):
        """Execute the command.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """
        self._environ = {'AFNIOUTPUTTYPE': self._outputtype}
        return super(AFNICommand, self).run()

    def _glob(self, fname):
        """Check if, given a filename, FSL actually produced it.

        The maing thing we're doing here is adding an appropriate extension
        while globbing. Note that it returns a single string, not a list
        (different from glob.glob)"""
        # Could be made more faster / less clunky, but don't care until the API
        # is sorted out

        # While this function is a little globby, it may not be the best name.
        # Certainly, glob here is more expensive than necessary (could just use
        # os.path.exists)

        # stripping the filename of extensions that FSL will recognize and
        # substitute
        for ext in AFNIInfo.ftypes.values():
            if fname.endswith(ext):
                fname = fname[:-len(ext)]
                break

        ext = AFNIInfo.outputtype_to_ext(self._outputtype)
        files = glob(fname) or glob(fname + ext)

        try:
            return files[0]
        except IndexError:
            return None

    def _gen_fname(self, basename, fname=None, cwd=None, suffix='_fsl',
                  check=False, cmd='unknown'):
        """Define a generic mapping for a single outfile

        The filename is potentially autogenerated by suffixing inputs.infile

        Parameters
        ----------
        basename : string (required)
            filename to base the new filename on
        fname : string
            if not None, just use this fname
        cwd : string
            prefix paths with cwd, otherwise os.getcwd()
        suffix : string
            default suffix
        check : bool
            check if file exists, adding appropriate extension, raise exception
            if it doesn't
        """
        if cwd is None:
            cwd = os.getcwd()

        ext = AFNIInfo.outputtype_to_ext(self._outputtype)
        if fname is None:
            suffix = ''.join((suffix, ext))
            fname = fname_presuffix(list_to_filename(basename), suffix=suffix,
                                    use_ext=False, newpath=cwd)
        if check:
            new_fname = self._glob(fname)
            if new_fname is None:
                raise FileNotFoundError('file %s not generated by %s' % (fname, cmd))

        # XXX This should ultimately somehow allow for relative paths if cwd is
        # specified or similar. For now, though, this needs to happen to make
        # the pipeline code work
        # return os.path.realpath(fname)
        return fname
'''


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
        print 'AFNI has no environment variable that sets filetype'
        print 'Nipype uses NIFTI_GZ as default'
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



''' Older AFNICommand
class AFNICommand(CommandLine):
    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        allargs = self._parseinputs()
        allargs.insert(0, self.cmd)
        return ' '.join(allargs)

    def _parseinputs(self, skip=()):
        """Parse all inputs and format options using the opt_map format string.

        Any inputs that are assigned (that are not None) are formatted
        to be added to the command line.

        Parameters
        ----------
        skip : tuple or list
            Inputs to skip in the parsing.  This is for inputs that
            require special handling, for example input files that
            often must be at the end of the command line.  Inputs that
            require special handling like this should be handled in a
            _parse_inputs method in the subclass.

        Returns
        -------
        allargs : list
            A list of all inputs formatted for the command line.

        """
        allargs = []
        inputs = [(k, v) for k, v in self.inputs.items() if v is not None ]
        for opt, value in inputs:
            if opt in skip:
                continue
            if opt == 'args':
                # XXX Where is this used?  Is self.inputs.args still
                # used?  Or is it leftover from the original design of
                # base.CommandLine?
                allargs.extend(value)
                continue
            try:
                argstr = self.opt_map[opt]
                if argstr.find('%') == -1:
                    # Boolean options have no format string.  Just
                    # append options if True.
                    if value is True:
                        allargs.append(argstr)
                    elif value is not False:
                        raise TypeError('Boolean option %s set to %s' %
                                         (opt, str(value)) )
                elif type(value) == list:
                    allargs.append(argstr % tuple(value))
                else:
                    # Append options using format string.
                    allargs.append(argstr % value)
            except TypeError, err:
                msg = 'Error when parsing option %s in class %s.\n%s' % \
                    (opt, self.__class__.__name__, err.message)
                warn(msg)
            except KeyError:
                msg = '%s: unsupported option: %s' % (
                    self.__class__.__name__, opt)
                raise AttributeError(msg)

        return allargs
'''

