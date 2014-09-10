
#!/usr/bin/env python
"""
================================================================
rsfMRI: SPM, FSL, aCompCor
================================================================


A preprocessing workflow for Siemens resting state data.

This workflow makes use of:

- SPM
- FSL
- aCompCor

For example::

  python rsfmri_preprocessing.py -d /data/12345-34-1.dcm -f /data/Resting.nii
      -s subj001 -n 2 --despike -o output
      -p PBS --plugin_args "dict(qsub_args='-q many')"

This workflow takes resting timeseries and a Siemens dicom file corresponding
to it and preprocesses it to produce timeseries coordinates or grayordinates.

This workflow also requires 2mm subcortical atlas and templates that are
available from:

http://mindboggle.info/data.html

specifically the 2mm versions of:

- `Joint Fusion Atlas <http://mindboggle.info/data/atlases/jointfusion/OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152_2mm.nii.gz>`_
- `MNI template <http://mindboggle.info/data/templates/ants/OASIS-30_Atropos_template_in_MNI152_2mm.nii.gz>`_

The 2mm version was generated with::

   >>> from nipype.interfaces import freesurfer as fs
   >>> rs = fs.Resample()
   >>> rs.inputs.in_file = 'OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152.nii.gz'
   >>> rs.inputs.resampled_file = 'OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152_2mm.nii.gz'
   >>> rs.inputs.voxel_size = (2., 2., 2.)
   >>> rs.inputs.args = '-rt nearest -ns 1'
   >>> res = rs.run()

"""

import os

from nipype.interfaces.base import CommandLine
CommandLine.set_default_terminal_output('allatonce')

from nipype.interfaces import (spm, fsl, Function, ants)
from nipype.interfaces.c3 import C3dAffineTool

fsl.FSLCommand.set_default_output_type('NIFTI')

from nipype import Workflow, Node, MapNode
from nipype.interfaces import matlab as mlab

mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodisplay")
# If SPM is not in your MATLAB path you should add it here
mlab.MatlabCommand.set_default_paths('/cm/shared/openmind/spm/spm12b/spm12b_r5918/')

from nipype.algorithms.rapidart import ArtifactDetect
from nipype.algorithms.misc import TSNR
from nipype.interfaces.utility import Rename, Merge, IdentityInterface
from nipype.utils.filemanip import filename_to_list
from nipype.interfaces.io import DataSink

import numpy as np
import scipy as sp
import nibabel as nb

imports = ['import os',
           'import nibabel as nb',
           'import numpy as np',
           'import scipy as sp',
           'from nipype.utils.filemanip import filename_to_list, list_to_filename, split_filename',
           'from scipy.special import legendre'
           ]


def median(in_files):
    """Computes an average of the median of each realigned timeseries

    Parameters
    ----------

    in_files: one or more realigned Nifti 4D time series

    Returns
    -------

    out_file: a 3D Nifti file
    """
    average = None
    for idx, filename in enumerate(filename_to_list(in_files)):
        img = nb.load(filename)
        data = np.median(img.get_data(), axis=3)
        if average is None:
            average = data
        else:
            average = average + data
    median_img = nb.Nifti1Image(average/float(idx + 1),
                                img.get_affine(), img.get_header())
    filename = os.path.join(os.getcwd(), 'median.nii.gz')
    median_img.to_filename(filename)
    return filename


