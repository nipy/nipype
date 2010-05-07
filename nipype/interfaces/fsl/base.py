"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

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

import os
from glob import glob
import warnings

from nipype.utils.filemanip import (fname_presuffix, list_to_filename,
                                    FileNotFoundError)
from nipype.interfaces.base import NEW_CommandLine, traits, TraitedSpec,\
    CommandLineInputSpec
from nipype.utils.misc import isdefined
from nipype.interfaces.base import OptMapCommand, CommandLine
from copy import deepcopy

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class FSLInfo(object):
    """Handle fsl output type and version information.
    """

    __outputtype = 'NIFTI'
    ftypes = {'NIFTI': '.nii',
              'NIFTI_PAIR': '.img',
              'NIFTI_GZ': '.nii.gz',
              'NIFTI_PAIR_GZ': '.img.gz',
              'ANALYZE_GZ': '.hdr.gz',
              'ANALYZE': '.hdr'}

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
        clout = CommandLine('which fsl').run()

        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(os.path.split(out)[0])[0]
        clout = CommandLine('cat %s/etc/fslversion' % (basedir)).run()
        out = clout.runtime.stdout
        return out.strip('\n')

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
            msg = 'Invalid FSLOUTPUTTYPE: ', outputtype
            raise KeyError(msg)

    @classmethod
    def outputtype(cls, ftype=None):
        """Check and or set the global FSL output file type FSLOUTPUTTYPE

        Parameters
        ----------
        ftype :  string
            Represents the file type to set based on string of valid FSL
            file types ftype == None to get current setting/ options

        Returns
        -------
        fsl_ftype : string
            Represents the current environment setting of FSLOUTPUTTYPE
        ext : string
            The extension associated with the FSLOUTPUTTYPE

        """
        if ftype is not None:
            try:
                # Grabbing extension only to confirm given ftype is a
                # valid key
                ext = cls.ftypes[ftype]
                cls.__outputtype = ftype
            except KeyError:
                msg = 'Invalid FSLOUTPUTTYPE: ', ftype
                raise KeyError(msg)
        return cls.__outputtype, cls.outputtype_to_ext(cls.__outputtype)

    @staticmethod
    def standard_image(img_name):
        '''Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability'''
        fsldir = os.environ['FSLDIR']
        return os.path.join(fsldir, 'data/standard', img_name)


class FSLCommand(OptMapCommand):
    '''General support for FSL commands. Every FSL command accepts 'outputtype'
    input. For example:
    fsl.ExtractRoi(tmin=42, tsize=1, outputtype='NIFTI')'''

    def __init__(self, *args, **inputs):
        super(FSLCommand, self).__init__(**inputs)

        if 'outputtype' not in inputs or inputs['outputtype'] == None:
            outputtype, _ = FSLInfo.outputtype()
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
        self._environ = {'FSLOUTPUTTYPE': self._outputtype}
        return super(FSLCommand, self).run()

    def _glob(self, fname):
        '''Check if, given a filename, FSL actually produced it.

        The maing thing we're doing here is adding an appropriate extension
        while globbing. Note that it returns a single string, not a list
        (different from glob.glob)'''
        # Could be made more faster / less clunky, but don't care until the API
        # is sorted out

        # While this function is a little globby, it may not be the best name.
        # Certainly, glob here is more expensive than necessary (could just use
        # os.path.exists)

        # stripping the filename of extensions that FSL will recognize and
        # substitute
        for ext in FSLInfo.ftypes.values():
            if fname.endswith(ext):
                fname = fname[:-len(ext)]
                break

        ext = FSLInfo.outputtype_to_ext(self._outputtype)
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

        ext = FSLInfo.outputtype_to_ext(self._outputtype)
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

###################################
#
# NEW_ FSL base class
#
###################################
class Info(object):
    """Handle fsl output type and version information.
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
        clout = NEW_CommandLine(command='which', args='fsl').run()

        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(os.path.split(out)[0])[0]
        clout = NEW_CommandLine(command='cat', args='%s/etc/fslversion' % (basedir)).run()
        out = clout.runtime.stdout
        return out.strip('\n')

    @classmethod
    def outputtype_to_ext(cls, outputtype):
        """Get the file extension for the given output type.

        Parameters
        ----------
        outputtype : {'NIFTI', 'NIFTI_GZ', 'NIFTI_PAIR', 'NIFTI_PAIR_GZ'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.
        """

        try:
            return cls.ftypes[outputtype]
        except KeyError:
            msg = 'Invalid FSLOUTPUTTYPE: ', outputtype
            raise KeyError(msg)

    @classmethod
    def outputtype(cls):
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
            raise Exception('FSL environment variables not set')

    @staticmethod
    def standard_image(img_name):
        '''Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability'''
        try:
            fsldir = os.environ['FSLDIR']
        except KeyError:
            raise Exception('FSL environment variables not set')
        return os.path.join(fsldir, 'data/standard', img_name)


class FSLTraitedSpec(CommandLineInputSpec):
    outputtype =  traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='FSL output type')
    
class NEW_FSLCommand(NEW_CommandLine):
    """General support for FSL commands. Every FSL command accepts 'outputtype'
    input. For example:
    fsl.ExtractRoi(tmin=42, tsize=1, outputtype='NIFTI')"""
    
    input_spec = FSLTraitedSpec
    _outputtype = None

    def __init__(self, **inputs):
        super(NEW_FSLCommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, 'outputtype')

        if self._outputtype is None:
            self._outputtype = Info.outputtype()

        if not isdefined(self.inputs.outputtype):
            self.inputs.outputtype = self._outputtype
        else:
            self._output_update()

    def _output_update(self):
        self._outputtype = self.inputs.outputtype
        self.inputs.environ.update({'FSLOUTPUTTYPE': self.inputs.outputtype})
    
    @classmethod
    def set_default_outputtype(cls, outputtype):
        """Set the default output type for FSL classes.

        This method is used to set the default output type for all fSL
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.outputtype.
        """

        if outputtype in Info.ftypes:
            cls._outputtype = outputtype
        else:
            raise AttributeError('Invalid FSL outputtype: %s' % outputtype)

    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extentions specified in
        <instance>intputs.outputtype.

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
