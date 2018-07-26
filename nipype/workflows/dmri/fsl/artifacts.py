# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ....interfaces.io import JSONFileGrabber
from ....interfaces import utility as niu
from ....interfaces import ants
from ....interfaces import fsl
from ....pipeline import engine as pe
from ...data import get_flirt_schedule

from .utils import (
    b0_indices,
    time_avg,
    apply_all_corrections,
    b0_average,
    hmc_split,
    dwi_flirt,
    eddy_rotate_bvecs,
    rotate_bvecs,
    insert_mat,
    extract_bval,
    recompose_dwi,
    recompose_xfm,
    siemens2rads,
    rads2radsec,
    demean_image,
    cleanup_edge_pipeline,
    add_empty_vol,
    vsm2warp,
    compute_readout,
)


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
    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file', 'in_bvec', 'in_bval', 'bmap_pha', 'bmap_mag',
            'epi_param'
        ]),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_mask', 'out_bvec']),
        name='outputnode')

    list_b0 = pe.Node(
        niu.Function(
            input_names=['in_bval'],
            output_names=['out_idx'],
            function=b0_indices),
        name='B0indices')

    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=['in_file', 'index'],
            output_names=['out_file'],
            function=time_avg),
        name='b0_avg_pre')
    avg_b0_1 = pe.Node(
        niu.Function(
            input_names=['in_file', 'index'],
            output_names=['out_file'],
            function=time_avg),
        name='b0_avg_post')

    bet_dwi0 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_pre')
    bet_dwi1 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_post')

    hmc = hmc_pipeline()
    sdc = sdc_fmb(fugue_params=fugue_params)
    ecc = ecc_pipeline()
    unwarp = apply_all_corrections()

    wf = pe.Workflow(name=name)
    wf.connect(
        [(inputnode, hmc,
          [('in_file', 'inputnode.in_file'), ('in_bvec', 'inputnode.in_bvec'),
           ('in_bval', 'inputnode.in_bval')]), (inputnode, list_b0,
                                                [('in_bval', 'in_bval')]),
         (inputnode, avg_b0_0, [('in_file', 'in_file')]), (list_b0, avg_b0_0,
                                                           [('out_idx',
                                                             'index')]),
         (avg_b0_0, bet_dwi0, [('out_file', 'in_file')]), (bet_dwi0, hmc, [
             ('mask_file', 'inputnode.in_mask')
         ]), (hmc, sdc, [('outputnode.out_file', 'inputnode.in_file')]),
         (bet_dwi0, sdc,
          [('mask_file', 'inputnode.in_mask')]), (inputnode, sdc, [
              ('bmap_pha', 'inputnode.bmap_pha'),
              ('bmap_mag', 'inputnode.bmap_mag'), ('epi_param',
                                                   'inputnode.settings')
          ]), (list_b0, sdc, [('out_idx', 'inputnode.in_ref')]), (hmc, ecc, [
              ('outputnode.out_xfms', 'inputnode.in_xfms')
          ]), (inputnode, ecc,
               [('in_file', 'inputnode.in_file'),
                ('in_bval', 'inputnode.in_bval')]), (bet_dwi0, ecc, [
                    ('mask_file', 'inputnode.in_mask')
                ]), (ecc, avg_b0_1, [('outputnode.out_file',
                                      'in_file')]), (list_b0, avg_b0_1,
                                                     [('out_idx', 'index')]),
         (avg_b0_1, bet_dwi1, [('out_file', 'in_file')]), (inputnode, unwarp, [
             ('in_file', 'inputnode.in_dwi')
         ]), (hmc, unwarp,
              [('outputnode.out_xfms', 'inputnode.in_hmc')]), (ecc, unwarp, [
                  ('outputnode.out_xfms', 'inputnode.in_ecc')
              ]), (sdc, unwarp, [('outputnode.out_warp',
                                  'inputnode.in_sdc')]), (hmc, outputnode, [
                                      ('outputnode.out_bvec', 'out_bvec')
                                  ]), (unwarp, outputnode,
                                       [('outputnode.out_file',
                                         'out_file')]), (bet_dwi1, outputnode,
                                                         [('mask_file',
                                                           'out_mask')])])
    return wf


