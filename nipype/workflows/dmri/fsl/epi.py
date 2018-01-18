# -*- coding: utf-8 -*-
# coding: utf-8
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import open, str

import warnings

from ....pipeline import engine as pe
from ....interfaces import utility as niu
from ....interfaces import fsl as fsl


def create_dmri_preprocessing(name='dMRI_preprocessing',
                              use_fieldmap=True,
                              fieldmap_registration=False):
    """
    Creates a workflow that chains the necessary pipelines to
    correct for motion, eddy currents, and, if selected, susceptibility
    artifacts in EPI dMRI sequences.

    .. deprecated:: 0.9.3
      Use :func:`nipype.workflows.dmri.preprocess.epi.all_fmb_pipeline` or
      :func:`nipype.workflows.dmri.preprocess.epi.all_peb_pipeline` instead.


    .. warning:: This workflow rotates the b-vectors, so please be
      advised that not all the dicom converters ensure the consistency between the resulting
      nifti orientation and the b matrix table (e.g. dcm2nii checks it).


    Example
    -------

    >>> nipype_dmri_preprocess = create_dmri_preprocessing('nipype_dmri_prep')
    >>> nipype_dmri_preprocess.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> nipype_dmri_preprocess.inputs.inputnode.ref_num = 0
    >>> nipype_dmri_preprocess.inputs.inputnode.fieldmap_mag = 'magnitude.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.fieldmap_pha = 'phase.nii'
    >>> nipype_dmri_preprocess.inputs.inputnode.te_diff = 2.46
    >>> nipype_dmri_preprocess.inputs.inputnode.epi_echospacing = 0.77
    >>> nipype_dmri_preprocess.inputs.inputnode.epi_rev_encoding = False
    >>> nipype_dmri_preprocess.inputs.inputnode.pi_accel_factor = True
    >>> nipype_dmri_preprocess.run() # doctest: +SKIP


    Inputs::

        inputnode.in_file - The diffusion data
        inputnode.in_bvec - The b-matrix file, in FSL format and consistent with the in_file orientation
        inputnode.ref_num - The reference volume (a b=0 volume in dMRI)
        inputnode.fieldmap_mag - The magnitude of the fieldmap
        inputnode.fieldmap_pha - The phase difference of the fieldmap
        inputnode.te_diff - TE increment used (in msec.) on the fieldmap acquisition (generally 2.46ms for 3T scanners)
        inputnode.epi_echospacing - The EPI EchoSpacing parameter (in msec.)
        inputnode.epi_rev_encoding - True if reverse encoding was used (generally False)
        inputnode.pi_accel_factor - Parallel imaging factor (aka GRAPPA acceleration factor)
        inputnode.vsm_sigma - Sigma (in mm.) of the gaussian kernel used for in-slice smoothing of the deformation field (voxel shift map, vsm)


    Outputs::

        outputnode.dmri_corrected
        outputnode.bvec_rotated


    Optional arguments::

        use_fieldmap - True if there are fieldmap files that should be used (default True)
        fieldmap_registration - True if registration to fieldmap should be performed (default False)


    """

    warnings.warn(
        ('This workflow is deprecated from v.1.0.0, use of available '
         'nipype.workflows.dmri.preprocess.epi.all_*'), DeprecationWarning)

    pipeline = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file', 'in_bvec', 'ref_num', 'fieldmap_mag', 'fieldmap_pha',
            'te_diff', 'epi_echospacing', 'epi_rev_encoding',
            'pi_accel_factor', 'vsm_sigma'
        ]),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['dmri_corrected', 'bvec_rotated']),
        name='outputnode')

    motion = create_motion_correct_pipeline()
    eddy = create_eddy_correct_pipeline()

    if use_fieldmap:  # we have a fieldmap, so lets use it (yay!)
        susceptibility = create_epidewarp_pipeline(
            fieldmap_registration=fieldmap_registration)

        pipeline.connect(
            [(inputnode, motion, [('in_file', 'inputnode.in_file'),
                                  ('in_bvec', 'inputnode.in_bvec'),
                                  ('ref_num', 'inputnode.ref_num')]),
             (inputnode, eddy,
              [('ref_num', 'inputnode.ref_num')]), (motion, eddy, [
                  ('outputnode.motion_corrected', 'inputnode.in_file')
              ]), (eddy, susceptibility,
                   [('outputnode.eddy_corrected', 'inputnode.in_file')]),
             (inputnode, susceptibility,
              [('ref_num', 'inputnode.ref_num'), ('fieldmap_mag',
                                                  'inputnode.fieldmap_mag'),
               ('fieldmap_pha', 'inputnode.fieldmap_pha'),
               ('te_diff', 'inputnode.te_diff'), ('epi_echospacing',
                                                  'inputnode.epi_echospacing'),
               ('epi_rev_encoding',
                'inputnode.epi_rev_encoding'), ('pi_accel_factor',
                                                'inputnode.pi_accel_factor'),
               ('vsm_sigma', 'inputnode.vsm_sigma')]), (motion, outputnode, [
                   ('outputnode.out_bvec', 'bvec_rotated')
               ]), (susceptibility, outputnode, [('outputnode.epi_corrected',
                                                  'dmri_corrected')])])
    else:  # we don't have a fieldmap, so we just carry on without it :(
        pipeline.connect([(inputnode, motion, [
            ('in_file', 'inputnode.in_file'), ('in_bvec', 'inputnode.in_bvec'),
            ('ref_num', 'inputnode.ref_num')
        ]), (inputnode, eddy, [('ref_num', 'inputnode.ref_num')]),
                          (motion, eddy, [('outputnode.motion_corrected',
                                           'inputnode.in_file')]),
                          (motion, outputnode,
                           [('outputnode.out_bvec',
                             'bvec_rotated')]), (eddy, outputnode,
                                                 [('outputnode.eddy_corrected',
                                                   'dmri_corrected')])])

    return pipeline


