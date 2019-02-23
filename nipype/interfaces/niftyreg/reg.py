# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The reg module provides classes for interfacing with the `niftyreg
<http://niftyreg.sourceforge.net>`_ registration command line tools.

The interfaces were written to work with niftyreg version 1.5.10
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import staticmethod
import os

from ..base import TraitedSpec, File, traits, isdefined
from .base import get_custom_path, NiftyRegCommand, NiftyRegCommandInputSpec
from ...utils.filemanip import split_filename


class RegAladinInputSpec(NiftyRegCommandInputSpec):
    """ Input Spec for RegAladin. """
    # Input reference file
    ref_file = File(
        exists=True,
        desc='The input reference/target image',
        argstr='-ref %s',
        mandatory=True)
    # Input floating file
    flo_file = File(
        exists=True,
        desc='The input floating/source image',
        argstr='-flo %s',
        mandatory=True)
    # No symmetric flag
    nosym_flag = traits.Bool(
        argstr='-noSym', desc='Turn off symmetric registration')
    # Rigid only registration
    rig_only_flag = traits.Bool(
        argstr='-rigOnly', desc='Do only a rigid registration')
    # Directly optimise affine flag
    desc = 'Directly optimise the affine parameters'
    aff_direct_flag = traits.Bool(argstr='-affDirect', desc=desc)
    # Input affine
    in_aff_file = File(
        exists=True,
        desc='The input affine transformation',
        argstr='-inaff %s')
    # Input reference mask
    rmask_file = File(
        exists=True, desc='The input reference mask', argstr='-rmask %s')
    # Input floating mask
    fmask_file = File(
        exists=True, desc='The input floating mask', argstr='-fmask %s')
    # Maximum number of iterations
    maxit_val = traits.Range(
        desc='Maximum number of iterations', argstr='-maxit %d', low=0)
    # Multiresolution levels
    ln_val = traits.Range(
        desc='Number of resolution levels to create', argstr='-ln %d', low=0)
    # Number of resolution levels to process
    lp_val = traits.Range(
        desc='Number of resolution levels to perform', argstr='-lp %d', low=0)
    # Smoothing to apply on reference image
    desc = 'Amount of smoothing to apply to reference image'
    smoo_r_val = traits.Float(desc=desc, argstr='-smooR %f')
    # Smoothing to apply on floating image
    desc = 'Amount of smoothing to apply to floating image'
    smoo_f_val = traits.Float(desc=desc, argstr='-smooF %f')
    # Use nifti header to initialise transformation
    desc = 'Use nifti header to initialise transformation'
    nac_flag = traits.Bool(desc=desc, argstr='-nac')
    # Use the input masks centre of mass to initialise the transformation
    desc = 'Use the masks centre of mass to initialise the transformation'
    cog_flag = traits.Bool(desc=desc, argstr='-cog')
    # Percent of blocks that are considered active.
    v_val = traits.Range(
        desc='Percent of blocks that are active', argstr='-pv %d', low=0)
    # Percent of inlier blocks
    i_val = traits.Range(
        desc='Percent of inlier blocks', argstr='-pi %d', low=0)
    # Lower threshold on reference image
    ref_low_val = traits.Float(
        desc='Lower threshold value on reference image',
        argstr='-refLowThr %f')
    # Upper threshold on reference image
    ref_up_val = traits.Float(
        desc='Upper threshold value on reference image', argstr='-refUpThr %f')
    # Lower threshold on floating image
    flo_low_val = traits.Float(
        desc='Lower threshold value on floating image', argstr='-floLowThr %f')
    # Upper threshold on floating image
    flo_up_val = traits.Float(
        desc='Upper threshold value on floating image', argstr='-floUpThr %f')
    # Platform to use
    platform_val = traits.Int(desc='Platform index', argstr='-platf %i')
    # Platform to use
    gpuid_val = traits.Int(desc='Device to use id', argstr='-gpuid %i')
    # Verbosity off
    verbosity_off_flag = traits.Bool(
        argstr='-voff', desc='Turn off verbose output')

    # Affine output transformation matrix file
    aff_file = File(
        name_source=['flo_file'],
        name_template='%s_aff.txt',
        desc='The output affine matrix file',
        argstr='-aff %s')
    # Result warped image file
    res_file = File(
        name_source=['flo_file'],
        name_template='%s_res.nii.gz',
        desc='The affine transformed floating image',
        argstr='-res %s')


