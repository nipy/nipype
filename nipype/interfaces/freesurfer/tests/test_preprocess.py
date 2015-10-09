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