def create_motion_correct_pipeline(name='motion_correct'):
    """Creates a pipeline that corrects for motion artifact in dMRI sequences.
    It takes a series of diffusion weighted images and rigidly co-registers
    them to one reference image. Finally, the b-matrix is rotated accordingly
    (Leemans et al. 2009 - http://www.ncbi.nlm.nih.gov/pubmed/19319973),
    making use of the rotation matrix obtained by FLIRT.


    .. deprecated:: 0.9.3
      Use :func:`nipype.workflows.dmri.preprocess.epi.hmc_pipeline` instead.


    .. warning:: This workflow rotates the b-vectors, so please be adviced
      that not all the dicom converters ensure the consistency between the resulting
      nifti orientation and the b matrix table (e.g. dcm2nii checks it).


    Example
    -------

    >>> nipype_motioncorrect = create_motion_correct_pipeline('nipype_motioncorrect')
    >>> nipype_motioncorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_motioncorrect.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> nipype_motioncorrect.inputs.inputnode.ref_num = 0
    >>> nipype_motioncorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file
        inputnode.ref_num
        inputnode.in_bvec

    Outputs::

        outputnode.motion_corrected
        outputnode.out_bvec

    """

    warnings.warn(
        ('This workflow is deprecated from v.1.0.0, use '
         'nipype.workflows.dmri.preprocess.epi.hmc_pipeline instead'),
        DeprecationWarning)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_file', 'ref_num', 'in_bvec']),
        name='inputnode')

    pipeline = pe.Workflow(name=name)

    split = pe.Node(fsl.Split(dimension='t'), name='split')
    pick_ref = pe.Node(niu.Select(), name='pick_ref')
    coregistration = pe.MapNode(
        fsl.FLIRT(no_search=True, interp='spline', padding_size=1, dof=6),
        name='coregistration',
        iterfield=['in_file'])
    rotate_bvecs = pe.Node(
        niu.Function(
            input_names=['in_bvec', 'in_matrix'],
            output_names=['out_file'],
            function=_rotate_bvecs),
        name='rotate_b_matrix')
    merge = pe.Node(fsl.Merge(dimension='t'), name='merge')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['motion_corrected', 'out_bvec']),
        name='outputnode')

    pipeline.connect(
        [(inputnode, split, [('in_file', 'in_file')]),
         (split, pick_ref, [('out_files', 'inlist')]), (inputnode, pick_ref, [
             ('ref_num', 'index')
         ]), (split, coregistration,
              [('out_files', 'in_file')]), (inputnode, rotate_bvecs,
                                            [('in_bvec', 'in_bvec')]),
         (coregistration, rotate_bvecs,
          [('out_matrix_file', 'in_matrix')]), (pick_ref, coregistration,
                                                [('out', 'reference')]),
         (coregistration, merge,
          [('out_file', 'in_files')]), (merge, outputnode, [
              ('merged_file', 'motion_corrected')
          ]), (rotate_bvecs, outputnode, [('out_file', 'out_bvec')])])

    return pipeline


