# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from ...niftyreg import get_custom_path

from ..dwi import FitDwi, DwiTool
from ...niftyreg.tests.test_regutils import no_nifty_tool


@pytest.mark.skipif(
    no_nifty_tool(cmd='fit_dwi'), reason="niftyfit is not installed")
def test_fit_dwi():
    """ Testing FitDwi interface."""
    # Create a node object
    fit_dwi = FitDwi()

    # Check if the command is properly defined
    cmd = get_custom_path('fit_dwi', env_dir='NIFTYFITDIR')
    assert fit_dwi.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        fit_dwi.run()

    # Assign some input data
    in_file = example_data('dwi.nii.gz')
    bval_file = example_data('bvals')
    bvec_file = example_data('bvecs')
    fit_dwi.inputs.source_file = in_file
    fit_dwi.inputs.bval_file = bval_file
    fit_dwi.inputs.bvec_file = bvec_file
    fit_dwi.inputs.dti_flag = True

    cmd_tmp = '{cmd} -source {in_file} -bval {bval} -bvec {bvec} -dti \
-error {error} -famap {fa} -mcmap {mc} -mcout {mcout} -mdmap {md} -nodiff \
{nodiff} -res {res} -rgbmap {rgb} -syn {syn} -tenmap2 {ten2}  -v1map {v1}'

    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        error='dwi_error.nii.gz',
        fa='dwi_famap.nii.gz',
        mc='dwi_mcmap.nii.gz',
        md='dwi_mdmap.nii.gz',
        nodiff='dwi_no_diff.nii.gz',
        res='dwi_resmap.nii.gz',
        rgb='dwi_rgbmap.nii.gz',
        syn='dwi_syn.nii.gz',
        ten2='dwi_tenmap2.nii.gz',
        v1='dwi_v1map.nii.gz',
        mcout='dwi_mcout.txt')

    assert fit_dwi.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd='dwi_tool'), reason="niftyfit is not installed")
def test_dwi_tool():
    """ Testing DwiTool interface."""
    # Create a node object
    dwi_tool = DwiTool()

    # Check if the command is properly defined
    cmd = get_custom_path('dwi_tool', env_dir='NIFTYFITDIR')
    assert dwi_tool.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        dwi_tool.run()

    # Assign some input data
    in_file = example_data('dwi.nii.gz')
    bval_file = example_data('bvals')
    bvec_file = example_data('bvecs')
    b0_file = example_data('b0.nii')
    mask_file = example_data('mask.nii.gz')
    dwi_tool.inputs.source_file = in_file
    dwi_tool.inputs.mask_file = mask_file
    dwi_tool.inputs.bval_file = bval_file
    dwi_tool.inputs.bvec_file = bvec_file
    dwi_tool.inputs.b0_file = b0_file
    dwi_tool.inputs.dti_flag = True

    cmd_tmp = '{cmd} -source {in_file} -bval {bval} -bvec {bvec} -b0 {b0} \
-mask {mask} -dti -famap {fa} -logdti2 {log} -mcmap {mc} -mdmap {md} \
-rgbmap {rgb} -syn {syn} -v1map {v1}'

    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        b0=b0_file,
        mask=mask_file,
        fa='dwi_famap.nii.gz',
        log='dwi_logdti2.nii.gz',
        mc='dwi_mcmap.nii.gz',
        md='dwi_mdmap.nii.gz',
        rgb='dwi_rgbmap.nii.gz',
        syn='dwi_syn.nii.gz',
        v1='dwi_v1map.nii.gz')

    assert dwi_tool.cmdline == expected_cmd
