# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nb
from nipype.testing import (assert_equal, assert_raises, skipif)
from nipype.interfaces.base import Undefined
import nipype.interfaces.fsl.maths as fsl
from nipype.interfaces.fsl import no_fsl


def create_files_in_directory():
    testdir = os.path.realpath(mkdtemp())
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
def test_maximage():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    maxer = fsl.MaxImage(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, maxer.cmd, "fslmaths"

    # Test the defualt opstring
    yield assert_equal, maxer.cmdline, "fslmaths a.nii -Tmax b.nii"

    # Test the other dimensions
    cmdline = "fslmaths a.nii -%smax b.nii"
    for dim in ["X","Y","Z","T"]:
        maxer.inputs.dimension=dim
        yield assert_equal, maxer.cmdline, cmdline%dim

    # Test the auto naming
    maxer = fsl.MaxImage(in_file="a.nii")
    yield assert_equal, maxer.cmdline, "fslmaths a.nii -Tmax %s"%os.path.join(testdir, "a_max.nii")

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
    yield assert_equal, masker.cmdline, "fslmaths a.nii -mas b.nii "+os.path.join(testdir, "a_masked.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


@skipif(no_fsl)
def test_dilation():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    diller = fsl.DilateImage(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, diller.cmd, "fslmaths"

    # Test that the dilation operation is mandatory
    yield assert_raises, ValueError, diller.run

    # Test the different dilation operations
    for op in ["mean", "modal", "max"]:
        cv = dict(mean="M", modal="D", max="F")
        diller.inputs.operation = op
        yield assert_equal, diller.cmdline, "fslmaths a.nii -dil%s b.nii"%cv[op]

    # Now test the different kernel options
    for k in ["3D", "2D", "box", "boxv", "gauss", "sphere"]:
        for size in [1, 1.5, 5]:
            diller.inputs.kernel_shape = k
            diller.inputs.kernel_size = size
            yield assert_equal, diller.cmdline, "fslmaths a.nii -kernel %s %.4f -dilF b.nii"%(k, size)

    # Test that we can use a file kernel
    f = open("kernel.txt","w").close()
    del f # Shut pyflakes up
    diller.inputs.kernel_shape = "file"
    diller.inputs.kernel_size = Undefined
    diller.inputs.kernel_file = "kernel.txt"
    yield assert_equal, diller.cmdline, "fslmaths a.nii -kernel file kernel.txt -dilF b.nii"

    # Test that we don't need to request an out name
    dil = fsl.DilateImage(in_file="a.nii", operation="max")
    yield assert_equal, dil.cmdline, "fslmaths a.nii -dilF %s"%os.path.join(testdir, "a_dil.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)

@skipif(no_fsl)
def test_erosion():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    erode = fsl.ErodeImage(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, erode.cmd, "fslmaths"

    # Test the basic command line
    yield assert_equal, erode.cmdline, "fslmaths a.nii -ero b.nii"

    # Test that something else happens when you minimum filter
    erode.inputs.minimum_filter = True
    yield assert_equal, erode.cmdline, "fslmaths a.nii -eroF b.nii"

    # Test that we don't need to request an out name
    erode = fsl.ErodeImage(in_file="a.nii")
    yield assert_equal, erode.cmdline, "fslmaths a.nii -ero %s"%os.path.join(testdir, "a_ero.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)

@skipif(no_fsl)
def test_spatial_filter():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    filter = fsl.SpatialFilter(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, filter.cmd, "fslmaths"

    # Test that it fails without an operation
    yield assert_raises, ValueError, filter.run

    # Test the different operations
    for op in ["mean", "meanu", "median"]:
        filter.inputs.operation = op
        yield assert_equal, filter.cmdline, "fslmaths a.nii -f%s b.nii"%op

    # Test that we don't need to ask for an out name
    filter = fsl.SpatialFilter(in_file="a.nii", operation="mean")
    yield assert_equal, filter.cmdline, "fslmaths a.nii -fmean %s"%os.path.join(testdir, "a_filt.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


@skipif(no_fsl)
def test_unarymaths():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    maths = fsl.UnaryMaths(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, maths.cmd, "fslmaths"

    # Test that it fails without an operation
    yield assert_raises, ValueError, maths.run

    # Test the different operations
    ops = ["exp", "log", "sin", "cos", "sqr", "sqrt", "recip", "abs", "bin", "index"]
    for op in ops:
        maths.inputs.operation = op
        yield assert_equal, maths.cmdline, "fslmaths a.nii -%s b.nii"%op

    # Test that we don't need to ask for an out file
    for op in ops:
        maths = fsl.UnaryMaths(in_file="a.nii", operation=op)
        yield assert_equal, maths.cmdline, "fslmaths a.nii -%s %s"%(op, os.path.join(testdir, "a_%s.nii"%op))

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


@skipif(no_fsl)
def test_binarymaths():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    maths = fsl.BinaryMaths(in_file="a.nii",out_file="c.nii")

    # Test the underlying command
    yield assert_equal, maths.cmd, "fslmaths"

    # Test that it fails without an operation an
    yield assert_raises, ValueError, maths.run

    # Test the different operations
    ops = ["add", "sub", "mul", "div", "rem", "min", "max"]
    operands = ["b.nii", -2, -0.5, 0, .123456, np.pi, 500]
    for op in ops:
        for ent in operands:
            maths = fsl.BinaryMaths(in_file="a.nii", out_file="c.nii", operation = op)
            if ent == "b.nii":
                maths.inputs.operand_file = ent
                yield assert_equal, maths.cmdline, "fslmaths a.nii -%s b.nii c.nii"%op
            else:
                maths.inputs.operand_value = ent
                yield assert_equal, maths.cmdline, "fslmaths a.nii -%s %.8f c.nii"%(op, ent)

    # Test that we don't need to ask for an out file
    for op in ops:
        maths = fsl.BinaryMaths(in_file="a.nii", operation=op, operand_file="b.nii")
        yield assert_equal, maths.cmdline, "fslmaths a.nii -%s b.nii %s"%(op,os.path.join(testdir,"a_maths.nii"))

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


@skipif(no_fsl)
def test_multimaths():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    maths = fsl.MultiImageMaths(in_file="a.nii",out_file="c.nii")

    # Test the underlying command
    yield assert_equal, maths.cmd, "fslmaths"

    # Test that it fails without an operation an
    yield assert_raises, ValueError, maths.run

    # Test a few operations
    maths.inputs.operand_files = ["a.nii", "b.nii"]
    opstrings = ["-add %s -div %s",
                 "-max 1 -sub %s -min %s",
                 "-mas %s -add %s"]
    for ostr in opstrings:
        maths.inputs.op_string = ostr
        yield assert_equal, maths.cmdline, "fslmaths a.nii %s c.nii"%ostr%("a.nii", "b.nii")

    # Test that we don't need to ask for an out file
    maths = fsl.MultiImageMaths(in_file="a.nii", op_string="-add %s -mul 5", operand_files=["b.nii"])
    yield assert_equal, maths.cmdline, \
    "fslmaths a.nii -add b.nii -mul 5 %s"%os.path.join(testdir,"a_maths.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


@skipif(no_fsl)
def test_tempfilt():
    files, testdir, origdir, ftype = create_files_in_directory()

    # Get the command
    filt = fsl.TemporalFilter(in_file="a.nii",out_file="b.nii")

    # Test the underlying command
    yield assert_equal, filt.cmd, "fslmaths"

    # Test that both filters are initialized off
    yield assert_equal, filt.cmdline, "fslmaths a.nii -bptf -1.000000 -1.000000 b.nii"

    # Test some filters
    windows = [(-1, -1), (0.1, 0.1), (-1, 20), (20, -1), (128, 248)]
    for win in windows:
        filt.inputs.highpass_sigma = win[0]
        filt.inputs.lowpass_sigma = win[1]
        yield assert_equal, filt.cmdline, "fslmaths a.nii -bptf %.6f %.6f b.nii"%win

    # Test that we don't need to ask for an out file
    filt = fsl.TemporalFilter(in_file="a.nii", highpass_sigma = 64)
    yield assert_equal, filt.cmdline, \
    "fslmaths a.nii -bptf 64.000000 -1.000000 %s"%os.path.join(testdir,"a_filt.nii")

    # Clean up our mess
    clean_directory(testdir, origdir, ftype)


