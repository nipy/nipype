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


class BrainMaskInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
                   desc='input diffusion weighted images')
    out_file = File(
        'brainmask.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output brain mask')
    # DW gradient table import options
    grad_file = File(exists=True, argstr='-grad %s',
                     desc='dw gradient scheme (MRTrix format')
    grad_fsl = traits.Tuple(
        File(exists=True), File(exists=True), argstr='-fslgrad %s %s',
        desc='(bvecs, bvals) dw gradient scheme (FSL format')
    bval_scale = traits.Enum(
        'yes', 'no', argstr='-bvalue_scaling %s',
        desc=('specifies whether the b - values should be scaled by the square'
              ' of the corresponding DW gradient norm, as often required for '
              'multishell or DSI DW acquisition schemes. The default action '
              'can also be set in the MRtrix config file, under the '
              'BValueScaling entry. Valid choices are yes / no, true / '
              'false, 0 / 1 (default: true).'))


class BrainMaskOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class BrainMask(CommandLine):

    """
    Convert a mesh surface to a partial volume estimation image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> bmsk = mrt.BrainMask()
    >>> bmsk.inputs.in_file = 'dwi.mif'
    >>> bmsk.cmdline                               # doctest: +ELLIPSIS
    'dwi2mask dwi.mif brainmask.mif'
    >>> bmsk.run()                                 # doctest: +SKIP
    """

    _cmd = 'dwi2mask'
    input_spec = BrainMaskInputSpec
    output_spec = BrainMaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class Mesh2PVEInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3,
                   desc='input mesh')
    reference = File(exists=True, argstr='%s', mandatory=True, position=-2,
                     desc='input reference image')
    in_first = File(
        exists=True, argstr='-first %s',
        desc='indicates that the mesh file is provided by FSL FIRST')

    out_file = File(
        'mesh2volume.nii.gz', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file containing SH coefficients')


class Mesh2PVEOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class Mesh2PVE(CommandLine):

    """
    Convert a mesh surface to a partial volume estimation image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> m2p = mrt.Mesh2PVE()
    >>> m2p.inputs.in_file = 'surf1.vtk'
    >>> m2p.inputs.reference = 'dwi.mif'
    >>> m2p.inputs.in_first = 'T1.nii.gz'
    >>> m2p.cmdline                               # doctest: +ELLIPSIS
    'mesh2pve -first T1.nii.gz surf1.vtk dwi.mif mesh2volume.nii.gz'
    >>> m2p.run()                                 # doctest: +SKIP
    """

    _cmd = 'mesh2pve'
    input_spec = Mesh2PVEInputSpec
    output_spec = Mesh2PVEOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class Generate5ttInputSpec(CommandLineInputSpec):
    in_fast = InputMultiPath(
        File(exists=True), argstr='%s', mandatory=True, position=-3,
        desc='list of PVE images from FAST')
    in_first = File(
        exists=True, argstr='%s', position=-2,
        desc='combined segmentation file from FIRST')
    out_file = File(
        'act-5tt.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='name of output file')


class Generate5ttOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='segmentation for ACT in 5tt format')


class Generate5tt(CommandLine):

    """
    Concatenate segmentation results from FSL FAST and FIRST into the 5TT
    format required for ACT


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> seg = mrt.Generate5tt()
    >>> seg.inputs.in_fast = ['tpm_00.nii.gz',
    ...                       'tpm_01.nii.gz', 'tpm_02.nii.gz']
    >>> seg.inputs.in_first = 'first_merged.nii.gz'
    >>> seg.cmdline                               # doctest: +ELLIPSIS
    '5ttgen tpm_00.nii.gz tpm_01.nii.gz tpm_02.nii.gz first_merged.nii.gz\
 act-5tt.mif'
    >>> seg.run()                                 # doctest: +SKIP
    """

    _cmd = '5ttgen'
    input_spec = Generate5ttInputSpec
    output_spec = Generate5ttOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs


class TensorMetricsInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-1,
                   desc='input DTI image')

    out_fa = File(argstr='-fa %s', desc='output FA file')
    out_adc = File(argstr='-adc %s', desc='output ADC file')
    out_evec = File(argstr='-vector %s',
                    desc='output selected eigenvector(s) file')
    out_eval = File(argstr='-value %s',
                    desc='output selected eigenvalue(s) file')
    component = traits.List(
        [1, 2, 3], argstr='-num %s', sep=',',
        desc=('specify the desired eigenvalue/eigenvector(s). Note that '
              'several eigenvalues can be specified as a number sequence'))
    in_mask = File(exists=True, argstr='-mask %s',
                   desc=('only perform computation within the specified binary'
                         ' brain mask image'))
    modulate = traits.Enum('FA', 'none', 'eval', argstr='-modulate %s',
                           desc=('how to modulate the magnitude of the'
                                 ' eigenvectors'))


class TensorMetricsOutputSpec(TraitedSpec):
    out_fa = File(desc='output FA file')
    out_adc = File(desc='output ADC file')
    out_evec = File(desc='output selected eigenvector(s) file')
    out_eval = File(desc='output selected eigenvalue(s) file')


class TensorMetrics(CommandLine):

    """
    Convert a mesh surface to a partial volume estimation image


    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> comp = mrt.TensorMetrics()
    >>> comp.inputs.in_file = 'dti.mif'
    >>> comp.inputs.out_fa = 'fa.mif'
    >>> comp.cmdline                               # doctest: +ELLIPSIS
    'tensor2metric -fa fa.mif dti.mif'
    >>> comp.run()                                 # doctest: +SKIP
    """

    _cmd = 'tensor2metric'
    input_spec = TensorMetricsInputSpec
    output_spec = TensorMetricsOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()

        for k in outputs.keys():
            if isdefined(getattr(self.inputs, k)):
                outputs[k] = op.abspath(getattr(self.inputs, k))

        return outputs
