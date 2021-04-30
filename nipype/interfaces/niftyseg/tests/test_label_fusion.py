# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from ...niftyreg import get_custom_path
from ...niftyreg.tests.test_regutils import no_nifty_tool
from .. import LabelFusion, CalcTopNCC


@pytest.mark.skipif(
    no_nifty_tool(cmd="seg_LabFusion"), reason="niftyseg is not installed"
)
def test_seg_lab_fusion():
    """Test interfaces for seg_labfusion"""
    # Create a node object
    steps = LabelFusion()

    # Check if the command is properly defined
    cmd = get_custom_path("seg_LabFusion", env_dir="NIFTYSEGDIR")
    assert steps.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        steps.run()

    # Assign some input data
    in_file = example_data("im1.nii")
    file_to_seg = example_data("im2.nii")
    template_file = example_data("im3.nii")
    steps.inputs.in_file = in_file
    steps.inputs.kernel_size = 2.0
    steps.inputs.file_to_seg = file_to_seg
    steps.inputs.template_file = template_file
    steps.inputs.template_num = 2
    steps.inputs.classifier_type = "STEPS"

    cmd_tmp = "{cmd} -in {in_file} -STEPS 2.000000 2 {file_to_seg} \
{template_file} -out {out_file}"

    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        file_to_seg=file_to_seg,
        template_file=template_file,
        out_file="im1_steps.nii",
    )

    assert steps.cmdline == expected_cmd

    # Staple
    staple = LabelFusion(kernel_size=2.0, template_num=2, classifier_type="STAPLE")
    in_file = example_data("im1.nii")
    file_to_seg = example_data("im2.nii")
    template_file = example_data("im3.nii")
    staple.inputs.in_file = in_file
    staple.inputs.file_to_seg = file_to_seg
    staple.inputs.template_file = template_file

    cmd_tmp = "{cmd} -in {in_file} -STAPLE -ALL -out {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        file_to_seg=file_to_seg,
        template_file=template_file,
        out_file="im1_staple.nii",
    )

    assert staple.cmdline == expected_cmd

    # Assign some input data
    mv_node = LabelFusion(
        template_num=2, classifier_type="MV", sm_ranking="ROINCC", dilation_roi=2
    )
    in_file = example_data("im1.nii")
    file_to_seg = example_data("im2.nii")
    template_file = example_data("im3.nii")
    mv_node.inputs.in_file = in_file
    mv_node.inputs.file_to_seg = file_to_seg
    mv_node.inputs.template_file = template_file

    cmd_tmp = "{cmd} -in {in_file} -MV -ROINCC 2 2 {file_to_seg} \
{template_file} -out {out_file}"

    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        file_to_seg=file_to_seg,
        template_file=template_file,
        out_file="im1_mv.nii",
    )

    assert mv_node.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd="seg_CalcTopNCC"), reason="niftyseg is not installed"
)
def test_seg_calctopncc():
    """Test interfaces for seg_CalctoNCC"""
    # Create a node object
    calctopncc = CalcTopNCC()

    # Check if the command is properly defined
    cmd = get_custom_path("seg_CalcTopNCC", env_dir="NIFTYSEGDIR")
    assert calctopncc.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        calctopncc.run()

    # Assign some input data
    in_file = example_data("im1.nii")
    file1 = example_data("im2.nii")
    file2 = example_data("im3.nii")
    calctopncc.inputs.in_file = in_file
    calctopncc.inputs.num_templates = 2
    calctopncc.inputs.in_templates = [file1, file2]
    calctopncc.inputs.top_templates = 1

    cmd_tmp = "{cmd} -target {in_file} -templates 2 {file1} {file2} -n 1"
    expected_cmd = cmd_tmp.format(cmd=cmd, in_file=in_file, file1=file1, file2=file2)

    assert calctopncc.cmdline == expected_cmd
