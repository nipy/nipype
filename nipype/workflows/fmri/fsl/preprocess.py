# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import division

import os
from ....interfaces import fsl as fsl  # fsl
from ....interfaces import utility as util  # utility
from ....pipeline import engine as pe  # pypeline engine
from ....interfaces import freesurfer as fs  # freesurfer
from ....interfaces import spm as spm
from ...smri.freesurfer.utils import create_getmask_flow
from .... import LooseVersion


def getthreshop(thresh):
    return ['-thr %.10f -Tmin -bin' % (0.1 * val[1]) for val in thresh]


def pickrun(files, whichrun):
    """pick file from list of files"""

    filemap = {'first': 0, 'last': -1, 'middle': len(files) // 2}

    if isinstance(files, list):

        # whichrun is given as integer
        if isinstance(whichrun, int):
            return files[whichrun]
        # whichrun is given as string
        elif isinstance(whichrun, str):
            if whichrun not in filemap.keys():
                raise (KeyError, 'Sorry, whichrun must be either integer index'
                       'or string in form of "first", "last" or "middle')
            else:
                return files[filemap[whichrun]]
    else:
        # in case single file name is given
        return files


def pickfirst(files):
    if isinstance(files, list):
        return files[0]
    else:
        return files


def pickmiddle(files):
    from nibabel import load
    import numpy as np
    from nipype.utils import NUMPY_MMAP
    middlevol = []
    for f in files:
        middlevol.append(int(np.ceil(load(f, mmap=NUMPY_MMAP).shape[3] / 2)))
    return middlevol


def pickvol(filenames, fileidx, which):
    from nibabel import load
    import numpy as np
    from nipype.utils import NUMPY_MMAP
    if which.lower() == 'first':
        idx = 0
    elif which.lower() == 'middle':
        idx = int(
            np.ceil(load(filenames[fileidx], mmap=NUMPY_MMAP).shape[3] / 2))
    elif which.lower() == 'last':
        idx = load(filenames[fileidx]).shape[3] - 1
    else:
        raise Exception('unknown value for volume selection : %s' % which)
    return idx


def getbtthresh(medianvals):
    return [0.75 * val for val in medianvals]


def chooseindex(fwhm):
    if fwhm < 1:
        return [0]
    else:
        return [1]


def getmeanscale(medianvals):
    return ['-mul %.10f' % (10000. / val) for val in medianvals]


def getusans(x):
    return [[tuple([val[0], 0.75 * val[1]])] for val in x]


tolist = lambda x: [x]
highpass_operand = lambda x: '-bptf %.10f -1' % x


def create_parallelfeat_preproc(name='featpreproc', highpass=True):
    """Preprocess each run with FSL independently of the others

    Parameters
    ----------

    ::

      name : name of workflow (default: featpreproc)
      highpass : boolean (default: True)

    Inputs::

        inputspec.func : functional runs (filename or list of filenames)
        inputspec.fwhm : fwhm for smoothing with SUSAN
        inputspec.highpass : HWHM in TRs (if created with highpass=True)

    Outputs::

        outputspec.reference : volume to which runs are realigned
        outputspec.motion_parameters : motion correction parameters
        outputspec.realigned_files : motion corrected files
        outputspec.motion_plots : plots of motion correction parameters
        outputspec.mask : mask file used to mask the brain
        outputspec.smoothed_files : smoothed functional data
        outputspec.highpassed_files : highpassed functional data (if highpass=True)
        outputspec.mean : mean file

    Example
    -------

    >>> preproc = create_parallelfeat_preproc()
    >>> preproc.inputs.inputspec.func = ['f3.nii', 'f5.nii']
    >>> preproc.inputs.inputspec.fwhm = 5
    >>> preproc.inputs.inputspec.highpass = 128./(2*2.5)
    >>> preproc.base_dir = '/tmp'
    >>> preproc.run() # doctest: +SKIP

    >>> preproc = create_parallelfeat_preproc(highpass=False)
    >>> preproc.inputs.inputspec.func = 'f3.nii'
    >>> preproc.inputs.inputspec.fwhm = 5
    >>> preproc.base_dir = '/tmp'
    >>> preproc.run() # doctest: +SKIP
    """
    version = 0
    if fsl.Info.version() and \
            LooseVersion(fsl.Info.version()) > LooseVersion('5.0.6'):
        version = 507

    featpreproc = pe.Workflow(name=name)
    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    if highpass:
        inputnode = pe.Node(
            interface=util.IdentityInterface(
                fields=['func', 'fwhm', 'highpass']),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask', 'smoothed_files', 'highpassed_files',
                'mean'
            ]),
            name='outputspec')
    else:
        inputnode = pe.Node(
            interface=util.IdentityInterface(fields=['func', 'fwhm']),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask', 'smoothed_files', 'mean'
            ]),
            name='outputspec')
    """
    Set up a node to define outputs for the preprocessing workflow

    """
    """
    Convert functional images to float representation. Since there can
    be more than one functional run we use a MapNode to convert each
    run.
    """

    img2float = pe.MapNode(
        interface=fsl.ImageMaths(
            out_data_type='float', op_string='', suffix='_dtype'),
        iterfield=['in_file'],
        name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')
    """
    Extract the first volume of the first run as the reference
    """

    extract_ref = pe.MapNode(
        interface=fsl.ExtractROI(t_size=1),
        iterfield=['in_file', 't_min'],
        name='extractref')

    featpreproc.connect(img2float, 'out_file', extract_ref, 'in_file')
    featpreproc.connect(img2float, ('out_file', pickmiddle), extract_ref,
                        't_min')
    featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')
    """
    Realign the functional runs to the reference (1st volume of first run)
    """

    motion_correct = pe.MapNode(
        interface=fsl.MCFLIRT(save_mats=True, save_plots=True),
        name='realign',
        iterfield=['in_file', 'ref_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    featpreproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')
    featpreproc.connect(motion_correct, 'par_file', outputnode,
                        'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode,
                        'realigned_files')
    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(
        interface=fsl.PlotMotionParams(in_source='fsl'),
        name='plot_motion',
        iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')
    """
    Extract the mean volume of the first functional run
    """

    meanfunc = pe.MapNode(
        interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
        iterfield=['in_file'],
        name='meanfunc')
    featpreproc.connect(motion_correct, 'out_file', meanfunc, 'in_file')
    """
    Strip the skull from the mean functional to generate a mask
    """

    meanfuncmask = pe.MapNode(
        interface=fsl.BET(mask=True, no_output=True, frac=0.3),
        iterfield=['in_file'],
        name='meanfuncmask')
    featpreproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')
    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_bet', op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')
    """
    Determine the 2nd and 98th percentile intensities of each functional run
    """

    getthresh = pe.MapNode(
        interface=fsl.ImageStats(op_string='-p 2 -p 98'),
        iterfield=['in_file'],
        name='getthreshold')
    featpreproc.connect(maskfunc, 'out_file', getthresh, 'in_file')
    """
    Threshold the first run of the functional data at 10% of the 98th percentile
    """

    threshold = pe.MapNode(
        interface=fsl.ImageMaths(out_data_type='char', suffix='_thresh'),
        iterfield=['in_file', 'op_string'],
        name='threshold')
    featpreproc.connect(maskfunc, 'out_file', threshold, 'in_file')
    """
    Define a function to get 10% of the intensity
    """

    featpreproc.connect(getthresh, ('out_stat', getthreshop), threshold,
                        'op_string')
    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(
        interface=fsl.ImageStats(op_string='-k %s -p 50'),
        iterfield=['in_file', 'mask_file'],
        name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(threshold, 'out_file', medianval, 'mask_file')
    """
    Dilate the mask
    """

    dilatemask = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_dil', op_string='-dilF'),
        iterfield=['in_file'],
        name='dilatemask')
    featpreproc.connect(threshold, 'out_file', dilatemask, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', outputnode, 'mask')
    """
    Mask the motion corrected functional runs with the dilated mask
    """

    maskfunc2 = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='maskfunc2')
    featpreproc.connect(motion_correct, 'out_file', maskfunc2, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', maskfunc2, 'in_file2')
    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    smooth = create_susan_smooth()

    featpreproc.connect(inputnode, 'fwhm', smooth, 'inputnode.fwhm')
    featpreproc.connect(maskfunc2, 'out_file', smooth, 'inputnode.in_files')
    featpreproc.connect(dilatemask, 'out_file', smooth, 'inputnode.mask_file')
    """
    Mask the smoothed data with the dilated mask
    """

    maskfunc3 = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3,
                        'in_file')

    featpreproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')

    concatnode = pe.Node(interface=util.Merge(2), name='concat')
    featpreproc.connect(maskfunc2, ('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3, ('out_file', tolist), concatnode, 'in2')
    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(), name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')
    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_gms'),
        iterfield=['in_file', 'op_string'],
        name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')
    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale,
                        'op_string')
    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(
            interface=fsl.ImageMaths(suffix='_tempfilt'),
            iterfield=['in_file'],
            name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand),
                            highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')

        if version < 507:
            featpreproc.connect(highpass, 'out_file', outputnode,
                                'highpassed_files')
        else:
            """
            Add back the mean removed by the highpass filter operation as of FSL 5.0.7
            """
            meanfunc4 = pe.MapNode(
                interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
                iterfield=['in_file'],
                name='meanfunc4')

            featpreproc.connect(meanscale, 'out_file', meanfunc4, 'in_file')
            addmean = pe.MapNode(
                interface=fsl.BinaryMaths(operation='add'),
                iterfield=['in_file', 'operand_file'],
                name='addmean')
            featpreproc.connect(highpass, 'out_file', addmean, 'in_file')
            featpreproc.connect(meanfunc4, 'out_file', addmean, 'operand_file')
            featpreproc.connect(addmean, 'out_file', outputnode,
                                'highpassed_files')
    """
    Generate a mean functional image from the first run
    """

    meanfunc3 = pe.MapNode(
        interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
        iterfield=['in_file'],
        name='meanfunc3')

    featpreproc.connect(meanscale, 'out_file', meanfunc3, 'in_file')
    featpreproc.connect(meanfunc3, 'out_file', outputnode, 'mean')

    return featpreproc


def create_featreg_preproc(name='featpreproc',
                           highpass=True,
                           whichvol='middle',
                           whichrun=0):
    """Create a FEAT preprocessing workflow with registration to one volume of the first run

    Parameters
    ----------

    ::

        name : name of workflow (default: featpreproc)
        highpass : boolean (default: True)
        whichvol : which volume of the first run to register to ('first', 'middle', 'last', 'mean')
        whichrun : which run to draw reference volume from (integer index or 'first', 'middle', 'last')

    Inputs::

        inputspec.func : functional runs (filename or list of filenames)
        inputspec.fwhm : fwhm for smoothing with SUSAN
        inputspec.highpass : HWHM in TRs (if created with highpass=True)

    Outputs::

        outputspec.reference : volume to which runs are realigned
        outputspec.motion_parameters : motion correction parameters
        outputspec.realigned_files : motion corrected files
        outputspec.motion_plots : plots of motion correction parameters
        outputspec.mask : mask file used to mask the brain
        outputspec.smoothed_files : smoothed functional data
        outputspec.highpassed_files : highpassed functional data (if highpass=True)
        outputspec.mean : mean file

    Example
    -------

    >>> preproc = create_featreg_preproc()
    >>> preproc.inputs.inputspec.func = ['f3.nii', 'f5.nii']
    >>> preproc.inputs.inputspec.fwhm = 5
    >>> preproc.inputs.inputspec.highpass = 128./(2*2.5)
    >>> preproc.base_dir = '/tmp'
    >>> preproc.run() # doctest: +SKIP

    >>> preproc = create_featreg_preproc(highpass=False, whichvol='mean')
    >>> preproc.inputs.inputspec.func = 'f3.nii'
    >>> preproc.inputs.inputspec.fwhm = 5
    >>> preproc.base_dir = '/tmp'
    >>> preproc.run() # doctest: +SKIP
    """

    version = 0
    if fsl.Info.version() and \
            LooseVersion(fsl.Info.version()) > LooseVersion('5.0.6'):
        version = 507

    featpreproc = pe.Workflow(name=name)
    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    if highpass:
        inputnode = pe.Node(
            interface=util.IdentityInterface(
                fields=['func', 'fwhm', 'highpass']),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask', 'smoothed_files', 'highpassed_files',
                'mean'
            ]),
            name='outputspec')
    else:
        inputnode = pe.Node(
            interface=util.IdentityInterface(fields=['func', 'fwhm']),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask', 'smoothed_files', 'mean'
            ]),
            name='outputspec')
    """
    Set up a node to define outputs for the preprocessing workflow

    """
    """
    Convert functional images to float representation. Since there can
    be more than one functional run we use a MapNode to convert each
    run.
    """

    img2float = pe.MapNode(
        interface=fsl.ImageMaths(
            out_data_type='float', op_string='', suffix='_dtype'),
        iterfield=['in_file'],
        name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')
    """
    Extract the middle (or what whichvol points to) volume of the first run as the reference
    """

    if whichvol != 'mean':
        extract_ref = pe.Node(
            interface=fsl.ExtractROI(t_size=1),
            iterfield=['in_file'],
            name='extractref')
        featpreproc.connect(img2float, ('out_file', pickrun, whichrun),
                            extract_ref, 'in_file')
        featpreproc.connect(img2float, ('out_file', pickvol, 0, whichvol),
                            extract_ref, 't_min')
        featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')
    """
    Realign the functional runs to the reference (`whichvol` volume of first run)
    """

    motion_correct = pe.MapNode(
        interface=fsl.MCFLIRT(
            save_mats=True, save_plots=True, interpolation='spline'),
        name='realign',
        iterfield=['in_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', motion_correct,
                            'ref_file')
    else:
        motion_correct.inputs.mean_vol = True
        featpreproc.connect(motion_correct, ('mean_img', pickrun, whichrun),
                            outputnode, 'reference')

    featpreproc.connect(motion_correct, 'par_file', outputnode,
                        'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode,
                        'realigned_files')
    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(
        interface=fsl.PlotMotionParams(in_source='fsl'),
        name='plot_motion',
        iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')
    """
    Extract the mean volume of the first functional run
    """

    meanfunc = pe.Node(
        interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
        name='meanfunc')
    featpreproc.connect(motion_correct, ('out_file', pickrun, whichrun),
                        meanfunc, 'in_file')
    """
    Strip the skull from the mean functional to generate a mask
    """

    meanfuncmask = pe.Node(
        interface=fsl.BET(mask=True, no_output=True, frac=0.3),
        name='meanfuncmask')
    featpreproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')
    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_bet', op_string='-mas'),
        iterfield=['in_file'],
        name='maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')
    """
    Determine the 2nd and 98th percentile intensities of each functional run
    """

    getthresh = pe.MapNode(
        interface=fsl.ImageStats(op_string='-p 2 -p 98'),
        iterfield=['in_file'],
        name='getthreshold')
    featpreproc.connect(maskfunc, 'out_file', getthresh, 'in_file')
    """
    Threshold the first run of the functional data at 10% of the 98th percentile
    """

    threshold = pe.MapNode(
        interface=fsl.ImageMaths(out_data_type='char', suffix='_thresh'),
        iterfield=['in_file', 'op_string'],
        name='threshold')
    featpreproc.connect(maskfunc, 'out_file', threshold, 'in_file')
    """
    Define a function to get 10% of the intensity
    """

    featpreproc.connect(getthresh, ('out_stat', getthreshop), threshold,
                        'op_string')
    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(
        interface=fsl.ImageStats(op_string='-k %s -p 50'),
        iterfield=['in_file', 'mask_file'],
        name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(threshold, 'out_file', medianval, 'mask_file')
    """
    Dilate the mask
    """

    dilatemask = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_dil', op_string='-dilF'),
        iterfield=['in_file'],
        name='dilatemask')
    featpreproc.connect(threshold, 'out_file', dilatemask, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', outputnode, 'mask')
    """
    Mask the motion corrected functional runs with the dilated mask
    """

    maskfunc2 = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='maskfunc2')
    featpreproc.connect(motion_correct, 'out_file', maskfunc2, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', maskfunc2, 'in_file2')
    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask constituting the mean
    functional
    """

    smooth = create_susan_smooth()

    featpreproc.connect(inputnode, 'fwhm', smooth, 'inputnode.fwhm')
    featpreproc.connect(maskfunc2, 'out_file', smooth, 'inputnode.in_files')
    featpreproc.connect(dilatemask, 'out_file', smooth, 'inputnode.mask_file')
    """
    Mask the smoothed data with the dilated mask
    """

    maskfunc3 = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
        iterfield=['in_file', 'in_file2'],
        name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3,
                        'in_file')

    featpreproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')

    concatnode = pe.Node(interface=util.Merge(2), name='concat')
    featpreproc.connect(maskfunc2, ('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3, ('out_file', tolist), concatnode, 'in2')
    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(), name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')
    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_gms'),
        iterfield=['in_file', 'op_string'],
        name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')
    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale,
                        'op_string')
    """
    Generate a mean functional image from the first run
    """

    meanfunc3 = pe.Node(
        interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
        iterfield=['in_file'],
        name='meanfunc3')

    featpreproc.connect(meanscale, ('out_file', pickrun, whichrun), meanfunc3,
                        'in_file')
    featpreproc.connect(meanfunc3, 'out_file', outputnode, 'mean')
    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(
            interface=fsl.ImageMaths(suffix='_tempfilt'),
            iterfield=['in_file'],
            name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand),
                            highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')

        if version < 507:
            featpreproc.connect(highpass, 'out_file', outputnode,
                                'highpassed_files')
        else:
            """
            Add back the mean removed by the highpass filter operation as of FSL 5.0.7
            """
            meanfunc4 = pe.MapNode(
                interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
                iterfield=['in_file'],
                name='meanfunc4')

            featpreproc.connect(meanscale, 'out_file', meanfunc4, 'in_file')
            addmean = pe.MapNode(
                interface=fsl.BinaryMaths(operation='add'),
                iterfield=['in_file', 'operand_file'],
                name='addmean')
            featpreproc.connect(highpass, 'out_file', addmean, 'in_file')
            featpreproc.connect(meanfunc4, 'out_file', addmean, 'operand_file')
            featpreproc.connect(addmean, 'out_file', outputnode,
                                'highpassed_files')

    return featpreproc


def create_susan_smooth(name="susan_smooth", separate_masks=True):
    """Create a SUSAN smoothing workflow

    Parameters
    ----------

    ::

        name : name of workflow (default: susan_smooth)
        separate_masks : separate masks for each run

    Inputs::

        inputnode.in_files : functional runs (filename or list of filenames)
        inputnode.fwhm : fwhm for smoothing with SUSAN (float or list of floats)
        inputnode.mask_file : mask used for estimating SUSAN thresholds (but not for smoothing)

    Outputs::

        outputnode.smoothed_files : functional runs (filename or list of filenames)

    Example
    -------

    >>> smooth = create_susan_smooth()
    >>> smooth.inputs.inputnode.in_files = 'f3.nii'
    >>> smooth.inputs.inputnode.fwhm = 5
    >>> smooth.inputs.inputnode.mask_file = 'mask.nii'
    >>> smooth.run() # doctest: +SKIP

    """

    # replaces the functionality of a "for loop"
    def cartesian_product(fwhms, in_files, usans, btthresh):
        from nipype.utils.filemanip import ensure_list
        # ensure all inputs are lists
        in_files = ensure_list(in_files)
        fwhms = [fwhms] if isinstance(fwhms, (int, float)) else fwhms
        # create cartesian product lists (s_<name> = single element of list)
        cart_in_file = [
            s_in_file for s_in_file in in_files for s_fwhm in fwhms
        ]
        cart_fwhm = [s_fwhm for s_in_file in in_files for s_fwhm in fwhms]
        cart_usans = [s_usans for s_usans in usans for s_fwhm in fwhms]
        cart_btthresh = [
            s_btthresh for s_btthresh in btthresh for s_fwhm in fwhms
        ]

        return cart_in_file, cart_fwhm, cart_usans, cart_btthresh

    susan_smooth = pe.Workflow(name=name)
    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=['in_files', 'fwhm', 'mask_file']),
        name='inputnode')
    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    multi_inputs = pe.Node(
        util.Function(
            function=cartesian_product,
            output_names=[
                'cart_in_file', 'cart_fwhm', 'cart_usans', 'cart_btthresh'
            ]),
        name='multi_inputs')

    smooth = pe.MapNode(
        interface=fsl.SUSAN(),
        iterfield=['in_file', 'brightness_threshold', 'usans', 'fwhm'],
        name='smooth')
    """
    Determine the median value of the functional runs using the mask
    """

    if separate_masks:
        median = pe.MapNode(
            interface=fsl.ImageStats(op_string='-k %s -p 50'),
            iterfield=['in_file', 'mask_file'],
            name='median')
    else:
        median = pe.MapNode(
            interface=fsl.ImageStats(op_string='-k %s -p 50'),
            iterfield=['in_file'],
            name='median')
    susan_smooth.connect(inputnode, 'in_files', median, 'in_file')
    susan_smooth.connect(inputnode, 'mask_file', median, 'mask_file')
    """
    Mask the motion corrected functional runs with the dilated mask
    """

    if separate_masks:
        mask = pe.MapNode(
            interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
            iterfield=['in_file', 'in_file2'],
            name='mask')
    else:
        mask = pe.MapNode(
            interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
            iterfield=['in_file'],
            name='mask')
    susan_smooth.connect(inputnode, 'in_files', mask, 'in_file')
    susan_smooth.connect(inputnode, 'mask_file', mask, 'in_file2')
    """
    Determine the mean image from each functional run
    """

    meanfunc = pe.MapNode(
        interface=fsl.ImageMaths(op_string='-Tmean', suffix='_mean'),
        iterfield=['in_file'],
        name='meanfunc2')
    susan_smooth.connect(mask, 'out_file', meanfunc, 'in_file')
    """
    Merge the median values with the mean functional images into a coupled list
    """

    merge = pe.Node(interface=util.Merge(2, axis='hstack'), name='merge')
    susan_smooth.connect(meanfunc, 'out_file', merge, 'in1')
    susan_smooth.connect(median, 'out_stat', merge, 'in2')
    """
    Define a function to get the brightness threshold for SUSAN
    """

    susan_smooth.connect([
        (inputnode, multi_inputs, [('in_files', 'in_files'), ('fwhm',
                                                              'fwhms')]),
        (median, multi_inputs, [(('out_stat', getbtthresh), 'btthresh')]),
        (merge, multi_inputs, [(('out', getusans), 'usans')]),
        (multi_inputs, smooth,
         [('cart_in_file', 'in_file'), ('cart_fwhm', 'fwhm'),
          ('cart_btthresh', 'brightness_threshold'), ('cart_usans', 'usans')]),
    ])

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=['smoothed_files']),
        name='outputnode')

    susan_smooth.connect(smooth, 'smoothed_file', outputnode, 'smoothed_files')

    return susan_smooth


def create_fsl_fs_preproc(name='preproc', highpass=True, whichvol='middle'):
    """Create a FEAT preprocessing workflow together with freesurfer

    Parameters
    ----------

    ::

        name : name of workflow (default: preproc)
        highpass : boolean (default: True)
        whichvol : which volume of the first run to register to ('first', 'middle', 'mean')

    Inputs::

        inputspec.func : functional runs (filename or list of filenames)
        inputspec.fwhm : fwhm for smoothing with SUSAN
        inputspec.highpass : HWHM in TRs (if created with highpass=True)
        inputspec.subject_id : freesurfer subject id
        inputspec.subjects_dir : freesurfer subjects dir

    Outputs::

        outputspec.reference : volume to which runs are realigned
        outputspec.motion_parameters : motion correction parameters
        outputspec.realigned_files : motion corrected files
        outputspec.motion_plots : plots of motion correction parameters
        outputspec.mask_file : mask file used to mask the brain
        outputspec.smoothed_files : smoothed functional data
        outputspec.highpassed_files : highpassed functional data (if highpass=True)
        outputspec.reg_file : bbregister registration files
        outputspec.reg_cost : bbregister registration cost files

    Example
    -------

    >>> preproc = create_fsl_fs_preproc(whichvol='first')
    >>> preproc.inputs.inputspec.highpass = 128./(2*2.5)
    >>> preproc.inputs.inputspec.func = ['f3.nii', 'f5.nii']
    >>> preproc.inputs.inputspec.subjects_dir = '.'
    >>> preproc.inputs.inputspec.subject_id = 's1'
    >>> preproc.inputs.inputspec.fwhm = 6
    >>> preproc.run() # doctest: +SKIP
    """

    featpreproc = pe.Workflow(name=name)
    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    if highpass:
        inputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'func', 'fwhm', 'subject_id', 'subjects_dir', 'highpass'
            ]),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask_file', 'smoothed_files',
                'highpassed_files', 'reg_file', 'reg_cost'
            ]),
            name='outputspec')
    else:
        inputnode = pe.Node(
            interface=util.IdentityInterface(
                fields=['func', 'fwhm', 'subject_id', 'subjects_dir']),
            name='inputspec')
        outputnode = pe.Node(
            interface=util.IdentityInterface(fields=[
                'reference', 'motion_parameters', 'realigned_files',
                'motion_plots', 'mask_file', 'smoothed_files', 'reg_file',
                'reg_cost'
            ]),
            name='outputspec')
    """
    Set up a node to define outputs for the preprocessing workflow

    """
    """
    Convert functional images to float representation. Since there can
    be more than one functional run we use a MapNode to convert each
    run.
    """

    img2float = pe.MapNode(
        interface=fsl.ImageMaths(
            out_data_type='float', op_string='', suffix='_dtype'),
        iterfield=['in_file'],
        name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')
    """
    Extract the first volume of the first run as the reference
    """

    if whichvol != 'mean':
        extract_ref = pe.Node(
            interface=fsl.ExtractROI(t_size=1),
            iterfield=['in_file'],
            name='extractref')
        featpreproc.connect(img2float, ('out_file', pickfirst), extract_ref,
                            'in_file')
        featpreproc.connect(img2float, ('out_file', pickvol, 0, whichvol),
                            extract_ref, 't_min')
        featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')
    """
    Realign the functional runs to the reference (1st volume of first run)
    """

    motion_correct = pe.MapNode(
        interface=fsl.MCFLIRT(
            save_mats=True, save_plots=True, interpolation='sinc'),
        name='realign',
        iterfield=['in_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', motion_correct,
                            'ref_file')
    else:
        motion_correct.inputs.mean_vol = True
        featpreproc.connect(motion_correct, 'mean_img', outputnode,
                            'reference')

    featpreproc.connect(motion_correct, 'par_file', outputnode,
                        'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode,
                        'realigned_files')
    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(
        interface=fsl.PlotMotionParams(in_source='fsl'),
        name='plot_motion',
        iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')
    """Get the mask from subject for each run
    """

    maskflow = create_getmask_flow()
    featpreproc.connect([(inputnode, maskflow,
                          [('subject_id', 'inputspec.subject_id'),
                           ('subjects_dir', 'inputspec.subjects_dir')])])
    maskflow.inputs.inputspec.contrast_type = 't2'
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', maskflow,
                            'inputspec.source_file')
    else:
        featpreproc.connect(motion_correct, ('mean_img', pickfirst), maskflow,
                            'inputspec.source_file')
    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_bet', op_string='-mas'),
        iterfield=['in_file'],
        name='maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst),
                        maskfunc, 'in_file2')
    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    smooth = create_susan_smooth(separate_masks=False)

    featpreproc.connect(inputnode, 'fwhm', smooth, 'inputnode.fwhm')
    featpreproc.connect(maskfunc, 'out_file', smooth, 'inputnode.in_files')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), smooth,
                        'inputnode.mask_file')
    """
    Mask the smoothed data with the dilated mask
    """

    maskfunc3 = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_mask', op_string='-mas'),
        iterfield=['in_file'],
        name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3,
                        'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst),
                        maskfunc3, 'in_file2')

    concatnode = pe.Node(interface=util.Merge(2), name='concat')
    featpreproc.connect(maskfunc, ('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3, ('out_file', tolist), concatnode, 'in2')
    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(), name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')
    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(
        interface=fsl.ImageMaths(suffix='_gms'),
        iterfield=['in_file', 'op_string'],
        name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')
    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(
        interface=fsl.ImageStats(op_string='-k %s -p 50'),
        iterfield=['in_file'],
        name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst),
                        medianval, 'mask_file')
    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale,
                        'op_string')
    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(
            interface=fsl.ImageMaths(suffix='_tempfilt'),
            iterfield=['in_file'],
            name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand),
                            highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')
        featpreproc.connect(highpass, 'out_file', outputnode,
                            'highpassed_files')

    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst),
                        outputnode, 'mask_file')
    featpreproc.connect(maskflow, 'outputspec.reg_file', outputnode,
                        'reg_file')
    featpreproc.connect(maskflow, 'outputspec.reg_cost', outputnode,
                        'reg_cost')

    return featpreproc


def create_reg_workflow(name='registration'):
    """Create a FEAT preprocessing workflow

    Parameters
    ----------

    ::

        name : name of workflow (default: 'registration')

    Inputs::

        inputspec.source_files : files (filename or list of filenames to register)
        inputspec.mean_image : reference image to use
        inputspec.anatomical_image : anatomical image to coregister to
        inputspec.target_image : registration target

    Outputs::

        outputspec.func2anat_transform : FLIRT transform
        outputspec.anat2target_transform : FLIRT+FNIRT transform
        outputspec.transformed_files : transformed files in target space
        outputspec.transformed_mean : mean image in target space

    Example
    -------

    """

    register = pe.Workflow(name=name)

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'source_files', 'mean_image', 'anatomical_image', 'target_image',
            'target_image_brain', 'config_file'
        ]),
        name='inputspec')
    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            'func2anat_transform',
            'anat2target_transform',
            'transformed_files',
            'transformed_mean',
        ]),
        name='outputspec')
    """
    Estimate the tissue classes from the anatomical image. But use spm's segment
    as FSL appears to be breaking.
    """

    stripper = pe.Node(fsl.BET(), name='stripper')
    register.connect(inputnode, 'anatomical_image', stripper, 'in_file')
    fast = pe.Node(fsl.FAST(), name='fast')
    register.connect(stripper, 'out_file', fast, 'in_files')
    """
    Binarize the segmentation
    """

    binarize = pe.Node(
        fsl.ImageMaths(op_string='-nan -thr 0.5 -bin'), name='binarize')
    pickindex = lambda x, i: x[i]
    register.connect(fast, ('partial_volume_files', pickindex, 2), binarize,
                     'in_file')
    """
    Calculate rigid transform from mean image to anatomical image
    """

    mean2anat = pe.Node(fsl.FLIRT(), name='mean2anat')
    mean2anat.inputs.dof = 6
    register.connect(inputnode, 'mean_image', mean2anat, 'in_file')
    register.connect(stripper, 'out_file', mean2anat, 'reference')
    """
    Now use bbr cost function to improve the transform
    """

    mean2anatbbr = pe.Node(fsl.FLIRT(), name='mean2anatbbr')
    mean2anatbbr.inputs.dof = 6
    mean2anatbbr.inputs.cost = 'bbr'
    mean2anatbbr.inputs.schedule = os.path.join(
        os.getenv('FSLDIR'), 'etc/flirtsch/bbr.sch')
    register.connect(inputnode, 'mean_image', mean2anatbbr, 'in_file')
    register.connect(binarize, 'out_file', mean2anatbbr, 'wm_seg')
    register.connect(inputnode, 'anatomical_image', mean2anatbbr, 'reference')
    register.connect(mean2anat, 'out_matrix_file', mean2anatbbr,
                     'in_matrix_file')
    """
    Calculate affine transform from anatomical to target
    """

    anat2target_affine = pe.Node(fsl.FLIRT(), name='anat2target_linear')
    anat2target_affine.inputs.searchr_x = [-180, 180]
    anat2target_affine.inputs.searchr_y = [-180, 180]
    anat2target_affine.inputs.searchr_z = [-180, 180]
    register.connect(stripper, 'out_file', anat2target_affine, 'in_file')
    register.connect(inputnode, 'target_image_brain', anat2target_affine,
                     'reference')
    """
    Calculate nonlinear transform from anatomical to target
    """

    anat2target_nonlinear = pe.Node(fsl.FNIRT(), name='anat2target_nonlinear')
    anat2target_nonlinear.inputs.fieldcoeff_file = True
    register.connect(anat2target_affine, 'out_matrix_file',
                     anat2target_nonlinear, 'affine_file')
    register.connect(inputnode, 'anatomical_image', anat2target_nonlinear,
                     'in_file')
    register.connect(inputnode, 'config_file', anat2target_nonlinear,
                     'config_file')
    register.connect(inputnode, 'target_image', anat2target_nonlinear,
                     'ref_file')
    """
    Transform the mean image. First to anatomical and then to target
    """

    warpmean = pe.Node(fsl.ApplyWarp(interp='spline'), name='warpmean')
    register.connect(inputnode, 'mean_image', warpmean, 'in_file')
    register.connect(mean2anatbbr, 'out_matrix_file', warpmean, 'premat')
    register.connect(inputnode, 'target_image', warpmean, 'ref_file')
    register.connect(anat2target_nonlinear, 'fieldcoeff_file', warpmean,
                     'field_file')
    """
    Transform the remaining images. First to anatomical and then to target
    """

    warpall = pe.MapNode(
        fsl.ApplyWarp(interp='spline'),
        iterfield=['in_file'],
        nested=True,
        name='warpall')
    register.connect(inputnode, 'source_files', warpall, 'in_file')
    register.connect(mean2anatbbr, 'out_matrix_file', warpall, 'premat')
    register.connect(inputnode, 'target_image', warpall, 'ref_file')
    register.connect(anat2target_nonlinear, 'fieldcoeff_file', warpall,
                     'field_file')
    """
    Assign all the output files
    """

    register.connect(warpmean, 'out_file', outputnode, 'transformed_mean')
    register.connect(warpall, 'out_file', outputnode, 'transformed_files')
    register.connect(mean2anatbbr, 'out_matrix_file', outputnode,
                     'func2anat_transform')
    register.connect(anat2target_nonlinear, 'fieldcoeff_file', outputnode,
                     'anat2target_transform')

    return register
