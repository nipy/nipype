# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nipype.interfaces.fsl.dti as fsl
from nipype.interfaces.fsl import Info, no_fsl
from nipype.interfaces.base import Undefined

import pytest
from nipype.testing.fixtures import create_files_in_directory


# test dtifit
@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_dtifit2(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    dti = fsl.DTIFit()
    # make sure command gets called
    assert dti.cmd == "dtifit"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        dti.run()

    # .inputs based parameters setting
    dti.inputs.dwi = filelist[0]
    dti.inputs.base_name = "foo.dti.nii"
    dti.inputs.mask = filelist[1]
    dti.inputs.bvecs = filelist[0]
    dti.inputs.bvals = filelist[1]
    dti.inputs.min_z = 10
    dti.inputs.max_z = 50

    assert (
        dti.cmdline
        == "dtifit -k %s -o foo.dti.nii -m %s -r %s -b %s -Z 50 -z 10"
        % (filelist[0], filelist[1], filelist[0], filelist[1])
    )


@pytest.mark.xfail(reason="These tests are skipped until we clean up some of this code")
def test_randomise2():

    rand = fsl.Randomise()

    # make sure command gets called
    assert rand.cmd == "randomise"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        rand.run()

    # .inputs based parameters setting
    rand.inputs.input_4D = "infile.nii"
    rand.inputs.output_rootname = "outfile"
    rand.inputs.design_matrix = "design.mat"
    rand.inputs.t_contrast = "infile.con"

    actualCmdline = sorted(rand.cmdline.split())
    cmd = "randomise -i infile.nii -o outfile -d design.mat -t infile.con"
    desiredCmdline = sorted(cmd.split())
    assert actualCmdline == desiredCmdline

    # .run based parameter setting
    rand2 = fsl.Randomise(
        input_4D="infile2",
        output_rootname="outfile2",
        f_contrast="infile.f",
        one_sample_gmean=True,
        int_seed=4,
    )

    actualCmdline = sorted(rand2.cmdline.split())
    cmd = "randomise -i infile2 -o outfile2 -1 -f infile.f --seed=4"
    desiredCmdline = sorted(cmd.split())
    assert actualCmdline == desiredCmdline

    rand3 = fsl.Randomise()
    results = rand3.run(input_4D="infile3", output_rootname="outfile3")
    assert results.runtime.cmdline == "randomise -i infile3 -o outfile3"

    # test arguments for opt_map
    opt_map = {
        "demean_data": ("-D", True),
        "one_sample_gmean": ("-1", True),
        "mask_image": ("-m inp_mask", "inp_mask"),
        "design_matrix": ("-d design.mat", "design.mat"),
        "t_contrast": ("-t input.con", "input.con"),
        "f_contrast": ("-f input.fts", "input.fts"),
        "xchange_block_labels": ("-e design.grp", "design.grp"),
        "print_unique_perm": ("-q", True),
        "print_info_parallelMode": ("-Q", True),
        "num_permutations": ("-n 10", 10),
        "vox_pvalus": ("-x", True),
        "fstats_only": ("--fonly", True),
        "thresh_free_cluster": ("-T", True),
        "thresh_free_cluster_2Dopt": ("--T2", True),
        "cluster_thresholding": ("-c 0.20", 0.20),
        "cluster_mass_thresholding": ("-C 0.40", 0.40),
        "fcluster_thresholding": ("-F 0.10", 0.10),
        "fcluster_mass_thresholding": ("-S 0.30", 0.30),
        "variance_smoothing": ("-v 0.20", 0.20),
        "diagnostics_off": ("--quiet", True),
        "output_raw": ("-R", True),
        "output_perm_vect": ("-P", True),
        "int_seed": ("--seed=20", 20),
        "TFCE_height_param": ("--tfce_H=0.11", 0.11),
        "TFCE_extent_param": ("--tfce_E=0.50", 0.50),
        "TFCE_connectivity": ("--tfce_C=0.30", 0.30),
        "list_num_voxel_EVs_pos": ("--vxl=1,2,3,4", "1,2,3,4"),
        "list_img_voxel_EVs": ("--vxf=6,7,8,9,3", "6,7,8,9,3"),
    }

    for name, settings in list(opt_map.items()):
        rand4 = fsl.Randomise(
            input_4D="infile", output_rootname="root", **{name: settings[1]}
        )
        assert rand4.cmdline == rand4.cmd + " -i infile -o root " + settings[0]


@pytest.mark.xfail(reason="These tests are skipped until we clean up some of this code")
def test_Randomise_parallel():
    rand = fsl.Randomise_parallel()

    # make sure command gets called
    assert rand.cmd == "randomise_parallel"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        rand.run()

    # .inputs based parameters setting
    rand.inputs.input_4D = "infile.nii"
    rand.inputs.output_rootname = "outfile"
    rand.inputs.design_matrix = "design.mat"
    rand.inputs.t_contrast = "infile.con"

    actualCmdline = sorted(rand.cmdline.split())
    cmd = "randomise_parallel -i infile.nii -o outfile -d design.mat -t " "infile.con"
    desiredCmdline = sorted(cmd.split())
    assert actualCmdline == desiredCmdline

    # .run based parameter setting
    rand2 = fsl.Randomise_parallel(
        input_4D="infile2",
        output_rootname="outfile2",
        f_contrast="infile.f",
        one_sample_gmean=True,
        int_seed=4,
    )

    actualCmdline = sorted(rand2.cmdline.split())
    cmd = "randomise_parallel -i infile2 -o outfile2 -1 -f infile.f --seed=4"
    desiredCmdline = sorted(cmd.split())
    assert actualCmdline == desiredCmdline

    rand3 = fsl.Randomise_parallel()
    results = rand3.run(input_4D="infile3", output_rootname="outfile3")
    assert results.runtime.cmdline == "randomise_parallel -i infile3 -o outfile3"

    # test arguments for opt_map
    opt_map = {
        "demean_data": ("-D", True),
        "one_sample_gmean": ("-1", True),
        "mask_image": ("-m inp_mask", "inp_mask"),
        "design_matrix": ("-d design.mat", "design.mat"),
        "t_contrast": ("-t input.con", "input.con"),
        "f_contrast": ("-f input.fts", "input.fts"),
        "xchange_block_labels": ("-e design.grp", "design.grp"),
        "print_unique_perm": ("-q", True),
        "print_info_parallelMode": ("-Q", True),
        "num_permutations": ("-n 10", 10),
        "vox_pvalus": ("-x", True),
        "fstats_only": ("--fonly", True),
        "thresh_free_cluster": ("-T", True),
        "thresh_free_cluster_2Dopt": ("--T2", True),
        "cluster_thresholding": ("-c 0.20", 0.20),
        "cluster_mass_thresholding": ("-C 0.40", 0.40),
        "fcluster_thresholding": ("-F 0.10", 0.10),
        "fcluster_mass_thresholding": ("-S 0.30", 0.30),
        "variance_smoothing": ("-v 0.20", 0.20),
        "diagnostics_off": ("--quiet", True),
        "output_raw": ("-R", True),
        "output_perm_vect": ("-P", True),
        "int_seed": ("--seed=20", 20),
        "TFCE_height_param": ("--tfce_H=0.11", 0.11),
        "TFCE_extent_param": ("--tfce_E=0.50", 0.50),
        "TFCE_connectivity": ("--tfce_C=0.30", 0.30),
        "list_num_voxel_EVs_pos": ("--vxl=" + repr([1, 2, 3, 4]), repr([1, 2, 3, 4])),
        "list_img_voxel_EVs": ("--vxf=" + repr([6, 7, 8, 9, 3]), repr([6, 7, 8, 9, 3])),
    }

    for name, settings in list(opt_map.items()):
        rand4 = fsl.Randomise_parallel(
            input_4D="infile", output_rootname="root", **{name: settings[1]}
        )
        assert rand4.cmdline == rand4.cmd + " -i infile -o root " + settings[0]


# test proj_thresh
@pytest.mark.xfail(reason="These tests are skipped until we clean up some of this code")
def test_Proj_thresh():
    proj = fsl.ProjThresh()

    # make sure command gets called
    assert proj.cmd == "proj_thresh"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        proj.run()

    # .inputs based parameters setting
    proj.inputs.volumes = ["vol1", "vol2", "vol3"]
    proj.inputs.threshold = 3
    assert proj.cmdline == "proj_thresh vol1 vol2 vol3 3"

    proj2 = fsl.ProjThresh(threshold=10, volumes=["vola", "volb"])
    assert proj2.cmdline == "proj_thresh vola volb 10"

    # .run based parameters setting
    proj3 = fsl.ProjThresh()
    results = proj3.run(volumes=["inp1", "inp3", "inp2"], threshold=2)
    assert results.runtime.cmdline == "proj_thresh inp1 inp3 inp2 2"
    assert results.runtime.returncode != 0
    assert isinstance(results.interface.inputs.volumes, list)
    assert results.interface.inputs.threshold == 2

    # test arguments for opt_map
    # Proj_thresh doesn't have an opt_map{}


# test vec_reg
@pytest.mark.xfail(reason="These tests are skipped until we clean up some of this code")
def test_Vec_reg():

    vrg = fsl.VecReg()

    # make sure command gets called
    assert vrg.cmd == "vecreg"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        vrg.run()

    # .inputs based parameters setting
    vrg.inputs.infile = "infile"
    vrg.inputs.outfile = "outfile"
    vrg.inputs.refVolName = "MNI152"
    vrg.inputs.affineTmat = "tmat.mat"
    assert vrg.cmdline == "vecreg -i infile -o outfile -r MNI152 -t tmat.mat"

    # .run based parameter setting
    vrg2 = fsl.VecReg(
        infile="infile2",
        outfile="outfile2",
        refVolName="MNI152",
        affineTmat="tmat2.mat",
        brainMask="nodif_brain_mask",
    )

    actualCmdline = sorted(vrg2.cmdline.split())
    cmd = "vecreg -i infile2 -o outfile2 -r MNI152 -t tmat2.mat -m nodif_brain_mask"
    desiredCmdline = sorted(cmd.split())
    assert actualCmdline == desiredCmdline

    vrg3 = fsl.VecReg()
    results = vrg3.run(
        infile="infile3",
        outfile="outfile3",
        refVolName="MNI152",
        affineTmat="tmat3.mat",
    )

    assert (
        results.runtime.cmdline
        == "vecreg -i infile3 -o outfile3 -r MNI152 -t tmat3.mat"
    )
    assert results.runtime.returncode != 0
    assert results.interface.inputs.infile == "infile3"
    assert results.interface.inputs.outfile == "outfile3"
    assert results.interface.inputs.refVolName == "MNI152"
    assert results.interface.inputs.affineTmat == "tmat3.mat"

    # test arguments for opt_map
    opt_map = {
        "verbose": ("-v", True),
        "helpDoc": ("-h", True),
        "tensor": ("--tensor", True),
        "affineTmat": ("-t Tmat", "Tmat"),
        "warpFile": ("-w wrpFile", "wrpFile"),
        "interpolation": ("--interp=sinc", "sinc"),
        "brainMask": ("-m mask", "mask"),
    }

    for name, settings in list(opt_map.items()):
        vrg4 = fsl.VecReg(
            infile="infile",
            outfile="outfile",
            refVolName="MNI152",
            **{name: settings[1]}
        )
        assert (
            vrg4.cmdline == vrg4.cmd + " -i infile -o outfile -r MNI152 " + settings[0]
        )


# test find_the_biggest
@pytest.mark.xfail(reason="These tests are skipped until we clean up some of this code")
def test_Find_the_biggest():
    fbg = fsl.FindTheBiggest()

    # make sure command gets called
    assert fbg.cmd == "find_the_biggest"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        fbg.run()

    # .inputs based parameters setting
    fbg.inputs.infiles = "seed*"
    fbg.inputs.outfile = "fbgfile"
    assert fbg.cmdline == "find_the_biggest seed* fbgfile"

    fbg2 = fsl.FindTheBiggest(infiles="seed2*", outfile="fbgfile2")
    assert fbg2.cmdline == "find_the_biggest seed2* fbgfile2"

    # .run based parameters setting
    fbg3 = fsl.FindTheBiggest()
    results = fbg3.run(infiles="seed3", outfile="out3")
    assert results.runtime.cmdline == "find_the_biggest seed3 out3"

    # test arguments for opt_map
    # Find_the_biggest doesn't have an opt_map{}


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_tbss_skeleton(create_files_in_directory):
    skeletor = fsl.TractSkeleton()

    files, newdir = create_files_in_directory

    # Test the underlying command
    assert skeletor.cmd == "tbss_skeleton"

    # It shouldn't run yet
    with pytest.raises(ValueError):
        skeletor.run()

    # Test the most basic way to use it
    skeletor.inputs.in_file = files[0]

    # First by implicit argument
    skeletor.inputs.skeleton_file = True
    assert skeletor.cmdline == "tbss_skeleton -i a.nii -o %s" % os.path.join(
        newdir, "a_skeleton.nii"
    )

    # Now with a specific name
    skeletor.inputs.skeleton_file = "old_boney.nii"
    assert skeletor.cmdline == "tbss_skeleton -i a.nii -o old_boney.nii"

    # Now test the more complicated usage
    bones = fsl.TractSkeleton(in_file="a.nii", project_data=True)

    # This should error
    with pytest.raises(ValueError):
        bones.run()

    # But we can set what we need
    bones.inputs.threshold = 0.2
    bones.inputs.distance_map = "b.nii"
    bones.inputs.data_file = "b.nii"  # Even though that's silly

    # Now we get a command line
    assert bones.cmdline == "tbss_skeleton -i a.nii -p 0.200 b.nii %s b.nii %s" % (
        Info.standard_image("LowerCingulum_1mm.nii.gz"),
        os.path.join(newdir, "b_skeletonised.nii"),
    )

    # Can we specify a mask?
    bones.inputs.use_cingulum_mask = Undefined
    bones.inputs.search_mask_file = "a.nii"
    assert (
        bones.cmdline
        == "tbss_skeleton -i a.nii -p 0.200 b.nii a.nii b.nii %s"
        % os.path.join(newdir, "b_skeletonised.nii")
    )


@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_distancemap(create_files_in_directory):
    mapper = fsl.DistanceMap()

    files, newdir = create_files_in_directory

    # Test the underlying command
    assert mapper.cmd == "distancemap"

    # It shouldn't run yet
    with pytest.raises(ValueError):
        mapper.run()

    # But if we do this...
    mapper.inputs.in_file = "a.nii"

    # It should
    assert mapper.cmdline == "distancemap --out=%s --in=a.nii" % os.path.join(
        newdir, "a_dstmap.nii"
    )

    # And we should be able to write out a maxima map
    mapper.inputs.local_max_file = True
    assert mapper.cmdline == "distancemap --out=%s --in=a.nii --localmax=%s" % (
        os.path.join(newdir, "a_dstmap.nii"),
        os.path.join(newdir, "a_lclmax.nii"),
    )

    # And call it whatever we want
    mapper.inputs.local_max_file = "max.nii"
    assert (
        mapper.cmdline
        == "distancemap --out=%s --in=a.nii --localmax=max.nii"
        % os.path.join(newdir, "a_dstmap.nii")
    )
