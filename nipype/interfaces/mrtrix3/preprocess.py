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
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os.path as op

from ..base import (CommandLineInputSpec, CommandLine, traits, TraitedSpec,
                    File, isdefined, Undefined)
from .base import MRTrix3BaseInputSpec, MRTrix3Base


class ResponseSDInputSpec(MRTrix3BaseInputSpec):
    algorithm = traits.Enum(
        'msmt_5tt',
        'dhollander',
        'tournier',
        'tax',
        argstr='%s',
        position=-6,
        mandatory=True,
        desc='response estimation algorithm (multi-tissue)')
    in_file = File(
        exists=True,
        argstr='%s',
        position=-5,
        mandatory=True,
        desc='input DWI image')
    mtt_file = File(argstr='%s', position=-4, desc='input 5tt image')
    wm_file = File(
        'wm.txt',
        argstr='%s',
        position=-3,
        usedefault=True,
        desc='output WM response text file')
    gm_file = File(
        argstr='%s', position=-2, desc='output GM response text file')
    csf_file = File(
        argstr='%s', position=-1, desc='output CSF response text file')
    in_mask = File(
        exists=True, argstr='-mask %s', desc='provide initial mask image')
    max_sh = traits.Int(
        8,
        argstr='-lmax %d',
        desc='maximum harmonic degree of response function')


class ResponseSDOutputSpec(TraitedSpec):
    wm_file = File(argstr='%s', desc='output WM response text file')
    gm_file = File(argstr='%s', desc='output GM response text file')
    csf_file = File(argstr='%s', desc='output CSF response text file')


class ResponseSD(MRTrix3Base):
    """
    Estimate response function(s) for spherical deconvolution using the specified algorithm.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> resp = mrt.ResponseSD()
    >>> resp.inputs.in_file = 'dwi.mif'
    >>> resp.inputs.algorithm = 'tournier'
    >>> resp.inputs.grad_fsl = ('bvecs', 'bvals')
    >>> resp.cmdline                               # doctest: +ELLIPSIS
    'dwi2response -fslgrad bvecs bvals tournier dwi.mif wm.txt'
    >>> resp.run()                                 # doctest: +SKIP
    """

    _cmd = 'dwi2response'
    input_spec = ResponseSDInputSpec
    output_spec = ResponseSDOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['wm_file'] = op.abspath(self.inputs.wm_file)
        if self.inputs.gm_file != Undefined:
            outputs['gm_file'] = op.abspath(self.inputs.gm_file)
        if self.inputs.csf_file != Undefined:
            outputs['csf_file'] = op.abspath(self.inputs.csf_file)
        return outputs


class ACTPrepareFSLInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-2,
        desc='input anatomical image')

    out_file = File(
        'act_5tt.mif',
        argstr='%s',
        mandatory=True,
        position=-1,
        usedefault=True,
        desc='output file after processing')


class ACTPrepareFSLOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class ACTPrepareFSL(CommandLine):
    """
    Generate anatomical information necessary for Anatomically
    Constrained Tractography (ACT).

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ACTPrepareFSL()
    >>> prep.inputs.in_file = 'T1.nii.gz'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'act_anat_prepare_fsl T1.nii.gz act_5tt.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = 'act_anat_prepare_fsl'
    input_spec = ACTPrepareFSLInputSpec
    output_spec = ACTPrepareFSLOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class ReplaceFSwithFIRSTInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-4,
        desc='input anatomical image')
    in_t1w = File(
        exists=True,
        argstr='%s',
        mandatory=True,
        position=-3,
        desc='input T1 image')
    in_config = File(
        exists=True,
        argstr='%s',
        position=-2,
        desc='connectome configuration file')

    out_file = File(
        'aparc+first.mif',
        argstr='%s',
        mandatory=True,
        position=-1,
        usedefault=True,
        desc='output file after processing')


class ReplaceFSwithFIRSTOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class ReplaceFSwithFIRST(CommandLine):
    """
    Replace deep gray matter structures segmented with FSL FIRST in a
    FreeSurfer parcellation.

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> prep = mrt.ReplaceFSwithFIRST()
    >>> prep.inputs.in_file = 'aparc+aseg.nii'
    >>> prep.inputs.in_t1w = 'T1.nii.gz'
    >>> prep.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> prep.cmdline                               # doctest: +ELLIPSIS
    'fs_parc_replace_sgm_first aparc+aseg.nii T1.nii.gz \
mrtrix3_labelconfig.txt aparc+first.mif'
    >>> prep.run()                                 # doctest: +SKIP
    """

    _cmd = 'fs_parc_replace_sgm_first'
    input_spec = ReplaceFSwithFIRSTInputSpec
    output_spec = ReplaceFSwithFIRSTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