class RegAladinOutputSpec(TraitedSpec):
    """ Output Spec for RegAladin. """
    aff_file = File(desc='The output affine file')
    res_file = File(desc='The output transformed image')
    desc = 'Output string in the format for reg_average'
    avg_output = traits.String(desc=desc)


class RegAladin(NiftyRegCommand):
    """Interface for executable reg_aladin from NiftyReg platform.

    Block Matching algorithm for symmetric global registration.
    Based on Modat et al., "Global image registration using
    asymmetric block-matching approach"
    J. Med. Img. 1(2) 024003, 2014, doi: 10.1117/1.JMI.1.2.024003

    `Source code <https://cmiclab.cs.ucl.ac.uk/mmodat/niftyreg>`_

    Examples
    --------
    >>> from nipype.interfaces import niftyreg
    >>> node = niftyreg.RegAladin()
    >>> node.inputs.ref_file = 'im1.nii'
    >>> node.inputs.flo_file = 'im2.nii'
    >>> node.inputs.rmask_file = 'mask.nii'
    >>> node.inputs.omp_core_val = 4
    >>> node.cmdline
    'reg_aladin -aff im2_aff.txt -flo im2.nii -omp 4 -ref im1.nii \
-res im2_res.nii.gz -rmask mask.nii'

    """
    _cmd = get_custom_path('reg_aladin')
    input_spec = RegAladinInputSpec
    output_spec = RegAladinOutputSpec

    def _list_outputs(self):
        outputs = super(RegAladin, self)._list_outputs()

        # Make a list of the linear transformation file and the input image
        aff = os.path.abspath(outputs['aff_file'])
        flo = os.path.abspath(self.inputs.flo_file)
        outputs['avg_output'] = '%s %s' % (aff, flo)
        return outputs


