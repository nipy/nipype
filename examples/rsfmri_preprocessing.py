#!/usr/bin/env python
"""
================================================================
rsfMRI: AFNI, ANTS, DicomStack, FreeSurfer, FSL, Nipy, aCompCorr
================================================================


A preprocessing workflow for Siemens resting state data.

This workflow makes use of:

- AFNI
- ANTS
- C3D_Affine_Tool
- DicomStack
- FreeSurfer
- FSL
- NiPy

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

   >>> from nipype import freesurfer as fs
   >>> rs = fs.Resample()
   >>> rs.inputs.in_file = 'OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152.nii.gz'
   >>> rs.inputs.resampled_file = 'OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152_2mm.nii.gz'
   >>> rs.inputs.voxel_size = (2., 2., 2.)
   >>> rs.inputs.args = '-rt nearest -ns 1'
   >>> res = rs.run()

"""

import os

from nipype.interfaces.base import CommandLine
CommandLine.set_default_terminal_output('file')

from nipype import config
config.enable_provenance()

from nipype import (ants, afni, fsl, freesurfer, nipy, Function, DataSink)
from nipype import Workflow, Node, MapNode

from nipype.algorithms.rapidart import ArtifactDetect
from nipype.algorithms.misc import TSNR
from nipype.interfaces.fsl import EPIDeWarp
from nipype.interfaces.io import FreeSurferSource
from nipype.interfaces.c3 import C3dAffineTool
from nipype.interfaces.utility import Merge, IdentityInterface
from nipype.utils.filemanip import filename_to_list

import numpy as np
import scipy as sp
import nibabel as nb
from dcmstack.extract import default_extractor
from dicom import read_file

imports = ['import os',
           'import nibabel as nb',
           'import numpy as np',
           'import scipy as sp',
           'from nipype.utils.filemanip import filename_to_list'
           ]


def get_info(dicom_files):
    """Given a Siemens dicom file return metadata

    Returns
    -------
    RepetitionTime
    Slice Acquisition Times
    Spacing between slices
    """
    meta = default_extractor(read_file(filename_to_list(dicom_files)[0],
                                       stop_before_pixels=True,
                                       force=True))
    return (meta['RepetitionTime']/1000., meta['CsaImage.MosaicRefAcqTimes'],
            meta['SpacingBetweenSlices'])


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
        if not average:
            average = data
        else:
            average = average + data
    median_img = nb.Nifti1Image(average/float(idx + 1),
                                img.get_affine(), img.get_header())
    filename = os.path.join(os.getcwd(), 'median.nii.gz')
    median_img.to_filename(filename)
    return filename


def get_aparc_aseg(files):
    """Return the aparc+aseg.mgz file"""
    for name in files:
        if 'aparc+aseg.mgz' in name:
            return name
    raise ValueError('aparc+aseg.mgz not found')


def motion_regressors(motion_params, order=2, derivatives=2):
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


