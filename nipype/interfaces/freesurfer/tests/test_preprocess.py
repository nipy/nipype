# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from shutil import rmtree
import nibabel as nif
import numpy as np
from tempfile import mkdtemp
from nipype.testing import (assert_equal, assert_false, assert_true,
                            assert_raises, skipif)
import nipype.interfaces.freesurfer as freesurfer

def no_freesurfer():
    if freesurfer.Info().version is None:
        return True
    else:
        return False

@skipif(no_freesurfer)
def test_applyvoltransform():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     fs_target = dict(xor=('target_file', 'tal', 'fs_target'),mandatory=True,requires=['reg_file'],argstr='--fstarg',),
                     fsl_reg_file = dict(xor=('reg_file', 'fsl_reg_file', 'xfm_reg_file', 'reg_header', 'subject'),argstr='--fsl %s',mandatory=True,),
                     interp = dict(argstr='--interp %s',),
                     inverse = dict(argstr='--inv',),
                     no_resample = dict(argstr='--no-resample',),
                     reg_file = dict(xor=('reg_file', 'fsl_reg_file', 'xfm_reg_file', 'reg_header', 'subject'),argstr='--reg %s',mandatory=True,),
                     reg_header = dict(xor=('reg_file', 'fsl_reg_file', 'xfm_reg_file', 'reg_header', 'subject'),argstr='--regheader',mandatory=True,),
                     source_file = dict(copyfile=False,mandatory=True,argstr='--mov %s',),
                     subject = dict(xor=('reg_file', 'fsl_reg_file', 'xfm_reg_file', 'reg_header', 'subject'),argstr='--s %s',mandatory=True,),
                     subjects_dir = dict(),
                     tal = dict(xor=('target_file', 'tal', 'fs_target'),argstr='--tal',mandatory=True,),
                     target_file = dict(xor=('target_file', 'tal', 'fs_target'),argstr='--targ %s',mandatory=True,),
                     transformed_file = dict(argstr='--o %s',),
                     xfm_reg_file = dict(xor=('reg_file', 'fsl_reg_file', 'xfm_reg_file', 'reg_header', 'subject'),argstr='--xfm %s',mandatory=True,),
                     )
    instance = freesurfer.ApplyVolTransform()

    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

@skipif(no_freesurfer)
def test_bbregister():
    input_map = dict(args=dict(argstr='%s',),
                     contrast_type=dict(argstr='--%s',mandatory=True,),
                     environ=dict(),
                     init=dict(argstr='--init-%s',xor=['init_reg_file'],),
                     init_reg_file=dict(xor=['init'],mandatory=True,),
                     out_reg_file=dict(argstr='--reg %s',),
                     registered_file=dict(argstr='--o %s',),
                     reg_frame=dict(argstr="--frame %d",),
                     reg_middle_frame=dict(argstr="--mid-frame",),
                     intermediate_file=dict(argstr="--int %s",),
                     source_file=dict(copyfile=False,
                                        mandatory=True,
                                        argstr='--mov %s',),
                     subject_id=dict(mandatory=True,argstr='--s %s',),
                     subjects_dir=dict(),
                     )
    instance = freesurfer.BBRegister()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield (assert_equal,
                   getattr(instance.inputs.traits()[key], metakey),
                   value)

@skipif(no_freesurfer)
def test_dicomconvert():
    input_map = dict(args = dict(argstr='%s',),
                     base_output_dir = dict(mandatory=True,),
                     dicom_dir = dict(mandatory=True,),
                     dicom_info = dict(),
                     environ = dict(),
                     file_mapping = dict(),
                     ignore_single_slice = dict(requires=['dicom_info'],),
                     out_type = dict(),
                     seq_list = dict(requires=['dicom_info'],),
                     subject_dir_template = dict(),
                     subject_id = dict(),
                     subjects_dir = dict(),
                     )
    instance = freesurfer.DICOMConvert()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


