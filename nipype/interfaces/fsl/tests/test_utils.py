# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

import numpy as np

import nibabel as nb
import pytest
import nipype.interfaces.fsl.utils as fsl
from nipype.interfaces.fsl import no_fsl, Info

from nipype.testing.fixtures import create_files_in_directory_plus_output_type


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_fslroi(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type

    roi = fsl.ExtractROI()

    # make sure command gets called
    assert roi.cmd == "fslroi"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        roi.run()

    # .inputs based parameters setting
    roi.inputs.in_file = filelist[0]
    roi.inputs.roi_file = "foo_roi.nii"
    roi.inputs.t_min = 10
    roi.inputs.t_size = 20
    assert roi.cmdline == "fslroi %s foo_roi.nii 10 20" % filelist[0]

    # .run based parameter setting
    roi2 = fsl.ExtractROI(
        in_file=filelist[0],
        roi_file="foo2_roi.nii",
        t_min=20,
        t_size=40,
        x_min=3,
        x_size=30,
        y_min=40,
        y_size=10,
        z_min=5,
        z_size=20,
    )
    assert roi2.cmdline == "fslroi %s foo2_roi.nii 3 30 40 10 5 20 20 40" % filelist[0]

    # test arguments for opt_map
    # Fslroi class doesn't have a filled opt_map{}


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_fslmerge(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type

    merger = fsl.Merge()

    # make sure command gets called
    assert merger.cmd == "fslmerge"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        merger.run()

    # .inputs based parameters setting
    merger.inputs.in_files = filelist
    merger.inputs.merged_file = "foo_merged.nii"
    merger.inputs.dimension = "t"
    merger.inputs.output_type = "NIFTI"
    assert merger.cmdline == "fslmerge -t foo_merged.nii %s" % " ".join(filelist)

    # verify that providing a tr value updates the dimension to tr
    merger.inputs.tr = 2.25
    assert merger.cmdline == "fslmerge -tr foo_merged.nii %s %.2f" % (
        " ".join(filelist),
        2.25,
    )

    # .run based parameter setting
    merger2 = fsl.Merge(
        in_files=filelist,
        merged_file="foo_merged.nii",
        dimension="t",
        output_type="NIFTI",
        tr=2.25,
    )

    assert merger2.cmdline == "fslmerge -tr foo_merged.nii %s %.2f" % (
        " ".join(filelist),
        2.25,
    )

    # test arguments for opt_map
    # Fslmerge class doesn't have a filled opt_map{}


# test fslmath


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_fslmaths(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    math = fsl.ImageMaths()

    # make sure command gets called
    assert math.cmd == "fslmaths"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        math.run()

    # .inputs based parameters setting
    math.inputs.in_file = filelist[0]
    math.inputs.op_string = "-add 2.5 -mul input_volume2"
    math.inputs.out_file = "foo_math.nii"
    assert (
        math.cmdline
        == "fslmaths %s -add 2.5 -mul input_volume2 foo_math.nii" % filelist[0]
    )

    # .run based parameter setting
    math2 = fsl.ImageMaths(
        in_file=filelist[0], op_string="-add 2.5", out_file="foo2_math.nii"
    )
    assert math2.cmdline == "fslmaths %s -add 2.5 foo2_math.nii" % filelist[0]

    # test arguments for opt_map
    # Fslmath class doesn't have opt_map{}


# test overlay


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_overlay(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    overlay = fsl.Overlay()

    # make sure command gets called
    assert overlay.cmd == "overlay"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        overlay.run()

    # .inputs based parameters setting
    overlay.inputs.stat_image = filelist[0]
    overlay.inputs.stat_thresh = (2.5, 10)
    overlay.inputs.background_image = filelist[1]
    overlay.inputs.auto_thresh_bg = True
    overlay.inputs.show_negative_stats = True
    overlay.inputs.out_file = "foo_overlay.nii"
    assert (
        overlay.cmdline
        == "overlay 1 0 %s -a %s 2.50 10.00 %s -2.50 -10.00 foo_overlay.nii"
        % (filelist[1], filelist[0], filelist[0])
    )

    # .run based parameter setting
    overlay2 = fsl.Overlay(
        stat_image=filelist[0],
        stat_thresh=(2.5, 10),
        background_image=filelist[1],
        auto_thresh_bg=True,
        out_file="foo2_overlay.nii",
    )
    assert overlay2.cmdline == "overlay 1 0 %s -a %s 2.50 10.00 foo2_overlay.nii" % (
        filelist[1],
        filelist[0],
    )


# test slicer


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_slicer(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    slicer = fsl.Slicer()

    # make sure command gets called
    assert slicer.cmd == "slicer"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        slicer.run()

    # .inputs based parameters setting
    slicer.inputs.in_file = filelist[0]
    slicer.inputs.image_edges = filelist[1]
    slicer.inputs.intensity_range = (10.0, 20.0)
    slicer.inputs.all_axial = True
    slicer.inputs.image_width = 750
    slicer.inputs.out_file = "foo_bar.png"
    assert slicer.cmdline == "slicer %s %s -L -i 10.000 20.000  -A 750 foo_bar.png" % (
        filelist[0],
        filelist[1],
    )

    # .run based parameter setting
    slicer2 = fsl.Slicer(
        in_file=filelist[0],
        middle_slices=True,
        label_slices=False,
        out_file="foo_bar2.png",
    )
    assert slicer2.cmdline == "slicer %s   -a foo_bar2.png" % (filelist[0])


def create_parfiles():
    np.savetxt("a.par", np.random.rand(6, 3))
    np.savetxt("b.par", np.random.rand(6, 3))
    return ["a.par", "b.par"]


# test fsl_tsplot


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_plottimeseries(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    parfiles = create_parfiles()
    plotter = fsl.PlotTimeSeries()

    # make sure command gets called
    assert plotter.cmd == "fsl_tsplot"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        plotter.run()

    # .inputs based parameters setting
    plotter.inputs.in_file = parfiles[0]
    plotter.inputs.labels = ["x", "y", "z"]
    plotter.inputs.y_range = (0, 1)
    plotter.inputs.title = "test plot"
    plotter.inputs.out_file = "foo.png"
    assert plotter.cmdline == (
        "fsl_tsplot -i %s -a x,y,z -o foo.png -t 'test plot' -u 1 --ymin=0 --ymax=1"
        % parfiles[0]
    )

    # .run based parameter setting
    plotter2 = fsl.PlotTimeSeries(
        in_file=parfiles, title="test2 plot", plot_range=(2, 5), out_file="bar.png"
    )
    assert (
        plotter2.cmdline
        == "fsl_tsplot -i %s,%s -o bar.png --start=2 --finish=5 -t 'test2 plot' -u 1"
        % tuple(parfiles)
    )


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_plotmotionparams(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    parfiles = create_parfiles()
    plotter = fsl.PlotMotionParams()

    # make sure command gets called
    assert plotter.cmd == "fsl_tsplot"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        plotter.run()

    # .inputs based parameters setting
    plotter.inputs.in_file = parfiles[0]
    plotter.inputs.in_source = "fsl"
    plotter.inputs.plot_type = "rotations"
    plotter.inputs.out_file = "foo.png"
    assert plotter.cmdline == (
        "fsl_tsplot -i %s -o foo.png -t 'MCFLIRT estimated rotations (radians)' "
        "--start=1 --finish=3 -a x,y,z" % parfiles[0]
    )

    # .run based parameter setting
    plotter2 = fsl.PlotMotionParams(
        in_file=parfiles[1],
        in_source="spm",
        plot_type="translations",
        out_file="bar.png",
    )
    assert plotter2.cmdline == (
        "fsl_tsplot -i %s -o bar.png -t 'Realign estimated translations (mm)' "
        "--start=1 --finish=3 -a x,y,z" % parfiles[1]
    )


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_convertxfm(create_files_in_directory_plus_output_type):
    filelist, outdir, _ = create_files_in_directory_plus_output_type
    cvt = fsl.ConvertXFM()

    # make sure command gets called
    assert cvt.cmd == "convert_xfm"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        cvt.run()

    # .inputs based parameters setting
    cvt.inputs.in_file = filelist[0]
    cvt.inputs.invert_xfm = True
    cvt.inputs.out_file = "foo.mat"
    assert cvt.cmdline == "convert_xfm -omat foo.mat -inverse %s" % filelist[0]

    # constructor based parameter setting
    cvt2 = fsl.ConvertXFM(
        in_file=filelist[0], in_file2=filelist[1], concat_xfm=True, out_file="bar.mat"
    )
    assert cvt2.cmdline == "convert_xfm -omat bar.mat -concat %s %s" % (
        filelist[1],
        filelist[0],
    )


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_swapdims(create_files_in_directory_plus_output_type):
    files, testdir, out_ext = create_files_in_directory_plus_output_type
    swap = fsl.SwapDimensions()

    # Test the underlying command
    assert swap.cmd == "fslswapdim"

    # Test mandatory args
    args = [dict(in_file=files[0]), dict(new_dims=("x", "y", "z"))]
    for arg in args:
        wontrun = fsl.SwapDimensions(**arg)
        with pytest.raises(ValueError):
            wontrun.run()

    # Now test a basic command line
    swap.inputs.in_file = files[0]
    swap.inputs.new_dims = ("x", "y", "z")
    assert swap.cmdline == "fslswapdim a.nii x y z %s" % os.path.realpath(
        os.path.join(testdir, "a_newdims%s" % out_ext)
    )

    # Test that we can set an output name
    swap.inputs.out_file = "b.nii"
    assert swap.cmdline == "fslswapdim a.nii x y z b.nii"