def create_eddy_correct_pipeline(name='eddy_correct'):
    """

    .. deprecated:: 0.9.3
      Use :func:`nipype.workflows.dmri.preprocess.epi.ecc_pipeline` instead.


    Creates a pipeline that replaces eddy_correct script in FSL. It takes a
    series of diffusion weighted images and linearly co-registers them to one
    reference image. No rotation of the B-matrix is performed, so this pipeline
    should be executed after the motion correction pipeline.

    Example
    -------

    >>> nipype_eddycorrect = create_eddy_correct_pipeline('nipype_eddycorrect')
    >>> nipype_eddycorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_eddycorrect.inputs.inputnode.ref_num = 0
    >>> nipype_eddycorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file
        inputnode.ref_num

    Outputs::

        outputnode.eddy_corrected
    """

    warnings.warn(
        ('This workflow is deprecated from v.1.0.0, use '
         'nipype.workflows.dmri.preprocess.epi.ecc_pipeline instead'),
        DeprecationWarning)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['in_file', 'ref_num']), name='inputnode')

    pipeline = pe.Workflow(name=name)

    split = pe.Node(fsl.Split(dimension='t'), name='split')
    pick_ref = pe.Node(niu.Select(), name='pick_ref')
    coregistration = pe.MapNode(
        fsl.FLIRT(no_search=True, padding_size=1, interp='trilinear'),
        name='coregistration',
        iterfield=['in_file'])
    merge = pe.Node(fsl.Merge(dimension='t'), name='merge')
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['eddy_corrected']), name='outputnode')

    pipeline.connect([(inputnode, split, [('in_file', 'in_file')]),
                      (split, pick_ref,
                       [('out_files', 'inlist')]), (inputnode, pick_ref,
                                                    [('ref_num', 'index')]),
                      (split, coregistration,
                       [('out_files', 'in_file')]), (pick_ref, coregistration,
                                                     [('out', 'reference')]),
                      (coregistration, merge,
                       [('out_file', 'in_files')]), (merge, outputnode,
                                                     [('merged_file',
                                                       'eddy_corrected')])])
    return pipeline


