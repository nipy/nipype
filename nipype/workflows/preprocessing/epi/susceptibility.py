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


def sdc_fmb(name='fmb_correction', interp='Linear',
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
    >>> fmb.inputs.inputnode.in_ref = range(0, 30, 6)
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

    epi_defaults = {'delta_te': 2.46e-3, 'echospacing': 0.77e-3,
                    'acc_factor': 2, 'enc_dir': u'AP'}

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_ref', 'in_mask', 'bmap_pha', 'bmap_mag',
                'settings']), name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_vsm', 'out_warp']), name='outputnode')

    r_params = pe.Node(JSONFileGrabber(defaults=epi_defaults),
                       name='SettingsGrabber')
    eff_echo = pe.Node(niu.Function(function=_eff_t_echo,
                                    input_names=['echospacing', 'acc_factor'],
                                    output_names=['eff_echo']), name='EffEcho')

    firstmag = pe.Node(fsl.ExtractROI(t_min=0, t_size=1), name='GetFirst')
    n4 = pe.Node(ants.N4BiasFieldCorrection(dimension=3), name='Bias')
    bet = pe.Node(fsl.BET(frac=0.4, mask=True), name='BrainExtraction')
    dilate = pe.Node(fsl.maths.MathsCommand(
        nan2zeros=True, args='-kernel sphere 5 -dilM'), name='MskDilate')
    pha2rads = pe.Node(niu.Function(
        input_names=['in_file'], output_names=['out_file'],
        function=siemens2rads), name='PreparePhase')
    prelude = pe.Node(fsl.PRELUDE(process3d=True), name='PhaseUnwrap')
    rad2rsec = pe.Node(niu.Function(
        input_names=['in_file', 'delta_te'], output_names=['out_file'],
        function=rads2radsec), name='ToRadSec')

    baseline = pe.Node(niu.Function(
        input_names=['in_file', 'index'], output_names=['out_file'],
        function=time_avg), name='Baseline')

    fmm2b0 = pe.Node(ants.Registration(output_warped_image=True),
                     name="FMm_to_B0")
    fmm2b0.inputs.transforms = ['Rigid'] * 2
    fmm2b0.inputs.transform_parameters = [(1.0,)] * 2
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

    applyxfm = pe.Node(ants.ApplyTransforms(
        dimension=3, interpolation=interp), name='FMp_to_B0')

    pre_fugue = pe.Node(fsl.FUGUE(save_fmap=True), name='PreliminaryFugue')
    demean = pe.Node(niu.Function(
        input_names=['in_file', 'in_mask'], output_names=['out_file'],
        function=demean_image), name='DemeanFmap')

    cleanup = cleanup_edge_pipeline()

    addvol = pe.Node(niu.Function(
        input_names=['in_file'], output_names=['out_file'],
        function=add_empty_vol), name='AddEmptyVol')

    vsm = pe.Node(fsl.FUGUE(save_shift=True, **fugue_params),
                  name="ComputeVSM")

    split = pe.Node(fsl.Split(dimension='t'), name='SplitDWIs')
    merge = pe.Node(fsl.Merge(dimension='t'), name='MergeDWIs')
    unwarp = pe.MapNode(fsl.FUGUE(icorr=True, forward_warping=False),
                        iterfield=['in_file'], name='UnwarpDWIs')
    thres = pe.MapNode(fsl.Threshold(thresh=0.0), iterfield=['in_file'],
                       name='RemoveNegative')
    vsm2dfm = vsm2warp()
    vsm2dfm.inputs.inputnode.scaling = 1.0

    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode,   r_params,   [('settings', 'in_file')]),
        (r_params,    eff_echo,   [('echospacing', 'echospacing'),
                                   ('acc_factor', 'acc_factor')]),
        (inputnode,   pha2rads,   [('bmap_pha', 'in_file')]),
        (inputnode,   firstmag,   [('bmap_mag', 'in_file')]),
        (inputnode,   baseline,   [('in_file', 'in_file'),
                                   ('in_ref', 'index')]),
        (firstmag,    n4,         [('roi_file', 'input_image')]),
        (n4,          bet,        [('output_image', 'in_file')]),
        (bet,         dilate,     [('mask_file', 'in_file')]),
        (pha2rads,    prelude,    [('out_file', 'phase_file')]),
        (n4,          prelude,    [('output_image', 'magnitude_file')]),
        (dilate,      prelude,    [('out_file', 'mask_file')]),
        (r_params,    rad2rsec,   [('delta_te', 'delta_te')]),
        (prelude,     rad2rsec,   [('unwrapped_phase_file', 'in_file')]),

        (baseline,    fmm2b0,     [('out_file', 'fixed_image')]),
        (n4,          fmm2b0,     [('output_image', 'moving_image')]),
        (inputnode,   fmm2b0,     [('in_mask', 'fixed_image_mask')]),
        (dilate,      fmm2b0,     [('out_file', 'moving_image_mask')]),

        (baseline,    applyxfm,   [('out_file', 'reference_image')]),
        (rad2rsec,    applyxfm,   [('out_file', 'input_image')]),
        (fmm2b0,      applyxfm, [
            ('forward_transforms', 'transforms'),
            ('forward_invert_flags', 'invert_transform_flags')]),

        (applyxfm,    pre_fugue,  [('output_image', 'fmap_in_file')]),
        (inputnode,   pre_fugue,  [('in_mask', 'mask_file')]),
        (pre_fugue,   demean,     [('fmap_out_file', 'in_file')]),
        (inputnode,   demean,     [('in_mask', 'in_mask')]),
        (demean,      cleanup,    [('out_file', 'inputnode.in_file')]),
        (inputnode,   cleanup,    [('in_mask', 'inputnode.in_mask')]),
        (cleanup,     addvol,     [('outputnode.out_file', 'in_file')]),
        (inputnode,   vsm,        [('in_mask', 'mask_file')]),
        (addvol,      vsm,        [('out_file', 'fmap_in_file')]),
        (r_params,    vsm,        [('delta_te', 'asym_se_time')]),
        (eff_echo,    vsm,        [('eff_echo', 'dwell_time')]),
        (inputnode,   split,      [('in_file', 'in_file')]),
        (split,       unwarp,     [('out_files', 'in_file')]),
        (vsm,         unwarp,     [('shift_out_file', 'shift_in_file')]),
        (r_params,    unwarp,     [
            (('enc_dir', _fix_enc_dir), 'unwarp_direction')]),
        (unwarp,      thres,      [('unwarped_file', 'in_file')]),
        (thres,       merge,      [('out_file', 'in_files')]),
        (r_params,    vsm2dfm,    [
            (('enc_dir', _fix_enc_dir), 'inputnode.enc_dir')]),
        (merge,       vsm2dfm,    [('merged_file', 'inputnode.in_ref')]),
        (vsm,         vsm2dfm,    [('shift_out_file', 'inputnode.in_vsm')]),
        (merge,       outputnode, [('merged_file', 'out_file')]),
        (vsm,         outputnode, [('shift_out_file', 'out_vsm')]),
        (vsm2dfm,     outputnode, [('outputnode.out_warp', 'out_warp')])
    ])
    return wf


