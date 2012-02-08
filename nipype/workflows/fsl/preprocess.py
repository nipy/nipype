# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine

from nipype.workflows.freesurfer.utils import create_getmask_flow

def getthreshop(thresh):
    return ['-thr %.10f -Tmin -bin'%(0.1*val[1]) for val in thresh]

def pickfirst(files):
    if isinstance(files, list):
        return files[0]
    else:
        return files

def pickmiddle(files):
    from nibabel import load
    import numpy as np
    middlevol = []
    for f in files:
        middlevol.append(int(np.ceil(load(f).get_shape()[3]/2)))
    return middlevol

def pickvol(filenames, fileidx, which):
    from nibabel import load
    import numpy as np
    if which.lower() == 'first':
        idx = 0
    elif which.lower() == 'middle':
        idx = int(np.ceil(load(filenames[fileidx]).get_shape()[3]/2))
    else:
        raise Exception('unknown value for volume selection : %s'%which)
    return idx

def getbtthresh(medianvals):
    return [0.75*val for val in medianvals]

def chooseindex(fwhm):
    if fwhm<1:
        return [0]
    else:
        return [1]

def getmeanscale(medianvals):
    return ['-mul %.10f'%(10000./val) for val in medianvals]

def getusans(x):
    return [[tuple([val[0],0.75*val[1]])] for val in x]

tolist = lambda x: [x]
highpass_operand = lambda x:'-bptf %.10f -1'%x

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

    >>> from nipype.workflows.fsl import create_parallelfeat_preproc
    >>> import os
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

    featpreproc = pe.Workflow(name=name)

    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    if highpass:
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm',
                                                                     'highpass']),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask',
                                                                  'smoothed_files',
                                                                  'highpassed_files',
                                                                  'mean']),
                         name='outputspec')
    else:
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm']),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask',
                                                                  'smoothed_files',
                                                                  'mean']),
                         name='outputspec')

    """
    Set up a node to define outputs for the preprocessing workflow

    """

    """
    Convert functional images to float representation. Since there can
    be more than one functional run we use a MapNode to convert each
    run.
    """

    img2float = pe.MapNode(interface=fsl.ImageMaths(out_data_type='float',
                                                 op_string = '',
                                                 suffix='_dtype'),
                           iterfield=['in_file'],
                           name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')

    """
    Extract the first volume of the first run as the reference
    """

    extract_ref = pe.MapNode(interface=fsl.ExtractROI(t_size=1),
                             iterfield=['in_file', 't_min'],
                             name = 'extractref')

    featpreproc.connect(img2float, 'out_file', extract_ref, 'in_file')
    featpreproc.connect(img2float, ('out_file', pickmiddle), extract_ref, 't_min')
    featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')

    """
    Realign the functional runs to the reference (1st volume of first run)
    """

    motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_mats = True,
                                                      save_plots = True),
                                name='realign',
                                iterfield = ['in_file', 'ref_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    featpreproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')
    featpreproc.connect(motion_correct, 'par_file', outputnode, 'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode, 'realigned_files')

    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(interface=fsl.PlotMotionParams(in_source='fsl'),
                            name='plot_motion',
                            iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')

    """
    Extract the mean volume of the first functional run
    """

    meanfunc = pe.MapNode(interface=fsl.ImageMaths(op_string = '-Tmean',
                                                   suffix='_mean'),
                          iterfield=['in_file'],
                          name='meanfunc')
    featpreproc.connect(motion_correct, 'out_file', meanfunc, 'in_file')

    """
    Strip the skull from the mean functional to generate a mask
    """

    meanfuncmask = pe.MapNode(interface=fsl.BET(mask = True,
                                             no_output=True,
                                             frac = 0.3),
                              iterfield=['in_file'],
                              name = 'meanfuncmask')
    featpreproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')

    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                                   op_string='-mas'),
                          iterfield=['in_file', 'in_file2'],
                          name = 'maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')


    """
    Determine the 2nd and 98th percentile intensities of each functional run
    """

    getthresh = pe.MapNode(interface=fsl.ImageStats(op_string='-p 2 -p 98'),
                           iterfield = ['in_file'],
                           name='getthreshold')
    featpreproc.connect(maskfunc, 'out_file', getthresh, 'in_file')


    """
    Threshold the first run of the functional data at 10% of the 98th percentile
    """

    threshold = pe.MapNode(interface=fsl.ImageMaths(out_data_type='char',
                                                 suffix='_thresh'),
                           iterfield=['in_file', 'op_string'],
                           name='threshold')
    featpreproc.connect(maskfunc, 'out_file', threshold, 'in_file')

    """
    Define a function to get 10% of the intensity
    """

    featpreproc.connect(getthresh, ('out_stat', getthreshop), threshold, 'op_string')

    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                           iterfield = ['in_file', 'mask_file'],
                           name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(threshold, 'out_file', medianval, 'mask_file')

    """
    Dilate the mask
    """

    dilatemask = pe.MapNode(interface=fsl.ImageMaths(suffix='_dil',
                                                  op_string='-dilF'),
                            iterfield=['in_file'],
                            name='dilatemask')
    featpreproc.connect(threshold, 'out_file', dilatemask, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', outputnode, 'mask')

    """
    Mask the motion corrected functional runs with the dilated mask
    """

    maskfunc2 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                    op_string='-mas'),
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

    maskfunc3 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                    op_string='-mas'),
                          iterfield=['in_file', 'in_file2'],
                          name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3, 'in_file')

    featpreproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')


    concatnode = pe.Node(interface=util.Merge(2),
                         name='concat')
    featpreproc.connect(maskfunc2,('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3,('out_file', tolist), concatnode, 'in2')

    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(),name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')


    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(interface=fsl.ImageMaths(suffix='_gms'),
                          iterfield=['in_file','op_string'],
                          name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')

    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale, 'op_string')

    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(interface=fsl.ImageMaths(suffix='_tempfilt'),
                              iterfield=['in_file'],
                              name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand), highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')
        featpreproc.connect(highpass, 'out_file', outputnode, 'highpassed_files')

    """
    Generate a mean functional image from the first run
    """

    meanfunc3 = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                    suffix='_mean'),
                           iterfield=['in_file'],
                          name='meanfunc3')
    if highpass:
        featpreproc.connect(highpass, 'out_file', meanfunc3, 'in_file')
    else:
        featpreproc.connect(meanscale, 'out_file', meanfunc3, 'in_file')

    featpreproc.connect(meanfunc3, 'out_file', outputnode, 'mean')


    return featpreproc