class RegF3DInputSpec(NiftyRegCommandInputSpec):
    """ Input Spec for RegF3D. """
    # Input reference file
    ref_file = File(
        exists=True,
        desc='The input reference/target image',
        argstr='-ref %s',
        mandatory=True)
    # Input floating file
    flo_file = File(
        exists=True,
        desc='The input floating/source image',
        argstr='-flo %s',
        mandatory=True)

    # Input Affine file
    aff_file = File(
        exists=True,
        desc='The input affine transformation file',
        argstr='-aff %s')

    # Input cpp file
    incpp_file = File(
        exists=True,
        desc='The input cpp transformation file',
        argstr='-incpp %s')

    # Reference mask
    rmask_file = File(
        exists=True, desc='Reference image mask', argstr='-rmask %s')

    # Smoothing kernel for reference
    desc = 'Smoothing kernel width for reference image'
    ref_smooth_val = traits.Float(desc=desc, argstr='-smooR %f')
    # Smoothing kernel for floating
    desc = 'Smoothing kernel width for floating image'
    flo_smooth_val = traits.Float(desc=desc, argstr='-smooF %f')

    # Lower threshold for reference image
    rlwth_thr_val = traits.Float(
        desc='Lower threshold for reference image', argstr='--rLwTh %f')
    # Upper threshold for reference image
    rupth_thr_val = traits.Float(
        desc='Upper threshold for reference image', argstr='--rUpTh %f')
    # Lower threshold for reference image
    flwth_thr_val = traits.Float(
        desc='Lower threshold for floating image', argstr='--fLwTh %f')
    # Upper threshold for reference image
    fupth_thr_val = traits.Float(
        desc='Upper threshold for floating image', argstr='--fUpTh %f')

    # Lower threshold for reference image
    desc = 'Lower threshold for reference image at the specified time point'
    rlwth2_thr_val = traits.Tuple(
        traits.Range(low=0), traits.Float, desc=desc, argstr='-rLwTh %d %f')
    # Upper threshold for reference image
    desc = 'Upper threshold for reference image at the specified time point'
    rupth2_thr_val = traits.Tuple(
        traits.Range(low=0), traits.Float, desc=desc, argstr='-rUpTh %d %f')
    # Lower threshold for reference image
    desc = 'Lower threshold for floating image at the specified time point'
    flwth2_thr_val = traits.Tuple(
        traits.Range(low=0), traits.Float, desc=desc, argstr='-fLwTh %d %f')
    # Upper threshold for reference image
    desc = 'Upper threshold for floating image at the specified time point'
    fupth2_thr_val = traits.Tuple(
        traits.Range(low=0), traits.Float, desc=desc, argstr='-fUpTh %d %f')

    # Final grid spacing along the 3 axes
    sx_val = traits.Float(
        desc='Final grid spacing along the x axes', argstr='-sx %f')
    sy_val = traits.Float(
        desc='Final grid spacing along the y axes', argstr='-sy %f')
    sz_val = traits.Float(
        desc='Final grid spacing along the z axes', argstr='-sz %f')

    # Regularisation options
    be_val = traits.Float(desc='Bending energy value', argstr='-be %f')
    le_val = traits.Float(
        desc='Linear elasticity penalty term', argstr='-le %f')
    jl_val = traits.Float(
        desc='Log of jacobian of deformation penalty value', argstr='-jl %f')
    desc = 'Do not approximate the log of jacobian penalty at control points \
only'

    no_app_jl_flag = traits.Bool(argstr='-noAppJL', desc=desc)

    # Similarity measure options
    desc = 'use NMI even when other options are specified'
    nmi_flag = traits.Bool(argstr='--nmi', desc=desc)
    desc = 'Number of bins in the histogram for reference image'
    rbn_val = traits.Range(low=0, desc=desc, argstr='--rbn %d')
    desc = 'Number of bins in the histogram for reference image'
    fbn_val = traits.Range(low=0, desc=desc, argstr='--fbn %d')
    desc = 'Number of bins in the histogram for reference image for given \
time point'

    rbn2_val = traits.Tuple(
        traits.Range(low=0),
        traits.Range(low=0),
        desc=desc,
        argstr='-rbn %d %d')

    desc = 'Number of bins in the histogram for reference image for given \
time point'

    fbn2_val = traits.Tuple(
        traits.Range(low=0),
        traits.Range(low=0),
        desc=desc,
        argstr='-fbn %d %d')

    lncc_val = traits.Float(
        desc='SD of the Gaussian for computing LNCC', argstr='--lncc %f')
    desc = 'SD of the Gaussian for computing LNCC for a given time point'
    lncc2_val = traits.Tuple(
        traits.Range(low=0), traits.Float, desc=desc, argstr='-lncc %d %f')

    ssd_flag = traits.Bool(
        desc='Use SSD as the similarity measure', argstr='--ssd')
    desc = 'Use SSD as the similarity measure for a given time point'
    ssd2_flag = traits.Range(low=0, desc=desc, argstr='-ssd %d')
    kld_flag = traits.Bool(
        desc='Use KL divergence as the similarity measure', argstr='--kld')
    desc = 'Use KL divergence as the similarity measure for a given time point'
    kld2_flag = traits.Range(low=0, desc=desc, argstr='-kld %d')
    amc_flag = traits.Bool(desc='Use additive NMI', argstr='-amc')

    nox_flag = traits.Bool(desc="Don't optimise in x direction", argstr='-nox')
    noy_flag = traits.Bool(desc="Don't optimise in y direction", argstr='-noy')
    noz_flag = traits.Bool(desc="Don't optimise in z direction", argstr='-noz')

    # Optimization options
    maxit_val = traits.Range(
        low=0,
        argstr='-maxit %d',
        desc='Maximum number of iterations per level')
    ln_val = traits.Range(
        low=0, argstr='-ln %d', desc='Number of resolution levels to create')
    lp_val = traits.Range(
        low=0, argstr='-lp %d', desc='Number of resolution levels to perform')
    nopy_flag = traits.Bool(
        desc='Do not use the multiresolution approach', argstr='-nopy')
    noconj_flag = traits.Bool(
        desc='Use simple GD optimization', argstr='-noConj')
    desc = 'Add perturbation steps after each optimization step'
    pert_val = traits.Range(low=0, desc=desc, argstr='-pert %d')

    # F3d2 options
    vel_flag = traits.Bool(
        desc='Use velocity field integration', argstr='-vel')
    fmask_file = File(
        exists=True, desc='Floating image mask', argstr='-fmask %s')

    # Other options
    desc = 'Kernel width for smoothing the metric gradient'
    smooth_grad_val = traits.Float(desc=desc, argstr='-smoothGrad %f')
    # Padding value
    pad_val = traits.Float(desc='Padding value', argstr='-pad %f')
    # verbosity off
    verbosity_off_flag = traits.Bool(
        argstr='-voff', desc='Turn off verbose output')

    # Output CPP image file
    cpp_file = File(
        name_source=['flo_file'],
        name_template='%s_cpp.nii.gz',
        desc='The output CPP file',
        argstr='-cpp %s')
    # Output warped image file
    res_file = File(
        name_source=['flo_file'],
        name_template='%s_res.nii.gz',
        desc='The output resampled image',
        argstr='-res %s')


