# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nb
from nipype.testing import (assert_equal, assert_not_equal,
                            assert_raises, parametric, skipif)
from nipype.interfaces.fsl.base import Info
import nipype.interfaces.fsl.maths as fsl
from nipype.interfaces.base import TraitError
from nipype.interfaces.fsl import no_fsl


def create_files_in_directory():
    testdir = mkdtemp()
    origdir = os.getcwd()
    os.chdir(testdir)

    ftype = os.environ["FSLOUTPUTTYPE"]
    os.environ["FSLOUTPUTTYPE"] = "NIFTI"

    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(testdir,f))
    return filelist, testdir, origdir, ftype

def clean_directory(testdir, origdir, ftype):
    if os.path.exists(testdir):
        rmtree(testdir)
    os.chdir(origdir)
    os.environ["FSLOUTPUTTYPE"] = ftype


@skipif(no_fsl)
def test_maths_base():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get some fslmaths 
    maths = fsl.MathsCommand()

    # Test that we got what we wanted
    yield assert_equal, maths.cmd, "fslmaths"

    # Test that it needs a mandatory argument
    yield assert_raises, ValueError, maths.run

    # Set an in file
    maths.inputs.in_file = "a.nii"

    # Now test the most basic command line
    yield assert_equal, maths.cmdline, "fslmaths a.nii %s"%os.path.join(testdir, "a_maths.nii")

    # Now test that we can set the various data types
    dtypes = ["float","char","int","short","double","input"]
    int_cmdline =  "fslmaths -dt %s a.nii " + os.path.join(testdir, "a_maths.nii")
    out_cmdline =  "fslmaths a.nii " + os.path.join(testdir, "a_maths.nii") + " -odt %s"
    duo_cmdline =  "fslmaths -dt %s a.nii " + os.path.join(testdir, "a_maths.nii") + " -odt %s"
    for dtype in dtypes:
        foo = fsl.MathsCommand(in_file="a.nii",internal_datatype=dtype)
        yield assert_equal, foo.cmdline, int_cmdline%dtype
        bar = fsl.MathsCommand(in_file="a.nii",output_datatype=dtype)
        yield assert_equal, bar.cmdline, out_cmdline%dtype
        foobar = fsl.MathsCommand(in_file="a.nii",internal_datatype=dtype,output_datatype=dtype)
        yield assert_equal, foobar.cmdline, duo_cmdline%(dtype, dtype)

    # Test that we can ask for an outfile name
    maths.inputs.out_file = "b.nii"
    yield assert_equal, maths.cmdline, "fslmaths a.nii b.nii"

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)

@skipif(no_fsl)
def test_changedt():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get some fslmaths 
    cdt = fsl.ChangeDataType()

    # Test that we got what we wanted
    yield assert_equal, cdt.cmd, "fslmaths"

    # Test that it needs a mandatory argument
    yield assert_raises, ValueError, cdt.run

    # Set an in file and out file
    cdt.inputs.in_file = "a.nii"
    cdt.inputs.out_file = "b.nii"

    # But it still shouldn't work
    yield assert_raises, ValueError, cdt.run

    # Now test that we can set the various data types
    dtypes = ["float","char","int","short","double","input"]
    cmdline =  "fslmaths a.nii b.nii -odt %s"
    for dtype in dtypes:
        foo = fsl.MathsCommand(in_file="a.nii",out_file="b.nii",output_datatype=dtype)
        yield assert_equal, foo.cmdline, cmdline%dtype

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)

@skipif(no_fsl)
def test_threshold():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    thresh = fsl.Threshold(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, thresh.cmd, "fslmaths"

    # Test mandtory args
    yield assert_raises, ValueError, thresh.run

    # Test the various opstrings
    cmdline = "fslmaths a.nii %s b.nii"
    for val in [0, 0., -1, -1.5, -0.5, 0.5, 3, 400, 400.5]:
        thresh.inputs.thresh = val
        yield assert_equal, thresh.cmdline, cmdline%"-thr %.10f"%val

    val = "%.10f"%42
    thresh = fsl.Threshold(in_file="a.nii",out_file="b.nii",thresh=42,use_robust_range=True)
    yield assert_equal, thresh.cmdline, cmdline%("-thrp "+val)
    thresh.inputs.use_nonzero_voxels = True
    yield assert_equal, thresh.cmdline, cmdline%("-thrP "+val)
    thresh = fsl.Threshold(in_file="a.nii",out_file="b.nii",thresh=42,direction="above")
    yield assert_equal, thresh.cmdline, cmdline%("-uthr "+val)
    thresh.inputs.use_robust_range=True
    yield assert_equal, thresh.cmdline, cmdline%("-uthrp "+val)
    thresh.inputs.use_nonzero_voxels = True
    yield assert_equal, thresh.cmdline, cmdline%("-uthrP "+val)

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)
        

@skipif(no_fsl)
def test_meanimage():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    meaner = fsl.MeanImage(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, meaner.cmd, "fslmaths"

    # Test the defualt opstring
    yield assert_equal, meaner.cmdline, "fslmaths a.nii -Tmean b.nii"

    # Test the other dimensions
    cmdline = "fslmaths a.nii -%smean b.nii"
    for dim in ["X","Y","Z","T"]:
        meaner.inputs.dimension=dim
        yield assert_equal, meaner.cmdline, cmdline%dim

    # Test the auto naming
    meaner = fsl.MeanImage(in_file="a.nii")
    yield assert_equal, meaner.cmdline, "fslmaths a.nii -Tmean %s"%os.path.join(testdir, "a_mean.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)
        
@skipif(no_fsl)
def test_smooth():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    smoother = fsl.IsotropicSmooth(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, smoother.cmd, "fslmaths"

    # Test that smoothing kernel is mandatory
    yield assert_raises, ValueError, smoother.run

    # Test smoothing kernels
    cmdline = "fslmaths a.nii -s %.5f b.nii"
    for val in [0,1.,1,25,0.5,8/3]:
        smoother = fsl.IsotropicSmooth(in_file="a.nii",out_file="b.nii",sigma=val)
        yield assert_equal, smoother.cmdline, cmdline%val 
        smoother = fsl.IsotropicSmooth(in_file="a.nii",out_file="b.nii",fwhm=val)
        val = float(val)/np.sqrt(8 * np.log(2))
        yield assert_equal, smoother.cmdline, cmdline%val
   
    # Test automatic naming
    smoother = fsl.IsotropicSmooth(in_file="a.nii", sigma=5)
    yield assert_equal, smoother.cmdline, "fslmaths a.nii -s %.5f %s"%(5, os.path.join(testdir, "a_smooth.nii"))

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)
        
@skipif(no_fsl)
def test_mask():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    masker = fsl.ApplyMask(in_file="a.nii",out_file="c.nii")

    # Test the underlying command
    yield assert_equal, masker.cmd, "fslmaths"

    # Test that the mask image is mandatory
    yield assert_raises, ValueError, masker.run

    # Test setting the mask image
    masker.inputs.mask_file = "b.nii"
    yield assert_equal, masker.cmdline, "fslmaths a.nii -mas b.nii c.nii"

    # Test auto name generation
    masker = fsl.ApplyMask(in_file="a.nii",mask_file="b.nii")
    yield assert_equal, masker.cmdline, "fslmaths a.nii -mas b.nii "+os.path.join(testdir, "a_mask.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


