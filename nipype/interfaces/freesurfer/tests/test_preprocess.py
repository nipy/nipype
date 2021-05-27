# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
from nipype.testing.fixtures import create_files_in_directory

from nipype.interfaces import freesurfer
from nipype.interfaces.freesurfer import Info
from nipype import LooseVersion


@pytest.mark.skipif(freesurfer.no_freesurfer(), reason="freesurfer is not installed")
def test_robustregister(create_files_in_directory):
    filelist, outdir = create_files_in_directory

    reg = freesurfer.RobustRegister()
    cwd = os.getcwd()

    # make sure command gets called
    assert reg.cmd == "mri_robust_register"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        reg.run()

    # .inputs based parameters setting
    reg.inputs.source_file = filelist[0]
    reg.inputs.target_file = filelist[1]
    reg.inputs.auto_sens = True
    assert reg.cmdline == (
        "mri_robust_register --satit --lta "
        "%s/%s_robustreg.lta --mov %s --dst %s"
        % (cwd, filelist[0][:-4], filelist[0], filelist[1])
    )

    # constructor based parameter setting
    reg2 = freesurfer.RobustRegister(
        source_file=filelist[0],
        target_file=filelist[1],
        outlier_sens=3.0,
        out_reg_file="foo.lta",
        half_targ=True,
    )
    assert reg2.cmdline == (
        "mri_robust_register --halfdst %s_halfway.nii --lta foo.lta "
        "--sat 3.0000 --mov %s --dst %s"
        % (os.path.join(outdir, filelist[1][:-4]), filelist[0], filelist[1])
    )


@pytest.mark.skipif(freesurfer.no_freesurfer(), reason="freesurfer is not installed")
def test_fitmsparams(create_files_in_directory):
    filelist, outdir = create_files_in_directory

    fit = freesurfer.FitMSParams()

    # make sure command gets called
    assert fit.cmd == "mri_ms_fitparms"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        fit.run()

    # .inputs based parameters setting
    fit.inputs.in_files = filelist
    fit.inputs.out_dir = outdir
    assert fit.cmdline == "mri_ms_fitparms  %s %s %s" % (
        filelist[0],
        filelist[1],
        outdir,
    )

    # constructor based parameter setting
    fit2 = freesurfer.FitMSParams(
        in_files=filelist, te_list=[1.5, 3.5], flip_list=[20, 30], out_dir=outdir
    )
    assert fit2.cmdline == (
        "mri_ms_fitparms  -te %.3f -fa %.1f %s -te %.3f -fa %.1f %s %s"
        % (1.500, 20.0, filelist[0], 3.500, 30.0, filelist[1], outdir)
    )


@pytest.mark.skipif(freesurfer.no_freesurfer(), reason="freesurfer is not installed")
def test_synthesizeflash(create_files_in_directory):
    filelist, outdir = create_files_in_directory

    syn = freesurfer.SynthesizeFLASH()

    # make sure command gets called
    assert syn.cmd == "mri_synthesize"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        syn.run()

    # .inputs based parameters setting
    syn.inputs.t1_image = filelist[0]
    syn.inputs.pd_image = filelist[1]
    syn.inputs.flip_angle = 30
    syn.inputs.te = 4.5
    syn.inputs.tr = 20

    assert syn.cmdline == (
        "mri_synthesize 20.00 30.00 4.500 %s %s %s"
        % (filelist[0], filelist[1], os.path.join(outdir, "synth-flash_30.mgz"))
    )

    # constructor based parameters setting
    syn2 = freesurfer.SynthesizeFLASH(
        t1_image=filelist[0], pd_image=filelist[1], flip_angle=20, te=5, tr=25
    )
    assert syn2.cmdline == (
        "mri_synthesize 25.00 20.00 5.000 %s %s %s"
        % (filelist[0], filelist[1], os.path.join(outdir, "synth-flash_20.mgz"))
    )


@pytest.mark.skipif(freesurfer.no_freesurfer(), reason="freesurfer is not installed")
def test_mandatory_outvol(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    mni = freesurfer.MNIBiasCorrection()

    # make sure command gets called
    assert mni.cmd == "mri_nu_correct.mni"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        mni.cmdline

    # test with minimal args
    mni.inputs.in_file = filelist[0]
    base, ext = os.path.splitext(os.path.basename(filelist[0]))
    if ext == ".gz":
        base, ext2 = os.path.splitext(base)
        ext = ext2 + ext

    assert mni.cmdline == (
        "mri_nu_correct.mni --i %s --n 4 --o %s_output%s" % (filelist[0], base, ext)
    )

    # test with custom outfile
    mni.inputs.out_file = "new_corrected_file.mgz"
    assert mni.cmdline == (
        "mri_nu_correct.mni --i %s --n 4 --o new_corrected_file.mgz" % (filelist[0])
    )

    # constructor based tests
    mni2 = freesurfer.MNIBiasCorrection(
        in_file=filelist[0], out_file="bias_corrected_output", iterations=2
    )
    assert mni2.cmdline == (
        "mri_nu_correct.mni --i %s --n 2 --o bias_corrected_output" % filelist[0]
    )


@pytest.mark.skipif(freesurfer.no_freesurfer(), reason="freesurfer is not installed")
def test_bbregister(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    bbr = freesurfer.BBRegister()

    # make sure command gets called
    assert bbr.cmd == "bbregister"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        bbr.cmdline

    bbr.inputs.subject_id = "fsaverage"
    bbr.inputs.source_file = filelist[0]
    bbr.inputs.contrast_type = "t2"

    # Check that 'init' is mandatory in FS < 6, but not in 6+
    if Info.looseversion() < LooseVersion("6.0.0"):
        with pytest.raises(ValueError):
            bbr.cmdline
    else:
        bbr.cmdline

    bbr.inputs.init = "fsl"

    base, ext = os.path.splitext(os.path.basename(filelist[0]))
    if ext == ".gz":
        base, _ = os.path.splitext(base)

    assert bbr.cmdline == (
        "bbregister --t2 --init-fsl "
        "--reg {base}_bbreg_fsaverage.dat "
        "--mov {full} --s fsaverage".format(full=filelist[0], base=base)
    )


def test_FSVersion():
    """Check that FSVersion is a string that can be compared with LooseVersion"""
    assert isinstance(freesurfer.preprocess.FSVersion, str)
    assert LooseVersion(freesurfer.preprocess.FSVersion) >= LooseVersion("0")
