# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

from nipype.testing import (assert_equal, assert_false, assert_true,
                            assert_raises, skipif)
import nibabel as nb
import nipype.interfaces.spm as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(outdir,f))
    return filelist, outdir, cwd

def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)

def test_slicetiming():
    yield assert_equal, spm.SliceTiming._jobtype, 'temporal'
    yield assert_equal, spm.SliceTiming._jobname, 'st'
    input_map = dict(in_files = dict(field='scans',
                                   mandatory=True,
                                   copyfile=False),
                     num_slices = dict(field='nslices'),
                     time_repetition = dict(field='tr'),
                     time_acquisition = dict(field='ta'),
                     slice_order = dict(field='so'),
                     ref_slice = dict(field='refslice'))
    st = spm.SliceTiming()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(st.inputs.traits()[key], metakey), value

def test_slicetiming_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    st = spm.SliceTiming(in_files=filelist[0])
    yield assert_equal, st._list_outputs()['timecorrected_files'][0][0], 'a'
    clean_directory(outdir, cwd)

def test_realign():
    yield assert_equal, spm.Realign._jobtype, 'spatial'
    yield assert_equal, spm.Realign._jobname, 'realign'
    yield assert_equal, spm.Realign().inputs.jobtype, 'estwrite'
    input_map = dict(in_files = dict(field='data', mandatory=True,
                                     copyfile=True),
                     quality = dict(field='eoptions.quality'),
                     fwhm = dict(field='eoptions.fwhm'),
                     separation = dict(field='eoptions.sep'),
                     register_to_mean = dict(field='eoptions.rtm'),
                     weight_img = dict(field='eoptions.weight'),
                     interp = dict(field='eoptions.interp'),
                     wrap = dict(field='eoptions.wrap'),
                     write_which = dict(field='roptions.which'),
                     write_interp = dict(field='roptions.interp'),
                     write_wrap = dict(field='roptions.wrap'),
                     write_mask = dict(field='roptions.mask'))
    rlgn = spm.Realign()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(rlgn.inputs.traits()[key], metakey), value

def test_realign_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    rlgn = spm.Realign(in_files=filelist[0])
    yield assert_true, rlgn._list_outputs()['realignment_parameters'][0].startswith('rp_')
    yield assert_true, rlgn._list_outputs()['realigned_files'][0].startswith('r')
    yield assert_true, rlgn._list_outputs()['mean_image'].startswith('mean')
    clean_directory(outdir, cwd)

def test_coregister():
    yield assert_equal, spm.Coregister._jobtype, 'spatial'
    yield assert_equal, spm.Coregister._jobname, 'coreg'
    yield assert_equal, spm.Coregister().inputs.jobtype, 'estwrite'
    input_map = dict(target = dict(field='ref', mandatory=True, copyfile=False),
                     source = dict(field='source', copyfile=True),
                     apply_to_files = dict(field='other',
                                           copyfile=True),
                     cost_function = dict(field='eoptions.cost_fun'),
                     fwhm = dict(field='eoptions.fwhm'),
                     separation = dict(field='eoptions.sep'),
                     tolerance = dict(field='eoptions.tol'),
                     write_interp = dict(field='roptions.interp'),
                     write_wrap = dict(field='roptions.wrap'),
                     write_mask = dict(field='roptions.mask'))
    coreg = spm.Coregister()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(coreg.inputs.traits()[key], metakey), value

def test_coregister_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    coreg = spm.Coregister(source=filelist[0])
    yield assert_true, coreg._list_outputs()['coregistered_source'][0].startswith('r')
    coreg = spm.Coregister(source=filelist[0],apply_to_files=filelist[1])
    yield assert_true, coreg._list_outputs()['coregistered_files'][0].startswith('r')
    clean_directory(outdir, cwd)

def test_normalize():
    yield assert_equal, spm.Normalize._jobtype, 'spatial'
    yield assert_equal, spm.Normalize._jobname, 'normalise'
    yield assert_equal, spm.Normalize().inputs.jobtype, 'estwrite'
    input_map = dict(template = dict(field='eoptions.template',
                                     mandatory=True, xor=['parameter_file'],
                                     copyfile=False),
                     source = dict(field='subj.source',
                                   xor=['parameter_file'],
                                   mandatory=True, copyfile=True),
                     apply_to_files = dict(field='subj.resample',
                                           copyfile=True),
                     parameter_file = dict(field='subj.matname', mandatory=True,
                                           xor=['source', 'template'],
                                           copyfile=False),
                     source_weight = dict(field='subj.wtsrc', copyfile=False),
                     template_weight = dict(field='eoptions.weight', copyfile=False),
                     source_image_smoothing = dict(field='eoptions.smosrc'),
                     template_image_smoothing = dict(field='eoptions.smoref'),
                     affine_regularization_type = dict(field='eoptions.regype'),
                     DCT_period_cutoff = dict(field='eoptions.cutoff'),
                     nonlinear_iterations = dict(field='eoptions.nits'),
                     nonlinear_regularization = dict(field='eoptions.reg'),
                     write_preserve = dict(field='roptions.preserve'),
                     write_bounding_box = dict(field='roptions.bb'),
                     write_voxel_sizes = dict(field='roptions.vox'),
                     write_interp = dict(field='roptions.interp'),
                     write_wrap = dict(field='roptions.wrap'))
    norm = spm.Normalize()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(norm.inputs.traits()[key], metakey), value

