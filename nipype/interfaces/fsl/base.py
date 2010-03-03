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

from nipype.utils.filemanip import fname_presuffix, list_to_filename
from nipype.interfaces.base import OptMapCommand, CommandLine

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


def fslversion():
    msg = """fsl.fslversion is no longer available. instead replace with:

             fsl.FSLInfo.version()

             This message will be removed in the next release
          """
    raise Exception(msg)


def fsloutputtype(ftype=None):
    msg = """fsl.fsloutputtype is no longer available. instead replace with:

             fsl.FSLInfo.outputtype(...)

             This message will be removed in the next release
          """
    raise Exception(msg)


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
        '''Define a generic mapping for a single outfile

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
        '''
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
                raise IOError('file %s not generated by %s' % (fname, cmd))
           
        # XXX This should ultimately somehow allow for relative paths if cwd is
        # specified or similar. For now, though, this needs to happen to make
        # the pipeline code work
        # return os.path.realpath(fname)
        return fname