class RegF3DOutputSpec(TraitedSpec):
    """ Output Spec for RegF3D. """
    cpp_file = File(desc='The output CPP file')
    res_file = File(desc='The output resampled image')
    invcpp_file = File(desc='The output inverse CPP file')
    invres_file = File(desc='The output inverse res file')
    desc = 'Output string in the format for reg_average'
    avg_output = traits.String(desc=desc)


class RegF3D(NiftyRegCommand):
    """Interface for executable reg_f3d from NiftyReg platform.

    Fast Free-Form Deformation (F3D) algorithm for non-rigid registration.
    Initially based on Modat et al., "Fast Free-Form Deformation using
    graphics processing units", CMPB, 2010

    `Source code <https://cmiclab.cs.ucl.ac.uk/mmodat/niftyreg>`_

    Examples
    --------
    >>> from nipype.interfaces import niftyreg
    >>> node = niftyreg.RegF3D()
    >>> node.inputs.ref_file = 'im1.nii'
    >>> node.inputs.flo_file = 'im2.nii'
    >>> node.inputs.rmask_file = 'mask.nii'
    >>> node.inputs.omp_core_val = 4
    >>> node.cmdline
    'reg_f3d -cpp im2_cpp.nii.gz -flo im2.nii -omp 4 -ref im1.nii \
-res im2_res.nii.gz -rmask mask.nii'

    """
    _cmd = get_custom_path('reg_f3d')
    input_spec = RegF3DInputSpec
    output_spec = RegF3DOutputSpec

    @staticmethod
    def _remove_extension(in_file):
        dn, bn, _ = split_filename(in_file)
        return os.path.join(dn, bn)

    def _list_outputs(self):
        outputs = super(RegF3D, self)._list_outputs()

        if self.inputs.vel_flag is True:
            res_name = self._remove_extension(outputs['res_file'])
            cpp_name = self._remove_extension(outputs['cpp_file'])
            outputs['invres_file'] = '%s_backward.nii.gz' % res_name
            outputs['invcpp_file'] = '%s_backward.nii.gz' % cpp_name

        # Make a list of the linear transformation file and the input image
        if self.inputs.vel_flag is True and isdefined(self.inputs.aff_file):
            cpp_file = os.path.abspath(outputs['cpp_file'])
            flo_file = os.path.abspath(self.inputs.flo_file)
            outputs['avg_output'] = '%s %s %s' % (self.inputs.aff_file,
                                                  cpp_file, flo_file)
        else:
            cpp_file = os.path.abspath(outputs['cpp_file'])
            flo_file = os.path.abspath(self.inputs.flo_file)
            outputs['avg_output'] = '%s %s' % (cpp_file, flo_file)

        return outputs