@skipif(no_freesurfer)
def test_mriconvert():
    input_map = dict(apply_inv_transform = dict(argstr='--apply_inverse_transform %s',),
                     apply_transform = dict(argstr='--apply_transform %s',),
                     args = dict(argstr='%s',),
                     ascii = dict(argstr='--ascii',),
                     autoalign_matrix = dict(argstr='--autoalign %s',),
                     color_file = dict(argstr='--color_file %s',),
                     conform = dict(argstr='--conform',),
                     conform_min = dict(argstr='--conform_min',),
                     conform_size = dict(argstr='--conform_size %s',),
                     crop_center = dict(argstr='--crop %d %d %d',),
                     crop_gdf = dict(argstr='--crop_gdf',),
                     crop_size = dict(argstr='--cropsize %d %d %d',),
                     cut_ends = dict(argstr='--cutends %d',),
                     devolve_transform = dict(argstr='--devolvexfm %s',),
                     drop_n = dict(argstr='--ndrop %d',),
                     environ = dict(),
                     fill_parcellation = dict(argstr='--fill_parcellation',),
                     force_ras = dict(argstr='--force_ras_good',),
                     frame = dict(argstr='--frame %d',),
                     frame_subsample = dict(argstr='--fsubsample %d %d %d',),
                     fwhm = dict(argstr='--fwhm %f',),
                     in_center = dict(argstr='--in_center %s',),
                     in_file = dict(mandatory=True,argstr='--input_volume %s',),
                     in_i_dir = dict(argstr='--in_i_direction %f %f %f',),
                     in_i_size = dict(argstr='--in_i_size %d',),
                     in_info = dict(argstr='--in_info',),
                     in_j_dir = dict(argstr='--in_j_direction %f %f %f',),
                     in_j_size = dict(argstr='--in_j_size %d',),
                     in_k_dir = dict(argstr='--in_k_direction %f %f %f',),
                     in_k_size = dict(argstr='--in_k_size %d',),
                     in_like = dict(argstr='--in_like %s',),
                     in_matrix = dict(argstr='--in_matrix',),
                     in_orientation = dict(argstr='--in_orientation %s',),
                     in_scale = dict(argstr='--scale %f',),
                     in_stats = dict(argstr='--in_stats',),
                     in_type = dict(argstr='--in_type %s',),
                     invert_contrast = dict(argstr='--invert_contrast %f',),
                     midframe = dict(argstr='--mid-frame',),
                     no_change = dict(argstr='--nochange',),
                     no_scale = dict(argstr='--no_scale 1',),
                     no_translate = dict(argstr='--no_translate',),
                     no_write = dict(argstr='--no_write',),
                     out_center = dict(argstr='--out_center %f %f %f',),
                     out_datatype = dict(argstr='--out_data_type %s',),
                     out_file = dict(argstr='--output_volume %s',),
                     out_i_count = dict(argstr='--out_i_count %d',),
                     out_i_dir = dict(argstr='--out_i_direction %f %f %f',),
                     out_i_size = dict(argstr='--out_i_size %d',),
                     out_info = dict(argstr='--out_info',),
                     out_j_count = dict(argstr='--out_j_count %d',),
                     out_j_dir = dict(argstr='--out_j_direction %f %f %f',),
                     out_j_size = dict(argstr='--out_j_size %d',),
                     out_k_count = dict(argstr='--out_k_count %d',),
                     out_k_dir = dict(argstr='--out_k_direction %f %f %f',),
                     out_k_size = dict(argstr='--out_k_size %d',),
                     out_matrix = dict(argstr='--out_matrix',),
                     out_orientation = dict(argstr='--out_orientation %s',),
                     out_scale = dict(argstr='--out-scale %d',),
                     out_stats = dict(argstr='--out_stats',),
                     out_type = dict(argstr='--out_type %s',),
                     parse_only = dict(argstr='--parse_only',),
                     read_only = dict(argstr='--read_only',),
                     reorder = dict(argstr='--reorder %d %d %d',),
                     resample_type = dict(argstr='--resample_type %s',),
                     reslice_like = dict(argstr='--reslice_like %s',),
                     sdcm_list = dict(argstr='--sdcmlist %s',),
                     skip_n = dict(argstr='--nskip %d',),
                     slice_bias = dict(argstr='--slice-bias %f',),
                     slice_crop = dict(argstr='--slice-crop %d %d',),
                     slice_reverse = dict(argstr='--slice-reverse',),
                     smooth_parcellation = dict(argstr='--smooth_parcellation',),
                     sphinx = dict(argstr='--sphinx',),
                     split = dict(argstr='--split',),
                     status_file = dict(argstr='--status %s',),
                     subject_name = dict(argstr='--subject_name %s',),
                     subjects_dir = dict(),
                     template_info = dict(),
                     template_type = dict(argstr='--template_type %s',),
                     unwarp_gradient = dict(argstr='--unwarp_gradient_nonlinearity',),
                     vox_size = dict(argstr='-voxsize %f %f %f',),
                     zero_ge_z_offset = dict(argstr='--zero_ge_z_offset',),
                     zero_outlines = dict(argstr='--zero_outlines',),
                     )
    instance = freesurfer.MRIConvert()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
