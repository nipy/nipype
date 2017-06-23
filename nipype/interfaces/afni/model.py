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
    in_files = InputMultiPath(
        File(
            exists=True),
        desc='   filename(s) of 3D+time input dataset '
             '   [more than one filename can be given] '
             '   [here, and these datasets will be] '
             '   [auto-catenated in time; if you do this,] '
             '   [\'concat\' is not needed and is ignored.] '
             '** You can input a 1D time series file here, '
             '   but the time axis should run along the '
             '   ROW direction, not the COLUMN direction as '
             '   in the \'input1D\' option.',
        argstr='-input %s',
        mandatory=True,
        copyfile=False,
        sep=" ")
    sat = traits.Bool(
        desc='* 3dDeconvolve can check the dataset time series'
             '  for initial saturation transients, which should'
             '  normally have been excised before data analysis.'
             '  If you want to have it do this somewhat time'
             '  consuming check, use the option \'sat\'.',
        argstr='-sat',
        xor=['trans'])
    trans = traits.Bool(
        desc='* 3dDeconvolve can check the dataset time series'
             '  for initial saturation transients, which should'
             '  normally have been excised before data analysis.'
             '  If you want to have it do this somewhat time'
             '  consuming check, use the option \'trans\'.',
        argstr='-trans',
        xor=['sat'])
    noblock = traits.Bool(
        desc='Normally, if you input multiple datasets with'
             '  \'input\', then the separate datasets are taken to'
             '  be separate image runs that get separate baseline'
             '  models.  If you want to have the program consider'
             '  these to be all one big run, use \'noblock\'.'
             '* If any of the input dataset has only 1 sub-brick,'
             '  then this option is automatically invoked!'
             '* If the auto-catenation feature isn\'t used, then'
             '  this option has no effect, no how, no way.',
        argstr='-noblock')
    force_TR = traits.Int(
        desc='Use this value of TR instead of the one in the -input dataset. '
             '(It\'s better to fix the input using 3drefit.)',
        argstr='-force_TR %d')
    input1D = File(
        desc='Filename of single (fMRI) .1D time series where time run downs '
             'the column.',
        argstr='-input1D %s',
        exists=True)
    mask = File(
        desc='Filename of 3D mask dataset; '
             'Only data time series from within the mask '
             'will be analyzed; results for voxels outside '
             'the mask will be set to zero.',
        argstr='-mask %s',
        exists=True)
    automask = traits.Bool(
        argstr='-automask',
        desc='Build a mask automatically from input data (will be slow for '
             'long time series datasets)')
    censor = File(
        desc='  filename of censor .1D time series '
             '* This is a file of 1s and 0s, indicating which '
             '  time points are to be included (1) and which are '
             '  to be excluded (0).',
        argstr='-censor %s',
        exists=True)
    polort = traits.Int(
        desc='Degree of polynomial corresponding to the null hypothesis '
             '[default: 1]',
        argstr='-polort %d')
    ortvec = traits.Tuple(
        File(
            desc='filename',
            exists=True),
        Str(
            desc='label'),
        desc='This option lets you input a rectangular array '
             'of 1 or more baseline vectors from file \'fff\', '
             'which will get the label \'lll\'.  Functionally, '
             'it is the same as using \'-stim_file\' on each '
             'column of \'fff\' separately (plus \'-stim_base\'). '
             'This method is just a faster and simpler way to '
             'include a lot of baseline regressors in one step. ',
        argstr='ortvec %s')
    x1D = File(
        desc='Save out X matrix',
        argstr='-x1D %s')
    x1D_stop = traits.Bool(
        desc='Stop running after writing .xmat.1D file',
        argstr='-x1D_stop')
    out_file = File(
        desc='Output statistics file',
        argstr='-bucket %s')
    jobs = traits.Int(
        desc='Run the program with provided number of sub-processes',
        argstr='-jobs %d')
    stim_times_subtract = traits.Float(
        desc='This option means to subtract specified seconds from each time '
             'encountered in any \'stim_times\' option. The purpose of this '
             'option is to make it simple to adjust timing files for the '
             'removal of images from the start of each imaging run.',
        argstr='-stim_times_subtract %f')
    num_stimts = traits.Int(
        desc='Number of stimulus timing files',
        argstr='-num_stimts %d')
    num_glt = traits.Int(
        desc='Number of general linear tests (i.e., contrasts)',
        argstr='-num_glt %d')
    global_times = traits.Bool(
        desc='Use global timing for stimulus timing files',
        argstr='-global_times',
        xor=['local_times'])
    local_times = traits.Bool(
        desc='Use local timing for stimulus timing files',
        argstr='-local_times',
        xor=['global_times'])
    fout = traits.Bool(
        desc='Output F-statistic for each stimulus',
        argstr='-fout')
    rout = traits.Bool(
        desc='Output the R^2 statistic for each stimulus',
        argstr='-rout')
    tout = traits.Bool(
        desc='Output the T-statistic for each stimulus',
        argstr='-tout')
    vout = traits.Bool(
        desc='Output the sample variance (MSE) for each stimulus',
        argstr='-vout')
    stim_times = traits.List(
        traits.Tuple(traits.Int(desc='k-th response model'),
                     File(desc='stimulus timing file',exists=True),
                     Str(desc='model')),
        desc='Generate a response model from a set of stimulus times'
             ' given in file.',
        argstr='-stim_times %d %s %s...')
    stim_label = traits.List(
        traits.Tuple(traits.Int(desc='k-th input stimulus'),
                     Str(desc='stimulus label')),
        desc='Label for kth input stimulus',
        argstr='-stim_label %d %s...',
        requires=['stim_times'])
    gltsym = traits.List(
        Str(desc='symbolic general linear test'),
        desc='General linear tests (i.e., contrasts) using symbolic '
             'conventions',
        argstr='-gltsym SYM: %s...')
    glt_labels = traits.List(
        traits.Tuple(traits.Int(desc='k-th general linear test'),
                     Str(desc='GLT label')),
        desc='General linear test (i.e., contrast) labels',
        argstr='-glt_label %d %s...',
        requires=['gltsym'])


