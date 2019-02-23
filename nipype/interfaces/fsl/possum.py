#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The possum module provides classes for interfacing with `POSSUM
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/POSSUM>`_ command line tools.
Please, check out the link for pertinent citations using POSSUM.

  .. Note:: This was written to work with FSL version 5.0.6.
"""

from .base import FSLCommand, FSLCommandInputSpec
from ..base import TraitedSpec, File, traits


class B0CalcInputSpec(FSLCommandInputSpec):
    in_file = File(
        exists=True,
        mandatory=True,
        argstr='-i %s',
        position=0,
        desc='filename of input image (usually a tissue/air segmentation)')
    out_file = File(
        argstr='-o %s',
        position=1,
        name_source=['in_file'],
        name_template='%s_b0field',
        output_name='out_file',
        desc='filename of B0 output volume')

    x_grad = traits.Float(
        0.0, usedefault=True,
        argstr='--gx=%0.4f',
        desc='Value for zeroth-order x-gradient field (per mm)')
    y_grad = traits.Float(
        0.0, usedefault=True,
        argstr='--gy=%0.4f',
        desc='Value for zeroth-order y-gradient field (per mm)')
    z_grad = traits.Float(
        0.0, usedefault=True,
        argstr='--gz=%0.4f',
        desc='Value for zeroth-order z-gradient field (per mm)')

    x_b0 = traits.Float(
        0.0, usedefault=True,
        argstr='--b0x=%0.2f',
        xor=['xyz_b0'],
        desc='Value for zeroth-order b0 field (x-component), in Tesla')
    y_b0 = traits.Float(
        0.0, usedefault=True,
        argstr='--b0y=%0.2f',
        xor=['xyz_b0'],
        desc='Value for zeroth-order b0 field (y-component), in Tesla')
    z_b0 = traits.Float(
        1.0, usedefault=True,
        argstr='--b0=%0.2f',
        xor=['xyz_b0'],
        desc='Value for zeroth-order b0 field (z-component), in Tesla')

    xyz_b0 = traits.Tuple(
        traits.Float,
        traits.Float,
        traits.Float,
        argstr='--b0x=%0.2f --b0y=%0.2f --b0=%0.2f',
        xor=['x_b0', 'y_b0', 'z_b0'],
        desc='Zeroth-order B0 field in Tesla')

    delta = traits.Float(
        -9.45e-6, usedefault=True,
         argstr='-d %e', desc='Delta value (chi_tissue - chi_air)')
    chi_air = traits.Float(
        4.0e-7, usedefault=True,
        argstr='--chi0=%e', desc='susceptibility of air')
    compute_xyz = traits.Bool(
        False, usedefault=True,
        argstr='--xyz',
        desc='calculate and save all 3 field components (i.e. x,y,z)')
    extendboundary = traits.Float(
        1.0, usedefault=True,
        argstr='--extendboundary=%0.2f',
        desc='Relative proportion to extend voxels at boundary')
    directconv = traits.Bool(
        False, usedefault=True,
        argstr='--directconv',
        desc='use direct (image space) convolution, not FFT')


class B0CalcOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='filename of B0 output volume')


class B0Calc(FSLCommand):
    """
    B0 inhomogeneities occur at interfaces of materials with different magnetic susceptibilities,
    such as tissue-air interfaces. These differences lead to distortion in the local magnetic field,
    as Maxwell’s equations need to be satisfied. An example of B0 inhomogneity is the first volume
    of the 4D volume ```$FSLDIR/data/possum/b0_ppm.nii.gz```.

    Examples
    --------

    >>> from nipype.interfaces.fsl import B0Calc
    >>> b0calc = B0Calc()
    >>> b0calc.inputs.in_file = 'tissue+air_map.nii'
    >>> b0calc.inputs.z_b0 = 3.0
    >>> b0calc.inputs.output_type = "NIFTI_GZ"
    >>> b0calc.cmdline
    'b0calc -i tissue+air_map.nii -o tissue+air_map_b0field.nii.gz --chi0=4.000000e-07 \
-d -9.450000e-06 --extendboundary=1.00 --b0x=0.00 --gx=0.0000 --b0y=0.00 --gy=0.0000 \
--b0=3.00 --gz=0.0000'

    """

    _cmd = 'b0calc'
    input_spec = B0CalcInputSpec
    output_spec = B0CalcOutputSpec
