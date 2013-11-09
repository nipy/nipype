# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nb
from nipype.testing import (assert_equal, assert_not_equal,
                            assert_raises, skipif)
import nipype.interfaces.fsl.utils as fsl
from nipype.interfaces.fsl import no_fsl


def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii', 'b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3, 3, 3, 4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img, np.eye(4), hdr),
                os.path.join(outdir, f))
    return filelist, outdir, cwd


def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)


@skipif(no_fsl)
def test_fslroi():
    filelist, outdir, cwd = create_files_in_directory()

    roi = fsl.ExtractROI()

    # make sure command gets called
    yield assert_equal, roi.cmd, 'fslroi'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, roi.run

    # .inputs based parameters setting
    roi.inputs.in_file = filelist[0]
    roi.inputs.roi_file = 'foo_roi.nii'
    roi.inputs.t_min = 10
    roi.inputs.t_size = 20
    yield assert_equal, roi.cmdline, 'fslroi %s foo_roi.nii 10 20' % filelist[0]

    # .run based parameter setting
    roi2 = fsl.ExtractROI(in_file=filelist[0],
                          roi_file='foo2_roi.nii',
                          t_min=20, t_size=40,
                          x_min=3, x_size=30,
                          y_min=40, y_size=10,
                          z_min=5, z_size=20)
    yield assert_equal, roi2.cmdline, \
        'fslroi %s foo2_roi.nii 3 30 40 10 5 20 20 40' % filelist[0]

    clean_directory(outdir, cwd)
    # test arguments for opt_map
    # Fslroi class doesn't have a filled opt_map{}


@skipif(no_fsl)
def test_fslmerge():
    filelist, outdir, cwd = create_files_in_directory()

    merger = fsl.Merge()

    # make sure command gets called
    yield assert_equal, merger.cmd, 'fslmerge'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, merger.run

    # .inputs based parameters setting
    merger.inputs.in_files = filelist
    merger.inputs.merged_file = 'foo_merged.nii'
    merger.inputs.dimension = 't'
    merger.inputs.output_type = 'NIFTI'
    yield assert_equal, merger.cmdline, 'fslmerge -t foo_merged.nii %s' % ' '.join(filelist)

    # verify that providing a tr value updates the dimension to tr
    merger.inputs.tr = 2.25
    yield assert_equal, merger.cmdline, 'fslmerge -tr foo_merged.nii %s %.2f' % (' '.join(filelist), 2.25)

    # .run based parameter setting
    merger2 = fsl.Merge(in_files=filelist,
                        merged_file='foo_merged.nii',
                        dimension='t',
                        output_type='NIFTI',
                        tr=2.25)

    yield assert_equal, merger2.cmdline, \
        'fslmerge -tr foo_merged.nii %s %.2f' % (' '.join(filelist), 2.25)

    clean_directory(outdir, cwd)
    # test arguments for opt_map
    # Fslmerge class doesn't have a filled opt_map{}

# test fslmath
@skipif(no_fsl)
def test_fslmaths():
    filelist, outdir, cwd = create_files_in_directory()
    math = fsl.ImageMaths()

    # make sure command gets called
    yield assert_equal, math.cmd, 'fslmaths'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, math.run

    # .inputs based parameters setting
    math.inputs.in_file = filelist[0]
    math.inputs.op_string = '-add 2.5 -mul input_volume2'
    math.inputs.out_file = 'foo_math.nii'
    yield assert_equal, math.cmdline, \
        'fslmaths %s -add 2.5 -mul input_volume2 foo_math.nii' % filelist[0]

    # .run based parameter setting
    math2 = fsl.ImageMaths(in_file=filelist[0], op_string='-add 2.5',
                           out_file='foo2_math.nii')
    yield assert_equal, math2.cmdline, 'fslmaths %s -add 2.5 foo2_math.nii' % filelist[0]

    # test arguments for opt_map
    # Fslmath class doesn't have opt_map{}
    clean_directory(outdir, cwd)

# test overlay


@skipif(no_fsl)
def test_overlay():
    filelist, outdir, cwd = create_files_in_directory()
    overlay = fsl.Overlay()

    # make sure command gets called
    yield assert_equal, overlay.cmd, 'overlay'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, overlay.run

    # .inputs based parameters setting
    overlay.inputs.stat_image = filelist[0]
    overlay.inputs.stat_thresh = (2.5, 10)
    overlay.inputs.background_image = filelist[1]
    overlay.inputs.auto_thresh_bg = True
    overlay.inputs.show_negative_stats = True
    overlay.inputs.out_file = 'foo_overlay.nii'
    yield assert_equal, overlay.cmdline, \
        'overlay 1 0 %s -a %s 2.50 10.00 %s -2.50 -10.00 foo_overlay.nii' % (
            filelist[1], filelist[0], filelist[0])

    # .run based parameter setting
    overlay2 = fsl.Overlay(stat_image=filelist[0], stat_thresh=(2.5, 10),
                           background_image=filelist[1], auto_thresh_bg=True,
                           out_file='foo2_overlay.nii')
    yield assert_equal, overlay2.cmdline, 'overlay 1 0 %s -a %s 2.50 10.00 foo2_overlay.nii' % (
        filelist[1], filelist[0])

    clean_directory(outdir, cwd)

# test slicer