def all_peb_pipeline(name='hmc_sdc_ecc',
                     epi_params=dict(
                         echospacing=0.77e-3,
                         acc_factor=3,
                         enc_dir='y-',
                         epi_factor=1),
                     altepi_params=dict(
                         echospacing=0.77e-3,
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
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_file', 'in_bvec', 'in_bval', 'alt_file']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_mask', 'out_bvec']),
        name='outputnode')

    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg_pre')
    avg_b0_1 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg_post')
    bet_dwi0 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_pre')
    bet_dwi1 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_post')

    hmc = hmc_pipeline()
    sdc = sdc_peb(epi_params=epi_params, altepi_params=altepi_params)
    ecc = ecc_pipeline()

    unwarp = apply_all_corrections()

    wf = pe.Workflow(name=name)
    wf.connect(
        [(inputnode, hmc,
          [('in_file', 'inputnode.in_file'), ('in_bvec', 'inputnode.in_bvec'),
           ('in_bval', 'inputnode.in_bval')]), (inputnode, avg_b0_0,
                                                [('in_file', 'in_dwi'),
                                                 ('in_bval', 'in_bval')]),
         (avg_b0_0, bet_dwi0, [('out_file', 'in_file')]), (bet_dwi0, hmc, [
             ('mask_file', 'inputnode.in_mask')
         ]), (hmc, sdc, [('outputnode.out_file', 'inputnode.in_file')]),
         (bet_dwi0, sdc,
          [('mask_file', 'inputnode.in_mask')]), (inputnode, sdc, [
              ('in_bval', 'inputnode.in_bval'), ('alt_file',
                                                 'inputnode.alt_file')
          ]), (inputnode, ecc, [('in_file', 'inputnode.in_file'),
                                ('in_bval', 'inputnode.in_bval')]),
         (bet_dwi0, ecc, [('mask_file', 'inputnode.in_mask')]), (hmc, ecc, [
             ('outputnode.out_xfms', 'inputnode.in_xfms')
         ]), (ecc, avg_b0_1, [('outputnode.out_file',
                               'in_dwi')]), (inputnode, avg_b0_1,
                                             [('in_bval', 'in_bval')]),
         (avg_b0_1, bet_dwi1, [('out_file', 'in_file')]), (inputnode, unwarp, [
             ('in_file', 'inputnode.in_dwi')
         ]), (hmc, unwarp,
              [('outputnode.out_xfms', 'inputnode.in_hmc')]), (ecc, unwarp, [
                  ('outputnode.out_xfms', 'inputnode.in_ecc')
              ]), (sdc, unwarp, [('outputnode.out_warp',
                                  'inputnode.in_sdc')]), (hmc, outputnode, [
                                      ('outputnode.out_bvec', 'out_bvec')
                                  ]), (unwarp, outputnode,
                                       [('outputnode.out_file',
                                         'out_file')]), (bet_dwi1, outputnode,
                                                         [('mask_file',
                                                           'out_mask')])])
    return wf


def all_fsl_pipeline(name='fsl_all_correct',
                     epi_params=dict(
                         echospacing=0.77e-3, acc_factor=3, enc_dir='y-'),
                     altepi_params=dict(
                         echospacing=0.77e-3, acc_factor=3, enc_dir='y')):
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

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_file', 'in_bvec', 'in_bval', 'alt_file']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_mask', 'out_bvec']),
        name='outputnode')

    def gen_index(in_file):
        import numpy as np
        import nibabel as nb
        import os
        from nipype.utils import NUMPY_MMAP
        out_file = os.path.abspath('index.txt')
        vols = nb.load(in_file, mmap=NUMPY_MMAP).get_data().shape[-1]
        np.savetxt(out_file, np.ones((vols, )).T)
        return out_file

    gen_idx = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=gen_index),
        name='gen_index')
    avg_b0_0 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg_pre')
    bet_dwi0 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_pre')

    sdc = sdc_peb(epi_params=epi_params, altepi_params=altepi_params)
    ecc = pe.Node(fsl.Eddy(method='jac'), name='fsl_eddy')
    rot_bvec = pe.Node(
        niu.Function(
            input_names=['in_bvec', 'eddy_params'],
            output_names=['out_file'],
            function=eddy_rotate_bvecs),
        name='Rotate_Bvec')
    avg_b0_1 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg_post')
    bet_dwi1 = pe.Node(
        fsl.BET(frac=0.3, mask=True, robust=True), name='bet_dwi_post')

    wf = pe.Workflow(name=name)
    wf.connect(
        [(inputnode, avg_b0_0, [('in_file', 'in_dwi'), ('in_bval',
                                                        'in_bval')]),
         (avg_b0_0, bet_dwi0, [('out_file', 'in_file')]), (bet_dwi0, sdc, [
             ('mask_file', 'inputnode.in_mask')
         ]), (inputnode, sdc, [('in_file', 'inputnode.in_file'),
                               ('alt_file', 'inputnode.alt_file'),
                               ('in_bval', 'inputnode.in_bval')]),
         (sdc, ecc, [('topup.out_enc_file', 'in_acqp'),
                     ('topup.out_fieldcoef', 'in_topup_fieldcoef'),
                     ('topup.out_movpar',
                      'in_topup_movpar')]), (bet_dwi0, ecc, [('mask_file',
                                                              'in_mask')]),
         (inputnode, gen_idx, [('in_file', 'in_file')]), (inputnode, ecc, [
             ('in_file', 'in_file'), ('in_bval', 'in_bval'), ('in_bvec',
                                                              'in_bvec')
         ]), (gen_idx, ecc,
              [('out_file', 'in_index')]), (inputnode, rot_bvec, [
                  ('in_bvec', 'in_bvec')
              ]), (ecc, rot_bvec,
                   [('out_parameter', 'eddy_params')]), (ecc, avg_b0_1, [
                       ('out_corrected', 'in_dwi')
                   ]), (inputnode, avg_b0_1, [('in_bval', 'in_bval')]),
         (avg_b0_1, bet_dwi1, [('out_file', 'in_file')]), (ecc, outputnode, [
             ('out_corrected', 'out_file')
         ]), (rot_bvec, outputnode,
              [('out_file', 'out_bvec')]), (bet_dwi1, outputnode,
                                            [('mask_file', 'out_mask')])])
    return wf