def fieldmap_correction(name='fieldmap_correction', nocheck=False):
    """

    .. deprecated:: 0.9.3
      Use :func:`nipype.workflows.dmri.preprocess.epi.sdc_fmb` instead.


    Fieldmap-based retrospective correction of EPI images for the susceptibility distortion
    artifact (Jezzard et al., 1995). Fieldmap images are assumed to be already registered
    to EPI data, and a brain mask is required.

    Replaces the former workflow, still available as create_epidewarp_pipeline().  The difference
    with respect the epidewarp pipeline is that now the workflow uses the new fsl_prepare_fieldmap
    available as of FSL 5.0.


    Example
    -------

    >>> nipype_epicorrect = fieldmap_correction('nipype_epidewarp')
    >>> nipype_epicorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_epicorrect.inputs.inputnode.in_mask = 'brainmask.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_pha = 'phase.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_mag = 'magnitude.nii'
    >>> nipype_epicorrect.inputs.inputnode.te_diff = 2.46
    >>> nipype_epicorrect.inputs.inputnode.epi_echospacing = 0.77
    >>> nipype_epicorrect.inputs.inputnode.encoding_direction = 'y'
    >>> nipype_epicorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - The volume acquired with EPI sequence
        inputnode.in_mask - A brain mask
        inputnode.fieldmap_pha - The phase difference map from the fieldmapping, registered to in_file
        inputnode.fieldmap_mag - The magnitud maps (usually 4D, one magnitude per GRE scan)
                                 from the fieldmapping, registered to in_file
        inputnode.te_diff - Time difference in msec. between TE in ms of the fieldmapping (usually a GRE sequence).
        inputnode.epi_echospacing - The effective echo spacing (aka dwell time) in msec. of the EPI sequence. If
                                    EPI was acquired with parallel imaging, then the effective echo spacing is
                                    eff_es = es / acc_factor.
        inputnode.encoding_direction - The phase encoding direction in EPI acquisition (default y)
        inputnode.vsm_sigma - Sigma value of the gaussian smoothing filter applied to the vsm (voxel shift map)


    Outputs::

        outputnode.epi_corrected
        outputnode.out_vsm

    """

    warnings.warn(('This workflow is deprecated from v.1.0.0, use '
                   'nipype.workflows.dmri.preprocess.epi.sdc_fmb instead'),
                  DeprecationWarning)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file', 'in_mask', 'fieldmap_pha', 'fieldmap_mag', 'te_diff',
            'epi_echospacing', 'vsm_sigma', 'encoding_direction'
        ]),
        name='inputnode')

    pipeline = pe.Workflow(name=name)

    # Keep first frame from magnitude
    select_mag = pe.Node(
        fsl.utils.ExtractROI(t_size=1, t_min=0), name='select_magnitude')

    # Mask magnitude (it is required by PreparedFieldMap)
    mask_mag = pe.Node(fsl.maths.ApplyMask(), name='mask_magnitude')

    # Run fsl_prepare_fieldmap
    fslprep = pe.Node(fsl.PrepareFieldmap(), name='prepare_fieldmap')

    if nocheck:
        fslprep.inputs.nocheck = True

    # Use FUGUE to generate the voxel shift map (vsm)
    vsm = pe.Node(fsl.FUGUE(save_shift=True), name='generate_vsm')

    # VSM demean is not anymore present in the epi_reg script
    # vsm_mean = pe.Node(niu.Function(input_names=['in_file', 'mask_file', 'in_unwarped'], output_names=[
    #                   'out_file'], function=_vsm_remove_mean), name='vsm_mean_shift')

    # fugue_epi
    dwi_split = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_files'],
            function=_split_dwi),
        name='dwi_split')

    # 'fugue -i %s -u %s --loadshift=%s --mask=%s' % ( vol_name, out_vol_name, vsm_name, mask_name )
    dwi_applyxfm = pe.MapNode(
        fsl.FUGUE(icorr=True, save_shift=False),
        iterfield=['in_file'],
        name='dwi_fugue')
    # Merge back all volumes
    dwi_merge = pe.Node(fsl.utils.Merge(dimension='t'), name='dwi_merge')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['epi_corrected', 'out_vsm']),
        name='outputnode')

    pipeline.connect(
        [(inputnode, select_mag,
          [('fieldmap_mag', 'in_file')]), (inputnode, fslprep, [
              ('fieldmap_pha', 'in_phase'), ('te_diff', 'delta_TE')
          ]), (inputnode, mask_mag,
               [('in_mask', 'mask_file')]), (select_mag, mask_mag,
                                             [('roi_file', 'in_file')]),
         (mask_mag, fslprep, [('out_file', 'in_magnitude')]), (fslprep, vsm, [
             ('out_fieldmap', 'phasemap_in_file')
         ]), (inputnode,
              vsm, [('fieldmap_mag',
                     'in_file'), ('encoding_direction', 'unwarp_direction'),
                    (('te_diff', _ms2sec), 'asym_se_time'),
                    ('vsm_sigma', 'smooth2d'), (('epi_echospacing', _ms2sec),
                                                'dwell_time')]),
         (mask_mag, vsm, [('out_file', 'mask_file')]), (inputnode, dwi_split, [
             ('in_file', 'in_file')
         ]), (dwi_split, dwi_applyxfm,
              [('out_files', 'in_file')]), (mask_mag, dwi_applyxfm,
                                            [('out_file', 'mask_file')]),
         (vsm, dwi_applyxfm,
          [('shift_out_file', 'shift_in_file')]), (inputnode, dwi_applyxfm, [
              ('encoding_direction', 'unwarp_direction')
          ]), (dwi_applyxfm, dwi_merge,
               [('unwarped_file', 'in_files')]), (dwi_merge, outputnode, [
                   ('merged_file', 'epi_corrected')
               ]), (vsm, outputnode, [('shift_out_file', 'out_vsm')])])

    return pipeline


