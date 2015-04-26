# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nipype.pipeline.engine as pe
from nipype.interfaces.io import JSONFileGrabber
from nipype.interfaces import utility as niu
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import ants
from nipype.interfaces import fsl
from .utils import *

def all_fmb_pipeline(name='hmc_sdc_ecc', fugue_params=dict(smooth3d=2.0)):
    """
    Builds a pipeline including three artifact corrections: head-motion
    correction (HMC), susceptibility-derived distortion correction (SDC),
    and Eddy currents-derived distortion correction (ECC).

    The displacement fields from each kind of distortions are combined. Thus,
    only one interpolation occurs between input data and result.

    .. warning:: this workflow rotates the gradients table (*b*-vectors)
      [Leemans09]_.


    Examples
    --------

    >>> from nipype.workflows.dmri.fsl.artifacts import all_fmb_pipeline
    >>> allcorr = all_fmb_pipeline()
    >>> allcorr.inputs.inputnode.in_file = 'epi.nii'
    >>> allcorr.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> allcorr.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> allcorr.inputs.inputnode.bmap_mag = 'magnitude.nii'
    >>> allcorr.inputs.inputnode.bmap_pha = 'phase.nii'
    >>> allcorr.inputs.inputnode.epi_param = 'epi_param.txt'
    >>> allcorr.run() # doctest: +SKIP

    """
    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bvec', 'in_bval', 'bmap_pha', 'bmap_mag',
                'epi_param']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_mask', 'out_bvec']), name='outputnode')

    list_b0 = pe.Node(niu.Function(
        input_names=['in_bval'], output_names=['out_idx'],
        function=b0_indices), name='B0indices')

    avg_b0_0 = pe.Node(niu.Function(
        input_names=['in_file', 'index'], output_names=['out_file'],
        function=time_avg), name='b0_avg_pre')
    avg_b0_1 = pe.Node(niu.Function(
        input_names=['in_file', 'index'], output_names=['out_file'],
        function=time_avg), name='b0_avg_post')

    bet_dwi0 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_pre')
    bet_dwi1 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_post')

    hmc = hmc_pipeline()
    sdc = sdc_fmb(fugue_params=fugue_params)
    ecc = ecc_pipeline()
    unwarp = apply_all_corrections()

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, hmc,        [('in_file', 'inputnode.in_file'),
                                 ('in_bvec', 'inputnode.in_bvec'),
                                 ('in_bval', 'inputnode.in_bval')]),
        (inputnode, list_b0,    [('in_bval', 'in_bval')]),
        (inputnode, avg_b0_0,   [('in_file', 'in_file')]),
        (list_b0,   avg_b0_0,   [('out_idx', 'index')]),
        (avg_b0_0,  bet_dwi0,   [('out_file', 'in_file')]),
        (bet_dwi0,  hmc,        [('mask_file', 'inputnode.in_mask')]),
        (hmc,       sdc,        [
         ('outputnode.out_file', 'inputnode.in_file')]),
        (bet_dwi0,  sdc,        [('mask_file', 'inputnode.in_mask')]),
        (inputnode, sdc,        [('bmap_pha', 'inputnode.bmap_pha'),
                                 ('bmap_mag', 'inputnode.bmap_mag'),
                                 ('epi_param', 'inputnode.settings')]),
        (list_b0,   sdc,        [('out_idx', 'inputnode.in_ref')]),
        (hmc,       ecc,        [
         ('outputnode.out_xfms', 'inputnode.in_xfms')]),
        (inputnode, ecc,        [('in_file', 'inputnode.in_file'),
                                 ('in_bval', 'inputnode.in_bval')]),
        (bet_dwi0,  ecc,        [('mask_file', 'inputnode.in_mask')]),
        (ecc,       avg_b0_1,   [('outputnode.out_file', 'in_file')]),
        (list_b0,   avg_b0_1,   [('out_idx', 'index')]),
        (avg_b0_1,  bet_dwi1,   [('out_file', 'in_file')]),
        (inputnode, unwarp,     [('in_file', 'inputnode.in_dwi')]),
        (hmc,       unwarp,     [('outputnode.out_xfms', 'inputnode.in_hmc')]),
        (ecc,       unwarp,     [('outputnode.out_xfms', 'inputnode.in_ecc')]),
        (sdc,       unwarp,     [('outputnode.out_warp', 'inputnode.in_sdc')]),
        (hmc,       outputnode, [('outputnode.out_bvec', 'out_bvec')]),
        (unwarp,    outputnode, [('outputnode.out_file', 'out_file')]),
        (bet_dwi1,  outputnode, [('mask_file', 'out_mask')])
    ])
    return wf