@skipif(no_fsl)
def test_slicer():
    filelist, outdir, cwd = create_files_in_directory()
    slicer = fsl.Slicer()

    # make sure command gets called
    yield assert_equal, slicer.cmd, 'slicer'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, slicer.run

    # .inputs based parameters setting
    slicer.inputs.in_file = filelist[0]
    slicer.inputs.image_edges = filelist[1]
    slicer.inputs.intensity_range = (10., 20.)
    slicer.inputs.all_axial = True
    slicer.inputs.image_width = 750
    slicer.inputs.out_file = 'foo_bar.png'
    yield assert_equal, slicer.cmdline, \
        'slicer %s %s -L -i 10.000 20.000  -A 750 foo_bar.png' % (
            filelist[0], filelist[1])

    # .run based parameter setting
    slicer2 = fsl.Slicer(
        in_file=filelist[0], middle_slices=True, label_slices=False,
        out_file='foo_bar2.png')
    yield assert_equal, slicer2.cmdline, 'slicer %s   -a foo_bar2.png' % (filelist[0])

    clean_directory(outdir, cwd)


def create_parfiles():

    np.savetxt('a.par', np.random.rand(6, 3))
    np.savetxt('b.par', np.random.rand(6, 3))
    return ['a.par', 'b.par']

# test fsl_tsplot


@skipif(no_fsl)
def test_plottimeseries():
    filelist, outdir, cwd = create_files_in_directory()
    parfiles = create_parfiles()
    plotter = fsl.PlotTimeSeries()

    # make sure command gets called
    yield assert_equal, plotter.cmd, 'fsl_tsplot'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, plotter.run

    # .inputs based parameters setting
    plotter.inputs.in_file = parfiles[0]
    plotter.inputs.labels = ['x', 'y', 'z']
    plotter.inputs.y_range = (0, 1)
    plotter.inputs.title = 'test plot'
    plotter.inputs.out_file = 'foo.png'
    yield assert_equal, plotter.cmdline, \
        ('fsl_tsplot -i %s -a x,y,z -o foo.png -t \'test plot\' -u 1 --ymin=0 --ymax=1'
         % parfiles[0])

    # .run based parameter setting
    plotter2 = fsl.PlotTimeSeries(
        in_file=parfiles, title='test2 plot', plot_range=(2, 5),
        out_file='bar.png')
    yield assert_equal, plotter2.cmdline, \
        'fsl_tsplot -i %s,%s -o bar.png --start=2 --finish=5 -t \'test2 plot\' -u 1' % tuple(
            parfiles)

    clean_directory(outdir, cwd)


@skipif(no_fsl)
def test_plotmotionparams():
    filelist, outdir, cwd = create_files_in_directory()
    parfiles = create_parfiles()
    plotter = fsl.PlotMotionParams()

    # make sure command gets called
    yield assert_equal, plotter.cmd, 'fsl_tsplot'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, plotter.run

    # .inputs based parameters setting
    plotter.inputs.in_file = parfiles[0]
    plotter.inputs.in_source = 'fsl'
    plotter.inputs.plot_type = 'rotations'
    plotter.inputs.out_file = 'foo.png'
    yield assert_equal, plotter.cmdline, \
        ('fsl_tsplot -i %s -o foo.png -t \'MCFLIRT estimated rotations (radians)\' '
         '--start=1 --finish=3 -a x,y,z' % parfiles[0])

    # .run based parameter setting
    plotter2 = fsl.PlotMotionParams(
        in_file=parfiles[1], in_source='spm', plot_type='translations',
        out_file='bar.png')
    yield assert_equal, plotter2.cmdline, \
        ('fsl_tsplot -i %s -o bar.png -t \'Realign estimated translations (mm)\' '
         '--start=1 --finish=3 -a x,y,z' % parfiles[1])

    clean_directory(outdir, cwd)


@skipif(no_fsl)
def test_convertxfm():
    filelist, outdir, cwd = create_files_in_directory()
    cvt = fsl.ConvertXFM()

    # make sure command gets called
    yield assert_equal, cvt.cmd, "convert_xfm"

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, cvt.run

    # .inputs based parameters setting
    cvt.inputs.in_file = filelist[0]
    cvt.inputs.invert_xfm = True
    cvt.inputs.out_file = "foo.mat"
    yield assert_equal, cvt.cmdline, 'convert_xfm -omat foo.mat -inverse %s' % filelist[0]

    # constructor based parameter setting
    cvt2 = fsl.ConvertXFM(
        in_file=filelist[0], in_file2=filelist[1], concat_xfm=True,
        out_file="bar.mat")
    yield assert_equal, cvt2.cmdline, \
        "convert_xfm -omat bar.mat -concat %s %s" % (filelist[1], filelist[0])

    clean_directory(outdir, cwd)


@skipif(no_fsl)
def test_swapdims():
    files, testdir, origdir = create_files_in_directory()
    swap = fsl.SwapDimensions()

    # Test the underlying command
    yield assert_equal, swap.cmd, "fslswapdim"

    # Test mandatory args
    args = [dict(in_file=files[0]), dict(new_dims=("x", "y", "z"))]
    for arg in args:
        wontrun = fsl.SwapDimensions(**arg)
        yield assert_raises, ValueError, wontrun.run

    # Now test a basic command line
    swap.inputs.in_file = files[0]
    swap.inputs.new_dims = ("x", "y", "z")
    yield assert_equal, swap.cmdline, "fslswapdim a.nii x y z %s" % os.path.realpath(os.path.join(testdir, "a_newdims.nii"))

    # Test that we can set an output name
    swap.inputs.out_file = "b.nii"
    yield assert_equal, swap.cmdline, "fslswapdim a.nii x y z b.nii"

    # Clean up
    clean_directory(testdir, origdir)