def topup_correction(name='topup_correction'):
    """

    .. deprecated:: 0.9.3
      Use :func:`nipype.workflows.dmri.preprocess.epi.sdc_peb` instead.


    Corrects for susceptibilty distortion of EPI images when one reverse encoding dataset has
    been acquired


    Example
    -------

    >>> nipype_epicorrect = topup_correction('nipype_topup')
    >>> nipype_epicorrect.inputs.inputnode.in_file_dir = 'epi.nii'
    >>> nipype_epicorrect.inputs.inputnode.in_file_rev = 'epi_rev.nii'
    >>> nipype_epicorrect.inputs.inputnode.encoding_direction = ['y', 'y-']
    >>> nipype_epicorrect.inputs.inputnode.ref_num = 0
    >>> nipype_epicorrect.run() # doctest: +SKIP


    Inputs::

        inputnode.in_file_dir - EPI volume acquired in 'forward' phase encoding
        inputnode.in_file_rev - EPI volume acquired in 'reversed' phase encoding
        inputnode.encoding_direction - Direction encoding of in_file_dir
        inputnode.ref_num - Identifier of the reference volumes (usually B0 volume)


    Outputs::

        outputnode.epi_corrected


    """

    warnings.warn(('This workflow is deprecated from v.1.0.0, use '
                   'nipype.workflows.dmri.preprocess.epi.sdc_peb instead'),
                  DeprecationWarning)

    pipeline = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file_dir', 'in_file_rev', 'encoding_direction',
            'readout_times', 'ref_num'
        ]),
        name='inputnode')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'out_fieldcoef', 'out_movpar', 'out_enc_file', 'epi_corrected'
        ]),
        name='outputnode')

    b0_dir = pe.Node(fsl.ExtractROI(t_size=1), name='b0_1')
    b0_rev = pe.Node(fsl.ExtractROI(t_size=1), name='b0_2')
    combin = pe.Node(niu.Merge(2), name='merge')
    combin2 = pe.Node(niu.Merge(2), name='merge2')
    merged = pe.Node(fsl.Merge(dimension='t'), name='b0_comb')

    topup = pe.Node(fsl.TOPUP(), name='topup')
    applytopup = pe.Node(fsl.ApplyTOPUP(in_index=[1, 2]), name='applytopup')

    pipeline.connect(
        [(inputnode, b0_dir, [('in_file_dir', 'in_file'), ('ref_num',
                                                           't_min')]),
         (inputnode, b0_rev,
          [('in_file_rev',
            'in_file'), ('ref_num', 't_min')]), (inputnode, combin2, [
                ('in_file_dir', 'in1'), ('in_file_rev', 'in2')
            ]), (b0_dir, combin, [('roi_file', 'in1')]), (b0_rev, combin, [
                ('roi_file', 'in2')
            ]), (combin, merged, [('out', 'in_files')]),
         (merged, topup, [('merged_file', 'in_file')]), (inputnode, topup, [
             ('encoding_direction', 'encoding_direction'), ('readout_times',
                                                            'readout_times')
         ]), (topup, applytopup, [('out_fieldcoef', 'in_topup_fieldcoef'),
                                  ('out_movpar', 'in_topup_movpar'),
                                  ('out_enc_file', 'encoding_file')]),
         (combin2, applytopup, [('out', 'in_files')]), (topup, outputnode, [
             ('out_fieldcoef', 'out_fieldcoef'), ('out_movpar', 'out_movpar'),
             ('out_enc_file', 'out_enc_file')
         ]), (applytopup, outputnode, [('out_corrected', 'epi_corrected')])])

    return pipeline