def hmc_pipeline(name='motion_correct'):
    """
    HMC stands for head-motion correction.

    Creates a pipeline that corrects for head motion artifacts in dMRI
    sequences.
    It takes a series of diffusion weighted images and rigidly co-registers
    them to one reference image. Finally, the `b`-matrix is rotated accordingly
    [Leemans09]_ making use of the rotation matrix obtained by FLIRT.

    Search angles have been limited to 4 degrees, based on results in
    [Yendiki13]_.

    A list of rigid transformation matrices is provided, so that transforms
    can be chained.
    This is useful to correct for artifacts with only one interpolation process
    (as previously discussed `here
    <https://github.com/nipy/nipype/pull/530#issuecomment-14505042>`_),
    and also to compute nuisance regressors as proposed by [Yendiki13]_.

    .. warning:: This workflow rotates the `b`-vectors, so please be advised
      that not all the dicom converters ensure the consistency between the
      resulting nifti orientation and the gradients table (e.g. dcm2nii
      checks it).

    .. admonition:: References

      .. [Leemans09] Leemans A, and Jones DK, `The B-matrix must be rotated
        when correcting for subject motion in DTI data
        <http://dx.doi.org/10.1002/mrm.21890>`_,
        Magn Reson Med. 61(6):1336-49. 2009. doi: 10.1002/mrm.21890.

      .. [Yendiki13] Yendiki A et al., `Spurious group differences due to head
        motion in a diffusion MRI study
        <http://dx.doi.org/10.1016/j.neuroimage.2013.11.027>`_.
        Neuroimage. 21(88C):79-90. 2013. doi: 10.1016/j.neuroimage.2013.11.027

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import hmc_pipeline
    >>> hmc = hmc_pipeline()
    >>> hmc.inputs.inputnode.in_file = 'diffusion.nii'
    >>> hmc.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> hmc.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> hmc.inputs.inputnode.in_mask = 'mask.nii'
    >>> hmc.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - input dwi file
        inputnode.in_mask - weights mask of reference image (a file with data \
range in [0.0, 1.0], indicating the weight of each voxel when computing the \
metric.
        inputnode.in_bval - b-values file
        inputnode.in_bvec - gradients file (b-vectors)
        inputnode.ref_num (optional, default=0) index of the b0 volume that \
should be taken as reference

    Outputs::

        outputnode.out_file - corrected dwi file
        outputnode.out_bvec - rotated gradient vectors table
        outputnode.out_xfms - list of transformation matrices

    """
    params = dict(
        dof=6,
        bgvalue=0,
        save_log=True,
        no_search=True,
        # cost='mutualinfo', cost_func='mutualinfo', bins=64,
        schedule=get_flirt_schedule('hmc'))

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_file', 'ref_num', 'in_bvec', 'in_bval', 'in_mask']),
        name='inputnode')
    split = pe.Node(
        niu.Function(
            output_names=['out_ref', 'out_mov', 'out_bval', 'volid'],
            input_names=['in_file', 'in_bval', 'ref_num'],
            function=hmc_split),
        name='SplitDWI')
    flirt = dwi_flirt(flirt_param=params)
    insmat = pe.Node(
        niu.Function(
            input_names=['inlist', 'volid'],
            output_names=['out'],
            function=insert_mat),
        name='InsertRefmat')
    rot_bvec = pe.Node(
        niu.Function(
            function=rotate_bvecs,
            input_names=['in_bvec', 'in_matrix'],
            output_names=['out_file']),
        name='Rotate_Bvec')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_bvec', 'out_xfms']),
        name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([(inputnode, split,
                 [('in_file', 'in_file'), ('in_bval', 'in_bval'),
                  ('ref_num', 'ref_num')]), (inputnode, flirt, [
                      ('in_mask', 'inputnode.ref_mask')
                  ]), (split, flirt, [('out_ref', 'inputnode.reference'),
                                      ('out_mov', 'inputnode.in_file'),
                                      ('out_bval', 'inputnode.in_bval')]),
                (flirt, insmat, [('outputnode.out_xfms', 'inlist')]),
                (split, insmat, [('volid', 'volid')]), (inputnode, rot_bvec, [
                    ('in_bvec', 'in_bvec')
                ]), (insmat, rot_bvec,
                     [('out', 'in_matrix')]), (rot_bvec, outputnode,
                                               [('out_file', 'out_bvec')]),
                (flirt, outputnode, [('outputnode.out_file',
                                      'out_file')]), (insmat, outputnode,
                                                      [('out', 'out_xfms')])])
    return wf