@skipif(no_freesurfer)
def test_parsedicomdir():
    input_map = dict(args = dict(argstr='%s',),
                     dicom_dir = dict(mandatory=True,argstr='--d %s',),
                     dicom_info_file = dict(argstr='--o %s',),
                     environ = dict(),
                     sortbyrun = dict(argstr='--sortbyrun',),
                     subjects_dir = dict(),
                     summarize = dict(argstr='--summarize',),
                     )
    instance = freesurfer.ParseDICOMDir()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
@skipif(no_freesurfer)
def test_reconall():
    input_map = dict(T1_files = dict(argstr='-i %s...',),
                     args = dict(argstr='%s',),
                     directive = dict(argstr='-%s',),
                     environ = dict(),
                     flags = dict(argstr='%s',),
                     hemi = dict(),
                     subject_id = dict(argstr='-subjid %s',),
                     subjects_dir = dict(argstr='-sd %s',),
                     )
    instance = freesurfer.ReconAll()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value, "key = %s"%key
@skipif(no_freesurfer)
def test_resample():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     in_file = dict(mandatory=True,argstr='-i %s',),
                     resampled_file = dict(argstr='-o %s',),
                     subjects_dir = dict(),
                     voxel_size = dict(argstr='-vs %.2f %.2f %.2f',mandatory=True,),
                     )
    instance = freesurfer.Resample()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
@skipif(no_freesurfer)
def test_smooth():
    input_map = dict(args = dict(argstr='%s',),
                     environ = dict(),
                     in_file = dict(argstr='--i %s',mandatory=True,),
                     num_iters = dict(xor=['surface_fwhm'],mandatory=True,),
                     proj_frac = dict(argstr='--projfrac %s',xor=['proj_frac_avg'],),
                     proj_frac_avg = dict(xor=['proj_frac'],argstr='--projfrac-avg %.2f %.2f %.2f',),
                     reg_file = dict(argstr='--reg %s',mandatory=True,),
                     smoothed_file = dict(argstr='--o %s',),
                     subjects_dir = dict(),
                     surface_fwhm = dict(xor=['num_iters'],mandatory=True,argstr='--fwhm %d',requires=['reg_file'],),
                     vol_fwhm = dict(argstr='--vol-fwhm %d',),
                     )
    instance = freesurfer.Smooth()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value
@skipif(no_freesurfer)
def test_unpacksdicomdir():
    input_map = dict(args = dict(argstr='%s',),
                     config = dict(mandatory=True,xor=('run_info', 'config', 'seq_config'),argstr='-cfg %s',),
                     dir_structure = dict(argstr='-%s',),
                     environ = dict(),
                     log_file = dict(argstr='-log %s',),
                     no_info_dump = dict(argstr='-noinfodump',),
                     no_unpack_err = dict(argstr='-no-unpackerr',),
                     output_dir = dict(argstr='-targ %s',),
                     run_info = dict(xor=('run_info', 'config', 'seq_config'),argstr='-run %d %s %s %s',mandatory=True,),
                     scan_only = dict(argstr='-scanonly %s',),
                     seq_config = dict(mandatory=True,xor=('run_info', 'config', 'seq_config'),argstr='-seqcfg %s',),
                     source_dir = dict(mandatory=True,argstr='-src %s',),
                     spm_zeropad = dict(argstr='-nspmzeropad %d',),
                     subjects_dir = dict(),
                     )
    instance = freesurfer.UnpackSDICOMDir()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value


