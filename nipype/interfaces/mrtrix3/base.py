# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__ ))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os
import os.path as op

from nipype.interfaces.base import (
    CommandLineInputSpec, CommandLine, traits, TraitedSpec, File,
    InputMultiPath)

from nipype.utils.filemanip import split_filename
from nipype.interfaces.traits_extension import isdefined

from ... import logging
logger = logging.getLogger('interface')


class MRTrix3BaseInputSpec(CommandLineInputSpec):
    nthreads = traits.Int(
        argstr='-nthreads %d', desc='number of threads. if zero, the number'
        ' of available cpus will be used', nohash=True)
    # DW gradient table import options
    grad_file = File(exists=True, argstr='-grad %s',
                     desc='dw gradient scheme (MRTrix format')
    grad_fsl = traits.Tuple(
        File(exists=True), File(exists=True), argstr='-fslgrad %s %s',
        desc='(bvecs, bvals) dw gradient scheme (FSL format')
    bval_scale = traits.Enum(
        'yes', 'no', argstr='-bvalue_scaling %s',
        desc='specifies whether the b - values should be scaled by the square'
        ' of the corresponding DW gradient norm, as often required for '
        'multishell or DSI DW acquisition schemes. The default action '
        'can also be set in the MRtrix config file, under the '
        'BValueScaling entry. Valid choices are yes / no, true / '
        'false, 0 / 1 (default: true).')


class MRTrix3Base(CommandLine):

    def _format_arg(self, name, trait_spec, value):
        if name == 'nthreads' and value == 0:
            value = 1
            try:
                from multiprocessing import cpu_count
                value = cpu_count()
            except:
                logger.warn('Number of threads could not be computed')
                pass
            return trait_spec.argstr % value

        return super(MRTrix3Base, self)._format_arg(name, trait_spec, value)
