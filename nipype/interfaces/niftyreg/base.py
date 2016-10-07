# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The niftyreg module provides classes for interfacing with `niftyreg
<http://sourceforge.net/projects/niftyreg/>`_ command line tools.

These are the base tools for working with niftyreg.

Registration tools are found in niftyreg/reg.py
Every other tool is found in niftyreg/regutils.py

Currently these tools are supported:

* reg_aladin: Global image registration
* reg_f3d: Non-rigid registration

Examples
--------
See the docstrings of the individual classes for examples.

"""

import warnings
import os
from distutils.version import StrictVersion
from nipype.interfaces.base import (CommandLine, isdefined)
from nipype.utils.filemanip import split_filename
import subprocess

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


def get_custom_path(command):
    try:
        specific_dir = os.environ['NIFTYREGDIR']
        command = os.path.join(specific_dir, command)
        return command
    except KeyError:
        return command


def no_niftyreg(cmd='reg_f3d'):
    if True in [os.path.isfile(os.path.join(path, cmd)) and
                os.access(os.path.join(path, cmd), os.X_OK)
                for path in os.environ["PATH"].split(os.pathsep)]:
        return False
    return True


class NiftyRegCommand(CommandLine):
    """
    Base support for NiftyReg commands
    """
    _min_version = '1.5.0'
    _suffix = '_nr'

    def __init__(self, **inputs):
        super(NiftyRegCommand, self).__init__(**inputs)
        current_version = self.get_version()
        if StrictVersion(current_version) < StrictVersion(self._min_version):
            raise ValueError('A later version of Niftyreg is required (%s < %s)' %
                             (current_version, self._min_version))

    def get_version(self):
        if no_niftyreg(cmd=self.cmd):
            return None
        exec_cmd = ''.join((self.cmd, ' -v'))
        return subprocess.check_output(exec_cmd, shell=True).strip('\n')

    @property
    def version(self):
        return self.get_version()

    def exists(self):
        if self.get_version() is None:
            return False
        return True

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
            return self._gen_fname(self.inputs.in_file, suffix=self._suffix, ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
        else:
            outputs['out_file'] = self._gen_filename('out_file')
        return outputs
