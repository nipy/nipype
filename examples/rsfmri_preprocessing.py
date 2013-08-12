import os

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
    return meta['RepetitionTime']/1000., meta['CsaImage.MosaicRefAcqTimes']


def motion_regressors(motion_params, order=2, derivatives=2):
    """
    motion + d(motion)/dt + d2(motion)/dt2 (linear + quadratic)
    """
    from nipype.utils.filemanip import filename_to_list
    import numpy as np
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

def create_workflow(files,
                    subject_id,
                    n_vol=0,
                    despike=True,
                    TR=None,
                    slice_times=None,
                    fieldmap_images=None,
                    norm_threshold=1):

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
        pass
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
    wmcsf.inputs.binary_file = 'wmcsf.nii.gz'
    wmcsf.inputs.erode = 2
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), wmcsf, 'in_file')

    wf.connect(calc_median, 'median_file', wmcsftransform, 'source_file')
    wf.connect(register, 'out_reg_file', wmcsftransform, 'reg_file')
    wf.connect(wmcsf, 'binary_file', wmcsftransform, 'target_file')

    mask.inputs.dilate = 3
    mask.inputs.binary_file = 'mask.nii.gz'
    mask.inputs.erode = 2
    mask.inputs.min = 0.5
    wf.connect(fssource, ('aparc_aseg', get_aparc_aseg), mask, 'in_file')

    masktransform = wmcsftransform.clone("masktransform")
    wf.connect(calc_median, 'median_file', masktransform, 'source_file')
    wf.connect(register, 'out_reg_file', masktransform, 'reg_file')
    wf.connect(wmcsf, 'binary_file', masktransform, 'target_file')

    #art outliers
    art = Node(interface=ArtifactDetect(use_differences=[True, False],
                                        use_norm=True,
                                        norm_threshold=norm_threshold,
                                        zintensity_threshold=3,
                                        parameter_source='NiPy',
                                        bound_by_brainmask=True,
                                        mask_type='file'),
               name="art")
    wf.connect(tsnr, 'detrended_file', art, 'realigned_files')
    wf.connect(realign, 'par_file',
               art, 'realignment_parameters')
    wf.connect(masktransform, 'transformed_file', art, 'mask_file')
    return wf

if __name__ == "__main__":
    import argparse
    dcmfile = '/software/data/sad_resting/500000-32-1.dcm'
    niifile = '/software/data/sad_resting/resting.nii.gz'
    TR, slice_times = get_info(dcmfile)
    wf = create_workflow(niifile,
                         'SAD_024',
                         n_vol=2,
                         despike=True,
                         TR=TR,
                         slice_times=slice_times,
                         )
    wf.config['execution'].update(**{'hash_method': 'content',
                                     'remove_unnecessary_outputs': False})
    wf.base_dir = os.getcwd()
    wf.run()

'''
#fieldmap dewarping
unwarp = MapNode(EPIDeWarp(), name='dewarp')


# regress motion + art (compnorm + outliers) from realigned data
def regress(filter):
    return filtered_data

#compute compcorr on wm, csf separately
def compcorr():
    return components

#regress those out
def regress(comps):
    return filtered_data

#smooth
freesurfer.SurfaceSmooth()

#bandpass
fsl.ImageMaths

#convert to grayordinates
def to_grayordinates():
    return grayordinates

#compute similarity matrix and partial correlation
def compute_similarity():
    return matrix

'''