def all_peb_pipeline(name='hmc_sdc_ecc',
                     epi_params=dict(echospacing=0.77e-3,
                                     acc_factor=3,
                                     enc_dir='y-',
                                     epi_factor=1),
                     altepi_params=dict(echospacing=0.77e-3,
                                        acc_factor=3,
                                        enc_dir='y',
                                        epi_factor=1)):
    """
    Builds a pipeline including three artifact corrections: head-motion
    correction (HMC), susceptibility-derived distortion correction (SDC),
    and Eddy currents-derived distortion correction (ECC).

    .. warning:: this workflow rotates the gradients table (*b*-vectors)
      [Leemans09]_.


    Examples
    --------

    >>> from nipype.workflows.dmri.fsl.artifacts import all_peb_pipeline
    >>> allcorr = all_peb_pipeline()
    >>> allcorr.inputs.inputnode.in_file = 'epi.nii'
    >>> allcorr.inputs.inputnode.alt_file = 'epi_rev.nii'
    >>> allcorr.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> allcorr.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> allcorr.run() # doctest: +SKIP

    """
    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bvec', 'in_bval', 'alt_file']),
        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_mask', 'out_bvec']), name='outputnode')

    avg_b0_0 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_pre')
    avg_b0_1 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_post')
    bet_dwi0 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_pre')
    bet_dwi1 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_post')

    hmc = hmc_pipeline()
    sdc = sdc_peb(epi_params=epi_params, altepi_params=altepi_params)
    ecc = ecc_pipeline()

    unwarp = apply_all_corrections()

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, hmc,        [('in_file', 'inputnode.in_file'),
                                 ('in_bvec', 'inputnode.in_bvec'),
                                 ('in_bval', 'inputnode.in_bval')]),
        (inputnode, avg_b0_0,   [('in_file', 'in_dwi'),
                                 ('in_bval', 'in_bval')]),
        (avg_b0_0,  bet_dwi0,   [('out_file', 'in_file')]),
        (bet_dwi0,  hmc,        [('mask_file', 'inputnode.in_mask')]),
        (hmc,       sdc,        [
         ('outputnode.out_file', 'inputnode.in_file')]),
        (bet_dwi0,  sdc,        [('mask_file', 'inputnode.in_mask')]),
        (inputnode, sdc,        [('in_bval', 'inputnode.in_bval'),
                                 ('alt_file', 'inputnode.alt_file')]),
        (inputnode, ecc,        [('in_file', 'inputnode.in_file'),
                                 ('in_bval', 'inputnode.in_bval')]),
        (bet_dwi0,  ecc,        [('mask_file', 'inputnode.in_mask')]),
        (hmc,       ecc,        [
         ('outputnode.out_xfms', 'inputnode.in_xfms')]),
        (ecc,       avg_b0_1,   [('outputnode.out_file', 'in_dwi')]),
        (inputnode, avg_b0_1,   [('in_bval', 'in_bval')]),
        (avg_b0_1,  bet_dwi1,   [('out_file', 'in_file')]),
        (inputnode, unwarp,     [('in_file', 'inputnode.in_dwi')]),
        (hmc,       unwarp,     [('outputnode.out_xfms', 'inputnode.in_hmc')]),
        (ecc,       unwarp,     [('outputnode.out_xfms', 'inputnode.in_ecc')]),
        (sdc,       unwarp,     [('outputnode.out_warp', 'inputnode.in_sdc')]),
        (hmc,       outputnode, [('outputnode.out_bvec', 'out_bvec')]),
        (unwarp,    outputnode, [('outputnode.out_file', 'out_file')]),
        (bet_dwi1,  outputnode, [('mask_file', 'out_mask')])
    ])
    return wf