def create_files_in_directory():
    outdir = os.path.realpath(mkdtemp())
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nif.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nif.save(nif.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(outdir,f))
    return filelist, outdir, cwd

def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)

@skipif(no_freesurfer)
def test_robustregister():
    filelist, outdir, cwd = create_files_in_directory()

    reg = freesurfer.RobustRegister()

    # make sure command gets called
    yield assert_equal, reg.cmd, 'mri_robust_register'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, reg.run

    # .inputs based parameters setting
    reg.inputs.source_file = filelist[0]
    reg.inputs.target_file = filelist[1]
    reg.inputs.auto_sens = True
    yield assert_equal, reg.cmdline, ('mri_robust_register '
        '--satit --lta %s_robustreg.lta --mov %s --dst %s'%(filelist[0][:-4],filelist[0],filelist[1]))

    # constructor based parameter setting
    reg2 = freesurfer.RobustRegister(source_file=filelist[0],target_file=filelist[1],outlier_sens=3.0,
                                     out_reg_file='foo.lta', half_targ=True)
    yield assert_equal, reg2.cmdline, ('mri_robust_register --halfdst %s_halfway.nii --lta foo.lta '
                                       '--sat 3.0000 --mov %s --dst %s'
                                       %(os.path.join(outdir,filelist[1][:-4]),filelist[0],filelist[1]))
    clean_directory(outdir, cwd)

@skipif(no_freesurfer)
def test_fitmsparams():
    filelist, outdir, cwd = create_files_in_directory()

    fit = freesurfer.FitMSParams()

    # make sure command gets called
    yield assert_equal, fit.cmd, 'mri_ms_fitparms'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, fit.run

    # .inputs based parameters setting
    fit.inputs.in_files = filelist
    fit.inputs.out_dir = outdir
    yield assert_equal, fit.cmdline, 'mri_ms_fitparms  %s %s %s'%(filelist[0],filelist[1],outdir)

    # constructor based parameter setting
    fit2 = freesurfer.FitMSParams(in_files=filelist,te_list=[1.5,3.5],flip_list=[20,30],out_dir=outdir)
    yield assert_equal, fit2.cmdline, ('mri_ms_fitparms  -te %.3f -fa %.1f %s -te %.3f -fa %.1f %s %s'
                                       %(1.500,20.0,filelist[0],3.500,30.0,filelist[1],outdir))

    clean_directory(outdir, cwd)

@skipif(no_freesurfer)
def test_synthesizeflash():
    filelist, outdir, cwd = create_files_in_directory()

    syn = freesurfer.SynthesizeFLASH()

    # make sure command gets called
    yield assert_equal, syn.cmd, 'mri_synthesize'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, syn.run

    # .inputs based parameters setting
    syn.inputs.t1_image = filelist[0]
    syn.inputs.pd_image = filelist[1]
    syn.inputs.flip_angle = 30
    syn.inputs.te = 4.5
    syn.inputs.tr = 20

    yield assert_equal, syn.cmdline, ('mri_synthesize 20.00 30.00 4.500 %s %s %s'
                                      %(filelist[0],filelist[1],os.path.join(outdir,'synth-flash_30.mgz')))

    # constructor based parameters setting
    syn2 = freesurfer.SynthesizeFLASH(t1_image=filelist[0],pd_image=filelist[1],flip_angle=20,te=5,tr=25)
    yield assert_equal, syn2.cmdline, ('mri_synthesize 25.00 20.00 5.000 %s %s %s'
                                       %(filelist[0],filelist[1],os.path.join(outdir,'synth-flash_20.mgz')))