def create_epidewarp_pipeline(name='epidewarp', fieldmap_registration=False):
    """
    Replaces the epidewarp.fsl script (http://www.nmr.mgh.harvard.edu/~greve/fbirn/b0/epidewarp.fsl)
    for susceptibility distortion correction of dMRI & fMRI acquired with EPI sequences and the fieldmap
    information (Jezzard et al., 1995) using FSL's FUGUE. The registration to the (warped) fieldmap
    (strictly following the original script) is available using fieldmap_registration=True.


    .. warning:: This workflow makes use of ``epidewarp.fsl`` a script of FSL deprecated long
      time ago. The use of this workflow is not recommended, use
      :func:`nipype.workflows.dmri.preprocess.epi.sdc_fmb` instead.


    Example
    -------

    >>> nipype_epicorrect = create_epidewarp_pipeline('nipype_epidewarp', fieldmap_registration=False)
    >>> nipype_epicorrect.inputs.inputnode.in_file = 'diffusion.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_mag = 'magnitude.nii'
    >>> nipype_epicorrect.inputs.inputnode.fieldmap_pha = 'phase.nii'
    >>> nipype_epicorrect.inputs.inputnode.te_diff = 2.46
    >>> nipype_epicorrect.inputs.inputnode.epi_echospacing = 0.77
    >>> nipype_epicorrect.inputs.inputnode.epi_rev_encoding = False
    >>> nipype_epicorrect.inputs.inputnode.ref_num = 0
    >>> nipype_epicorrect.inputs.inputnode.pi_accel_factor = 1.0
    >>> nipype_epicorrect.run() # doctest: +SKIP

    Inputs::

        inputnode.in_file - The volume acquired with EPI sequence
        inputnode.fieldmap_mag - The magnitude of the fieldmap
        inputnode.fieldmap_pha - The phase difference of the fieldmap
        inputnode.te_diff - Time difference between TE in ms.
        inputnode.epi_echospacing - The echo spacing (aka dwell time) in the EPI sequence
        inputnode.epi_ph_encoding_dir - The phase encoding direction in EPI acquisition (default y)
        inputnode.epi_rev_encoding - True if it is acquired with reverse encoding
        inputnode.pi_accel_factor - Acceleration factor used for EPI parallel imaging (GRAPPA)
        inputnode.vsm_sigma - Sigma value of the gaussian smoothing filter applied to the vsm (voxel shift map)
        inputnode.ref_num - The reference volume (B=0 in dMRI or a central frame in fMRI)


    Outputs::

        outputnode.epi_corrected


    Optional arguments::

        fieldmap_registration - True if registration to fieldmap should be done (default False)

    """

    warnings.warn(('This workflow reproduces a deprecated FSL script.'),
                  DeprecationWarning)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=[
            'in_file', 'fieldmap_mag', 'fieldmap_pha', 'te_diff',
            'epi_echospacing', 'epi_ph_encoding_dir', 'epi_rev_encoding',
            'pi_accel_factor', 'vsm_sigma', 'ref_num', 'unwarp_direction'
        ]),
        name='inputnode')

    pipeline = pe.Workflow(name=name)

    # Keep first frame from magnitude
    select_mag = pe.Node(
        fsl.utils.ExtractROI(t_size=1, t_min=0), name='select_magnitude')

    # mask_brain
    mask_mag = pe.Node(fsl.BET(mask=True), name='mask_magnitude')
    mask_mag_dil = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=_dilate_mask),
        name='mask_dilate')

    # Compute dwell time
    dwell_time = pe.Node(
        niu.Function(
            input_names=['dwell_time', 'pi_factor', 'is_reverse_encoding'],
            output_names=['dwell_time'],
            function=_compute_dwelltime),
        name='dwell_time')

    # Normalize phase diff to be [-pi, pi)
    norm_pha = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=_prepare_phasediff),
        name='normalize_phasediff')
    # Execute FSL PRELUDE: prelude -p %s -a %s -o %s -f -v -m %s
    prelude = pe.Node(fsl.PRELUDE(process3d=True), name='phase_unwrap')
    fill_phase = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_file'],
            function=_fill_phase),
        name='fill_phasediff')

    # to assure that vsm is same dimension as mag. The input only affects the output dimension.
    # The content of the input has no effect on the vsm. The de-warped mag volume is
    # meaningless and will be thrown away
    # fugue -i %s -u %s -p %s --dwell=%s --asym=%s --mask=%s --saveshift=%s %
    # ( mag_name, magdw_name, ph_name, esp, tediff, mask_name, vsmmag_name)
    vsm = pe.Node(fsl.FUGUE(save_shift=True), name='generate_vsm')
    vsm_mean = pe.Node(
        niu.Function(
            input_names=['in_file', 'mask_file', 'in_unwarped'],
            output_names=['out_file'],
            function=_vsm_remove_mean),
        name='vsm_mean_shift')

    # fugue_epi
    dwi_split = pe.Node(
        niu.Function(
            input_names=['in_file'],
            output_names=['out_files'],
            function=_split_dwi),
        name='dwi_split')
    # 'fugue -i %s -u %s --loadshift=%s --mask=%s' % ( vol_name, out_vol_name, vsm_name, mask_name )
    dwi_applyxfm = pe.MapNode(
        fsl.FUGUE(icorr=True, save_shift=False),
        iterfield=['in_file'],
        name='dwi_fugue')
    # Merge back all volumes
    dwi_merge = pe.Node(fsl.utils.Merge(dimension='t'), name='dwi_merge')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['epi_corrected']), name='outputnode')

    pipeline.connect(
        [(inputnode, dwell_time,
          [('epi_echospacing', 'dwell_time'), ('pi_accel_factor', 'pi_factor'),
           ('epi_rev_encoding',
            'is_reverse_encoding')]), (inputnode, select_mag, [('fieldmap_mag',
                                                                'in_file')]),
         (inputnode, norm_pha, [('fieldmap_pha',
                                 'in_file')]), (select_mag, mask_mag,
                                                [('roi_file', 'in_file')]),
         (mask_mag, mask_mag_dil,
          [('mask_file', 'in_file')]), (select_mag, prelude, [
              ('roi_file', 'magnitude_file')
          ]), (norm_pha, prelude,
               [('out_file', 'phase_file')]), (mask_mag_dil, prelude, [
                   ('out_file', 'mask_file')
               ]), (prelude, fill_phase,
                    [('unwrapped_phase_file', 'in_file')]), (inputnode, vsm, [
                        ('fieldmap_mag', 'in_file')
                    ]), (fill_phase, vsm, [('out_file', 'phasemap_in_file')]),
         (inputnode, vsm, [(('te_diff', _ms2sec), 'asym_se_time'),
                           ('vsm_sigma', 'smooth2d')]), (dwell_time, vsm, [
                               (('dwell_time', _ms2sec), 'dwell_time')
                           ]), (mask_mag_dil, vsm, [('out_file',
                                                     'mask_file')]),
         (mask_mag_dil, vsm_mean,
          [('out_file', 'mask_file')]), (vsm, vsm_mean, [
              ('unwarped_file', 'in_unwarped'), ('shift_out_file', 'in_file')
          ]), (inputnode, dwi_split,
               [('in_file', 'in_file')]), (dwi_split, dwi_applyxfm, [
                   ('out_files', 'in_file')
               ]), (dwi_applyxfm, dwi_merge,
                    [('unwarped_file', 'in_files')]), (dwi_merge, outputnode,
                                                       [('merged_file',
                                                         'epi_corrected')])])

    if fieldmap_registration:
        """ Register magfw to example epi. There are some parameters here that may need to be tweaked. Should probably strip the mag
            Pre-condition: forward warp the mag in order to reg with func. What does mask do here?
        """
        # Select reference volume from EPI (B0 in dMRI and a middle frame in
        # fMRI)
        select_epi = pe.Node(fsl.utils.ExtractROI(t_size=1), name='select_epi')

        # fugue -i %s -w %s --loadshift=%s --mask=%s % ( mag_name, magfw_name,
        # vsmmag_name, mask_name ), log ) # Forward Map
        vsm_fwd = pe.Node(fsl.FUGUE(forward_warping=True), name='vsm_fwd')
        vsm_reg = pe.Node(
            fsl.FLIRT(
                bins=256,
                cost='corratio',
                dof=6,
                interp='spline',
                searchr_x=[-10, 10],
                searchr_y=[-10, 10],
                searchr_z=[-10, 10]),
            name='vsm_registration')
        # 'flirt -in %s -ref %s -out %s -init %s -applyxfm' % ( vsmmag_name, ref_epi, vsmmag_name, magfw_mat_out )
        vsm_applyxfm = pe.Node(
            fsl.ApplyXfm(interp='spline'), name='vsm_apply_xfm')
        # 'flirt -in %s -ref %s -out %s -init %s -applyxfm' % ( mask_name, ref_epi, mask_name, magfw_mat_out )
        msk_applyxfm = pe.Node(
            fsl.ApplyXfm(interp='nearestneighbour'), name='msk_apply_xfm')

        pipeline.connect(
            [(inputnode, select_epi,
              [('in_file', 'in_file'),
               ('ref_num', 't_min')]), (select_epi, vsm_reg, [('roi_file',
                                                               'reference')]),
             (vsm, vsm_fwd, [('shift_out_file', 'shift_in_file')]),
             (mask_mag_dil, vsm_fwd,
              [('out_file', 'mask_file')]), (inputnode, vsm_fwd, [
                  ('fieldmap_mag', 'in_file')
              ]), (vsm_fwd, vsm_reg,
                   [('warped_file', 'in_file')]), (vsm_reg, msk_applyxfm, [
                       ('out_matrix_file', 'in_matrix_file')
                   ]), (select_epi, msk_applyxfm, [('roi_file', 'reference')]),
             (mask_mag_dil, msk_applyxfm,
              [('out_file', 'in_file')]), (vsm_reg, vsm_applyxfm, [
                  ('out_matrix_file', 'in_matrix_file')
              ]), (select_epi, vsm_applyxfm,
                   [('roi_file', 'reference')]), (vsm_mean, vsm_applyxfm,
                                                  [('out_file', 'in_file')]),
             (msk_applyxfm, dwi_applyxfm,
              [('out_file', 'mask_file')]), (vsm_applyxfm, dwi_applyxfm,
                                             [('out_file', 'shift_in_file')])])
    else:
        pipeline.connect(
            [(mask_mag_dil, dwi_applyxfm, [('out_file', 'mask_file')]),
             (vsm_mean, dwi_applyxfm, [('out_file', 'shift_in_file')])])

    return pipeline