def test_normalize_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    norm = spm.Normalize(source=filelist[0])
    yield assert_true, norm._list_outputs()['normalized_source'][0].startswith('w')
    norm = spm.Normalize(source=filelist[0],apply_to_files=filelist[1])
    yield assert_true, norm._list_outputs()['normalized_files'][0].startswith('w')
    clean_directory(outdir, cwd)

def test_segment():
    yield assert_equal, spm.Segment._jobtype, 'spatial'
    yield assert_equal, spm.Segment._jobname, 'preproc'
    input_map = dict(data = dict(field='data', copyfile=False, mandatory=True),
                     gm_output_type = dict(field='output.GM'),
                     wm_output_type = dict(field='output.WM'),
                     csf_output_type = dict(field='output.CSF'),
                     save_bias_corrected = dict(field='output.biascor'),
                     clean_masks = dict(field='output.cleanup'),
                     tissue_prob_maps = dict(field='opts.tpm'),
                     gaussians_per_class = dict(field='opts.ngaus'),
                     affine_regularization = dict(field='opts.regtype'),
                     warping_regularization = dict(field='opts.warpreg'),
                     warp_frequency_cutoff = dict(field='opts.warpco'),
                     bias_regularization = dict(field='opts.biasreg'),
                     bias_fwhm = dict(field='opts.biasfwhm'),
                     sampling_distance = dict(field='opts.samp'),
                     mask_image = dict(field='opts.msk'))
    seg = spm.Segment()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(seg.inputs.traits()[key], metakey), value

def test_newsegment():
    yield assert_equal, spm.NewSegment._jobtype, 'tools'
    yield assert_equal, spm.NewSegment._jobname, 'preproc8'
    input_map = dict(affine_regularization = dict(field='warp.affreg',),
                     channel_files = dict(copyfile=False,mandatory=True,field='channel',),
                     channel_info = dict(field='channel',),
                     ignore_exception = dict(usedefault=True,),
                     matlab_cmd = dict(),
                     mfile = dict(usedefault=True,),
                     paths = dict(),
                     sampling_distance = dict(field='warp.samp',),
                     tissues = dict(field='tissue',),
                     use_mcr = dict(),
                     warping_regularization = dict(field='warp.reg',),
                     write_deformation_fields = dict(field='warp.write',),
                     )
    instance = spm.NewSegment()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_smooth():
    yield assert_equal, spm.Smooth._jobtype, 'spatial'
    yield assert_equal, spm.Smooth._jobname, 'smooth'
    input_map = dict(data_type = dict(field='dtype',),
                     fwhm = dict(field='fwhm',),
                     in_files = dict(copyfile=False,mandatory=True,field='data',),
                     )
    instance = spm.Smooth()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_dartel():
    yield assert_equal, spm.DARTEL._jobtype, 'tools'
    yield assert_equal, spm.DARTEL._jobname, 'dartel'
    input_map = dict(ignore_exception = dict(usedefault=True,),
                     image_files = dict(copyfile=False,mandatory=True,field='warp.images',),
                     iteration_parameters = dict(field='warp.settings.param',),
                     matlab_cmd = dict(),
                     mfile = dict(usedefault=True,),
                     optimization_parameters = dict(field='warp.settings.optim',),
                     paths = dict(),
                     regularization_form = dict(field='warp.settings.rform',),
                     template_prefix = dict(field='warp.settings.template',usedefault=True,),
                     use_mcr = dict(),
                     )
    instance = spm.DARTEL()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

def test_dartelnorm2mni():
    yield assert_equal, spm.DARTELNorm2MNI._jobtype, 'tools'
    yield assert_equal, spm.DARTELNorm2MNI._jobname, 'dartel'
    input_map = dict(apply_to_files = dict(copyfile=False,mandatory=True,field='mni_norm.data.subjs.images',),
                     bounding_box = dict(field='mni_norm.bb',),
                     flowfield_files = dict(field='mni_norm.data.subjs.flowfields',mandatory=True,),
                     fwhm = dict(field='mni_norm.fwhm',),
                     ignore_exception = dict(usedefault=True,),
                     matlab_cmd = dict(),
                     mfile = dict(usedefault=True,),
                     modulate = dict(field='mni_norm.preserve',),
                     paths = dict(),
                     template_file = dict(copyfile=False,mandatory=True,field='mni_norm.template',),
                     use_mcr = dict(),
                     voxel_size = dict(field='mni_norm.vox',),
                     )
    instance = spm.DARTELNorm2MNI()
    for key, metadata in input_map.items():
        for metakey, value in metadata.items():
            yield assert_equal, getattr(instance.inputs.traits()[key], metakey), value

#@skipif(no_spm, "SPM not found")
#def test_spm_realign_inputs():
#    pass
