# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The niftyseg module provides classes for interfacing with `niftyseg
<https://sourceforge.net/projects/niftyseg/>`_ command line tools.

These are the base tools for working with niftyseg.

EM Statistical Segmentation tool is found in niftyseg/em.py
Fill lesions tool is found in niftyseg/lesions.py
Mathematical operation tool is found in niftyseg/maths.py
Patch Match tool is found in niftyseg/patchmatch.py
Statistical operation tool is found in niftyseg/stats.py
Label Fusion and CalcTopNcc tools are in niftyseg/steps.py

Examples
--------
See the docstrings of the individual classes for examples.

"""

from nipype.interfaces.base import CommandLine, isdefined
from nipype.utils.filemanip import split_filename
import os
import subprocess
import warnings


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


def get_custom_path(command):
    """Get path of niftyseg."""
    try:
        specific_dir = os.environ['NIFTYSEGDIR']
        command = os.path.join(specific_dir, command)
        return command
    except KeyError:
        return command


def no_niftyseg(cmd='seg_LabFusion'):
    """Check if niftyseg is installed."""
    if True in [os.path.isfile(os.path.join(path, cmd)) and
                os.access(os.path.join(path, cmd), os.X_OK)
                for path in os.environ["PATH"].split(os.pathsep)]:
        return False
    return True


class NiftySegCommand(CommandLine):
    """
    Base support interface for NiftySeg commands.
    """
    _suffix = '_ns'

    def __init__(self, **inputs):
        super(NiftySegCommand, self).__init__(**inputs)

    def get_version(self):
        if no_niftyseg(cmd=self.cmd):
            return None
        # exec_cmd = ''.join((self.cmd, ' --version'))
        exec_cmd = 'seg_EM --version'
        # Using seg_EM for version (E.G: seg_stats --version doesn't work)
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
            return self._gen_fname(self.inputs.in_file, suffix=self._suffix)
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.out_file):
            outputs['out_file'] = self.inputs.out_file
        else:
            outputs['out_file'] = self._gen_filename('out_file')
        return outputs