def _rotate_bvecs(in_bvec, in_matrix):
    import os
    import numpy as np

    name, fext = os.path.splitext(os.path.basename(in_bvec))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_rotated.bvec' % name)
    bvecs = np.loadtxt(in_bvec)
    new_bvecs = np.zeros(
        shape=bvecs.T.shape)  # pre-initialise array, 3 col format

    for i, vol_matrix in enumerate(in_matrix[0::]):  # start index at 0
        bvec = np.matrix(bvecs[:, i])
        rot = np.matrix(np.loadtxt(vol_matrix)[0:3, 0:3])
        new_bvecs[i] = (np.array(
            rot * bvec.T).T)[0]  # fill each volume with x,y,z as we go along
    np.savetxt(out_file, np.array(new_bvecs).T, fmt=b'%0.15f')
    return out_file


def _cat_logs(in_files):
    import shutil
    import os

    name, fext = os.path.splitext(os.path.basename(in_files[0]))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_ecclog.log' % name)
    with open(out_file, 'wb') as totallog:
        for i, fname in enumerate(in_files):
            totallog.write('\n\npreprocessing %d\n' % i)
            with open(fname) as inlog:
                for line in inlog:
                    totallog.write(line)
    return out_file


def _compute_dwelltime(dwell_time=0.68,
                       pi_factor=1.0,
                       is_reverse_encoding=False):
    dwell_time *= (1.0 / pi_factor)

    if is_reverse_encoding:
        dwell_time *= -1.0

    return dwell_time