def ecc_pipeline(name='eddy_correct'):
    """
    ECC stands for Eddy currents correction.

    Creates a pipeline that corrects for artifacts induced by Eddy currents in
    dMRI sequences.
    It takes a series of diffusion weighted images and linearly co-registers
    them to one reference image (the average of all b0s in the dataset).

    DWIs are also modulated by the determinant of the Jacobian as indicated by
    [Jones10]_ and [Rohde04]_.

    A list of rigid transformation matrices can be provided, sourcing from a
    :func:`.hmc_pipeline` workflow, to initialize registrations in a *motion
    free* framework.

    A list of affine transformation matrices is available as output, so that
    transforms can be chained (discussion
    `here <https://github.com/nipy/nipype/pull/530#issuecomment-14505042>`_).

    .. admonition:: References

      .. [Jones10] Jones DK, `The signal intensity must be modulated by the
        determinant of the Jacobian when correcting for eddy currents in
        diffusion MRI
        <http://cds.ismrm.org/protected/10MProceedings/files/1644_129.pdf>`_,
        Proc. ISMRM 18th Annual Meeting, (2010).

      .. [Rohde04] Rohde et al., `Comprehensive Approach for Correction of
        Motion and Distortion in Diffusion-Weighted MRI
        <http://stbb.nichd.nih.gov/pdf/com_app_cor_mri04.pdf>`_, MRM
        51:103-114 (2004).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import ecc_pipeline
    >>> ecc = ecc_pipeline()
    >>> ecc.inputs.inputnode.in_file = 'diffusion.nii'
    >>> ecc.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> ecc.inputs.inputnode.in_mask = 'mask.nii'
    >>> ecc.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - input dwi file
        inputnode.in_mask - weights mask of reference image (a file with data \
range sin [0.0, 1.0], indicating the weight of each voxel when computing the \
metric.
        inputnode.in_bval - b-values table
        inputnode.in_xfms - list of matrices to initialize registration (from \
head-motion correction)

    Outputs::

        outputnode.out_file - corrected dwi file
        outputnode.out_xfms - list of transformation matrices
    """

    params = dict(
        dof=12,
        no_search=True,
        interp='spline',
        bgvalue=0,
        schedule=get_flirt_schedule('ecc'))
    # cost='normmi', cost_func='normmi', bins=64,

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_file', 'in_bval', 'in_mask', 'in_xfms']),
        name='inputnode')
    avg_b0 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg')
    pick_dws = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval', 'b'],
            output_names=['out_file'],
            function=extract_bval),
        name='ExtractDWI')
    pick_dws.inputs.b = 'diff'

    flirt = dwi_flirt(flirt_param=params, excl_nodiff=True)

    mult = pe.MapNode(
        fsl.BinaryMaths(operation='mul'),
        name='ModulateDWIs',
        iterfield=['in_file', 'operand_value'])
    thres = pe.MapNode(
        fsl.Threshold(thresh=0.0),
        iterfield=['in_file'],
        name='RemoveNegative')

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    get_mat = pe.Node(
        niu.Function(
            input_names=['in_bval', 'in_xfms'],
            output_names=['out_files'],
            function=recompose_xfm),
        name='GatherMatrices')
    merge = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval', 'in_corrected'],
            output_names=['out_file'],
            function=recompose_dwi),
        name='MergeDWIs')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_xfms']),
        name='outputnode')

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, avg_b0, [('in_file', 'in_dwi'), ('in_bval', 'in_bval')]),
        (inputnode, pick_dws, [('in_file', 'in_dwi'), ('in_bval', 'in_bval')]),
        (inputnode, merge,
         [('in_file', 'in_dwi'), ('in_bval', 'in_bval')]), (inputnode, flirt, [
             ('in_mask', 'inputnode.ref_mask'),
             ('in_xfms', 'inputnode.in_xfms'), ('in_bval', 'inputnode.in_bval')
         ]), (inputnode, get_mat, [('in_bval', 'in_bval')]), (avg_b0, flirt, [
             ('out_file', 'inputnode.reference')
         ]), (pick_dws, flirt, [('out_file', 'inputnode.in_file')]),
        (flirt, get_mat, [('outputnode.out_xfms', 'in_xfms')]), (flirt, mult, [
            (('outputnode.out_xfms', _xfm_jacobian), 'operand_value')
        ]), (flirt, split,
             [('outputnode.out_file', 'in_file')]), (split, mult, [
                 ('out_files', 'in_file')
             ]), (mult, thres, [('out_file', 'in_file')]), (thres, merge, [
                 ('out_file', 'in_corrected')
             ]), (get_mat, outputnode,
                  [('out_files', 'out_xfms')]), (merge, outputnode,
                                                 [('out_file', 'out_file')])
    ])
    return wf


