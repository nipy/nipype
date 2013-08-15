import os

from nipype.interfaces.base import CommandLine
CommandLine.set_default_terminal_output('allatonce')

from nipype import (afni, fsl, freesurfer, nipy, Function,
                    DataGrabber, DataSink)
from nipype import Workflow, Node, MapNode

from nipype.algorithms.rapidart import ArtifactDetect
from nipype.algorithms.misc import TSNR
from nipype.interfaces.fsl.utils import EPIDeWarp
from nipype.interfaces.io import FreeSurferSource

import numpy as np


#robust mean
def median(in_files):
    import os
    import nibabel as nb
    import numpy as np
    from nipype.utils.filemanip import filename_to_list
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


def get_info(dicom_files):
    from dcmstack.extract import default_extractor
    from dicom import read_file
    from nipype.utils.filemanip import filename_to_list
    meta = default_extractor(read_file(filename_to_list(dicom_files)[0],
                                       stop_before_pixels=True,
                                       force=True))
    return (meta['RepetitionTime']/1000., meta['CsaImage.MosaicRefAcqTimes'],
            meta['SpacingBetweenSlices'])


def motion_regressors(motion_params, order=2, derivatives=2):
    """
    motion + d(motion)/dt + d2(motion)/dt2 (linear + quadratic)
    """
    from nipype.utils.filemanip import filename_to_list
    import numpy as np
    import os
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
    """
    from nipype.utils.filemanip import filename_to_list
    import numpy as np
    import os
    out_files = []
    for idx, filename in enumerate(filename_to_list(motion_params)):
        params = np.genfromtxt(filename)
        norm_val = np.genfromtxt(filename_to_list(comp_norm)[idx])
        out_params = np.hstack((params, norm_val[:, None]))
        try:
            outlier_val = np.genfromtxt(filename_to_list(outliers)[idx])
        except IOError:
            outlier_val = np.empty((0))
        if outlier_val.shape[0] != 0:
            for index in outlier_val:
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
    realigned_file :
    mask_file :
    num_components :

    Returns
    -------
    components_file :
    """

    import os
    from nibabel import load
    import numpy as np
    import scipy as sp

    imgseries = load(realigned_file)
    noise_mask = load(mask_file)
    voxel_timecourses = imgseries.get_data()[np.nonzero(noise_mask.get_data())]
    voxel_timecourses = voxel_timecourses.byteswap().newbyteorder()
    voxel_timecourses[np.isnan(np.sum(voxel_timecourses, axis=1)), :] = 0
    _, _, v = sp.linalg.svd(voxel_timecourses, full_matrices=False)
    components_file = os.path.join(os.getcwd(), 'noise_components.txt')
    np.savetxt(components_file, v[:num_components, :].T)
    return components_file


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
                    surf_fwhm=10,
                    lowpass_freq=-1,
                    highpass_freq=-1,
		    sink_directory=os.getcwd(),
	            FM_TEdiff=2.46,
	            FM_sigma=2,
	            FM_echo_spacing=.7):

    wf = Workflow(name='resting')

    #skip vols
    remove_vol = MapNode(fsl.ExtractROI(t_min=n_vol, t_size=-1),
                         iterfield=['in_file'],
                         name="remove_volumes")
    remove_vol.inputs.in_file = files

    # despike
    despike = MapNode(afni.Despike(outputtype='NIFTI_GZ'),
                      iterfield=['in_file'],
                      name='despike')
    #despike.plugin_args = {'qsub_args': '-l nodes=1:ppn='}

    wf.connect(remove_vol, 'roi_file', despike, 'in_file')

    #nipy realign
    realign = Node(nipy.FmriRealign4d(), name='realign')
    realign.inputs.tr = TR
    realign.inputs.time_interp = True
    realign.inputs.slice_order = np.argsort(np.argsort(slice_times)).tolist()
    if despike:
        wf.connect(despike, 'out_file', realign, 'in_file')
    else:
        wf.connect(remove_vol, 'roi_file', realign, 'in_file')

    #TSNR
    tsnr = MapNode(TSNR(regress_poly=2), iterfield=['in_file'], name='tsnr')
    wf.connect(realign, 'out_file', tsnr, 'in_file')

    calc_median = Node(Function(input_names=['in_files'],
                                output_names=['median_file'],
                                function=median),
                       name='median')
    wf.connect(tsnr, 'detrended_file', calc_median, 'in_files')

    register = Node(freesurfer.BBRegister(),
                    name='bbregister')
    register.inputs.subject_id = subject_id
    register.inputs.init = 'fsl'
    register.inputs.contrast_type = 't2'
    register.inputs.out_fsl_file = True

    if fieldmap_images:
	fieldmap=Node(interface=EPIDeWarp(), name ='fieldmap_unwarp')
	dewarper=MapNode(interface=fsl.FUGUE(), iterfield=['in_file'], name = 'dewarper')
	fieldmap.inputs.tediff=FM_TEdiff
	fieldmap.inputs.esp=FM_echo_spacing
	fieldmap.inputs.sigma=FM_sigma
	fieldmap.inputs.mag_file=fieldmap_images[0]
	fieldmap.inputs.dph_file=fieldmap_images[1]
	wf.connect(calc_median,'median_file',fieldmap,'exf_file')
	wf.connect(tsnr, 'detrended_file', dewarper, 'in_file')
	wf.connect(fieldmap,'exf_mask', dewarper,'mask_file')
	wf.connect(fieldmap, 'vsm_file', dewarper,'shift_in_file')
	wf.connect(fieldmap,'exfdw',register, 'source_file')

    else:
        wf.connect(calc_median, 'median_file', register, 'source_file')

    fssource = Node(FreeSurferSource(),
                    name='fssource')
    fssource.inputs.subject_id = subject_id
    fssource.inputs.subjects_dir = os.environ['SUBJECTS_DIR']

    #extract wm+csf, brain masks by eroding freesurfer lables
    wmcsf = Node(freesurfer.Binarize(), name='wmcsfmask')
    mask = wmcsf.clone('anatmask')

    wmcsftransform = Node(freesurfer.ApplyVolTransform(inverse=True,
                                                       interp='nearest'),
                          name='wmcsftransform')
    wmcsftransform.inputs.subjects_dir = os.environ['SUBJECTS_DIR']

    wmcsf.inputs.wm_ven_csf = True
    wmcsf.inputs.match = [4, 5, 14, 15, 24, 31, 43, 44, 63]
    wmcsf.inputs.binary_file = 'wmcsf.nii.gz'
    wmcsf.inputs.erode = 1
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), wmcsf, 'in_file')
    
    if fieldmap_images:
        wf.connect(fieldmap,'exf_mask',wmcsftransform,'source_file')
    else:
    	wf.connect(calc_median, 'median_file', wmcsftransform, 'source_file')
    wf.connect(register, 'out_reg_file', wmcsftransform, 'reg_file')
    wf.connect(wmcsf, 'binary_file', wmcsftransform, 'target_file')

    mask.inputs.dilate = 3
    mask.inputs.binary_file = 'mask.nii.gz'
    mask.inputs.erode = int(slice_thickness)
    mask.inputs.min = 0.5
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), mask, 'in_file')

    masktransform = wmcsftransform.clone("masktransform")
    if fieldmap_images:
        wf.connect(fieldmap,'exf_mask',masktransform,'source_file')
    else:
        wf.connect(calc_median, 'median_file', masktransform, 'source_file')
    wf.connect(register, 'out_reg_file', masktransform, 'reg_file')
    wf.connect(mask, 'binary_file', masktransform, 'target_file')

    #art outliers
    art = Node(interface=ArtifactDetect(use_differences=[True, False],
                                        use_norm=True,
                                        norm_threshold=norm_threshold,
                                        zintensity_threshold=3,
                                        parameter_source='NiPy',
                                        bound_by_brainmask=True,
                                        mask_type='file'),
               name="art")
    if fieldmap_images:
        wf.connect(dewarper,'unwarped_file',art,'realigned_files')
    else:
        wf.connect(tsnr, 'detrended_file', art, 'realigned_files')
    wf.connect(realign, 'par_file',
               art, 'realignment_parameters')
    wf.connect(masktransform, 'transformed_file', art, 'mask_file')

    motreg = Node(Function(input_names=['motion_params', 'order',
                                        'derivatives'],
                           output_names=['out_files'],
                           function=motion_regressors),
                  name='getmotionregress')
    wf.connect(realign, 'par_file', motreg, 'motion_params')

    createfilter1 = Node(Function(input_names=['motion_params', 'comp_norm',
                                               'outliers'],
                                  output_names=['out_files'],
                                  function=build_filter1),
                         name='makemotionbasedfilter')
    wf.connect(motreg, 'out_files', createfilter1, 'motion_params')
    wf.connect(art, 'norm_files', createfilter1, 'comp_norm')
    wf.connect(art, 'outlier_files', createfilter1, 'outliers')