def create_featreg_preproc(name='featpreproc', highpass=True, whichvol='middle'):
    """Create a FEAT preprocessing workflow with registration to one volume of the first run

    Parameters
    ----------

    ::

        name : name of workflow (default: featpreproc)
        highpass : boolean (default: True)
        whichvol : which volume of the first run to register to ('first', 'middle', 'mean')

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

    >>> from nipype.workflows.fsl import create_featreg_preproc
    >>> import os
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

    featpreproc = pe.Workflow(name=name)

    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    if highpass:
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm',
                                                                     'highpass']),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask',
                                                                  'smoothed_files',
                                                                  'highpassed_files',
                                                                  'mean']),
                         name='outputspec')
    else:
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm']),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask',
                                                                  'smoothed_files',
                                                                  'mean']),
                         name='outputspec')

    """
    Set up a node to define outputs for the preprocessing workflow

    """

    """
    Convert functional images to float representation. Since there can
    be more than one functional run we use a MapNode to convert each
    run.
    """

    img2float = pe.MapNode(interface=fsl.ImageMaths(out_data_type='float',
                                                 op_string = '',
                                                 suffix='_dtype'),
                           iterfield=['in_file'],
                           name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')

    """
    Extract the first volume of the first run as the reference
    """

    if whichvol != 'mean':
        extract_ref = pe.Node(interface=fsl.ExtractROI(t_size=1),
                                 iterfield=['in_file'],
                                 name = 'extractref')
        featpreproc.connect(img2float, ('out_file', pickfirst), extract_ref, 'in_file')
        featpreproc.connect(img2float, ('out_file', pickvol, 0, whichvol), extract_ref, 't_min')
        featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')


    """
    Realign the functional runs to the reference (1st volume of first run)
    """

    motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_mats = True,
                                                      save_plots = True,
                                                      interpolation = 'sinc'),
                                name='realign',
                                iterfield = ['in_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')
    else:
        motion_correct.inputs.mean_vol = True
        featpreproc.connect(motion_correct, ('mean_img', pickfirst), outputnode, 'reference')

    featpreproc.connect(motion_correct, 'par_file', outputnode, 'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode, 'realigned_files')

    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(interface=fsl.PlotMotionParams(in_source='fsl'),
                            name='plot_motion',
                            iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')

    """
    Extract the mean volume of the first functional run
    """

    meanfunc = pe.Node(interface=fsl.ImageMaths(op_string = '-Tmean',
                                                   suffix='_mean'),
                          name='meanfunc')
    featpreproc.connect(motion_correct, ('out_file', pickfirst), meanfunc, 'in_file')

    """
    Strip the skull from the mean functional to generate a mask
    """

    meanfuncmask = pe.Node(interface=fsl.BET(mask = True,
                                             no_output=True,
                                             frac = 0.3),
                              name = 'meanfuncmask')
    featpreproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')

    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                                   op_string='-mas'),
                          iterfield=['in_file'],
                          name = 'maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')


    """
    Determine the 2nd and 98th percentile intensities of each functional run
    """

    getthresh = pe.MapNode(interface=fsl.ImageStats(op_string='-p 2 -p 98'),
                           iterfield = ['in_file'],
                           name='getthreshold')
    featpreproc.connect(maskfunc, 'out_file', getthresh, 'in_file')


    """
    Threshold the first run of the functional data at 10% of the 98th percentile
    """

    threshold = pe.MapNode(interface=fsl.ImageMaths(out_data_type='char',
                                                 suffix='_thresh'),
                           iterfield=['in_file', 'op_string'],
                           name='threshold')
    featpreproc.connect(maskfunc, 'out_file', threshold, 'in_file')

    """
    Define a function to get 10% of the intensity
    """

    featpreproc.connect(getthresh, ('out_stat', getthreshop), threshold, 'op_string')

    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                           iterfield = ['in_file', 'mask_file'],
                           name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(threshold, 'out_file', medianval, 'mask_file')

    """
    Dilate the mask
    """

    dilatemask = pe.MapNode(interface=fsl.ImageMaths(suffix='_dil',
                                                  op_string='-dilF'),
                            iterfield=['in_file'],
                            name='dilatemask')
    featpreproc.connect(threshold, 'out_file', dilatemask, 'in_file')
    featpreproc.connect(dilatemask, 'out_file', outputnode, 'mask')

    """
    Mask the motion corrected functional runs with the dilated mask
    """

    maskfunc2 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                    op_string='-mas'),
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

    maskfunc3 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                    op_string='-mas'),
                          iterfield=['in_file', 'in_file2'],
                          name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3, 'in_file')

    featpreproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')


    concatnode = pe.Node(interface=util.Merge(2),
                         name='concat')
    featpreproc.connect(maskfunc2,('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3,('out_file', tolist), concatnode, 'in2')

    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(),name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')


    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(interface=fsl.ImageMaths(suffix='_gms'),
                          iterfield=['in_file','op_string'],
                          name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')

    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale, 'op_string')

    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(interface=fsl.ImageMaths(suffix='_tempfilt'),
                              iterfield=['in_file'],
                              name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand), highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')
        featpreproc.connect(highpass, 'out_file', outputnode, 'highpassed_files')

    """
    Generate a mean functional image from the first run
    """

    meanfunc3 = pe.Node(interface=fsl.ImageMaths(op_string='-Tmean',
                                                    suffix='_mean'),
                           iterfield=['in_file'],
                          name='meanfunc3')
    if highpass:
        featpreproc.connect(highpass, ('out_file', pickfirst), meanfunc3, 'in_file')
    else:
        featpreproc.connect(meanscale, ('out_file', pickfirst), meanfunc3, 'in_file')

    featpreproc.connect(meanfunc3, 'out_file', outputnode, 'mean')


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
        inputnode.fwhm : fwhm for smoothing with SUSAN
        inputnode.mask_file : mask used for estimating SUSAN thresholds (but not for smoothing)

    Outputs::

        outputnode.smoothed_files : functional runs (filename or list of filenames)

    Example
    -------

    >>> from nipype.workflows.fsl import create_susan_smooth
    >>> smooth = create_susan_smooth()
    >>> smooth.inputs.inputnode.in_files = 'f3.nii'
    >>> smooth.inputs.inputnode.fwhm = 5
    >>> smooth.inputs.inputnode.mask_file = 'mask.nii'
    >>> smooth.run() # doctest: +SKIP

    """

    susan_smooth = pe.Workflow(name=name)

    """
    Set up a node to define all inputs required for the preprocessing workflow

    """

    inputnode = pe.Node(interface=util.IdentityInterface(fields=['in_files',
                                                                 'fwhm',
                                                                 'mask_file']),
                        name='inputnode')

    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    smooth = pe.MapNode(interface=fsl.SUSAN(),
                        iterfield=['in_file', 'brightness_threshold','usans'],
                        name='smooth')

    """
    Determine the median value of the functional runs using the mask
    """


    if separate_masks:
        median = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                            iterfield = ['in_file', 'mask_file'],
                            name='median')
    else:
        median = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                            iterfield = ['in_file'],
                            name='median')
    susan_smooth.connect(inputnode, 'in_files', median, 'in_file')
    susan_smooth.connect(inputnode, 'mask_file', median, 'mask_file')

    """
    Mask the motion corrected functional runs with the dilated mask
    """

    if separate_masks:
        mask = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                   op_string='-mas'),
                          iterfield=['in_file', 'in_file2'],
                          name='mask')
    else:
        mask = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                   op_string='-mas'),
                          iterfield=['in_file'],
                          name='mask')
    susan_smooth.connect(inputnode, 'in_files', mask, 'in_file')
    susan_smooth.connect(inputnode, 'mask_file', mask, 'in_file2')

    """
    Determine the mean image from each functional run
    """

    meanfunc = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                    suffix='_mean'),
                           iterfield=['in_file'],
                           name='meanfunc2')
    susan_smooth.connect(mask, 'out_file', meanfunc, 'in_file')

    """
    Merge the median values with the mean functional images into a coupled list
    """

    merge = pe.Node(interface=util.Merge(2, axis='hstack'),
                        name='merge')
    susan_smooth.connect(meanfunc,'out_file', merge, 'in1')
    susan_smooth.connect(median,'out_stat', merge, 'in2')

    """
    Define a function to get the brightness threshold for SUSAN
    """
    susan_smooth.connect(inputnode, 'fwhm', smooth, 'fwhm')
    susan_smooth.connect(inputnode, 'in_files', smooth, 'in_file')
    susan_smooth.connect(median, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
    susan_smooth.connect(merge, ('out', getusans), smooth, 'usans')

    outputnode = pe.Node(interface=util.IdentityInterface(fields=['smoothed_files']),
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

    >>> import os
    >>> from nipype.workflows.fsl import create_fsl_fs_preproc
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
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm',
                                                                     'subject_id',
                                                                     'subjects_dir',
                                                                     'highpass']),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask_file',
                                                                  'smoothed_files',
                                                                  'highpassed_files',
                                                                  'reg_file',
                                                                  'reg_cost'
                                                                  ]),
                         name='outputspec')
    else:
        inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                                     'fwhm',
                                                                     'subject_id',
                                                                     'subjects_dir'
                                                                     ]),
                            name='inputspec')
        outputnode = pe.Node(interface=util.IdentityInterface(fields=['reference',
                                                                  'motion_parameters',
                                                                  'realigned_files',
                                                                  'motion_plots',
                                                                  'mask_file',
                                                                  'smoothed_files',
                                                                  'reg_file',
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

    img2float = pe.MapNode(interface=fsl.ImageMaths(out_data_type='float',
                                                 op_string = '',
                                                 suffix='_dtype'),
                           iterfield=['in_file'],
                           name='img2float')
    featpreproc.connect(inputnode, 'func', img2float, 'in_file')


    """
    Extract the first volume of the first run as the reference
    """

    if whichvol != 'mean':
        extract_ref = pe.Node(interface=fsl.ExtractROI(t_size=1),
                                 iterfield=['in_file'],
                                 name = 'extractref')
        featpreproc.connect(img2float, ('out_file', pickfirst), extract_ref, 'in_file')
        featpreproc.connect(img2float, ('out_file', pickvol, 0, whichvol), extract_ref, 't_min')
        featpreproc.connect(extract_ref, 'roi_file', outputnode, 'reference')


    """
    Realign the functional runs to the reference (1st volume of first run)
    """

    motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_mats = True,
                                                      save_plots = True,
                                                      interpolation = 'sinc'),
                                name='realign',
                                iterfield = ['in_file'])
    featpreproc.connect(img2float, 'out_file', motion_correct, 'in_file')
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')
    else:
        motion_correct.inputs.mean_vol = True
        featpreproc.connect(motion_correct, 'mean_img', outputnode, 'reference')

    featpreproc.connect(motion_correct, 'par_file', outputnode, 'motion_parameters')
    featpreproc.connect(motion_correct, 'out_file', outputnode, 'realigned_files')

    """
    Plot the estimated motion parameters
    """

    plot_motion = pe.MapNode(interface=fsl.PlotMotionParams(in_source='fsl'),
                            name='plot_motion',
                            iterfield=['in_file'])
    plot_motion.iterables = ('plot_type', ['rotations', 'translations'])
    featpreproc.connect(motion_correct, 'par_file', plot_motion, 'in_file')
    featpreproc.connect(plot_motion, 'out_file', outputnode, 'motion_plots')

    """Get the mask from subject for each run
    """

    maskflow = create_getmask_flow()
    featpreproc.connect([(inputnode, maskflow, [('subject_id','inputspec.subject_id'),
                                             ('subjects_dir', 'inputspec.subjects_dir')])])
    maskflow.inputs.inputspec.contrast_type = 't2'
    if whichvol != 'mean':
        featpreproc.connect(extract_ref, 'roi_file', maskflow, 'inputspec.source_file')
    else:
        featpreproc.connect(motion_correct, ('mean_img', pickfirst), maskflow, 'inputspec.source_file')


    """
    Mask the functional runs with the extracted mask
    """

    maskfunc = pe.MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                                   op_string='-mas'),
                          iterfield=['in_file'],
                          name = 'maskfunc')
    featpreproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), maskfunc, 'in_file2')

    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    smooth = create_susan_smooth(separate_masks=False)

    featpreproc.connect(inputnode, 'fwhm', smooth, 'inputnode.fwhm')
    featpreproc.connect(maskfunc, 'out_file', smooth, 'inputnode.in_files')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), smooth, 'inputnode.mask_file')

    """
    Mask the smoothed data with the dilated mask
    """

    maskfunc3 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                    op_string='-mas'),
                          iterfield=['in_file'],
                          name='maskfunc3')
    featpreproc.connect(smooth, 'outputnode.smoothed_files', maskfunc3, 'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), maskfunc3, 'in_file2')


    concatnode = pe.Node(interface=util.Merge(2),
                         name='concat')
    featpreproc.connect(maskfunc, ('out_file', tolist), concatnode, 'in1')
    featpreproc.connect(maskfunc3, ('out_file', tolist), concatnode, 'in2')

    """
    The following nodes select smooth or unsmoothed data depending on the
    fwhm. This is because SUSAN defaults to smoothing the data with about the
    voxel size of the input data if the fwhm parameter is less than 1/3 of the
    voxel size.
    """
    selectnode = pe.Node(interface=util.Select(),name='select')

    featpreproc.connect(concatnode, 'out', selectnode, 'inlist')

    featpreproc.connect(inputnode, ('fwhm', chooseindex), selectnode, 'index')
    featpreproc.connect(selectnode, 'out', outputnode, 'smoothed_files')


    """
    Scale the median value of the run is set to 10000
    """

    meanscale = pe.MapNode(interface=fsl.ImageMaths(suffix='_gms'),
                          iterfield=['in_file','op_string'],
                          name='meanscale')
    featpreproc.connect(selectnode, 'out', meanscale, 'in_file')

    """
    Determine the median value of the functional runs using the mask
    """

    medianval = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                           iterfield = ['in_file'],
                           name='medianval')
    featpreproc.connect(motion_correct, 'out_file', medianval, 'in_file')
    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), medianval, 'mask_file')

    """
    Define a function to get the scaling factor for intensity normalization
    """

    featpreproc.connect(medianval, ('out_stat', getmeanscale), meanscale, 'op_string')

    """
    Perform temporal highpass filtering on the data
    """

    if highpass:
        highpass = pe.MapNode(interface=fsl.ImageMaths(suffix='_tempfilt'),
                              iterfield=['in_file'],
                              name='highpass')
        featpreproc.connect(inputnode, ('highpass', highpass_operand), highpass, 'op_string')
        featpreproc.connect(meanscale, 'out_file', highpass, 'in_file')
        featpreproc.connect(highpass, 'out_file', outputnode, 'highpassed_files')

    featpreproc.connect(maskflow, ('outputspec.mask_file', pickfirst), outputnode, 'mask_file')
    featpreproc.connect(maskflow, 'outputspec.reg_file', outputnode, 'reg_file')
    featpreproc.connect(maskflow, 'outputspec.reg_cost', outputnode, 'reg_cost')

    return featpreproc