def sdc_fmb(name='fmb_correction',
            interp='Linear',
            fugue_params=dict(smooth3d=2.0)):
    """
    SDC stands for susceptibility distortion correction. FMB stands for
    fieldmap-based.

    The fieldmap based (FMB) method implements SDC by using a mapping of the
    B0 field as proposed by [Jezzard95]_. This workflow uses the implementation
    of FSL (`FUGUE <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FUGUE>`_). Phase
    unwrapping is performed using `PRELUDE
    <http://fsl.fmrib.ox.ac.uk/fsl/fsl-4.1.9/fugue/prelude.html>`_
    [Jenkinson03]_. Preparation of the fieldmap is performed reproducing the
    script in FSL `fsl_prepare_fieldmap
    <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FUGUE/Guide#SIEMENS_data>`_.



    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import sdc_fmb
    >>> fmb = sdc_fmb()
    >>> fmb.inputs.inputnode.in_file = 'diffusion.nii'
    >>> fmb.inputs.inputnode.in_ref = list(range(0, 30, 6))
    >>> fmb.inputs.inputnode.in_mask = 'mask.nii'
    >>> fmb.inputs.inputnode.bmap_mag = 'magnitude.nii'
    >>> fmb.inputs.inputnode.bmap_pha = 'phase.nii'
    >>> fmb.inputs.inputnode.settings = 'epi_param.txt'
    >>> fmb.run() # doctest: +SKIP

    .. warning:: Only SIEMENS format fieldmaps are supported.

    .. admonition:: References

      .. [Jezzard95] Jezzard P, and Balaban RS, `Correction for geometric
        distortion in echo planar images from B0 field variations
        <http://dx.doi.org/10.1002/mrm.1910340111>`_,
        MRM 34(1):65-73. (1995). doi: 10.1002/mrm.1910340111.

      .. [Jenkinson03] Jenkinson M., `Fast, automated, N-dimensional
        phase-unwrapping algorithm <http://dx.doi.org/10.1002/mrm.10354>`_,
        MRM 49(1):193-197, 2003, doi: 10.1002/mrm.10354.

    """

    epi_defaults = {
        'delta_te': 2.46e-3,
        'echospacing': 0.77e-3,
        'acc_factor': 2,
        'enc_dir': u'AP'
    }

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file', 'in_ref', 'in_mask', 'bmap_pha', 'bmap_mag', 'settings'
        ]),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_vsm', 'out_warp']),
        name='outputnode')

    r_params = pe.Node(
        JSONFileGrabber(defaults=epi_defaults), name='SettingsGrabber')
    eff_echo = pe.Node(
        niu.Function(
            function=_eff_t_echo,
            input_names=['echospacing', 'acc_factor'],
            output_names=['eff_echo']),
        name='EffEcho')

    firstmag = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name='GetFirst')
    n4 = pe.Node(ants.N4BiasFieldCorrection(dimension=3), name='Bias')
    bet = pe.Node(fsl.BET(frac=0.4, mask=True), name='BrainExtraction')
    dilate = pe.Node(
        fsl.maths.MathsCommand(nan2zeros=True, args='-kernel sphere 5 -dilM'),
        name='MskDilate')
    pha2rads = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=siemens2rads),
        name='PreparePhase')
    prelude = pe.Node(fsl.PRELUDE(process3d=True), name='PhaseUnwrap')
    rad2rsec = pe.Node(
        niu.Function(
            input_names=['in_file', 'delta_te'],
            output_names=['out_file'],
            function=rads2radsec),
        name='ToRadSec')

    baseline = pe.Node(
        niu.Function(
            input_names=['in_file', 'index'],
            output_names=['out_file'],
            function=time_avg),
        name='Baseline')

    fmm2b0 = pe.Node(
        ants.Registration(output_warped_image=True), name="FMm_to_B0")
    fmm2b0.inputs.transforms = ['Rigid'] * 2
    fmm2b0.inputs.transform_parameters = [(1.0, )] * 2
    fmm2b0.inputs.number_of_iterations = [[50], [20]]
    fmm2b0.inputs.dimension = 3
    fmm2b0.inputs.metric = ['Mattes', 'Mattes']
    fmm2b0.inputs.metric_weight = [1.0] * 2
    fmm2b0.inputs.radius_or_number_of_bins = [64, 64]
    fmm2b0.inputs.sampling_strategy = ['Regular', 'Random']
    fmm2b0.inputs.sampling_percentage = [None, 0.2]
    fmm2b0.inputs.convergence_threshold = [1.e-5, 1.e-8]
    fmm2b0.inputs.convergence_window_size = [20, 10]
    fmm2b0.inputs.smoothing_sigmas = [[6.0], [2.0]]
    fmm2b0.inputs.sigma_units = ['vox'] * 2
    fmm2b0.inputs.shrink_factors = [[6], [1]]  # ,[1] ]
    fmm2b0.inputs.use_estimate_learning_rate_once = [True] * 2
    fmm2b0.inputs.use_histogram_matching = [True] * 2
    fmm2b0.inputs.initial_moving_transform_com = 0
    fmm2b0.inputs.collapse_output_transforms = True
    fmm2b0.inputs.winsorize_upper_quantile = 0.995

    applyxfm = pe.Node(
        ants.ApplyTransforms(dimension=3, interpolation=interp),
        name='FMp_to_B0')

    pre_fugue = pe.Node(fsl.FUGUE(save_fmap=True), name='PreliminaryFugue')
    demean = pe.Node(
        niu.Function(
            input_names=['in_file', 'in_mask'],
            output_names=['out_file'],
            function=demean_image),
        name='DemeanFmap')

    cleanup = cleanup_edge_pipeline()

    addvol = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=add_empty_vol),
        name='AddEmptyVol')

    vsm = pe.Node(
        fsl.FUGUE(save_shift=True, **fugue_params), name="ComputeVSM")

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    merge = pe.Node(fsl.Merge(dimension='t'), name='MergeDWIs')
    unwarp = pe.MapNode(
        fsl.FUGUE(icorr=True, forward_warping=False),
        iterfield=['in_file'],
        name='UnwarpDWIs')
    thres = pe.MapNode(
        fsl.Threshold(thresh=0.0),
        iterfield=['in_file'],
        name='RemoveNegative')
    vsm2dfm = vsm2warp()
    vsm2dfm.inputs.inputnode.scaling = 1.0

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, r_params,
         [('settings', 'in_file')]), (r_params, eff_echo, [
             ('echospacing', 'echospacing'), ('acc_factor', 'acc_factor')
         ]), (inputnode, pha2rads,
              [('bmap_pha', 'in_file')]), (inputnode, firstmag,
                                           [('bmap_mag', 'in_file')]),
        (inputnode, baseline,
         [('in_file', 'in_file'), ('in_ref', 'index')]), (firstmag, n4, [
             ('roi_file', 'input_image')
         ]), (n4, bet, [('output_image', 'in_file')]), (bet, dilate, [
             ('mask_file', 'in_file')
         ]), (pha2rads, prelude, [('out_file', 'phase_file')]), (n4, prelude, [
             ('output_image', 'magnitude_file')
         ]), (dilate, prelude, [('out_file', 'mask_file')]),
        (r_params, rad2rsec, [('delta_te', 'delta_te')]), (prelude, rad2rsec, [
            ('unwrapped_phase_file', 'in_file')
        ]), (baseline, fmm2b0, [('out_file', 'fixed_image')]), (n4, fmm2b0, [
            ('output_image', 'moving_image')
        ]), (inputnode, fmm2b0,
             [('in_mask', 'fixed_image_mask')]), (dilate, fmm2b0, [
                 ('out_file', 'moving_image_mask')
             ]), (baseline, applyxfm, [('out_file', 'reference_image')]),
        (rad2rsec, applyxfm,
         [('out_file', 'input_image')]), (fmm2b0, applyxfm, [
             ('forward_transforms', 'transforms'), ('forward_invert_flags',
                                                    'invert_transform_flags')
         ]), (applyxfm, pre_fugue,
              [('output_image', 'fmap_in_file')]), (inputnode, pre_fugue, [
                  ('in_mask', 'mask_file')
              ]), (pre_fugue, demean,
                   [('fmap_out_file', 'in_file')]), (inputnode, demean, [
                       ('in_mask', 'in_mask')
                   ]), (demean, cleanup, [('out_file', 'inputnode.in_file')]),
        (inputnode, cleanup,
         [('in_mask', 'inputnode.in_mask')]), (cleanup, addvol, [
             ('outputnode.out_file', 'in_file')
         ]), (inputnode, vsm, [('in_mask', 'mask_file')]), (addvol, vsm, [
             ('out_file', 'fmap_in_file')
         ]), (r_params, vsm, [('delta_te', 'asym_se_time')]), (eff_echo, vsm, [
             ('eff_echo', 'dwell_time')
         ]), (inputnode, split, [('in_file', 'in_file')]), (split, unwarp, [
             ('out_files', 'in_file')
         ]), (vsm, unwarp,
              [('shift_out_file', 'shift_in_file')]), (r_params, unwarp, [
                  (('enc_dir', _fix_enc_dir), 'unwarp_direction')
              ]), (unwarp, thres, [('unwarped_file', 'in_file')]),
        (thres, merge, [('out_file', 'in_files')]), (r_params, vsm2dfm, [
            (('enc_dir', _fix_enc_dir), 'inputnode.enc_dir')
        ]), (merge, vsm2dfm,
             [('merged_file', 'inputnode.in_ref')]), (vsm, vsm2dfm, [
                 ('shift_out_file', 'inputnode.in_vsm')
             ]), (merge, outputnode,
                  [('merged_file', 'out_file')]), (vsm, outputnode, [
                      ('shift_out_file', 'out_vsm')
                  ]), (vsm2dfm, outputnode, [('outputnode.out_warp',
                                              'out_warp')])
    ])
    return wf