class DeconvolveOutputSpec(AFNICommandOutputSpec):
    out_file = File(desc='output statistics file',
                    exists=True)


class Deconvolve(AFNICommand):
    """Performs OLS regression given a 4D neuroimage file and stimulus timings

    For complete details, see the `3dDeconvolve Documentation.
    <https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html>`_

    Examples
    ========

    >>> from nipype.interfaces import afni
    >>> deconvolve = afni.Deconvolve()
    >>> deconvolve.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> deconvolve.inputs.out_file = 'output.nii'
    >>> deconvolve.inputs.x1D = 'output.1D'
    >>> stim_times = [(1, 'timeseries.txt', 'SPMG1(4)'), (2, 'timeseries.txt', 'SPMG2(4)')]
    >>> deconvolve.inputs.stim_times = stim_times
    >>> deconvolve.cmdline  # doctest: +ALLOW_UNICODE
    '3dDeconvolve -input functional.nii functional2.nii -num_stimts 2 -bucket output.nii -stim_times 1 timeseries.txt SPMG1(4) -stim_times 2 timeseries.txt SPMG2(4) -x1D output.1D'
    >>> res = deconvolve.run()  # doctest: +SKIP

    >>> from nipype.interfaces import afni
    >>> deconvolve = afni.Deconvolve()
    >>> deconvolve.inputs.in_files = ['functional.nii', 'functional2.nii']
    >>> deconvolve.inputs.out_file = 'output.nii'
    >>> deconvolve.inputs.x1D = 'output.1D'
    >>> stim_times = [(1, 'timeseries.txt', 'SPMG1(4)'), (2, 'timeseries.txt', 'SPMG2(4)')]
    >>> deconvolve.inputs.stim_times = stim_times
    >>> deconvolve.inputs.stim_label = [(1, 'Houses'), (2, 'Apartments')]
    >>> deconvolve.inputs.gltsym = [('+Houses -Apartments')]
    >>> deconvolve.inputs.glt_label = [(1, 'Houses_Apartments')]
    >>> deconvolve.cmdline  # doctest: +ALLOW_UNICODE
    "3dDeconvolve -glt_label 1 Houses_Apartments -gltsym SYM: +Houses -Apartments -input functional.nii functional2.nii -num_glt 1 -num_stimts 2 -bucket output.nii -stim_label 1 Houses -stim_label 2 Apartments -stim_times 1 timeseries.txt SPMG1(4) -stim_times 2 timeseries.txt SPMG2(4) -x1D output.1D"
    >>> res = deconvolve.run()  # doctest: +SKIP
    """

    _cmd = '3dDeconvolve'
    input_spec = DeconvolveInputSpec
    output_spec = AFNICommandOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        if len(self.inputs.stim_times) and not isdefined(self.inputs.num_stimts):
            self.inputs.num_stimts = len(self.inputs.stim_times)
        if len(self.inputs.gltsym) and not isdefined(self.inputs.num_glt):
            self.inputs.num_glt = len(self.inputs.gltsym)
        return super(Deconvolve, self)._parse_inputs(skip)

    def _list_outputs(self):
        outputs = super(Deconvolve, self)._list_outputs()
        if isdefined(self.inputs.x1D):
            if not self.inputs.x1D.endswith('.xmat.1D'):
                outputs['x1D'] = self.inputs.x1D + '.xmat.1D'
            else:
                outputs['x1D'] = self.inputs.x1D

        outputs['out_file'] = self.inputs.out_file
        return outputs
