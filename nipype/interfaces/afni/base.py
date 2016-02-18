# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""

import os
from builtins import object

from ... import logging
from ...utils.filemanip import split_filename
from ..base import traits, File, CommandLine, CommandLineInputSpec, TraitedSpec

# Use nipype's logging system
IFLOGGER = logging.getLogger('interface')

AFNI_FTYPES = {'NIFTI': '.nii', 'AFNI': '', 'NIFTI_GZ': '.nii.gz'}

class Info(object):
    """Handle afni output type and version information. """

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
        try:
            clout = CommandLine(command='afni_vcheck',
                                terminal_output='allatonce').run()

            # Try to parse the version number
            currv = clout.runtime.stdout.split('\n')[1].split('=', 1)[1].strip()
        except IOError:
            # If afni_vcheck is not present, return None
            IFLOGGER.warn('afni_vcheck executable not found.')
            return None
        except RuntimeError as err:
            # If AFNI is outdated, afni_vcheck throws error.
            # Show new version, but parse current anyways.
            currv = str(err).split('\n')[4].split('=', 1)[1].strip()
            nextv = str(err).split('\n')[6].split('=', 1)[1].strip()
            IFLOGGER.warn(
                'AFNI is outdated, detected version %s and %s is available.', currv, nextv)

        if currv.startswith('AFNI_'):
            currv = currv[5:]

        version = currv.split('.')
        try:
            version = [int(n) for n in version]
        except ValueError:
            return currv
        return tuple(version)

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
        return AFNI_FTYPES.get(outputtype, 'AFNI')


    @staticmethod
    def standard_image(img_name):
        """Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability"""
        clout = CommandLine('which afni', terminal_output='allatonce').run()
        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)


class AFNICommandBase(CommandLine):
    """
    A base class to fix a linking problem in OSX and afni.
    See http://afni.nimh.nih.gov/afni/community/board/read.php?1,145346,145347#msg-145347
    """
    def _run_interface(self, runtime):
        if runtime.platform == 'darwin':
            runtime.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/usr/local/afni/'
        return super(AFNICommandBase, self)._run_interface(runtime)


class AFNICommandInputSpec(CommandLineInputSpec):
    outputtype = traits.Enum(tuple(AFNI_FTYPES.keys()), desc='AFNI output filetype')
    out_file = File(name_template="%s_afni", desc='output image file name', keep_extension=False,
                    name_source=["in_file"], argstr='-prefix %s')

    def _overload_extension(self, value, name=None, ext=None):
        # Do not overload certain extensions
        if value.endswith('+orig.BRIK') or value.endswith('.1D'):
            return value
        return value + AFNI_FTYPES.get(self.outputtype, '')


class AFNICommandOutputSpec(TraitedSpec):
    out_file = File(desc='output file', exists=True)


class AFNICommand(AFNICommandBase):
    """Shared options for several AFNI commands """
    input_spec = AFNICommandInputSpec

def no_afni():
    """ Checks if AFNI is available """
    if Info.version() is None:
        return True
    return False