def sdc_peb(name='peb_correction',
            epi_params=dict(
                echospacing=0.77e-3, acc_factor=3, enc_dir='y-', epi_factor=1),
            altepi_params=dict(
                echospacing=0.77e-3, acc_factor=3, enc_dir='y', epi_factor=1)):
    """
    SDC stands for susceptibility distortion correction. PEB stands for
    phase-encoding-based.

    The phase-encoding-based (PEB) method implements SDC by acquiring
    diffusion images with two different enconding directions [Andersson2003]_.
    The most typical case is acquiring with opposed phase-gradient blips
    (e.g. *A>>>P* and *P>>>A*, or equivalently, *-y* and *y*)
    as in [Chiou2000]_, but it is also possible to use orthogonal
    configurations [Cordes2000]_ (e.g. *A>>>P* and *L>>>R*,
    or equivalently *-y* and *x*).
    This workflow uses the implementation of FSL
    (`TOPUP <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TOPUP>`_).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import sdc_peb
    >>> peb = sdc_peb()
    >>> peb.inputs.inputnode.in_file = 'epi.nii'
    >>> peb.inputs.inputnode.alt_file = 'epi_rev.nii'
    >>> peb.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> peb.inputs.inputnode.in_mask = 'mask.nii'
    >>> peb.run() # doctest: +SKIP

    .. admonition:: References

      .. [Andersson2003] Andersson JL et al., `How to correct susceptibility
        distortions in spin-echo echo-planar images: application to diffusion
        tensor imaging <http://dx.doi.org/10.1016/S1053-8119(03)00336-7>`_.
        Neuroimage. 2003 Oct;20(2):870-88. doi: 10.1016/S1053-8119(03)00336-7

      .. [Cordes2000] Cordes D et al., Geometric distortion correction in EPI
        using two images with orthogonal phase-encoding directions, in Proc.
        ISMRM (8), p.1712, Denver, US, 2000.

      .. [Chiou2000] Chiou JY, and Nalcioglu O, A simple method to correct
        off-resonance related distortion in echo planar imaging, in Proc.
        ISMRM (8), p.1712, Denver, US, 2000.

    """

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['in_file', 'in_bval', 'in_mask', 'alt_file', 'ref_num']),
        name='inputnode')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file', 'out_vsm', 'out_warp']),
        name='outputnode')

    b0_ref = pe.Node(fsl.ExtractROI(t_size=1), name='b0_ref')
    b0_alt = pe.Node(fsl.ExtractROI(t_size=1), name='b0_alt')
    b0_comb = pe.Node(niu.Merge(2), name='b0_list')
    b0_merge = pe.Node(fsl.Merge(dimension='t'), name='b0_merged')

    topup = pe.Node(fsl.TOPUP(), name='topup')
    topup.inputs.encoding_direction = [
        epi_params['enc_dir'], altepi_params['enc_dir']
    ]

    readout = compute_readout(epi_params)
    topup.inputs.readout_times = [readout, compute_readout(altepi_params)]

    unwarp = pe.Node(fsl.ApplyTOPUP(in_index=[1], method='jac'), name='unwarp')

    # scaling = pe.Node(niu.Function(input_names=['in_file', 'enc_dir'],
    #                   output_names=['factor'], function=_get_zoom),
    #                   name='GetZoom')
    # scaling.inputs.enc_dir = epi_params['enc_dir']
    vsm2dfm = vsm2warp()
    vsm2dfm.inputs.inputnode.enc_dir = epi_params['enc_dir']
    vsm2dfm.inputs.inputnode.scaling = readout

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, b0_ref, [('in_file', 'in_file'), (('ref_num', _checkrnum),
                                                      't_min')]),
        (inputnode, b0_alt, [('alt_file', 'in_file'), (('ref_num', _checkrnum),
                                                       't_min')]),
        (b0_ref, b0_comb, [('roi_file', 'in1')]),
        (b0_alt, b0_comb, [('roi_file', 'in2')]),
        (b0_comb, b0_merge, [('out', 'in_files')]),
        (b0_merge, topup, [('merged_file', 'in_file')]),
        (topup, unwarp, [('out_fieldcoef', 'in_topup_fieldcoef'),
                         ('out_movpar', 'in_topup_movpar'),
                         ('out_enc_file', 'encoding_file')]),
        (inputnode, unwarp, [('in_file', 'in_files')]),
        (unwarp, outputnode, [('out_corrected', 'out_file')]),
        # (b0_ref,      scaling,    [('roi_file', 'in_file')]),
        # (scaling,     vsm2dfm,    [('factor', 'inputnode.scaling')]),
        (b0_ref, vsm2dfm, [('roi_file', 'inputnode.in_ref')]),
        (topup, vsm2dfm, [('out_field', 'inputnode.in_vsm')]),
        (topup, outputnode, [('out_field', 'out_vsm')]),
        (vsm2dfm, outputnode, [('outputnode.out_warp', 'out_warp')])
    ])
    return wf


