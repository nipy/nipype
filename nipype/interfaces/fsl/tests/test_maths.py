# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import division
from __future__ import unicode_literals
from builtins import open
import os
import numpy as np

from nipype.interfaces.base import Undefined
import nipype.interfaces.fsl.maths as fsl
from nipype.interfaces.fsl import no_fsl

import pytest
from nipype.testing.fixtures import create_files_in_directory_plus_output_type


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_maths_base(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get some fslmaths
    maths = fsl.MathsCommand()

    # Test that we got what we wanted
    assert maths.cmd == "fslmaths"

    # Test that it needs a mandatory argument
    with pytest.raises(ValueError):
        maths.run()

    # Set an in file
    maths.inputs.in_file = "a.nii"
    out_file = "a_maths{}".format(out_ext)

    # Now test the most basic command line
    assert maths.cmdline == "fslmaths a.nii {}".format(
        os.path.join(testdir, out_file))

    # Now test that we can set the various data types
    dtypes = ["float", "char", "int", "short", "double", "input"]
    int_cmdline = "fslmaths -dt {} a.nii " + os.path.join(testdir, out_file)
    out_cmdline = "fslmaths a.nii " + os.path.join(testdir,
                                                   out_file) + " -odt {}"
    duo_cmdline = "fslmaths -dt {} a.nii " + os.path.join(
        testdir, out_file) + " -odt {}"
    for dtype in dtypes:
        foo = fsl.MathsCommand(in_file="a.nii", internal_datatype=dtype)
        assert foo.cmdline == int_cmdline.format(dtype)
        bar = fsl.MathsCommand(in_file="a.nii", output_datatype=dtype)
        assert bar.cmdline == out_cmdline.format(dtype)
        foobar = fsl.MathsCommand(
            in_file="a.nii", internal_datatype=dtype, output_datatype=dtype)
        assert foobar.cmdline == duo_cmdline.format(dtype, dtype)

    # Test that we can ask for an outfile name
    maths.inputs.out_file = "b.nii"
    assert maths.cmdline == "fslmaths a.nii b.nii"


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_changedt(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get some fslmaths
    cdt = fsl.ChangeDataType()

    # Test that we got what we wanted
    assert cdt.cmd == "fslmaths"

    # Test that it needs a mandatory argument
    with pytest.raises(ValueError):
        cdt.run()

    # Set an in file and out file
    cdt.inputs.in_file = "a.nii"
    cdt.inputs.out_file = "b.nii"

    # But it still shouldn't work
    with pytest.raises(ValueError):
        cdt.run()

    # Now test that we can set the various data types
    dtypes = ["float", "char", "int", "short", "double", "input"]
    cmdline = "fslmaths a.nii b.nii -odt {}"
    for dtype in dtypes:
        foo = fsl.MathsCommand(
            in_file="a.nii", out_file="b.nii", output_datatype=dtype)
        assert foo.cmdline == cmdline.format(dtype)


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_threshold(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    thresh = fsl.Threshold(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert thresh.cmd == "fslmaths"

    # Test mandtory args
    with pytest.raises(ValueError):
        thresh.run()

    # Test the various opstrings
    cmdline = "fslmaths a.nii {} b.nii"
    for val in [0, 0., -1, -1.5, -0.5, 0.5, 3, 400, 400.5]:
        thresh.inputs.thresh = val
        assert thresh.cmdline == cmdline.format("-thr {:.10f}".format(val))

    val = "{:.10f}".format(42)
    thresh = fsl.Threshold(
        in_file="a.nii", out_file="b.nii", thresh=42, use_robust_range=True)
    assert thresh.cmdline == cmdline.format("-thrp " + val)
    thresh.inputs.use_nonzero_voxels = True
    assert thresh.cmdline == cmdline.format("-thrP " + val)
    thresh = fsl.Threshold(
        in_file="a.nii", out_file="b.nii", thresh=42, direction="above")
    assert thresh.cmdline == cmdline.format("-uthr " + val)
    thresh.inputs.use_robust_range = True
    assert thresh.cmdline == cmdline.format("-uthrp " + val)
    thresh.inputs.use_nonzero_voxels = True
    assert thresh.cmdline == cmdline.format("-uthrP " + val)


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_meanimage(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    meaner = fsl.MeanImage(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert meaner.cmd == "fslmaths"

    # Test the defualt opstring
    assert meaner.cmdline == "fslmaths a.nii -Tmean b.nii"

    # Test the other dimensions
    cmdline = "fslmaths a.nii -{}mean b.nii"
    for dim in ["X", "Y", "Z", "T"]:
        meaner.inputs.dimension = dim
        assert meaner.cmdline == cmdline.format(dim)

    # Test the auto naming
    meaner = fsl.MeanImage(in_file="a.nii")
    assert meaner.cmdline == "fslmaths a.nii -Tmean {}".format(
        os.path.join(testdir, "a_mean{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_stdimage(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    stder = fsl.StdImage(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert stder.cmd == "fslmaths"

    # Test the defualt opstring
    assert stder.cmdline == "fslmaths a.nii -Tstd b.nii"

    # Test the other dimensions
    cmdline = "fslmaths a.nii -{}std b.nii"
    for dim in ["X", "Y", "Z", "T"]:
        stder.inputs.dimension = dim
        assert stder.cmdline == cmdline.format(dim)

    # Test the auto naming
    stder = fsl.StdImage(in_file="a.nii", output_type='NIFTI')
    assert stder.cmdline == "fslmaths a.nii -Tstd {}".format(
        os.path.join(testdir, "a_std.nii"))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_maximage(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    maxer = fsl.MaxImage(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert maxer.cmd == "fslmaths"

    # Test the defualt opstring
    assert maxer.cmdline == "fslmaths a.nii -Tmax b.nii"

    # Test the other dimensions
    cmdline = "fslmaths a.nii -{}max b.nii"
    for dim in ["X", "Y", "Z", "T"]:
        maxer.inputs.dimension = dim
        assert maxer.cmdline == cmdline.format(dim)

    # Test the auto naming
    maxer = fsl.MaxImage(in_file="a.nii")
    assert maxer.cmdline == "fslmaths a.nii -Tmax {}".format(
        os.path.join(testdir, "a_max{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_smooth(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    smoother = fsl.IsotropicSmooth(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert smoother.cmd == "fslmaths"

    # Test that smoothing kernel is mandatory
    with pytest.raises(ValueError):
        smoother.run()

    # Test smoothing kernels
    cmdline = "fslmaths a.nii -s {:.5f} b.nii"
    for val in [0, 1., 1, 25, 0.5, 8 / 3.]:
        smoother = fsl.IsotropicSmooth(
            in_file="a.nii", out_file="b.nii", sigma=val)
        assert smoother.cmdline == cmdline.format(val)
        smoother = fsl.IsotropicSmooth(
            in_file="a.nii", out_file="b.nii", fwhm=val)
        val = float(val) / np.sqrt(8 * np.log(2))
        assert smoother.cmdline == cmdline.format(val)

    # Test automatic naming
    smoother = fsl.IsotropicSmooth(in_file="a.nii", sigma=5)
    assert smoother.cmdline == "fslmaths a.nii -s {:.5f} {}".format(
        5, os.path.join(testdir, "a_smooth{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_mask(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    masker = fsl.ApplyMask(in_file="a.nii", out_file="c.nii")

    # Test the underlying command
    assert masker.cmd == "fslmaths"

    # Test that the mask image is mandatory
    with pytest.raises(ValueError):
        masker.run()

    # Test setting the mask image
    masker.inputs.mask_file = "b.nii"
    assert masker.cmdline == "fslmaths a.nii -mas b.nii c.nii"

    # Test auto name generation
    masker = fsl.ApplyMask(in_file="a.nii", mask_file="b.nii")
    assert masker.cmdline == "fslmaths a.nii -mas b.nii " + os.path.join(
        testdir, "a_masked{}".format(out_ext))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_dilation(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    diller = fsl.DilateImage(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert diller.cmd == "fslmaths"

    # Test that the dilation operation is mandatory
    with pytest.raises(ValueError):
        diller.run()

    # Test the different dilation operations
    for op in ["mean", "modal", "max"]:
        cv = dict(mean="M", modal="D", max="F")
        diller.inputs.operation = op
        assert diller.cmdline == "fslmaths a.nii -dil{} b.nii".format(cv[op])

    # Now test the different kernel options
    for k in ["3D", "2D", "box", "boxv", "gauss", "sphere"]:
        for size in [1, 1.5, 5]:
            diller.inputs.kernel_shape = k
            diller.inputs.kernel_size = size
            assert diller.cmdline == "fslmaths a.nii -kernel {} {:.4f} -dilF b.nii".format(
                k, size)

    # Test that we can use a file kernel
    f = open("kernel.txt", "w").close()
    del f  # Shut pyflakes up
    diller.inputs.kernel_shape = "file"
    diller.inputs.kernel_size = Undefined
    diller.inputs.kernel_file = "kernel.txt"
    assert diller.cmdline == "fslmaths a.nii -kernel file kernel.txt -dilF b.nii"

    # Test that we don't need to request an out name
    dil = fsl.DilateImage(in_file="a.nii", operation="max")
    assert dil.cmdline == "fslmaths a.nii -dilF {}".format(
        os.path.join(testdir, "a_dil{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_erosion(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    erode = fsl.ErodeImage(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert erode.cmd == "fslmaths"

    # Test the basic command line
    assert erode.cmdline == "fslmaths a.nii -ero b.nii"

    # Test that something else happens when you minimum filter
    erode.inputs.minimum_filter = True
    assert erode.cmdline == "fslmaths a.nii -eroF b.nii"

    # Test that we don't need to request an out name
    erode = fsl.ErodeImage(in_file="a.nii")
    assert erode.cmdline == "fslmaths a.nii -ero {}".format(
        os.path.join(testdir, "a_ero{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_spatial_filter(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    filter = fsl.SpatialFilter(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert filter.cmd == "fslmaths"

    # Test that it fails without an operation
    with pytest.raises(ValueError):
        filter.run()

    # Test the different operations
    for op in ["mean", "meanu", "median"]:
        filter.inputs.operation = op
        assert filter.cmdline == "fslmaths a.nii -f{} b.nii".format(op)

    # Test that we don't need to ask for an out name
    filter = fsl.SpatialFilter(in_file="a.nii", operation="mean")
    assert filter.cmdline == "fslmaths a.nii -fmean {}".format(
        os.path.join(testdir, "a_filt{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_unarymaths(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    maths = fsl.UnaryMaths(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert maths.cmd == "fslmaths"

    # Test that it fails without an operation
    with pytest.raises(ValueError):
        maths.run()

    # Test the different operations
    ops = [
        "exp", "log", "sin", "cos", "sqr", "sqrt", "recip", "abs", "bin",
        "index"
    ]
    for op in ops:
        maths.inputs.operation = op
        assert maths.cmdline == "fslmaths a.nii -{} b.nii".format(op)

    # Test that we don't need to ask for an out file
    for op in ops:
        maths = fsl.UnaryMaths(in_file="a.nii", operation=op)
        assert maths.cmdline == "fslmaths a.nii -{} {}".format(
            op, os.path.join(testdir, "a_{}{}".format(op, out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_binarymaths(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    maths = fsl.BinaryMaths(in_file="a.nii", out_file="c.nii")

    # Test the underlying command
    assert maths.cmd == "fslmaths"

    # Test that it fails without an operation an
    with pytest.raises(ValueError):
        maths.run()

    # Test the different operations
    ops = ["add", "sub", "mul", "div", "rem", "min", "max"]
    operands = ["b.nii", -2, -0.5, 0, .123456, np.pi, 500]
    for op in ops:
        for ent in operands:
            maths = fsl.BinaryMaths(
                in_file="a.nii", out_file="c.nii", operation=op)
            if ent == "b.nii":
                maths.inputs.operand_file = ent
                assert maths.cmdline == "fslmaths a.nii -{} b.nii c.nii".format(
                    op)
            else:
                maths.inputs.operand_value = ent
                assert maths.cmdline == "fslmaths a.nii -{} {:.8f} c.nii".format(
                    op, ent)

    # Test that we don't need to ask for an out file
    for op in ops:
        maths = fsl.BinaryMaths(
            in_file="a.nii", operation=op, operand_file="b.nii")
        assert maths.cmdline == "fslmaths a.nii -{} b.nii {}".format(
            op, os.path.join(testdir, "a_maths{}".format(out_ext)))


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_multimaths(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    maths = fsl.MultiImageMaths(in_file="a.nii", out_file="c.nii")

    # Test the underlying command
    assert maths.cmd == "fslmaths"

    # Test that it fails without an operation an
    with pytest.raises(ValueError):
        maths.run()

    # Test a few operations
    maths.inputs.operand_files = ["a.nii", "b.nii"]
    opstrings = [
        "-add %s -div %s", "-max 1 -sub %s -min %s", "-mas %s -add %s"
    ]
    for ostr in opstrings:
        maths.inputs.op_string = ostr
        assert maths.cmdline == "fslmaths a.nii %s c.nii" % ostr % ("a.nii",
                                                                    "b.nii")

    # Test that we don't need to ask for an out file
    maths = fsl.MultiImageMaths(
        in_file="a.nii", op_string="-add %s -mul 5", operand_files=["b.nii"])
    assert maths.cmdline == \
        "fslmaths a.nii -add b.nii -mul 5 %s" % os.path.join(testdir, "a_maths%s" % out_ext)


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_tempfilt(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type

    # Get the command
    filt = fsl.TemporalFilter(in_file="a.nii", out_file="b.nii")

    # Test the underlying command
    assert filt.cmd == "fslmaths"

    # Test that both filters are initialized off
    assert filt.cmdline == "fslmaths a.nii -bptf -1.000000 -1.000000 b.nii"

    # Test some filters
    windows = [(-1, -1), (0.1, 0.1), (-1, 20), (20, -1), (128, 248)]
    for win in windows:
        filt.inputs.highpass_sigma = win[0]
        filt.inputs.lowpass_sigma = win[1]
        assert filt.cmdline == "fslmaths a.nii -bptf {:.6f} {:.6f} b.nii".format(
            win[0], win[1])

    # Test that we don't need to ask for an out file
    filt = fsl.TemporalFilter(in_file="a.nii", highpass_sigma=64)
    assert filt.cmdline == \
        "fslmaths a.nii -bptf 64.000000 -1.000000 {}".format(os.path.join(testdir, "a_filt{}".format(out_ext)))