def bandpass_filter(files, lowpass_freq, highpass_freq, fs):
    """Bandpass filter the input files

    Parameters
    ----------
    files: list of 4d nifti files
    lowpass_freq: cutoff frequency for the low pass filter (in Hz)
    highpass_freq: cutoff frequency for the high pass filter (in Hz)
    fs: sampling rate (in Hz)
    """
    out_files = []
    for filename in filename_to_list(files):
        path, name, ext = split_filename(filename)
        out_file = os.path.join(os.getcwd(), name + '_bp' + ext)
        img = nb.load(filename)
        timepoints = img.shape[-1]
        F = np.zeros((timepoints))
        lowidx = timepoints/2 + 1
        if lowpass_freq > 0:
            lowidx = np.round(lowpass_freq / fs * timepoints)
        highidx = 0
        if highpass_freq > 0:
            highidx = np.round(highpass_freq / fs * timepoints)
        F[highidx:lowidx] = 1
        F = ((F + F[::-1]) > 0).astype(int)
        data = img.get_data()
        if np.all(F == 1):
            filtered_data = data
        else:
            filtered_data = np.real(np.fft.ifftn(np.fft.fftn(data) * F))
        img_out = nb.Nifti1Image(filtered_data, img.get_affine(),
                                 img.get_header())
        img_out.to_filename(out_file)
        out_files.append(out_file)
    return list_to_filename(out_files)


