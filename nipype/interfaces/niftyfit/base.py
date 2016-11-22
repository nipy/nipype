# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The niftyfit module provide an interface with the niftyfit software
developed in TIG, UCL.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import warnings
from ..base import (CommandLine, isdefined)
from nipype.utils.filemanip import split_filename

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


def get_custom_path(command):
    """Get path of niftyfit."""
    try:
        specific_dir = os.environ['NIFTYFITDIR']
        command = os.path.join(specific_dir, command)
        return command
    except KeyError:
        return command


def no_niftyfit(cmd='fit_dwi'):
    """Check if niftyfit is installed."""
    if True in [os.path.isfile(os.path.join(path, cmd)) and
                os.access(os.path.join(path, cmd), os.X_OK)
                for path in os.environ["PATH"].split(os.pathsep)]:
        return False
    return True


class NiftyFitCommand(CommandLine):
    """
    Base support for NiftyFit commands.
    """
    _suffix = '_nf'
    # _min_version = '0.9.4'

    def __init__(self, required_version=None, **inputs):
        super(NiftyFitCommand, self).__init__(**inputs)
        """current_version = self.get_version()
        if StrictVersion(current_version) < StrictVersion(self._min_version):
            msg = 'A later version of NiftySeg is required (%s < %s)'
            raise ValueError(msg % (current_version, self._min_version))
        if required_version is not None and \
           StrictVersion(current_version) != StrictVersion(required_version):
            msg = 'The version of NiftySeg differs from the required (%s!=%s)'
            raise ValueError(msg % (current_version, required_version))"""

    def _gen_fname(self, basename, out_dir=None, suffix=None, ext=None):
        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        _, final_bn, final_ext = split_filename(basename)
        if out_dir is None:
            out_dir = os.getcwd()
        if ext is not None:
            final_ext = ext
        if suffix is not None:
            final_bn = ''.join((final_bn, suffix))
        return os.path.abspath(os.path.join(out_dir, final_bn + final_ext))

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_fname(self.inputs.in_file, suffix=self._suffix,
                                   ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
        else:
            outputs['out_file'] = self._gen_filename('out_file')
        return outputs