<<<<<<< HEAD
    filter1 = MapNode(fsl.FilterRegressor(filter_all=True),
                      iterfield=['in_file', 'design_file'],
                      name='filtermotion')
    if fieldmap_images:
        wf.connect(dewarper,'unwarped_file',filter1,'in_file')
    else:
        wf.connect(tsnr, 'detrended_file', filter1, 'in_file')
=======
    #filter1 = MapNode(fsl.FilterRegressor(filter_all=True),
    #                  iterfield=['in_file', 'design_file'],
    #                  name='filtermotion')
    #wf.connect(tsnr, 'detrended_file', filter1, 'in_file')
    #wf.connect(createfilter1, 'out_files', filter1, 'design_file')
    #wf.connect(masktransform, 'transformed_file', filter1, 'mask')

    filter1 = MapNode(fsl.GLM(),
		     iterfield=['in_file', 'design_file'],
		     name='filtermotion')
    wf.connect(tsnr, 'detrended_file', filter1, 'in_file')
>>>>>>> 39793ef71c08dae4a64f789808bd957362e0b729
    wf.connect(createfilter1, 'out_files', filter1, 'design_file')
    wf.connect(masktransform,'transformed_file',filter1,'mask')


  #  filter1 = MapNode(fsl.GLM(),
#		     iterfield=['in_file', 'design_file'],
#		     name='filtermotion')
    #wf.connect(tsnr, 'detrended_file', filter1, 'in_file')
   # wf.connect(createfilter1, 'out_files', filter1, 'design_file')
    #wf.connect(masktransform,'transformed_file',filter1,'mask')


    createfilter2 = MapNode(Function(input_names=['realigned_file', 'mask_file',
                                                  'num_components'],
                                     output_names=['out_files'],
                                     function=extract_noise_components),
                            iterfield=['realigned_file'],
                            name='makecompcorrfilter')
    createfilter2.inputs.num_components = num_components