def build_filter1(motion_params, comp_norm, outliers):
    """Builds a regressor set comprisong motion parameters, composite norm and
    outliers

    The outliers are added as a single time point column for each outlier


    Parameters
    ----------

    motion_params: a text file containing motion parameters and its derivatives
    comp_norm: a text file containing the composite norm
    outliers: a text file containing 0-based outlier indices

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
        filename = os.path.join(os.getcwd(), "filter_regressor%02d.txt" % idx)
        np.savetxt(filename, out_params, fmt="%.10f")
        out_files.append(filename)
    return out_files


def extract_noise_components(realigned_file, mask_file, num_components=6):
    """Derive components most reflective of physiological noise

    Parameters
    ----------
    realigned_file: a 4D Nifti file containing realigned volumes
    mask_file: a 3D Nifti file containing white matter + ventricular masks
    num_components: number of components to use for noise decomposition

    Returns
    -------
    components_file: a text file containing the noise components
    """
    imgseries = nb.load(realigned_file)
    noise_mask = nb.load(mask_file)
    voxel_timecourses = imgseries.get_data()[np.nonzero(noise_mask.get_data())]
    voxel_timecourses = voxel_timecourses.byteswap().newbyteorder()
    voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0
    _, _, v = sp.linalg.svd(voxel_timecourses, full_matrices=False)
    components_file = os.path.join(os.getcwd(), 'noise_components.txt')
    np.savetxt(components_file, v[:num_components, :].T)
    return components_file


def extract_subrois(timeseries_file, label_file, indices):
    """Extract voxel time courses for each subcortical roi index

    Parameters
    ----------

    timeseries_file: a 4D Nifti file
    label_file: a 3D file containing rois in the same space/size of the 4D file
    indices: a list of indices for ROIs to extract.

    Returns
    -------
    out_file: a text file containing time courses for each voxel of each roi
        The first four columns are: freesurfer index, i, j, k positions in the
        label file
    """
    img = nb.load(timeseries_file)
    data = img.get_data()
    roiimg = nb.load(label_file)
    rois = roiimg.get_data()
    out_ts_file = os.path.join(os.getcwd(), 'subcortical_timeseries.txt')
    with open(out_ts_file, 'wt') as fp:
        for fsindex in indices:
            ijk = np.nonzero(rois == fsindex)
            ts = data[ijk]
            for i0, row in enumerate(ts):
                fp.write('%d,%d,%d,%d,' % (fsindex, ijk[0][i0],
                                           ijk[1][i0], ijk[2][i0]) +
                         ','.join(['%.10f' % val for val in row]) + '\n')
    return out_ts_file


def combine_hemi(left, right):
    """Combine left and right hemisphere time series into a single text file
    """
    lh_data = nb.load(left).get_data()
    rh_data = nb.load(right).get_data()

    indices = np.vstack((1000000 + np.arange(0, lh_data.shape[0])[:, None],
                         2000000 + np.arange(0, rh_data.shape[0])[:, None]))
    all_data = np.hstack((indices, np.vstack((lh_data.squeeze(),
                                              rh_data.squeeze()))))
    filename = 'combined_surf.txt'
    np.savetxt(filename, all_data,
               fmt=','.join(['%d'] + ['%.10f'] * (all_data.shape[1] - 1)))
    return os.path.abspath(filename)


"""
Creates the main preprocessing workflow
"""


def create_workflow(files,
                    subject_id,
                    n_vol=0,
                    despike=True,
                    TR=None,
                    slice_times=None,
                    slice_thickness=None,
                    fieldmap_images=[],
                    norm_threshold=1,
                    num_components=6,
                    vol_fwhm=None,
                    surf_fwhm=None,
                    lowpass_freq=-1,
                    highpass_freq=-1,
                    sink_directory=os.getcwd(),
                    FM_TEdiff=2.46,
                    FM_sigma=2,
                    FM_echo_spacing=.7,
                    target_subject=['fsaverage3', 'fsaverage4'],
                    name='resting'):

    wf = Workflow(name=name)

    # Skip starting volumes
    remove_vol = MapNode(fsl.ExtractROI(t_min=n_vol, t_size=-1),
                         iterfield=['in_file'],
                         name="remove_volumes")
    remove_vol.inputs.in_file = files

    # Run AFNI's despike. This is always run, however, whether this is fed to
    # realign depends on the input configuration
    despiker = MapNode(afni.Despike(outputtype='NIFTI_GZ'),
                       iterfield=['in_file'],
                       name='despike')
    #despiker.plugin_args = {'qsub_args': '-l nodes=1:ppn='}

    wf.connect(remove_vol, 'roi_file', despiker, 'in_file')

    # Run Nipy joint slice timing and realignment algorithm
    realign = Node(nipy.SpaceTimeRealigner(), name='realign')
    realign.inputs.tr = TR
    realign.inputs.slice_times = slice_times
    realign.inputs.slice_info = 2

    if despike:
        wf.connect(despiker, 'out_file', realign, 'in_file')
    else:
        wf.connect(remove_vol, 'roi_file', realign, 'in_file')

    # Comute TSNR on realigned data regressing polynomials upto order 2
    tsnr = MapNode(TSNR(regress_poly=2), iterfield=['in_file'], name='tsnr')
    wf.connect(realign, 'out_file', tsnr, 'in_file')

    # Compute the median image across runs
    calc_median = Node(Function(input_names=['in_files'],
                                output_names=['median_file'],
                                function=median,
                                imports=imports),
                       name='median')
    wf.connect(tsnr, 'detrended_file', calc_median, 'in_files')

    # Coregister the median to the surface
    register = Node(freesurfer.BBRegister(),
                    name='bbregister')
    register.inputs.subject_id = subject_id
    register.inputs.init = 'fsl'
    register.inputs.contrast_type = 't2'
    register.inputs.out_fsl_file = True
    register.inputs.epi_mask = True

    # Compute fieldmaps and unwarp using them
    if fieldmap_images:
        fieldmap = Node(interface=EPIDeWarp(), name='fieldmap_unwarp')
        fieldmap.inputs.tediff = FM_TEdiff
        fieldmap.inputs.esp = FM_echo_spacing
        fieldmap.inputs.sigma = FM_sigma
        fieldmap.inputs.mag_file = fieldmap_images[0]
        fieldmap.inputs.dph_file = fieldmap_images[1]
        wf.connect(calc_median, 'median_file', fieldmap, 'exf_file')

        dewarper = MapNode(interface=fsl.FUGUE(), iterfield=['in_file'],
                           name='dewarper')
        wf.connect(tsnr, 'detrended_file', dewarper, 'in_file')
        wf.connect(fieldmap, 'exf_mask', dewarper, 'mask_file')
        wf.connect(fieldmap, 'vsm_file', dewarper, 'shift_in_file')
        wf.connect(fieldmap, 'exfdw', register, 'source_file')
    else:
        wf.connect(calc_median, 'median_file', register, 'source_file')

    # Get the subject's freesurfer source directory
    fssource = Node(FreeSurferSource(),
                    name='fssource')
    fssource.inputs.subject_id = subject_id
    fssource.inputs.subjects_dir = os.environ['SUBJECTS_DIR']

    # Extract wm+csf, brain masks by eroding freesurfer lables and then
    # transform the masks into the space of the median
    wmcsf = Node(freesurfer.Binarize(), name='wmcsfmask')
    mask = wmcsf.clone('anatmask')
    wmcsftransform = Node(freesurfer.ApplyVolTransform(inverse=True,
                                                       interp='nearest'),
                          name='wmcsftransform')
    wmcsftransform.inputs.subjects_dir = os.environ['SUBJECTS_DIR']
    wmcsf.inputs.wm_ven_csf = True
    wmcsf.inputs.match = [4, 5, 14, 15, 24, 31, 43, 44, 63]
    wmcsf.inputs.binary_file = 'wmcsf.nii.gz'
    wmcsf.inputs.erode = int(np.ceil(slice_thickness))
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), wmcsf, 'in_file')
    if fieldmap_images:
        wf.connect(fieldmap, 'exf_mask', wmcsftransform, 'source_file')
    else:
        wf.connect(calc_median, 'median_file', wmcsftransform, 'source_file')
    wf.connect(register, 'out_reg_file', wmcsftransform, 'reg_file')
    wf.connect(wmcsf, 'binary_file', wmcsftransform, 'target_file')

    mask.inputs.binary_file = 'mask.nii.gz'
    mask.inputs.dilate = int(np.ceil(slice_thickness)) + 1
    mask.inputs.erode = int(np.ceil(slice_thickness))
    mask.inputs.min = 0.5
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), mask, 'in_file')
    masktransform = wmcsftransform.clone("masktransform")
    if fieldmap_images:
        wf.connect(fieldmap, 'exf_mask', masktransform, 'source_file')
    else:
        wf.connect(calc_median, 'median_file', masktransform, 'source_file')
    wf.connect(register, 'out_reg_file', masktransform, 'reg_file')
    wf.connect(mask, 'binary_file', masktransform, 'target_file')

    # Compute Art outliers
    art = Node(interface=ArtifactDetect(use_differences=[True, False],
                                        use_norm=True,
                                        norm_threshold=norm_threshold,
                                        zintensity_threshold=3,
                                        parameter_source='NiPy',
                                        bound_by_brainmask=True,
                                        save_plot=False,
                                        mask_type='file'),
               name="art")
    if fieldmap_images:
        wf.connect(dewarper, 'unwarped_file', art, 'realigned_files')
    else:
        wf.connect(tsnr, 'detrended_file', art, 'realigned_files')
    wf.connect(realign, 'par_file',
               art, 'realignment_parameters')
    wf.connect(masktransform, 'transformed_file', art, 'mask_file')

    # Compute motion regressors
    motreg = Node(Function(input_names=['motion_params', 'order',
                                        'derivatives'],
                           output_names=['out_files'],
                           function=motion_regressors,
                           imports=imports),
                  name='getmotionregress')
    wf.connect(realign, 'par_file', motreg, 'motion_params')

    # Create a filter to remove motion and art confounds
    createfilter1 = Node(Function(input_names=['motion_params', 'comp_norm',
                                               'outliers'],
                                  output_names=['out_files'],
                                  function=build_filter1,
                                  imports=imports),
                         name='makemotionbasedfilter')
    wf.connect(motreg, 'out_files', createfilter1, 'motion_params')
    wf.connect(art, 'norm_files', createfilter1, 'comp_norm')
    wf.connect(art, 'outlier_files', createfilter1, 'outliers')

    # Filter the motion and art confounds
    filter1 = MapNode(fsl.GLM(out_res_name='timeseries.nii.gz',
                              demean=True),
                      iterfield=['in_file', 'design'],
                      name='filtermotion')
    if fieldmap_images:
        wf.connect(dewarper, 'unwarped_file', filter1, 'in_file')
    else:
        wf.connect(tsnr, 'detrended_file', filter1, 'in_file')
    wf.connect(createfilter1, 'out_files', filter1, 'design')
    wf.connect(masktransform, 'transformed_file', filter1, 'mask')

    # Create a filter to remove noise components based on white matter and CSF
    createfilter2 = MapNode(Function(input_names=['realigned_file', 'mask_file',
                                                  'num_components'],
                                     output_names=['out_files'],
                                     function=extract_noise_components,
                                     imports=imports),
                            iterfield=['realigned_file'],
                            name='makecompcorrfilter')
    createfilter2.inputs.num_components = num_components
    wf.connect(filter1, 'out_res', createfilter2, 'realigned_file')
    wf.connect(masktransform, 'transformed_file', createfilter2, 'mask_file')

    # Filter noise components
    filter2 = MapNode(fsl.GLM(out_res_name='timeseries_cleaned.nii.gz',
                              demean=True),
                      iterfield=['in_file', 'design'],
                      name='filtercompcorr')
    wf.connect(filter1, 'out_res', filter2, 'in_file')
    wf.connect(createfilter2, 'out_files', filter2, 'design')
    wf.connect(masktransform, 'transformed_file', filter2, 'mask')

    # Smoothing using surface and volume smoothing
    smooth = MapNode(freesurfer.Smooth(),
                     iterfield=['in_file'],
                     name='smooth')
    smooth.inputs.proj_frac_avg = (0.1, 0.9, 0.1)
    if surf_fwhm is None:
        surf_fwhm = 5 * slice_thickness
    smooth.inputs.surface_fwhm = surf_fwhm
    if vol_fwhm is None:
        vol_fwhm = 2 * slice_thickness
    smooth.inputs.vol_fwhm = vol_fwhm
    wf.connect(filter2, 'out_res',  smooth, 'in_file')
    wf.connect(register, 'out_reg_file', smooth, 'reg_file')

    # Bandpass filter the data
    bandpass = MapNode(fsl.TemporalFilter(),
                       iterfield=['in_file'],
                       name='bandpassfilter')
    if highpass_freq < 0:
            bandpass.inputs.highpass_sigma = -1
    else:
            bandpass.inputs.highpass_sigma = 1. / (2 * TR * highpass_freq)
    if lowpass_freq < 0:
            bandpass.inputs.lowpass_sigma = -1
    else:
            bandpass.inputs.lowpass_sigma = 1. / (2 * TR * lowpass_freq)
    wf.connect(smooth, 'smoothed_file', bandpass, 'in_file')

    # Convert aparc to subject functional space
    aparctransform = wmcsftransform.clone("aparctransform")
    if fieldmap_images:
        wf.connect(fieldmap, 'exf_mask', aparctransform, 'source_file')
    else:
        wf.connect(calc_median, 'median_file', aparctransform, 'source_file')
    wf.connect(register, 'out_reg_file', aparctransform, 'reg_file')
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg),
               aparctransform, 'target_file')

    # Sample the average time series in aparc ROIs
    sampleaparc = MapNode(freesurfer.SegStats(avgwf_txt_file=True,
                                              default_color_table=True),
                          iterfield=['in_file'],
                          name='aparc_ts')
    sampleaparc.inputs.segment_id = ([8] + range(10, 14) + [17, 18, 26, 47] +
                                     range(49, 55) + [58] + range(1001, 1036) +
                                     range(2001, 2036))

    wf.connect(aparctransform, 'transformed_file',
               sampleaparc, 'segmentation_file')
    wf.connect(bandpass, 'out_file', sampleaparc, 'in_file')

    # Sample the time series onto the surface of the target surface. Performs
    # sampling into left and right hemisphere
    target = Node(IdentityInterface(fields=['target_subject']), name='target')
    target.iterables = ('target_subject', filename_to_list(target_subject))

    samplerlh = MapNode(freesurfer.SampleToSurface(),
                        iterfield=['source_file'],
                        name='sampler_lh')
    samplerlh.inputs.sampling_method = "average"
    samplerlh.inputs.sampling_range = (0.1, 0.9, 0.1)
    samplerlh.inputs.sampling_units = "frac"
    samplerlh.inputs.interp_method = "trilinear"
    #samplerlh.inputs.cortex_mask = True
    samplerlh.inputs.out_type = 'niigz'
    samplerlh.inputs.subjects_dir = os.environ['SUBJECTS_DIR']

    samplerrh = samplerlh.clone('sampler_rh')

    samplerlh.inputs.hemi = 'lh'
    wf.connect(bandpass, 'out_file', samplerlh, 'source_file')
    wf.connect(register, 'out_reg_file', samplerlh, 'reg_file')
    wf.connect(target, 'target_subject', samplerlh, 'target_subject')

    samplerrh.set_input('hemi', 'rh')
    wf.connect(bandpass, 'out_file', samplerrh, 'source_file')
    wf.connect(register, 'out_reg_file', samplerrh, 'reg_file')
    wf.connect(target, 'target_subject', samplerrh, 'target_subject')

    # Combine left and right hemisphere to text file
    combiner = MapNode(Function(input_names=['left', 'right'],
                                output_names=['out_file'],
                                function=combine_hemi,
                                imports=imports),
                       iterfield=['left', 'right'],
                       name="combiner")
    wf.connect(samplerlh, 'out_file', combiner, 'left')
    wf.connect(samplerrh, 'out_file', combiner, 'right')

    # Compute registration between the subject's structural and MNI template
    # This is currently set to perform a very quick registration. However, the
    # registration can be made significantly more accurate for cortical
    # structures by increasing the number of iterations
    # All parameters are set using the example from:
    # https://github.com/stnava/ANTs/blob/master/Scripts/newAntsExample.sh
    reg = Node(ants.Registration(), name='antsRegister')
    reg.inputs.output_transform_prefix = "output_"
    reg.inputs.transforms = ['Translation', 'Rigid', 'Affine', 'SyN']
    reg.inputs.transform_parameters = [(0.1,), (0.1,), (0.1,), (0.2, 3.0, 0.0)]
    # reg.inputs.number_of_iterations = ([[10000, 111110, 11110]]*3 +
    #                                    [[100, 50, 30]])
    reg.inputs.number_of_iterations = [[100, 100, 100]] * 3 + [[100, 20, 10]]
    reg.inputs.dimension = 3
    reg.inputs.write_composite_transform = True
    reg.inputs.collapse_output_transforms = False
    reg.inputs.metric = ['Mattes'] * 3 + [['Mattes', 'CC']]
    reg.inputs.metric_weight = [1] * 3 + [[0.5, 0.5]]
    reg.inputs.radius_or_number_of_bins = [32] * 3 + [[32, 4]]
    reg.inputs.sampling_strategy = ['Regular'] * 3 + [[None, None]]
    reg.inputs.sampling_percentage = [0.3] * 3 + [[None, None]]
    reg.inputs.convergence_threshold = [1.e-8] * 3 + [-0.01]
    reg.inputs.convergence_window_size = [20] * 3 + [5]
    reg.inputs.smoothing_sigmas = [[4, 2, 1]] * 3 + [[1, 0.5, 0]]
    reg.inputs.sigma_units = ['vox'] * 4
    reg.inputs.shrink_factors = [[6, 4, 2]] + [[3, 2, 1]]*2 + [[4, 2, 1]]
    reg.inputs.use_estimate_learning_rate_once = [True] * 4
    reg.inputs.use_histogram_matching = [False] * 3 + [True]
    reg.inputs.output_warped_image = 'output_warped_image.nii.gz'
    reg.inputs.fixed_image = \
        os.path.abspath('OASIS-30_Atropos_template_in_MNI152_2mm.nii.gz')
    reg.inputs.num_threads = 4
    reg.plugin_args = {'qsub_args': '-l nodes=1:ppn=4'}

    # Convert T1.mgz to nifti for using with ANTS
    convert = Node(freesurfer.MRIConvert(out_type='niigz'), name='convert2nii')
    wf.connect(fssource, 'T1', convert, 'in_file')

    # Mask the T1.mgz file with the brain mask computed earlier
    maskT1 = Node(fsl.BinaryMaths(operation='mul'), name='maskT1')
    wf.connect(mask, 'binary_file', maskT1, 'operand_file')
    wf.connect(convert, 'out_file', maskT1, 'in_file')
    wf.connect(maskT1, 'out_file', reg, 'moving_image')

    # Convert the BBRegister transformation to ANTS ITK format
    convert2itk = MapNode(C3dAffineTool(),
                          iterfield=['transform_file', 'source_file'],
                          name='convert2itk')
    convert2itk.inputs.fsl2ras = True
    convert2itk.inputs.itk_transform = True
    wf.connect(register, 'out_fsl_file', convert2itk, 'transform_file')
    if fieldmap_images:
        wf.connect(fieldmap, 'exf_mask', convert2itk, 'source_file')
    else:
        wf.connect(calc_median, 'median_file', convert2itk, 'source_file')
    wf.connect(convert, 'out_file', convert2itk, 'reference_file')

    # Concatenate the affine and ants transforms into a list
    pickfirst = lambda x: x[0]
    merge = MapNode(Merge(2), iterfield=['in2'], name='mergexfm')
    wf.connect(convert2itk, 'itk_transform', merge, 'in2')
    wf.connect(reg, ('composite_transform', pickfirst), merge, 'in1')

    # Apply the combined transform to the time series file
    sample2mni = MapNode(ants.ApplyTransforms(),
                         iterfield=['input_image', 'transforms'],
                         name='sample2mni')
    sample2mni.inputs.input_image_type = 3
    sample2mni.inputs.interpolation = 'BSpline'
    sample2mni.inputs.invert_transform_flags = [False, False]
    sample2mni.inputs.reference_image = \
        os.path.abspath('OASIS-30_Atropos_template_in_MNI152_2mm.nii.gz')
    sample2mni.inputs.terminal_output = 'file'
    wf.connect(bandpass, 'out_file', sample2mni, 'input_image')
    wf.connect(merge, 'out', sample2mni, 'transforms')

    # Sample the time series file for each subcortical roi
    ts2txt = MapNode(Function(input_names=['timeseries_file', 'label_file',
                                           'indices'],
                              output_names=['out_file'],
                              function=extract_subrois,
                              imports=imports),
                     iterfield=['timeseries_file'],
                     name='getsubcortts')
    ts2txt.inputs.indices = [8] + range(10, 14) + [17, 18, 26, 47] +\
                            range(49, 55) + [58]
    ts2txt.inputs.label_file = \
        os.path.abspath(('OASIS-TRT-20_jointfusion_DKT31_CMA_labels_in_MNI152_'
                         '2mm.nii.gz'))
    wf.connect(sample2mni, 'output_image', ts2txt, 'timeseries_file')

    # Save the relevant data into an output directory
    datasink = Node(interface=DataSink(), name="datasink")
    datasink.inputs.base_directory = sink_directory
    datasink.inputs.container = subject_id
    datasink.inputs.substitutions = [('_target_subject_', '')]
    datasink.inputs.regexp_substitutions = (r'(/_.*(\d+/))', r'/run\2')
    wf.connect(despiker, 'out_file', datasink, 'resting.qa.despike')
    wf.connect(realign, 'par_file', datasink, 'resting.qa.motion')
    wf.connect(tsnr, 'tsnr_file', datasink, 'resting.qa.tsnr')
    wf.connect(tsnr, 'mean_file', datasink, 'resting.qa.tsnr.@mean')
    wf.connect(tsnr, 'stddev_file', datasink, 'resting.qa.@tsnr_stddev')
    if fieldmap_images:
        wf.connect(fieldmap, 'exf_mask', datasink, 'resting.reference')
    else:
        wf.connect(calc_median, 'median_file', datasink, 'resting.reference')
    wf.connect(art, 'norm_files', datasink, 'resting.qa.art.@norm')
    wf.connect(art, 'intensity_files', datasink, 'resting.qa.art.@intensity')
    wf.connect(art, 'outlier_files', datasink, 'resting.qa.art.@outlier_files')
    wf.connect(mask, 'binary_file', datasink, 'resting.mask')
    wf.connect(masktransform, 'transformed_file',
               datasink, 'resting.mask.@transformed_file')
    wf.connect(register, 'out_reg_file', datasink, 'resting.registration.bbreg')
    wf.connect(reg, ('composite_transform', pickfirst),
               datasink, 'resting.registration.ants')
    wf.connect(register, 'min_cost_file',
               datasink, 'resting.qa.bbreg.@mincost')
    wf.connect(smooth, 'smoothed_file', datasink, 'resting.timeseries.fullpass')
    wf.connect(bandpass, 'out_file', datasink, 'resting.timeseries.bandpassed')
    wf.connect(sample2mni, 'output_image', datasink, 'resting.timeseries.mni')
    wf.connect(createfilter1, 'out_files',
               datasink, 'resting.regress.@regressors')
    wf.connect(createfilter2, 'out_files',
               datasink, 'resting.regress.@compcorr')
    wf.connect(sampleaparc, 'summary_file',
               datasink, 'resting.parcellations.aparc')
    wf.connect(sampleaparc, 'avgwf_txt_file',
               datasink, 'resting.parcellations.aparc.@avgwf')
    wf.connect(ts2txt, 'out_file',
               datasink, 'resting.parcellations.grayo.@subcortical')
    datasink2 = Node(interface=DataSink(), name="datasink2")
    datasink2.inputs.base_directory = sink_directory
    datasink2.inputs.container = subject_id
    datasink2.inputs.substitutions = [('_target_subject_', '')]
    datasink2.inputs.regexp_substitutions = (r'(/_.*(\d+/))', r'/run\2')
    wf.connect(combiner, 'out_file',
               datasink2, 'resting.parcellations.grayo.@surface')
    return wf


"""
Creates the full workflow including getting information from dicom files
"""


def create_resting_workflow(args, name='resting'):
    TR = args.TR
    slice_times = args.slice_times
    slice_thickness = None
    if args.dicom_file:
        TR, slice_times, slice_thickness = get_info(args.dicom_file)
        slice_times = (np.array(slice_times)/1000.).tolist()

    if slice_thickness is None:
        from nibabel import load
        img = load(args.files[0])
        slice_thickness = max(img.get_header().get_zooms()[:3])

    kwargs = dict(files=[os.path.abspath(filename) for
                         filename in args.files],
                  subject_id=args.subject_id,
                  n_vol=args.n_vol,
                  despike=args.despike,
                  TR=TR,
                  slice_times=slice_times,
                  slice_thickness=slice_thickness,
                  lowpass_freq=args.lowpass_freq,
                  highpass_freq=args.highpass_freq,
                  sink_directory=os.path.abspath(args.sink),
                  name=name)
    if args.field_maps:
        kwargs.update(**dict(fieldmap_images=args.field_maps,
                             FM_TEdiff=args.TE_diff,
                             FM_echo_spacing=args.echo_spacing,
                             FM_sigma=args.sigma))
    wf = create_workflow(**kwargs)
    return wf

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--dicom_file", dest="dicom_file",
                        help="an example dicom file from the resting series")
    parser.add_argument("-f", "--files", dest="files", nargs="+",
                        help="4d nifti files for resting state",
                        required=True)
    parser.add_argument("-s", "--subject_id", dest="subject_id",
                        help="FreeSurfer subject id", required=True)
    parser.add_argument("-n", "--n_vol", dest="n_vol", default=0, type=int,
                        help="Volumes to skip at the beginning")
    parser.add_argument("--despike", dest="despike", default=False,
                        action="store_true", help="Use despiked data")
    parser.add_argument("--TR", dest="TR", default=None,
                        help="TR if dicom not provided in seconds")
    parser.add_argument("--slice_times", dest="slice_times", nargs="+",
                        type=float, help="Slice times in seconds")
    parser.add_argument("-l", "--lowpass_freq", dest="lowpass_freq",
                        default=-1, help="Low pass frequency (Hz)")
    parser.add_argument("-u", "--highpass_freq", dest="highpass_freq",
                        default=-1, help="High pass frequency (Hz)")
    parser.add_argument("-o", "--output_dir", dest="sink",
                        help="Output directory base")
    parser.add_argument("-w", "--work_dir", dest="work_dir",
                        help="Output directory base")
    parser.add_argument("-p", "--plugin", dest="plugin",
                        default='Linear',
                        help="Plugin to use")
    parser.add_argument("--plugin_args", dest="plugin_args",
                        help="Plugin arguments")
    parser.add_argument("--field_maps", dest="field_maps", nargs="+",
                        help="field map niftis")
    parser.add_argument("--fm_echospacing", dest="echo_spacing", type=float,
                        help="field map echo spacing")
    parser.add_argument("--fm_TE_diff", dest='TE_diff', type=float,
                        help="field map echo time difference")
    parser.add_argument("--fm_sigma", dest='sigma', type=float,
                        help="field map sigma value")
    args = parser.parse_args()

    wf = create_resting_workflow(args)

    if args.work_dir:
        work_dir = os.path.abspath(args.work_dir)
    else:
        work_dir = os.getcwd()

    wf.base_dir = work_dir
    if args.plugin_args:
        wf.run(args.plugin, plugin_args=eval(args.plugin_args))
    else:
        wf.run(args.plugin)