def remove_bias(name='bias_correct'):
    """
    This workflow estimates a single multiplicative bias field from the
    averaged *b0* image, as suggested in [Jeurissen2014]_.

    .. admonition:: References

      .. [Jeurissen2014] Jeurissen B. et al., `Multi-tissue constrained
        spherical deconvolution for improved analysis of multi-shell diffusion
        MRI data <http://dx.doi.org/10.1016/j.neuroimage.2014.07.061>`_.
        NeuroImage (2014). doi: 10.1016/j.neuroimage.2014.07.061


    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import remove_bias
    >>> bias = remove_bias()
    >>> bias.inputs.inputnode.in_file = 'epi.nii'
    >>> bias.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> bias.inputs.inputnode.in_mask = 'mask.nii'
    >>> bias.run() # doctest: +SKIP

    """
    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_file', 'in_bval', 'in_mask']),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['out_file']), name='outputnode')

    avg_b0 = pe.Node(
        niu.Function(
            input_names=['in_dwi', 'in_bval'],
            output_names=['out_file'],
            function=b0_average),
        name='b0_avg')
    n4 = pe.Node(
        ants.N4BiasFieldCorrection(
            dimension=3, save_bias=True, bspline_fitting_distance=600),
        name='Bias_b0')
    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    mult = pe.MapNode(
        fsl.MultiImageMaths(op_string='-div %s'),
        iterfield=['in_file'],
        name='RemoveBiasOfDWIs')
    thres = pe.MapNode(
        fsl.Threshold(thresh=0.0),
        iterfield=['in_file'],
        name='RemoveNegative')
    merge = pe.Node(fsl.utils.Merge(dimension='t'), name='MergeDWIs')

    wf = pe.Workflow(name=name)
    wf.connect([(inputnode, avg_b0, [
        ('in_file', 'in_dwi'), ('in_bval', 'in_bval')
    ]), (avg_b0, n4, [('out_file', 'input_image')]), (inputnode, n4, [
        ('in_mask', 'mask_image')
    ]), (inputnode, split, [('in_file', 'in_file')]), (n4, mult, [
        ('bias_image', 'operand_files')
    ]), (split, mult, [('out_files', 'in_file')]), (mult, thres,
                                                    [('out_file', 'in_file')]),
                (thres, merge, [('out_file', 'in_files')]),
                (merge, outputnode, [('merged_file', 'out_file')])])
    return wf