<<<<<<< HEAD
    wf.connect(filter1, 'out_file', createfilter2, 'realigned_file')
    #wf.connect(filter1, 'out_res', createfilter2,'realigned_file')

    wf.connect(wmcsftransform, 'transformed_file', createfilter2, 'mask_file')
=======
    #wf.connect(filter1, 'out_file', createfilter2, 'realigned_file')
    wf.connect(filter1, 'out_res', createfilter2,'realigned_file')

    wf.connect(masktransform, 'transformed_file', createfilter2, 'mask_file')
>>>>>>> 39793ef71c08dae4a64f789808bd957362e0b729

    filter2 = MapNode(fsl.FilterRegressor(filter_all=True),
                      iterfield=['in_file', 'design_file'],
                      name='filtercompcorr')
    wf.connect(filter1, 'out_file', filter2, 'in_file')
    wf.connect(createfilter2, 'out_files', filter2, 'design_file')
    wf.connect(masktransform, 'transformed_file', filter2, 'mask')

    smooth = MapNode(freesurfer.Smooth(),
                     iterfield=['in_file'],
                     name='smooth')
    smooth.inputs.proj_frac_avg = (0.1, 0.9, 0.1)
    smooth.inputs.surface_fwhm = surf_fwhm
    if vol_fwhm is None:
        vol_fwhm = 2 * slice_thickness
    smooth.inputs.vol_fwhm = vol_fwhm
    wf.connect(filter2, 'out_file',  smooth, 'in_file')
    wf.connect(register, 'out_reg_file', smooth, 'reg_file')

    bandpass = MapNode(fsl.TemporalFilter(),
                       iterfield=['in_file'],
                       name='bandpassfilter')
    if highpass_freq < 0:
            bandpass.inputs.highpass_sigma = -1
    else:
            bandpass.inputs.highpass_sigma = 1 / (2 * TR * highpass_freq)
    if lowpass_freq < 0:
            bandpass.inputs.lowpass_sigma = -1
    else:
            bandpass.inputs.lowpass_sigma = 1 / (2 * TR * lowpass_freq)
    wf.connect(smooth, 'smoothed_file', bandpass, 'in_file')

    datasink=Node(interface=DataSink(),
                  name="datasink")
    datasink.inputs.base_directory=sink_directory
    wf.connect(despike,'out_file',datasink,'resting.despike')
    wf.connect(realign,'par_file',datasink,'resting.motion')
    wf.connect(tsnr,'tsnr_file',datasink,'resting.tsnr')
    wf.connect(tsnr,'mean_file',datasink,'resting.tsnr.@mean')
    wf.connect(tsnr,'stddev_file',datasink,'resting.tsnr.@stddev')
    wf.connect(art,'norm_files',datasink,'resting.art')
    wf.connect(art,'outlier_files',datasink,'resting.art.@outlier_files')
    wf.connect(mask,'binary_file',datasink,'resting.mask')
    wf.connect(masktransform,'transformed_file',datasink,'resting.mask.@transformed_file')
    wf.connect(register,'out_reg_file',datasink,'resting.out_reg_file')
    wf.connect(smooth,'smoothed_file',datasink,'resting.output.fullpass')
    wf.connect(bandpass,'out_file',datasink,'resting.output.bandpassed')
    wf.connect(createfilter1,'out_files',datasink,'resting.motion.@regressors')
    wf.connect(createfilter2,'out_files',datasink,'resting.compcorr')
    wf.connect(wmcsftransform,'transformed_file',datasink,'resting.compcorr.@transformed_file')

    return wf