def _effective_echospacing(dwell_time, pi_factor=1.0):
    dwelltime = 1.0e-3 * dwell_time * (1.0 / pi_factor)
    return dwelltime


def _prepare_phasediff(in_file):
    import nibabel as nb
    import os
    import numpy as np
    from nipype.utils import NUMPY_MMAP
    img = nb.load(in_file, mmap=NUMPY_MMAP)
    max_diff = np.max(img.get_data().reshape(-1))
    min_diff = np.min(img.get_data().reshape(-1))
    A = (2.0 * np.pi) / (max_diff - min_diff)
    B = np.pi - (A * max_diff)
    diff_norm = img.get_data() * A + B

    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_2pi.nii.gz' % name)
    nb.save(nb.Nifti1Image(diff_norm, img.affine, img.header), out_file)
    return out_file


def _dilate_mask(in_file, iterations=4):
    import nibabel as nb
    import scipy.ndimage as ndimage
    import os
    from nipype.utils import NUMPY_MMAP
    img = nb.load(in_file, mmap=NUMPY_MMAP)
    dilated_img = img.__class__(
        ndimage.binary_dilation(img.get_data(), iterations=iterations),
        img.affine, img.header)

    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_dil.nii.gz' % name)
    nb.save(dilated_img, out_file)
    return out_file


def _fill_phase(in_file):
    import nibabel as nb
    import os
    import numpy as np
    from nipype.utils import NUMPY_MMAP
    img = nb.load(in_file, mmap=NUMPY_MMAP)
    dumb_img = nb.Nifti1Image(np.zeros(img.shape), img.affine, img.header)
    out_nii = nb.funcs.concat_images((img, dumb_img))
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_fill.nii.gz' % name)
    nb.save(out_nii, out_file)
    return out_file


def _vsm_remove_mean(in_file, mask_file, in_unwarped):
    import nibabel as nb
    import os
    import numpy as np
    import numpy.ma as ma
    from nipype.utils import NUMPY_MMAP
    img = nb.load(in_file, mmap=NUMPY_MMAP)
    msk = nb.load(mask_file, mmap=NUMPY_MMAP).get_data()
    img_data = img.get_data()
    img_data[msk == 0] = 0
    vsmmag_masked = ma.masked_values(img_data.reshape(-1), 0.0)
    vsmmag_masked = vsmmag_masked - vsmmag_masked.mean()
    masked_img = img.__class__(
        vsmmag_masked.reshape(img.shape), img.affine, img.header)
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    out_file = os.path.abspath('./%s_demeaned.nii.gz' % name)
    nb.save(masked_img, out_file)
    return out_file


def _ms2sec(val):
    return val * 1e-3


def _split_dwi(in_file):
    import nibabel as nb
    import os
    from nipype.utils import NUMPY_MMAP
    out_files = []
    frames = nb.funcs.four_to_three(nb.load(in_file, mmap=NUMPY_MMAP))
    name, fext = os.path.splitext(os.path.basename(in_file))
    if fext == '.gz':
        name, _ = os.path.splitext(name)
    for i, frame in enumerate(frames):
        out_file = os.path.abspath('./%s_%03d.nii.gz' % (name, i))
        nb.save(frame, out_file)
        out_files.append(out_file)
    return out_files
