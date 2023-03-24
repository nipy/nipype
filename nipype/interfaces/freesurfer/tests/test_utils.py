# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import os.path as op
import pytest
from nipype.testing.fixtures import (
    create_files_in_directory_plus_dummy_file,
    create_surf_file_in_directory,
)

from nipype.pipeline import engine as pe
from nipype.interfaces import freesurfer as fs
from nipype.interfaces.base import TraitError
from nipype.interfaces.io import FreeSurferSource


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_sample2surf(create_files_in_directory_plus_dummy_file):
    s2s = fs.SampleToSurface()
    # Test underlying command
    assert s2s.cmd == "mri_vol2surf"

    # Test mandatory args exception
    with pytest.raises(ValueError):
        s2s.run()

    # Create testing files
    files, cwd = create_files_in_directory_plus_dummy_file

    # Test input settings
    s2s.inputs.source_file = files[0]
    s2s.inputs.reference_file = files[1]
    s2s.inputs.hemi = "lh"
    s2s.inputs.reg_file = files[2]
    s2s.inputs.sampling_range = 0.5
    s2s.inputs.sampling_units = "frac"
    s2s.inputs.sampling_method = "point"

    # Test a basic command line
    assert s2s.cmdline == (
        "mri_vol2surf "
        "--hemi lh --o %s --ref %s --reg reg.dat --projfrac 0.500 --mov %s"
        % (os.path.join(cwd, "lh.a.mgz"), files[1], files[0])
    )

    # Test identity
    s2sish = fs.SampleToSurface(
        source_file=files[1], reference_file=files[0], hemi="rh"
    )
    assert s2s != s2sish

    # Test hits file name creation
    s2s.inputs.hits_file = True
    assert s2s._get_outfilename("hits_file") == os.path.join(cwd, "lh.a_hits.mgz")

    # Test that a 2-tuple range raises an error
    def set_illegal_range():
        s2s.inputs.sampling_range = (0.2, 0.5)

    with pytest.raises(TraitError):
        set_illegal_range()


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_surfsmooth(create_surf_file_in_directory):
    smooth = fs.SurfaceSmooth()

    # Test underlying command
    assert smooth.cmd == "mri_surf2surf"

    # Test mandatory args exception
    with pytest.raises(ValueError):
        smooth.run()

    # Create testing files
    surf, cwd = create_surf_file_in_directory

    # Test input settings
    smooth.inputs.in_file = surf
    smooth.inputs.subject_id = "fsaverage"
    fwhm = 5
    smooth.inputs.fwhm = fwhm
    smooth.inputs.hemi = "lh"

    # Test the command line
    assert smooth.cmdline == (
        "mri_surf2surf --cortex --fwhm 5.0000 --hemi lh --sval %s --tval %s/lh.a_smooth%d.nii --s fsaverage"
        % (surf, cwd, fwhm)
    )

    # Test identity
    shmooth = fs.SurfaceSmooth(
        subject_id="fsaverage",
        fwhm=6,
        in_file=surf,
        hemi="lh",
        out_file="lh.a_smooth.nii",
    )
    assert smooth != shmooth


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_surfxfm(create_surf_file_in_directory):
    xfm = fs.SurfaceTransform()

    # Test underlying command
    assert xfm.cmd == "mri_surf2surf"

    # Test mandatory args exception
    with pytest.raises(ValueError):
        xfm.run()

    # Create testing files
    surf, cwd = create_surf_file_in_directory

    # Test input settings
    xfm.inputs.source_file = surf
    xfm.inputs.source_subject = "my_subject"
    xfm.inputs.target_subject = "fsaverage"
    xfm.inputs.hemi = "lh"

    # Test the command line
    assert xfm.cmdline == (
        "mri_surf2surf --hemi lh --tval %s/lh.a.fsaverage.nii --sval %s --srcsubject my_subject --trgsubject fsaverage"
        % (cwd, surf)
    )

    # Test identity
    xfmish = fs.SurfaceTransform(
        source_subject="fsaverage",
        target_subject="my_subject",
        source_file=surf,
        hemi="lh",
    )
    assert xfm != xfmish


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_surfshots(create_files_in_directory_plus_dummy_file):
    fotos = fs.SurfaceSnapshots()

    # Test underlying command
    assert fotos.cmd == "tksurfer"

    # Test mandatory args exception
    with pytest.raises(ValueError):
        fotos.run()

    # Create testing files
    files, cwd = create_files_in_directory_plus_dummy_file

    # Test input settings
    fotos.inputs.subject_id = "fsaverage"
    fotos.inputs.hemi = "lh"
    fotos.inputs.surface = "pial"

    # Test a basic command line
    assert fotos.cmdline == "tksurfer fsaverage lh pial -tcl snapshots.tcl"

    # Test identity
    schmotos = fs.SurfaceSnapshots(subject_id="mysubject", hemi="rh", surface="white")
    assert fotos != schmotos

    # Test that the tcl script gets written
    fotos._write_tcl_script()
    assert os.path.exists("snapshots.tcl")

    # Test that we can use a different tcl script
    foo = open("other.tcl", "w").close()
    fotos.inputs.tcl_script = "other.tcl"
    assert fotos.cmdline == "tksurfer fsaverage lh pial -tcl other.tcl"

    # Test that the interface crashes politely if graphics aren't enabled
    try:
        hold_display = os.environ["DISPLAY"]
        del os.environ["DISPLAY"]
        with pytest.raises(RuntimeError):
            fotos.run()
        os.environ["DISPLAY"] = hold_display
    except KeyError:
        pass


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_mrisexpand(tmpdir):
    fssrc = FreeSurferSource(
        subjects_dir=fs.Info.subjectsdir(), subject_id="fsaverage", hemi="lh"
    )

    fsavginfo = fssrc.run().outputs.get()

    # dt=60 to ensure very short runtime
    expand_if = fs.MRIsExpand(
        in_file=fsavginfo["smoothwm"], out_name="expandtmp", distance=1, dt=60
    )

    expand_nd = pe.Node(
        fs.MRIsExpand(
            in_file=fsavginfo["smoothwm"], out_name="expandtmp", distance=1, dt=60
        ),
        name="expand_node",
    )

    # Interfaces should have same command line at instantiation
    orig_cmdline = "mris_expand -T 60 {} 1 expandtmp".format(fsavginfo["smoothwm"])
    assert expand_if.cmdline == orig_cmdline
    assert expand_nd.interface.cmdline == orig_cmdline

    # Run Node interface
    nd_res = expand_nd.run()

    # Commandlines differ
    node_cmdline = (
        "mris_expand -T 60 -pial {cwd}/lh.pial {cwd}/lh.smoothwm "
        "1 expandtmp".format(cwd=nd_res.runtime.cwd)
    )
    assert nd_res.runtime.cmdline == node_cmdline

    # Check output
    if_out_file = expand_if._list_outputs()["out_file"]
    nd_out_file = nd_res.outputs.get()["out_file"]
    # Same filename
    assert op.basename(if_out_file) == op.basename(nd_out_file)
    # Interface places output in source directory
    assert op.dirname(if_out_file) == op.dirname(fsavginfo["smoothwm"])
    # Node places output in working directory
    assert op.dirname(nd_out_file) == nd_res.runtime.cwd


@pytest.mark.skipif(fs.no_freesurfer(), reason="freesurfer is not installed")
def test_eulernumber(tmpdir):
    # grab a surface from fsaverage
    fssrc = FreeSurferSource(
        subjects_dir=fs.Info.subjectsdir(), subject_id="fsaverage", hemi="lh"
    )
    pial = fssrc.run().outputs.pial
    assert isinstance(pial, str), "Problem when fetching surface file"

    eu = fs.EulerNumber()
    eu.inputs.in_file = pial
    res = eu.run()
    assert res.outputs.defects == 0
    assert res.outputs.euler == 2