def motion_regressors(motion_params, order=0, derivatives=1):
    """Compute motion regressors upto given order and derivative

    motion + d(motion)/dt + d2(motion)/dt2 (linear + quadratic)
    """
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        out_params = params
        for d in range(1, derivatives + 1):
            cparams = np.vstack((np.repeat(params[0, :][None, :], d, axis=0),
                                 params))
            out_params = np.hstack((out_params, np.diff(cparams, d, axis=0)))
        out_params2 = out_params
        for i in range(2, order + 1):
            out_params2 = np.hstack((out_params2, np.power(out_params, i)))
        filename = os.path.join(os.getcwd(), "motion_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params2, fmt="%.10f")
        out_files.append(filename)
    return out_files


def build_filter1(motion_params, comp_norm, outliers, detrend_poly=None):
    """Builds a regressor set comprisong motion parameters, composite norm and
    outliers

    The outliers are added as a single time point column for each outlier


    Parameters
    ----------

    motion_params: a text file containing motion parameters and its derivatives
    comp_norm: a text file containing the composite norm
    outliers: a text file containing 0-based outlier indices
    detrend_poly: number of polynomials to add to detrend

    Returns
    -------
    components_file: a text file containing all the regressors
    """
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        norm_val = np.genfromtxt(filename_to_list(comp_norm)[idx])
        out_params = np.hstack((params, norm_val[:, None]))
        try:
            outlier_val = np.genfromtxt(filename_to_list(outliers)[idx])
        except IOError:
            outlier_val = np.empty((0))
        for index in np.atleast_1d(outlier_val):
            outlier_vector = np.zeros((out_params.shape[0], 1))
            outlier_vector[index] = 1
            out_params = np.hstack((out_params, outlier_vector))
        if detrend_poly:
            timepoints = out_params.shape[0]
            X = np.ones((timepoints, 1))
            for i in range(detrend_poly):
                X = np.hstack((X, legendre(
                    i + 1)(np.linspace(-1, 1, timepoints))[:, None]))
            out_params = np.hstack((out_params, X))
        filename = os.path.join(os.getcwd(), "filter_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params, fmt="%.10f")
        out_files.append(filename)
    return out_files


def extract_noise_components(realigned_file, mask_file, num_components=5,
                             extra_regressors=None):
    """Derive components most reflective of physiological noise

    Parameters
    ----------
    realigned_file: a 4D Nifti file containing realigned volumes
    mask_file: a 3D Nifti file containing white matter + ventricular masks
    num_components: number of components to use for noise decomposition
    extra_regressors: additional regressors to add

    Returns
    -------
    components_file: a text file containing the noise components
    """
    imgseries = nb.load(realigned_file)
    components = None
    for filename in filename_to_list(mask_file):
        mask = nb.load(filename).get_data()
        if len(np.nonzero(mask > 0)[0]) == 0:
            continue
        voxel_timecourses = imgseries.get_data()[mask > 0]
        voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0
        # remove mean and normalize by variance
        # voxel_timecourses.shape == [nvoxels, time]
        X = voxel_timecourses.T
        stdX = np.std(X, axis=0)
        stdX[stdX == 0] = 1.
        stdX[np.isnan(stdX)] = 1.
        stdX[np.isinf(stdX)] = 1.
        X = (X - np.mean(X, axis=0))/stdX
        u, _, _ = sp.linalg.svd(X, full_matrices=False)
        if components is None:
            components = u[:, :num_components]
        else:
            components = np.hstack((components, u[:, :num_components]))
    if extra_regressors:
        regressors = np.genfromtxt(extra_regressors)
        components = np.hstack((components, regressors))
    components_file = os.path.join(os.getcwd(), 'noise_components.txt')
    np.savetxt(components_file, components, fmt="%.10f")
    return components_file


def rename(in_files, suffix=None):
    from nipype.utils.filemanip import (filename_to_list, split_filename,
                                        list_to_filename)
    out_files = []
    for idx, filename in enumerate(filename_to_list(in_files)):
        _, name, ext = split_filename(filename)
        if suffix is None:
            out_files.append(name + ('_%03d' % idx) + ext)
        else:
            out_files.append(name + suffix + ext)
    return list_to_filename(out_files)

def create_reg_workflow(name='registration'):
    """Create a FEAT preprocessing workflow together with freesurfer

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

    register = Workflow(name=name)

    inputnode = Node(interface=IdentityInterface(fields=['source_files',
                                                         'mean_image',
                                                         'anatomical_image',
                                                         'target_image']),
                     name='inputspec')

    outputnode = Node(interface=IdentityInterface(fields=['func2anat_transform',
                                                          'anat2target_transform',
                                                          'transforms',
                                                          'transformed_mean',
                                                          'segmentation_files',
                                                          'anat2target'
                                                          ]),
                      name='outputspec')

    """
    Estimate the tissue classes from the anatomical image. But use spm's segment
    as FSL appears to be breaking.
    """

    stripper = Node(fsl.BET(), name='stripper')
    register.connect(inputnode, 'anatomical_image', stripper, 'in_file')
    fast = Node(fsl.FAST(), name='fast')
    register.connect(stripper, 'out_file', fast, 'in_files')

    """
    Binarize the segmentation
    """

    binarize = MapNode(fsl.ImageMaths(op_string='-nan -thr 0.5 -bin'),
                       iterfield=['in_file'],
                       name='binarize')
    pickindex = lambda x, i: x[i]
    register.connect(fast, 'partial_volume_files', binarize, 'in_file')

    """
    Calculate rigid transform from mean image to anatomical image
    """

    mean2anat = Node(fsl.FLIRT(), name='mean2anat')
    mean2anat.inputs.dof = 6
    register.connect(inputnode, 'mean_image', mean2anat, 'in_file')
    register.connect(stripper, 'out_file', mean2anat, 'reference')

    """
    Now use bbr cost function to improve the transform
    """

    mean2anatbbr = Node(fsl.FLIRT(), name='mean2anatbbr')
    mean2anatbbr.inputs.dof = 6
    mean2anatbbr.inputs.cost = 'bbr'
    mean2anatbbr.inputs.schedule = os.path.join(os.getenv('FSLDIR'),
                                                'etc/flirtsch/bbr.sch')
    register.connect(inputnode, 'mean_image', mean2anatbbr, 'in_file')
    register.connect(binarize, ('out_file', pickindex, 2),
                     mean2anatbbr, 'wm_seg')
    register.connect(inputnode, 'anatomical_image', mean2anatbbr, 'reference')
    register.connect(mean2anat, 'out_matrix_file',
                     mean2anatbbr, 'in_matrix_file')

    """
    Invert transform
    """
    invert_xfm = Node(fsl.ConvertXFM(invert_xfm=True), name='invert_transform')
    register.connect(mean2anatbbr, 'out_matrix_file', invert_xfm, 'in_file')

    """
    Apply inverse transform to take segmentations to functional space
    """
    applyxfm = MapNode(fsl.ApplyXfm(), iterfield=['in_file'],
                       name="inverse_transform")
    applyxfm.inputs.interp = 'nearestneighbour'
    register.connect(invert_xfm, 'out_file', applyxfm, 'in_matrix_file')
    register.connect(binarize, 'out_file', applyxfm, 'in_file')
    register.connect(inputnode, 'mean_image', applyxfm, 'reference')

    """
    Convert the BBRegister transformation to ANTS ITK format
    """

    convert2itk = Node(C3dAffineTool(), name='convert2itk')
    convert2itk.inputs.fsl2ras = True
    convert2itk.inputs.itk_transform = True
    register.connect(mean2anatbbr, 'out_matrix_file', convert2itk, 'transform_file')
    register.connect(inputnode, 'mean_image',convert2itk, 'source_file')
    register.connect(stripper, 'out_file', convert2itk, 'reference_file')

    """
    Compute registration between the subject's structural and MNI template
    This is currently set to perform a very quick registration. However, the
    registration can be made significantly more accurate for cortical
    structures by increasing the number of iterations
    All parameters are set using the example from:
    #https://github.com/stnava/ANTs/blob/master/Scripts/newAntsExample.sh
    """

    reg = Node(ants.Registration(), name='antsRegister')
    reg.inputs.output_transform_prefix = "output_"
    reg.inputs.transforms = ['Rigid', 'Affine', 'SyN']
    reg.inputs.transform_parameters = [(0.1,), (0.1,), (0.2, 3.0, 0.0)]
    reg.inputs.number_of_iterations = [[10000, 11110, 11110]] * 2 + [[100, 30, 20]]
    reg.inputs.dimension = 3
    reg.inputs.write_composite_transform = True
    reg.inputs.collapse_output_transforms = True
    reg.inputs.initial_moving_transform_com = True
    reg.inputs.metric = ['Mattes'] * 2 + [['Mattes', 'CC']]
    reg.inputs.metric_weight = [1] * 2 + [[0.5, 0.5]]
    reg.inputs.radius_or_number_of_bins = [32] * 2 + [[32, 4]]
    reg.inputs.sampling_strategy = ['Regular'] * 2 + [[None, None]]
    reg.inputs.sampling_percentage = [0.3] * 2 + [[None, None]]
    reg.inputs.convergence_threshold = [1.e-8] * 2 + [-0.01]
    reg.inputs.convergence_window_size = [20] * 2 + [5]
    reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 2 + [[1, 0.5, 0]]
    reg.inputs.sigma_units = ['vox'] * 3
    reg.inputs.shrink_factors = [[3, 2, 1]]*2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 3
    reg.inputs.use_histogram_matching = [False] * 2 + [True]
    reg.inputs.winsorize_lower_quantile = 0.005
    reg.inputs.winsorize_upper_quantile = 0.995
    reg.inputs.args = '--float'
    reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    reg.inputs.num_threads = 4
    reg.plugin_args = {'qsub_args': '-l nodes=1:ppn=4'}
    register.connect(stripper, 'out_file', reg, 'moving_image')
    register.connect(inputnode,'target_image', reg,'fixed_image')


    """
    Concatenate the affine and ants transforms into a list
    """

    pickfirst = lambda x: x[0]

    merge = Node(Merge(2), iterfield=['in2'], name='mergexfm')
    register.connect(convert2itk, 'itk_transform', merge, 'in2')
    register.connect(reg, ('composite_transform', pickfirst), merge, 'in1')


    """
    Transform the mean image. First to anatomical and then to target
    """
    warpmean = Node(ants.ApplyTransforms(), name='warpmean')
    warpmean.inputs.input_image_type = 3
    warpmean.inputs.interpolation = 'BSpline'
    warpmean.inputs.invert_transform_flags = [False, False]
    warpmean.inputs.terminal_output = 'file'
    warpmean.inputs.args = '--float'
    warpmean.inputs.num_threads = 4

    register.connect(inputnode,'target_image', warpmean,'reference_image')
    register.connect(inputnode, 'mean_image', warpmean, 'input_image')
    register.connect(merge, 'out', warpmean, 'transforms')


    """
    Assign all the output files
    """

    register.connect(reg, 'warped_image', outputnode, 'anat2target')
    register.connect(warpmean, 'output_image', outputnode, 'transformed_mean')
    register.connect(applyxfm, 'out_file', outputnode, 'segmentation_files')
    register.connect(mean2anatbbr, 'out_matrix_file',
                     outputnode, 'func2anat_transform')
    register.connect(reg, 'composite_transform',
                     outputnode, 'anat2target_transform')
    register.connect(merge, 'out', outputnode, 'transforms')

    return register


"""
Creates the main preprocessing workflow
"""


def create_workflow(files,
                    anat_file,
                    target_file,
                    subject_id,
                    TR,
                    num_slices,
                    norm_threshold=1,
                    num_components=5,
                    vol_fwhm=None,
                    lowpass_freq=-1,
                    highpass_freq=-1,
                    sink_directory=os.getcwd(),
                    name='resting'):

    wf = Workflow(name=name)

    # Rename files in case they are named identically
    name_unique = MapNode(Rename(format_string='rest_%(run)02d'),
                          iterfield=['in_file', 'run'],
                          name='rename')
    name_unique.inputs.keep_ext = True
    name_unique.inputs.run = range(1, len(files) + 1)
    name_unique.inputs.in_file = files

    realign = Node(interface=spm.Realign(), name="realign")
    realign.inputs.jobtype = 'estwrite'

    slice_timing = Node(interface=spm.SliceTiming(), name="slice_timing")
    slice_timing.inputs.num_slices = num_slices
    slice_timing.inputs.time_repetition = TR
    slice_timing.inputs.time_acquisition = TR - TR/float(num_slices)
    slice_timing.inputs.slice_order = range(1, num_slices + 1, 2) + range(2, num_slices + 1, 2)
    slice_timing.inputs.ref_slice = int(num_slices/2)

    # Comute TSNR on realigned data regressing polynomials upto order 2
    tsnr = MapNode(TSNR(regress_poly=2), iterfield=['in_file'], name='tsnr')
    wf.connect(slice_timing, 'timecorrected_files', tsnr, 'in_file')

    # Compute the median image across runs
    calc_median = Node(Function(input_names=['in_files'],
                                output_names=['median_file'],
                                function=median,
                                imports=imports),
                       name='median')
    wf.connect(tsnr, 'detrended_file', calc_median, 'in_files')

    """Segment and Register
    """
    registration = create_reg_workflow(name='registration')
    wf.connect(calc_median, 'median_file', registration, 'inputspec.mean_image')
    registration.inputs.inputspec.anatomical_image = anat_file
    registration.inputs.inputspec.target_image = target_file

    """Use :class:`nipype.algorithms.rapidart` to determine which of the
    images in the functional series are outliers based on deviations in
    intensity or movement.
    """

    art = Node(interface=ArtifactDetect(), name="art")
    art.inputs.use_differences = [True, False]
    art.inputs.use_norm = True
    art.inputs.norm_threshold = norm_threshold
    art.inputs.zintensity_threshold = 3
    art.inputs.mask_type = 'spm_global'
    art.inputs.parameter_source = 'SPM'


    """Here we are connecting all the nodes together. Notice that we add the merge node only if you choose
    to use 4D. Also `get_vox_dims` function is passed along the input volume of normalise to set the optimal
    voxel sizes.
    """

    wf.connect([(name_unique, realign, [('out_file', 'in_files')]),
                (realign, slice_timing, [('realigned_files', 'in_files')]),
                (slice_timing, art, [('timecorrected_files', 'realigned_files')]),
                (realign, art, [('realignment_parameters', 'realignment_parameters')]),
                ])

    def selectindex(files, idx):
        import numpy as np
        from nipype.utils.filemanip import filename_to_list, list_to_filename
        return list_to_filename(np.array(filename_to_list(files))[idx].tolist())

    mask = Node(fsl.BET(), name='getmask')
    mask.inputs.mask = True
    wf.connect(calc_median, 'median_file', mask, 'in_file')
    # get segmentation in normalized functional space

    def merge_files(in1, in2):
        out_files = filename_to_list(in1)
        out_files.extend(filename_to_list(in2))
        return out_files

    # filter some noise

    # Compute motion regressors
    motreg = Node(Function(input_names=['motion_params', 'order',
                                        'derivatives'],
                           output_names=['out_files'],
                           function=motion_regressors,
                           imports=imports),
                  name='getmotionregress')
    wf.connect(realign, 'realignment_parameters', motreg, 'motion_params')

    # Create a filter to remove motion and art confounds
    createfilter1 = Node(Function(input_names=['motion_params', 'comp_norm',
                                               'outliers', 'detrend_poly'],
                                  output_names=['out_files'],
                                  function=build_filter1,
                                  imports=imports),
                         name='makemotionbasedfilter')
    createfilter1.inputs.detrend_poly = 2
    wf.connect(motreg, 'out_files', createfilter1, 'motion_params')
    wf.connect(art, 'norm_files', createfilter1, 'comp_norm')
    wf.connect(art, 'outlier_files', createfilter1, 'outliers')


    filter1 = MapNode(fsl.GLM(out_f_name='F_mcart.nii',
                              out_pf_name='pF_mcart.nii',
                              demean=True),
                      iterfield=['in_file', 'design', 'out_res_name'],
                      name='filtermotion')

    wf.connect(slice_timing, 'timecorrected_files', filter1, 'in_file')
    wf.connect(slice_timing, ('timecorrected_files', rename, '_filtermotart'),
               filter1, 'out_res_name')
    wf.connect(createfilter1, 'out_files', filter1, 'design')


    createfilter2 = MapNode(Function(input_names=['realigned_file', 'mask_file',
                                                  'num_components',
                                                  'extra_regressors'],
                                     output_names=['out_files'],
                                     function=extract_noise_components,
                                     imports=imports),
                            iterfield=['realigned_file', 'extra_regressors'],
                            name='makecompcorrfilter')
    createfilter2.inputs.num_components = num_components

    wf.connect(createfilter1, 'out_files', createfilter2, 'extra_regressors')
    wf.connect(filter1, 'out_res', createfilter2, 'realigned_file')
    wf.connect(registration, ('outputspec.segmentation_files', selectindex, [0, 2]),
               createfilter2, 'mask_file')


    filter2 = MapNode(fsl.GLM(out_f_name='F.nii',
                              out_pf_name='pF.nii',
                              demean=True),
                      iterfield=['in_file', 'design', 'out_res_name'],
                      name='filter_noise_nosmooth')
    wf.connect(filter1, 'out_res', filter2, 'in_file')
    wf.connect(filter1, ('out_res', rename, '_cleaned'),
               filter2, 'out_res_name')
    wf.connect(createfilter2, 'out_files', filter2, 'design')
    wf.connect(mask, 'mask_file', filter2, 'mask')

    bandpass = Node(Function(input_names=['files', 'lowpass_freq',
                                           'highpass_freq', 'fs'],
                              output_names=['out_files'],
                              function=bandpass_filter,
                              imports=imports),
                     name='bandpass_unsmooth')
    bandpass.inputs.fs = 1./TR
    bandpass.inputs.highpass_freq = highpass_freq
    bandpass.inputs.lowpass_freq = lowpass_freq
    wf.connect(filter2, 'out_res', bandpass, 'files')

    """Smooth the functional data using
    :class:`nipype.interfaces.spm.Smooth`.
    """

    smooth = Node(interface=spm.Smooth(), name="smooth")
    smooth.inputs.fwhm = vol_fwhm

    wf.connect(bandpass, 'out_files', smooth, 'in_files')


    collector = Node(Merge(2), name='collect_streams')
    wf.connect(smooth, 'smoothed_files', collector, 'in1')
    wf.connect(bandpass, 'out_files', collector, 'in2')

    """
    Transform the remaining images. First to anatomical and then to target
    """

    warpall = MapNode(ants.ApplyTransforms(), iterfield=['input_image'],
                      name='warpall')
    warpall.inputs.input_image_type = 3
    warpall.inputs.interpolation = 'BSpline'
    warpall.inputs.invert_transform_flags = [False, False]
    warpall.inputs.terminal_output = 'file'
    warpall.inputs.reference_image = target_file
    warpall.inputs.args = '--float'
    warpall.inputs.num_threads = 1

    # transform to target
    wf.connect(collector, 'out', warpall, 'input_image')
    wf.connect(registration, 'outputspec.transforms', warpall, 'transforms')

    mask_target = Node(fsl.ImageMaths(op_string='-bin'), name='target_mask')

    wf.connect(registration, 'outputspec.anat2target', mask_target, 'in_file')

    maskts = MapNode(fsl.ApplyMask(), iterfield=['in_file'], name='ts_masker')
    wf.connect(warpall, 'output_image', maskts, 'in_file')
    wf.connect(mask_target, 'out_file', maskts, 'mask_file')

    # Save the relevant data into an output directory
    datasink = Node(interface=DataSink(), name="datasink")
    datasink.inputs.base_directory = sink_directory
    datasink.inputs.container = subject_id
    #datasink.inputs.substitutions = [('_target_subject_', '')]
    #datasink.inputs.regexp_substitutions = (r'(/_.*(\d+/))', r'/run\2')
    wf.connect(realign, 'realignment_parameters', datasink, 'resting.qa.motion')
    wf.connect(art, 'norm_files', datasink, 'resting.qa.art.@norm')
    wf.connect(art, 'intensity_files', datasink, 'resting.qa.art.@intensity')
    wf.connect(art, 'outlier_files', datasink, 'resting.qa.art.@outlier_files')
    wf.connect(registration, 'outputspec.segmentation_files', datasink, 'resting.mask_files')
    wf.connect(registration, 'outputspec.anat2target', datasink, 'resting.qa.ants')
    wf.connect(mask, 'mask_file', datasink, 'resting.mask_files.@brainmask')
    wf.connect(mask_target, 'out_file', datasink, 'resting.mask_files.target')
    wf.connect(filter1, 'out_f', datasink, 'resting.qa.compmaps.@mc_F')
    wf.connect(filter1, 'out_pf', datasink, 'resting.qa.compmaps.@mc_pF')
    wf.connect(filter2, 'out_f', datasink, 'resting.qa.compmaps')
    wf.connect(filter2, 'out_pf', datasink, 'resting.qa.compmaps.@p')
    wf.connect(bandpass, 'out_files', datasink, 'resting.timeseries.bandpassed')
    wf.connect(smooth, 'smoothed_files', datasink, 'resting.timeseries.smoothed')
    wf.connect(createfilter1, 'out_files',
               datasink, 'resting.regress.@regressors')
    wf.connect(createfilter2, 'out_files',
               datasink, 'resting.regress.@compcorr')
    wf.connect(maskts, 'out_file', datasink, 'resting.timeseries.target')
    return wf


if __name__ == "__main__":
    from glob import glob

    subj_id = 'SUB_1024011'
    files = sorted(glob(os.path.abspath('%s/E?/func/rest.nii' % subj_id)))
    anat_file = glob(os.path.abspath('%s/EO/anat/anat.nii' % subj_id))[0]
    target_file = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
    wf = create_workflow(files, anat_file, target_file, subj_id,
                         2.0, 33, vol_fwhm=6.0,
                         lowpass_freq=0.1, highpass_freq=0.01,
                         sink_directory=os.getcwd(),
                         name='resting_' + subj_id)
    wf.base_dir = os.getcwd()
    wf.run(plugin='MultiProc', plugin_args={'nprocs': 4})
    #wf.write_graph(graph2use='colored')
    #wf.run()

