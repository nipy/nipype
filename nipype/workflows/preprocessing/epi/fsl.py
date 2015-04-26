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


def all_dmri(name='fsl_all_correct',
             epi_params=dict(echospacing=0.77e-3,
                             acc_factor=3,
                             enc_dir='y-'),
             altepi_params=dict(echospacing=0.77e-3,
                                acc_factor=3,
                                enc_dir='y')):
    """
    Workflow that integrates FSL ``topup`` and ``eddy``.


    .. warning:: this workflow rotates the gradients table (*b*-vectors)
      [Leemans09]_.


    .. warning:: this workflow does not perform jacobian modulation of each
      *DWI* [Jones10]_.


    Examples
    --------

    >>> from nipype.workflows.dmri.fsl.artifacts import all_fsl_pipeline
    >>> allcorr = all_fsl_pipeline()
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

    def _gen_index(in_file):
        import numpy as np
        import nibabel as nb
        import os
        out_file = os.path.abspath('index.txt')
        vols = nb.load(in_file).get_data().shape[-1]
        np.savetxt(out_file, np.ones((vols,)).T)
        return out_file

    avg_b0_0 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_pre')
    bet_dwi0 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_pre')

    sdc = sdc_peb(epi_params=epi_params, altepi_params=altepi_params)
    ecc = pe.Node(fsl.Eddy(method='jac'), name='fsl_eddy')
    rot_bvec = pe.Node(niu.Function(
        input_names=['in_bvec', 'eddy_params'], output_names=['out_file'],
        function=eddy_rotate_bvecs), name='Rotate_Bvec')
    avg_b0_1 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_post')
    bet_dwi1 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_post')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode,   avg_b0_0,   [('in_file', 'in_dwi'),
                                   ('in_bval', 'in_bval')]),
        (avg_b0_0,    bet_dwi0,   [('out_file', 'in_file')]),
        (bet_dwi0,    sdc,        [('mask_file', 'inputnode.in_mask')]),
        (inputnode,   sdc,        [('in_file', 'inputnode.in_file'),
                                   ('alt_file', 'inputnode.alt_file'),
                                   ('in_bval', 'inputnode.in_bval')]),
        (sdc,         ecc,        [('topup.out_enc_file', 'in_acqp'),
                                   ('topup.out_fieldcoef',
                                    'in_topup_fieldcoef'),
                                   ('topup.out_movpar', 'in_topup_movpar')]),
        (bet_dwi0,    ecc,        [('mask_file', 'in_mask')]),
        (inputnode,   ecc,        [('in_file', 'in_file'),
                                   (('in_file', _gen_index), 'in_index'),
                                   ('in_bval', 'in_bval'),
                                   ('in_bvec', 'in_bvec')]),
        (inputnode,   rot_bvec,   [('in_bvec', 'in_bvec')]),
        (ecc,         rot_bvec,   [('out_parameter', 'eddy_params')]),
        (ecc,         avg_b0_1,   [('out_corrected', 'in_dwi')]),
        (inputnode,   avg_b0_1,   [('in_bval', 'in_bval')]),
        (avg_b0_1,    bet_dwi1,   [('out_file', 'in_file')]),
        (ecc,         outputnode, [('out_corrected', 'out_file')]),
        (rot_bvec,    outputnode, [('out_file', 'out_bvec')]),
        (bet_dwi1,    outputnode, [('mask_file', 'out_mask')])
    ])
    return wf