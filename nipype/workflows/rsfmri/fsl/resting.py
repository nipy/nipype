# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str

from ....interfaces import fsl as fsl  # fsl
from ....interfaces import utility as util  # utility
from ....pipeline import engine as pe  # pypeline engine
from ....algorithms import confounds


def select_volume(filename, which):
    """Return the middle index of a file
    """
    from nibabel import load
    import numpy as np
    from nipype.utils import NUMPY_MMAP

    if which.lower() == 'first':
        idx = 0
    elif which.lower() == 'middle':
        idx = int(np.ceil(load(filename, mmap=NUMPY_MMAP).shape[3] / 2))
    else:
        raise Exception('unknown value for volume selection : %s' % which)
    return idx


def create_realign_flow(name='realign'):
    """Realign a time series to the middle volume using spline interpolation

    Uses MCFLIRT to realign the time series and ApplyWarp to apply the rigid
    body transformations using spline interpolation (unknown order).

    Example
    -------

    >>> wf = create_realign_flow()
    >>> wf.inputs.inputspec.func = 'f3.nii'
    >>> wf.run() # doctest: +SKIP

    """
    realignflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'func',
        ]), name='inputspec')
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'realigned_file',
        ]),
        name='outputspec')
    realigner = pe.Node(
        fsl.MCFLIRT(save_mats=True, stats_imgs=True), name='realigner')
    splitter = pe.Node(fsl.Split(dimension='t'), name='splitter')
    warper = pe.MapNode(
        fsl.ApplyWarp(interp='spline'),
        iterfield=['in_file', 'premat'],
        name='warper')
    joiner = pe.Node(fsl.Merge(dimension='t'), name='joiner')

    realignflow.connect(inputnode, 'func', realigner, 'in_file')
    realignflow.connect(inputnode, ('func', select_volume, 'middle'),
                        realigner, 'ref_vol')
    realignflow.connect(realigner, 'out_file', splitter, 'in_file')
    realignflow.connect(realigner, 'mat_file', warper, 'premat')
    realignflow.connect(realigner, 'variance_img', warper, 'ref_file')
    realignflow.connect(splitter, 'out_files', warper, 'in_file')
    realignflow.connect(warper, 'out_file', joiner, 'in_files')
    realignflow.connect(joiner, 'merged_file', outputnode, 'realigned_file')
    return realignflow


def create_resting_preproc(name='restpreproc', base_dir=None):
    """Create a "resting" time series preprocessing workflow

    The noise removal is based on Behzadi et al. (2007)

    Parameters
    ----------

    name : name of workflow (default: restpreproc)

    Inputs::

        inputspec.func : functional run (filename or list of filenames)

    Outputs::

        outputspec.noise_mask_file : voxels used for PCA to derive noise
                                     components
        outputspec.filtered_file : bandpass filtered and noise-reduced time
                                   series

    Example
    -------

    >>> TR = 3.0
    >>> wf = create_resting_preproc()
    >>> wf.inputs.inputspec.func = 'f3.nii'
    >>> wf.inputs.inputspec.num_noise_components = 6
    >>> wf.inputs.inputspec.highpass_sigma = 100/(2*TR)
    >>> wf.inputs.inputspec.lowpass_sigma = 12.5/(2*TR)
    >>> wf.run() # doctest: +SKIP

    """

    restpreproc = pe.Workflow(name=name, base_dir=base_dir)

    # Define nodes
    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'func', 'num_noise_components', 'highpass_sigma', 'lowpass_sigma'
        ]),
        name='inputspec')
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'noise_mask_file',
            'filtered_file',
        ]),
        name='outputspec')
    slicetimer = pe.Node(fsl.SliceTimer(), name='slicetimer')
    realigner = create_realign_flow()
    tsnr = pe.Node(confounds.TSNR(regress_poly=2), name='tsnr')
    getthresh = pe.Node(
        interface=fsl.ImageStats(op_string='-p 98'), name='getthreshold')
    threshold_stddev = pe.Node(fsl.Threshold(), name='threshold')
    compcor = pe.Node(
        confounds.ACompCor(
            components_file="noise_components.txt", pre_filter=False),
        name='compcor')
    remove_noise = pe.Node(
        fsl.FilterRegressor(filter_all=True), name='remove_noise')
    bandpass_filter = pe.Node(fsl.TemporalFilter(), name='bandpass_filter')

    # Define connections
    restpreproc.connect(inputnode, 'func', slicetimer, 'in_file')
    restpreproc.connect(slicetimer, 'slice_time_corrected_file', realigner,
                        'inputspec.func')
    restpreproc.connect(realigner, 'outputspec.realigned_file', tsnr,
                        'in_file')
    restpreproc.connect(tsnr, 'stddev_file', threshold_stddev, 'in_file')
    restpreproc.connect(tsnr, 'stddev_file', getthresh, 'in_file')
    restpreproc.connect(getthresh, 'out_stat', threshold_stddev, 'thresh')
    restpreproc.connect(realigner, 'outputspec.realigned_file', compcor,
                        'realigned_file')
    restpreproc.connect(threshold_stddev, 'out_file', compcor, 'mask_files')
    restpreproc.connect(inputnode, 'num_noise_components', compcor,
                        'num_components')
    restpreproc.connect(tsnr, 'detrended_file', remove_noise, 'in_file')
    restpreproc.connect(compcor, 'components_file', remove_noise,
                        'design_file')
    restpreproc.connect(inputnode, 'highpass_sigma', bandpass_filter,
                        'highpass_sigma')
    restpreproc.connect(inputnode, 'lowpass_sigma', bandpass_filter,
                        'lowpass_sigma')
    restpreproc.connect(remove_noise, 'out_file', bandpass_filter, 'in_file')
    restpreproc.connect(threshold_stddev, 'out_file', outputnode,
                        'noise_mask_file')
    restpreproc.connect(bandpass_filter, 'out_file', outputnode,
                        'filtered_file')
    return restpreproc
