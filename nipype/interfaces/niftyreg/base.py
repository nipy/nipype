# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The niftyreg module provides classes for interfacing with `niftyreg
<http://sourceforge.net/projects/niftyreg/>`_ command line tools.

These are the base tools for working with niftyreg.

Registration tools are found in niftyreg/reg.py
Every other tool is found in niftyreg/regutils.py

Examples
--------
See the docstrings of the individual classes for examples.

"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import property, super
from distutils.version import StrictVersion
import os
import shutil
import subprocess
from warnings import warn

from ..base import CommandLine, CommandLineInputSpec, traits, Undefined
from ...utils.filemanip import split_filename


def get_custom_path(command, env_dir='NIFTYREGDIR'):
    return os.path.join(os.getenv(env_dir, ''), command)


def no_nifty_package(cmd='reg_f3d'):
    try:
        return shutil.which(cmd) is None
    except AttributeError:  # Python < 3.3
        return not any(
            [os.path.isfile(os.path.join(path, cmd)) and
             os.access(os.path.join(path, cmd), os.X_OK)
             for path in os.environ["PATH"].split(os.pathsep)])


class NiftyRegCommandInputSpec(CommandLineInputSpec):
    """Input Spec for niftyreg interfaces."""
    # Set the number of omp thread to use
    omp_core_val = traits.Int(int(os.environ.get('OMP_NUM_THREADS', '1')),
                              desc='Number of openmp thread to use',
                              argstr='-omp %i', usedefault=True)


class NiftyRegCommand(CommandLine):
    """
    Base support interface for NiftyReg commands.
    """
    _suffix = '_nr'
    _min_version = '1.5.30'

    input_spec = NiftyRegCommandInputSpec

    def __init__(self, required_version=None, **inputs):
        self.num_threads = 1
        super(NiftyRegCommand, self).__init__(**inputs)
        self.required_version = required_version
        _version = self.get_version()
        if _version:
            _version = _version.decode("utf-8")
            if self._min_version is not None and \
               StrictVersion(_version) < StrictVersion(self._min_version):
                msg = 'A later version of Niftyreg is required (%s < %s)'
                warn(msg % (_version, self._min_version))
            if required_version is not None:
                if StrictVersion(_version) != StrictVersion(required_version):
                    msg = 'The version of NiftyReg differs from the required'
                    msg += '(%s != %s)'
                    warn(msg % (_version, self.required_version))
        self.inputs.on_trait_change(self._omp_update, 'omp_core_val')
        self.inputs.on_trait_change(self._environ_update, 'environ')
        self._omp_update()

    def _omp_update(self):
        if self.inputs.omp_core_val:
            self.inputs.environ['OMP_NUM_THREADS'] = \
                str(self.inputs.omp_core_val)
            self.num_threads = self.inputs.omp_core_val
        else:
            if 'OMP_NUM_THREADS' in self.inputs.environ:
                del self.inputs.environ['OMP_NUM_THREADS']
            self.num_threads = 1

    def _environ_update(self):
        if self.inputs.environ:
            if 'OMP_NUM_THREADS' in self.inputs.environ:
                self.inputs.omp_core_val = \
                    int(self.inputs.environ['OMP_NUM_THREADS'])
            else:
                self.inputs.omp_core_val = Undefined
        else:
            self.inputs.omp_core_val = Undefined

    def check_version(self):
        _version = self.get_version()
        if not _version:
            raise Exception('Niftyreg not found')
        # Decoding to string:
        _version = _version.decode("utf-8")
        if StrictVersion(_version) < StrictVersion(self._min_version):
            err = 'A later version of Niftyreg is required (%s < %s)'
            raise ValueError(err % (_version, self._min_version))
        if self.required_version:
            if StrictVersion(_version) != StrictVersion(self.required_version):
                err = 'The version of NiftyReg differs from the required'
                err += '(%s != %s)'
                raise ValueError(err % (_version, self.required_version))

    def get_version(self):
        if no_nifty_package(cmd=self.cmd):
            return None
        exec_cmd = ''.join((self.cmd, ' -v'))
        return subprocess.check_output(exec_cmd, shell=True).strip()

    @property
    def version(self):
        return self.get_version()

    def exists(self):
        return self.get_version() is not None

    def _format_arg(self, name, spec, value):
        if name == 'omp_core_val':
            self.numthreads = value
        return super(NiftyRegCommand, self)._format_arg(name, spec, value)

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