def _eff_t_echo(echospacing, acc_factor):
    eff_echo = echospacing / (1.0 * acc_factor)
    return eff_echo


def _fix_enc_dir(enc_dir):
    enc_dir = enc_dir.lower()
    if enc_dir == 'lr':
        return 'x-'
    if enc_dir == 'rl':
        return 'x'
    if enc_dir == 'ap':
        return 'y-'
    if enc_dir == 'pa':
        return 'y'
    return enc_dir


def _checkrnum(ref_num):
    from nipype.interfaces.base import isdefined
    if (ref_num is None) or not isdefined(ref_num):
        return 0
    return ref_num


def _nonb0(in_bval):
    import numpy as np
    bvals = np.loadtxt(in_bval)
    return np.where(bvals != 0)[0].tolist()


def _xfm_jacobian(in_xfm):
    import numpy as np
    from math import fabs
    return [fabs(np.linalg.det(np.loadtxt(xfm))) for xfm in in_xfm]


def _get_zoom(in_file, enc_dir):
    import nibabel as nb
    from nipype.utils import NUMPY_MMAP

    zooms = nb.load(in_file, mmap=NUMPY_MMAP).header.get_zooms()

    if 'y' in enc_dir:
        return zooms[1]
    elif 'x' in enc_dir:
        return zooms[0]
    elif 'z' in enc_dir:
        return zooms[2]
    else:
        raise ValueError('Wrong encoding direction string')
