# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nipype.externals.pynifti as nif
from nipype.testing import (assert_equal, assert_not_equal,
                            assert_raises, parametric, skipif)
from nipype.interfaces.base import TraitError

import nipype.interfaces.freesurfer as fs

def no_freesurfer():
    if fs.Info().version is None:
        return True
    else:
        return False

def create_files_in_directory():
    outdir = mkdtemp()
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

def create_surf_file():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    surf = 'lh.a.nii'
    hdr = nif.Nifti1Header()
    shape = (1,100,1)
    hdr.set_data_shape(shape)
    img = np.random.random(shape)
    nif.save(nif.Nifti1Image(surf,np.eye(4),hdr),
             os.path.join(outdir,f))
    return surf, outdir, cwd

def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)

@skipif(no_freesurfer)
def test_sample2surf():

    s2s = fs.SampleToSurface()
    # Test underlying command
    yield assert_equal, s2s.cmd, 'mri_vol2surf'

    # Test mandatory args exception
    yield assert_raises, ValueError, s2s.run

    # Create testing files
    files, cwd, oldwd = create_files_in_directory()

    # Test input settings
    s2s.inputs.source_file = files[0]
    s2s.inputs.reference_file = files[1]
    s2s.inputs.hemi = "lh"
    s2s.inputs.sampling_range = .5
    s2s.inputs.sampling_units = "frac"
    s2s.inputs.sampling_method = "point"

    # Test a basic command line
    yield assert_equal, s2s.cmdline, ("mri_vol2surf "
    "--hemi lh --o %s --ref %s --projfrac 0.500 --mov %s"
    %(os.path.join(cwd, "lh.a.mgz"),files[1],files[0]))
    
    # Test identity
    s2sish = fs.SampleToSurface(source_file = files[1], reference_file = files[0],hemi="rh")
    yield assert_not_equal, s2s, s2sish

    # Test hits file name creation
    s2s.inputs.hits_file = True
    yield assert_equal, s2s._get_outfilename("hits_file"), os.path.join(cwd, "lh.a_hits.mgz")

    # Test that a 2-tuple range raises an error
    def set_illegal_range():
        s2s.inputs.sampling_range = (.2, .5)
    yield assert_raises, TraitError, set_illegal_range

    # Clean up our mess
    clean_directory(cwd, oldwd)

@skipif(no_freesurfer)
def test_surfsmooth():
    
    smooth = fs.SurfaceSmooth()

    # Test underlying command
    yield assert_equal, smooth.cmd, "mri_surf2surf"

    # Test mandatory args exception
    yield assert_raises, ValueError, smooth.run

    # Create testing files
    surf, cwd, oldwd = create_surf_file()

    # Test input settings
    smooth.inputs.in_file = surf
    smooth.inputs.subject = "fsaverage"
    smooth.inputs.fwhm = 5
    smooth.inputs.out_file = "lh.a_smooth.nii"
    smooth.inputs.hemi = "lh"

    # Test the command line
    yield assert_equal, smooth.cmdline, \
    "mri_surf2surf --sval %s --subject fsaverage --hemi lh --fwhm 5.0000 --tval lh.a_smooth.nii"%surf

    # Test identity
    shmooth = fs.SurfaceSmooth(
        subject="fsaverage", fwhm=6, in_file=surf, hemi="lh", out_file="lh.a_smooth.nii")
    yield assert_not_equal, smooth, shmooth

    # Clean up
    clean_directory(cwd, oldwd)




@skipif(no_freesurfer)
def test_surfshots():

    fotos = fs.SurfaceScreenshots()

    # Test underlying command
    yield assert_equal, fotos.cmd, "tksurfer"

    # Test mandatory args exception
    yield assert_raises, ValueError, fotos.run

    # Create testing files
    files, cwd, oldwd = create_files_in_directory()

    # Test input settins
    fotos.inputs.subject = "fsaverage"
    fotos.inputs.hemi = "lh"
    fotos.inputs.surface = "pial"

    # Test a basic command line
    yield assert_equal, fotos.cmdline, "tksurfer fsaverage lh pial -tcl screenshots.tcl"

    # Test identity
    schmotos = fs.SurfaceScreenshots(subject="mysubject",hemi="rh",surface="white")
    yield assert_not_equal, fotos, schmotos

    # Test that the tcl script gets written
    fotos._write_tcl_script()
    yield assert_equal, True, os.path.exists("screenshots.tcl") 

    # Test that we can use a different tcl script
    foo = open("other.tcl", "w").close()
    fotos.inputs.tcl_script = "other.tcl"
    yield assert_equal, fotos.cmdline, "tksurfer fsaverage lh pial -tcl other.tcl"

    # Test that the interface crashes politely if graphics aren't enabled
    hold_display = os.environ["DISPLAY"]
    del os.environ["DISPLAY"]
    yield assert_raises, RuntimeError, fotos.run
    os.environ["DISPLAY"] = hold_display

    # Clean up our mess
    clean_directory(cwd, oldwd)