def sdc_peb(name='peb_correction',
            epi_params=dict(echospacing=0.77e-3,
                            acc_factor=3,
                            enc_dir='y-',
                            epi_factor=1),
            altepi_params=dict(echospacing=0.77e-3,
                               acc_factor=3,
                               enc_dir='y',
                               epi_factor=1)):
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

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bval', 'in_mask', 'alt_file', 'ref_num']),
        name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_vsm', 'out_warp']), name='outputnode')

    b0_ref = pe.Node(fsl.ExtractROI(t_size=1), name='b0_ref')
    b0_alt = pe.Node(fsl.ExtractROI(t_size=1), name='b0_alt')
    b0_comb = pe.Node(niu.Merge(2), name='b0_list')
    b0_merge = pe.Node(fsl.Merge(dimension='t'), name='b0_merged')

    topup = pe.Node(fsl.TOPUP(), name='topup')
    topup.inputs.encoding_direction = [epi_params['enc_dir'],
                                       altepi_params['enc_dir']]

    readout = compute_readout(epi_params)
    topup.inputs.readout_times = [readout,
                                  compute_readout(altepi_params)]

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
        (inputnode,  b0_ref,     [('in_file', 'in_file'),
                                  (('ref_num', _checkrnum), 't_min')]),
        (inputnode,  b0_alt,     [('alt_file', 'in_file'),
                                  (('ref_num', _checkrnum), 't_min')]),
        (b0_ref,     b0_comb,    [('roi_file', 'in1')]),
        (b0_alt,     b0_comb,    [('roi_file', 'in2')]),
        (b0_comb,    b0_merge,   [('out', 'in_files')]),
        (b0_merge,   topup,      [('merged_file', 'in_file')]),
        (topup,      unwarp,     [('out_fieldcoef', 'in_topup_fieldcoef'),
                                  ('out_movpar', 'in_topup_movpar'),
                                  ('out_enc_file', 'encoding_file')]),
        (inputnode,  unwarp,     [('in_file', 'in_files')]),
        (unwarp,     outputnode, [('out_corrected', 'out_file')]),
        # (b0_ref,      scaling,    [('roi_file', 'in_file')]),
        # (scaling,     vsm2dfm,    [('factor', 'inputnode.scaling')]),
        (b0_ref,      vsm2dfm,    [('roi_file', 'inputnode.in_ref')]),
        (topup,       vsm2dfm,    [('out_field', 'inputnode.in_vsm')]),
        (topup,       outputnode, [('out_field', 'out_vsm')]),
        (vsm2dfm,     outputnode, [('outputnode.out_warp', 'out_warp')])
    ])
    return wf
