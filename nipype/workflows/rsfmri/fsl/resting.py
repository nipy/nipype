# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.interfaces.fsl as fsl          # fsl
from nipype.algorithms.misc import TSNR
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine

def extract_noise_components(realigned_file, noise_mask_file, num_components):
    """Derive components most reflective of physiological noise
    """
    import os
    from nibabel import load
    import numpy as np
    import scipy as sp
    from scipy.signal import detrend
    imgseries = load(realigned_file)
    noise_mask = load(noise_mask_file)
    voxel_timecourses = imgseries.get_data()[np.nonzero(noise_mask.get_data())]
    for timecourse in voxel_timecourses:
        timecourse[:] = detrend(timecourse, type='constant')
    u,s,v = sp.linalg.svd(voxel_timecourses, full_matrices=False)
    components_file = os.path.join(os.getcwd(), 'noise_components.txt')
    np.savetxt(components_file, v[:,:num_components])
    return components_file

def select_volume(filename, which):
    """Return the middle index of a file
    """
    from nibabel import load
    import numpy as np
    if which.lower() == 'first':
        idx = 0
    elif which.lower() == 'middle':
        idx = int(np.ceil(load(filename).get_shape()[3]/2))
    else:
        raise Exception('unknown value for volume selection : %s'%which)
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
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                 ]),
                        name='inputspec')
    outputnode = pe.Node(interface=util.IdentityInterface(fields=[
                                                               'realigned_file',
                                                                 ]),
                        name='outputspec')
    realigner = pe.Node(fsl.MCFLIRT(save_mats=True, stats_imgs=True),
                        name='realigner')
    splitter = pe.Node(fsl.Split(dimension='t'), name='splitter')
    warper = pe.MapNode(fsl.ApplyWarp(interp='spline'),
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

def create_resting_preproc(name='restpreproc'):
    """Create a "resting" time series preprocessing workflow

    The noise removal is based on Behzadi et al. (2007)

    Parameters
    ----------

    name : name of workflow (default: restpreproc)

    Inputs::

        inputspec.func : functional run (filename or list of filenames)

    Outputs::

        outputspec.noise_mask_file : voxels used for PCA to derive noise components
        outputspec.filtered_file : bandpass filtered and noise-reduced time series

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

    restpreproc = pe.Workflow(name=name)

    # Define nodes
    inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                 'num_noise_components',
                                                                 'highpass_sigma',
                                                                 'lowpass_sigma'
                                                                 ]),
                        name='inputspec')
    outputnode = pe.Node(interface=util.IdentityInterface(fields=[
                                                              'noise_mask_file',
                                                              'filtered_file',
                                                              ]),
                     name='outputspec')
    slicetimer = pe.Node(fsl.SliceTimer(), name='slicetimer')
    realigner = create_realign_flow()
    tsnr = pe.Node(TSNR(regress_poly=2), name='tsnr')
    getthresh = pe.Node(interface=fsl.ImageStats(op_string='-p 98'),
                           name='getthreshold')
    threshold_stddev = pe.Node(fsl.Threshold(), name='threshold')
    compcor = pe.Node(util.Function(input_names=['realigned_file',
                                                 'noise_mask_file',
                                                 'num_components'],
                                     output_names=['noise_components'],
                                     function=extract_noise_components),
                       name='compcorr')
    remove_noise = pe.Node(fsl.FilterRegressor(filter_all=True),
                           name='remove_noise')
    bandpass_filter = pe.Node(fsl.TemporalFilter(),
                              name='bandpass_filter')

    # Define connections
    restpreproc.connect(inputnode, 'func', slicetimer, 'in_file')
    restpreproc.connect(slicetimer, 'slice_time_corrected_file',
                        realigner, 'inputspec.func')
    restpreproc.connect(realigner, 'outputspec.realigned_file', tsnr, 'in_file')
    restpreproc.connect(tsnr, 'stddev_file', threshold_stddev, 'in_file')
    restpreproc.connect(tsnr, 'stddev_file', getthresh, 'in_file')
    restpreproc.connect(getthresh, 'out_stat', threshold_stddev, 'thresh')
    restpreproc.connect(realigner, 'outputspec.realigned_file',
                        compcor, 'realigned_file')
    restpreproc.connect(threshold_stddev, 'out_file',
                        compcor, 'noise_mask_file')
    restpreproc.connect(inputnode, 'num_noise_components',
                        compcor, 'num_components')
    restpreproc.connect(tsnr, 'detrended_file',
                        remove_noise, 'in_file')
    restpreproc.connect(compcor, 'noise_components',
                        remove_noise, 'design_file')
    restpreproc.connect(inputnode, 'highpass_sigma',
                        bandpass_filter, 'highpass_sigma')
    restpreproc.connect(inputnode, 'lowpass_sigma',
                        bandpass_filter, 'lowpass_sigma')
    restpreproc.connect(remove_noise, 'out_file', bandpass_filter, 'in_file')
    restpreproc.connect(threshold_stddev, 'out_file',
                        outputnode, 'noise_mask_file')
    restpreproc.connect(bandpass_filter, 'out_file',
                        outputnode, 'filtered_file')
    return restpreproc