if __name__ == "__main__":
    import argparse
    #dcmfile = '/software/data/sad_resting/500000-32-1.dcm'
    #niifile = '/software/data/sad_resting/resting.nii.gz'
    #subject_id = 'SAD_024'
    #dcmfile = '/software/data/sad_resting/allyson/562000-34-1.dcm'
    #niifile = '/software/data/sad_resting/allyson/Resting1.nii'
    #fieldmaps = ['/software/data/sad_resting/allyson/fieldmap_resting1.nii',
    #             '/software/data/sad_resting/allyson/fieldmap_resting2.nii']
    echo_time = 0.7
    subject_id = '308'
    #dcmfile = '/mindhive/xnat/dicom_storage/sad/SAD_024/dicoms/500000-32-1.dcm'
    #niifile = '/mindhive/xnat/data/sad/SAD_024/BOLD/resting.nii.gz'
    dcmfile = '/mindhive/xnat/data/GATES/308/dicoms/562000-34-1.dcm'
    niifile= '/mindhive/xnat/data/GATES/308/niftis/Resting1.nii'
    fieldmap_images=['/mindhive/xnat/data/GATES/308/niftis/fieldmap_resting1.nii',
		     '/mindhive/xnat/data/GATES/308/niftis/fieldmap_resting2.nii']
    TR, slice_times, slice_thickness = get_info(dcmfile)

    wf = create_workflow(niifile,
                         subject_id,
                         n_vol=2,
                         despike=True,
                         TR=TR,
                         slice_times=slice_times,
                         slice_thickness=np.round(slice_thickness),
                         lowpass_freq=.08,
                    	 highpass_freq=.9,
			 vol_fwhm=6,
                    	 surf_fwhm=10,
		    	 sink_directory=os.path.abspath('/mindhive/scratch/Wed/cdla/resting/sink/'),
			 FM_TEdiff=2.46 ,
			 FM_sigma=2 ,
			 FM_echo_spacing=.7 ,
			 fieldmap_images=fieldmap_images
			 )

    wf.config['execution'].update(**{'hash_method': 'content',
                                     'remove_unnecessary_outputs': False})
    wf.base_dir = os.getcwd()
    wf.write_graph(graph2use='flat')
    wf.run(plugin='MultiProc')

'''
#fieldmap dewarping
unwarp = MapNode(EPIDeWarp(), name='dewarp')

#convert to grayordinates
def to_grayordinates():
    return grayordinates

#compute similarity matrix and partial correlation
def compute_similarity():
    return matrix
'''
