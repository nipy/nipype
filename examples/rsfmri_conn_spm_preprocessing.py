
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

from nipype.interfaces import (spm, fsl, Function)
fsl.FSLCommand.set_default_output_type('NIFTI')

from nipype import Workflow, Node, MapNode
from nipype.interfaces import matlab as mlab

mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodisplay")
# If SPM is not in your MATLAB path you should add it here
mlab.MatlabCommand.set_default_paths('/cm/shared/openmind/spm/spm12b/spm12b_r5918/')

from nipype.algorithms.rapidart import ArtifactDetect
from nipype.interfaces.utility import Rename, Merge
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


"""
Creates the main preprocessing workflow
"""


def create_workflow(files,
                    anat_file,
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

    """Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
    body registration of the functional data to the structural data.
    """

    coregister = Node(interface=spm.Coregister(), name="coregister")
    coregister.inputs.jobtype = 'estimate'
    coregister.inputs.target = anat_file

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

    segment = Node(interface=spm.Segment(), name="segment")
    segment.inputs.save_bias_corrected = True
    segment.inputs.data = anat_file

    """Uncomment the following line for faster execution
    """

    #segment.inputs.gaussians_per_class = [1, 1, 1, 4]

    """Warp functional and structural data to SPM's T1 template using
    :class:`nipype.interfaces.spm.Normalize`.  The tutorial data set
    includes the template image, T1.nii.
    """

    normalize_func = Node(interface=spm.Normalize(), name = "normalize_func")
    normalize_func.inputs.jobtype = "write"
    normalize_func.inputs.write_voxel_sizes =[2., 2., 2.]

    """Smooth the functional data using
    :class:`nipype.interfaces.spm.Smooth`.
    """

    smooth = Node(interface=spm.Smooth(), name = "smooth")
    smooth.inputs.fwhm = vol_fwhm

    """Here we are connecting all the nodes together. Notice that we add the merge node only if you choose
    to use 4D. Also `get_vox_dims` function is passed along the input volume of normalise to set the optimal
    voxel sizes.
    """

    wf.connect([(name_unique, realign, [('out_file', 'in_files')]),
                (realign, coregister, [('mean_image', 'source')]),
                (segment, normalize_func, [('transformation_mat', 'parameter_file')]),
                (realign, slice_timing, [('realigned_files', 'in_files')]),
                (slice_timing, normalize_func, [('timecorrected_files', 'apply_to_files')]),
                (normalize_func, smooth, [('normalized_files', 'in_files')]),
                (realign, art, [('realignment_parameters', 'realignment_parameters')]),
                (smooth, art, [('smoothed_files', 'realigned_files')]),
                ])

    def selectN(files, N=1):
        from nipype.utils.filemanip import filename_to_list, list_to_filename
        return list_to_filename(filename_to_list(files)[:N])

    mask = Node(fsl.BET(), name='getmask')
    mask.inputs.mask = True
    wf.connect(normalize_func, ('normalized_files', selectN, 1), mask, 'in_file')
    # get segmentation in normalized functional space

    segment.inputs.wm_output_type = [False, False, True]
    segment.inputs.csf_output_type = [False, False, True]
    segment.inputs.gm_output_type = [False, False, True]

    def merge_files(in1, in2):
        out_files = filename_to_list(in1)
        out_files.extend(filename_to_list(in2))
        return out_files

    merge = Node(Merge(3), name='merge')
    wf.connect(segment, 'native_wm_image', merge, 'in1')
    wf.connect(segment, 'native_csf_image', merge, 'in2')
    wf.connect(segment, 'native_gm_image', merge, 'in3')

    normalize_segs = Node(interface=spm.Normalize(), name = "normalize_segs")
    normalize_segs.inputs.jobtype = "write"
    normalize_segs.inputs.write_voxel_sizes = [2., 2., 2.]

    wf.connect(merge, 'out', normalize_segs, 'apply_to_files')
    wf.connect(segment, 'transformation_mat', normalize_segs, 'parameter_file')

    # binarize and erode
    bin_and_erode = MapNode(fsl.ImageMaths(),
                            iterfield=['in_file'],
                            name='bin_and_erode')
    bin_and_erode.inputs.op_string = '-thr 0.99 -bin -ero'

    wf.connect(normalize_segs, 'normalized_files',
               bin_and_erode, 'in_file')

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

    # Filter the motion and art confounds and detrend
    filter1 = MapNode(fsl.GLM(out_f_name='F_mcart.nii',
                              out_pf_name='pF_mcart.nii',
                              demean=True),
                      iterfield=['in_file', 'design', 'out_res_name'],
                      name='filtermotion')

    wf.connect(normalize_func, 'normalized_files', filter1, 'in_file')
    wf.connect(normalize_func, ('normalized_files', rename, '_filtermotart'),
               filter1, 'out_res_name')
    wf.connect(createfilter1, 'out_files', filter1, 'design')
    #wf.connect(masktransform, 'transformed_file', filter1, 'mask')

    # Create a filter to remove noise components based on white matter and CSF
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
    wf.connect(bin_and_erode, ('out_file', selectN, 2), createfilter2, 'mask_file')

    # Filter noise components from unsmoothed data
    filter2 = MapNode(fsl.GLM(out_f_name='F.nii',
                              out_pf_name='pF.nii',
                              demean=True),
                      iterfield=['in_file', 'design', 'out_res_name'],
                      name='filter_noise_nosmooth')
    wf.connect(normalize_func, 'normalized_files', filter2, 'in_file')
    wf.connect(normalize_func, ('normalized_files', rename, '_unsmooth_cleaned'),
               filter2, 'out_res_name')
    wf.connect(createfilter2, 'out_files', filter2, 'design')
    wf.connect(mask, 'mask_file', filter2, 'mask')

    # Filter noise components from smoothed data
    filter3 = MapNode(fsl.GLM(out_f_name='F.nii',
                              out_pf_name='pF.nii',
                              demean=True),
                      iterfield=['in_file', 'design', 'out_res_name'],
                      name='filter_noise_smooth')
    wf.connect(smooth, ('smoothed_files', rename, '_cleaned'),
               filter3, 'out_res_name')
    wf.connect(smooth, 'smoothed_files', filter3, 'in_file')
    wf.connect(createfilter2, 'out_files', filter3, 'design')
    wf.connect(mask, 'mask_file', filter3, 'mask')

    # Bandpass filter the data
    bandpass1 = Node(Function(input_names=['files', 'lowpass_freq',
                                           'highpass_freq', 'fs'],
                              output_names=['out_files'],
                              function=bandpass_filter,
                              imports=imports),
                     name='bandpass_unsmooth')
    bandpass1.inputs.fs = 1./TR

    bandpass1.inputs.highpass_freq = highpass_freq
    bandpass1.inputs.lowpass_freq = lowpass_freq
    wf.connect(filter2, 'out_res', bandpass1, 'files')

    bandpass2 = bandpass1.clone(name='bandpass_smooth')
    wf.connect(filter3, 'out_res', bandpass2, 'files')

    bandpass = Node(Function(input_names=['in1', 'in2'],
                              output_names=['out_file'],
                              function=merge_files,
                              imports=imports),
                     name='bandpass_merge')
    wf.connect(bandpass1, 'out_files', bandpass, 'in1')
    wf.connect(bandpass2, 'out_files', bandpass, 'in2')

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
    wf.connect(smooth, 'smoothed_files', datasink, 'resting.timeseries.fullpass')
    wf.connect(bin_and_erode, 'out_file', datasink, 'resting.mask_files')
    wf.connect(mask, 'mask_file', datasink, 'resting.mask_files.@brainmask')
    wf.connect(filter1, 'out_f', datasink, 'resting.qa.compmaps.@mc_F')
    wf.connect(filter1, 'out_pf', datasink, 'resting.qa.compmaps.@mc_pF')
    wf.connect(filter2, 'out_f', datasink, 'resting.qa.compmaps')
    wf.connect(filter2, 'out_pf', datasink, 'resting.qa.compmaps.@p')
    wf.connect(filter3, 'out_f', datasink, 'resting.qa.compmaps.@sF')
    wf.connect(filter3, 'out_pf', datasink, 'resting.qa.compmaps.@sp')
    wf.connect(bandpass, 'out_file', datasink, 'resting.timeseries.bandpassed')
    wf.connect(createfilter1, 'out_files',
               datasink, 'resting.regress.@regressors')
    wf.connect(createfilter2, 'out_files',
               datasink, 'resting.regress.@compcorr')
    return wf


if __name__ == "__main__":
    from glob import glob

    subj_id = 'SUB_1024011'
    files = sorted(glob(os.path.abspath('%s/E?/func/rest.nii' % subj_id)))
    anat_file = glob(os.path.abspath('%s/EO/anat/anat.nii' % subj_id))[0]
    wf = create_workflow(files, anat_file, subj_id, 2.0, 33, vol_fwhm=6.0,
                         lowpass_freq=0.1, highpass_freq=0.01,
                         sink_directory=os.getcwd(),
                         name='resting_' + subj_id)
    wf.base_dir = os.getcwd()
    #wf.run(plugin='MultiProc', plugin_args={'nprocs': 4})
    wf.run()

