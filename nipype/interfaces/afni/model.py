# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft = python sts = 4 ts = 4 sw = 4 et:
"""AFNI modeling interfaces

Examples
--------
See the docstrings of the individual classes for examples.
  .. testsetup::
    # Change directory to provide relative paths for doctests
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str, bytes

import os
import os.path as op
import re
import numpy as np

from ...utils.filemanip import (load_json, save_json, split_filename)
from ..base import (
    CommandLineInputSpec, CommandLine, Directory, TraitedSpec,
    traits, isdefined, File, InputMultiPath, Undefined, Str)
from ...external.due import BibTeX

from .base import (
    AFNICommandBase, AFNICommand, AFNICommandInputSpec, AFNICommandOutputSpec)

class DeconvolveInputSpec(AFNICommandInputSpec):
    pass


class DeconvolveOutputSpec(TraitedSpec):
    pass


class Deconvolve(AFNICommand):
    """Performs OLS regression given a 4D neuroimage file and stimulus timings

    For complete details, see the `3dDeconvolve Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> deconvolve = afni.Deconvolve()
    >>> deconvolve.inputs.in_file = 'functional.nii'
    >>> deconvolve.inputs.bucket = 'output.nii'
    >>> deconvolve.inputs.x1D = 'output.1D'
    >>> stim_times = [(1, 'stims1.txt', 'SPMG1(4)'), (2, 'stims2.txt', 'SPMG2(4)')]
    >>> deconvolve.inputs.stim_times = stim_times
    >>> deconvolve.cmdline  # doctest: +ALLOW_UNICODE
    '3dDeconvolve -input functional.nii -bucket output.nii -x1D output.1D -stim_times 1 stims1.txt SPMG1(4) 2 stims2.txt SPMG2(4)'
    >>> res = deconvolve.run()  # doctest: +SKIP
    """
    _cmd = '3dDeconvolve'
    input_spec = DeconvolveInputSpec
    output_spec = DeconvolveOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.x1D):
            if not self.inputs.x1D.endswith('.xmat.1D'):
                outputs['x1D'] = outputs['x1D'] + '.xmat.1D'
        return outputs

    def _format_arg(self, name, trait_spec, value):
        """
        Argument num_glt is defined automatically from the number of contrasts
        desired (defined by the length of glt_sym). No effort has been made to
        make this compatible with glt.
        """
        if name in ['stim_times', 'stim_labels']:
            arg = ''
            for st in value:
                arg += trait_spec.argstr % value
            arg = arg.rstrip()
            return arg
        elif name == 'glt_sym':
            self.inputs.num_glt = len(value)
