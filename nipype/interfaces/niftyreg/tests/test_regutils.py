# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import pytest

from ....utils.filemanip import which
from ....testing import example_data
from .. import (
    get_custom_path,
    RegAverage,
    RegResample,
    RegJacobian,
    RegTools,
    RegMeasure,
    RegTransform,
)


def no_nifty_tool(cmd=None):
    return which(cmd) is None


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_resample"),
    reason="niftyreg is not installed. reg_resample not found.",
)
def test_reg_resample_res():
    """tests for reg_resample interface"""
    # Create a reg_resample object
    nr_resample = RegResample()

    # Check if the command is properly defined
    assert nr_resample.cmd == get_custom_path("reg_resample")

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_resample.run()

    # Resample res
    ref_file = example_data("im1.nii")
    flo_file = example_data("im2.nii")
    trans_file = example_data("warpfield.nii")
    nr_resample.inputs.ref_file = ref_file
    nr_resample.inputs.flo_file = flo_file
    nr_resample.inputs.trans_file = trans_file
    nr_resample.inputs.inter_val = "LIN"
    nr_resample.inputs.omp_core_val = 4

    cmd_tmp = "{cmd} -flo {flo} -inter 1 -omp 4 -ref {ref} -trans {trans} \
-res {res}"

    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_resample"),
        flo=flo_file,
        ref=ref_file,
        trans=trans_file,
        res="im2_res.nii.gz",
    )

    assert nr_resample.cmdline == expected_cmd

    # test_reg_resample_blank()
    nr_resample_2 = RegResample(type="blank", inter_val="LIN", omp_core_val=4)
    ref_file = example_data("im1.nii")
    flo_file = example_data("im2.nii")
    trans_file = example_data("warpfield.nii")
    nr_resample_2.inputs.ref_file = ref_file
    nr_resample_2.inputs.flo_file = flo_file
    nr_resample_2.inputs.trans_file = trans_file

    cmd_tmp = "{cmd} -flo {flo} -inter 1 -omp 4 -ref {ref} -trans {trans} \
-blank {blank}"

    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_resample"),
        flo=flo_file,
        ref=ref_file,
        trans=trans_file,
        blank="im2_blank.nii.gz",
    )

    assert nr_resample_2.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_jacobian"),
    reason="niftyreg is not installed. reg_jacobian not found.",
)
def test_reg_jacobian_jac():
    """Test interface for RegJacobian"""
    # Create a reg_jacobian object
    nr_jacobian = RegJacobian()

    # Check if the command is properly defined
    assert nr_jacobian.cmd == get_custom_path("reg_jacobian")

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_jacobian.run()

    # Test Reg Jacobian: jac
    ref_file = example_data("im1.nii")
    trans_file = example_data("warpfield.nii")
    nr_jacobian.inputs.ref_file = ref_file
    nr_jacobian.inputs.trans_file = trans_file
    nr_jacobian.inputs.omp_core_val = 4

    cmd_tmp = "{cmd} -omp 4 -ref {ref} -trans {trans} -jac {jac}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_jacobian"),
        ref=ref_file,
        trans=trans_file,
        jac="warpfield_jac.nii.gz",
    )

    assert nr_jacobian.cmdline == expected_cmd

    # Test Reg Jacobian: jac m
    nr_jacobian_2 = RegJacobian(type="jacM", omp_core_val=4)
    ref_file = example_data("im1.nii")
    trans_file = example_data("warpfield.nii")
    nr_jacobian_2.inputs.ref_file = ref_file
    nr_jacobian_2.inputs.trans_file = trans_file

    cmd_tmp = "{cmd} -omp 4 -ref {ref} -trans {trans} -jacM {jac}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_jacobian"),
        ref=ref_file,
        trans=trans_file,
        jac="warpfield_jacM.nii.gz",
    )

    assert nr_jacobian_2.cmdline == expected_cmd

    # Test Reg Jacobian: jac l
    nr_jacobian_3 = RegJacobian(type="jacL", omp_core_val=4)
    ref_file = example_data("im1.nii")
    trans_file = example_data("warpfield.nii")
    nr_jacobian_3.inputs.ref_file = ref_file
    nr_jacobian_3.inputs.trans_file = trans_file

    cmd_tmp = "{cmd} -omp 4 -ref {ref} -trans {trans} -jacL {jac}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_jacobian"),
        ref=ref_file,
        trans=trans_file,
        jac="warpfield_jacL.nii.gz",
    )

    assert nr_jacobian_3.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_tools"),
    reason="niftyreg is not installed. reg_tools not found.",
)
def test_reg_tools_mul():
    """tests for reg_tools interface"""
    # Create a reg_tools object
    nr_tools = RegTools()

    # Check if the command is properly defined
    assert nr_tools.cmd == get_custom_path("reg_tools")

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_tools.run()

    # Test reg_tools: mul
    in_file = example_data("im1.nii")
    nr_tools.inputs.in_file = in_file
    nr_tools.inputs.mul_val = 4
    nr_tools.inputs.omp_core_val = 4

    cmd_tmp = "{cmd} -in {in_file} -mul 4.0 -omp 4 -out {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_tools"), in_file=in_file, out_file="im1_tools.nii.gz"
    )

    assert nr_tools.cmdline == expected_cmd

    # Test reg_tools: iso
    nr_tools_2 = RegTools(iso_flag=True, omp_core_val=4)
    in_file = example_data("im1.nii")
    nr_tools_2.inputs.in_file = in_file

    cmd_tmp = "{cmd} -in {in_file} -iso -omp 4 -out {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_tools"), in_file=in_file, out_file="im1_tools.nii.gz"
    )

    assert nr_tools_2.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_average"),
    reason="niftyreg is not installed. reg_average not found.",
)
def test_reg_average():
    """tests for reg_average interface"""
    # Create a reg_average object
    nr_average = RegAverage()

    # Check if the command is properly defined
    assert nr_average.cmd == get_custom_path("reg_average")

    # Average niis
    one_file = example_data("im1.nii")
    two_file = example_data("im2.nii")
    three_file = example_data("im3.nii")
    nr_average.inputs.avg_files = [one_file, two_file, three_file]
    nr_average.inputs.omp_core_val = 1
    generated_cmd = nr_average.cmdline

    # Read the reg_average_cmd
    reg_average_cmd = os.path.join(os.getcwd(), "reg_average_cmd")
    with open(reg_average_cmd, "rb") as f_obj:
        argv = f_obj.read()
    os.remove(reg_average_cmd)

    expected_argv = "{} {} -avg {} {} {} -omp 1".format(
        get_custom_path("reg_average"),
        os.path.join(os.getcwd(), "avg_out.nii.gz"),
        one_file,
        two_file,
        three_file,
    )

    assert argv.decode("utf-8") == expected_argv

    # Test command line with text file
    expected_cmd = "{} --cmd_file {}".format(
        get_custom_path("reg_average"),
        reg_average_cmd,
    )

    assert generated_cmd == expected_cmd

    # Test Reg Average: average txt
    nr_average_2 = RegAverage()
    one_file = example_data("TransformParameters.0.txt")
    two_file = example_data("ants_Affine.txt")
    three_file = example_data("elastix.txt")
    nr_average_2.inputs.avg_files = [one_file, two_file, three_file]
    nr_average_2.inputs.omp_core_val = 1
    generated_cmd = nr_average_2.cmdline

    # Read the reg_average_cmd
    reg_average_cmd = os.path.join(os.getcwd(), "reg_average_cmd")
    with open(reg_average_cmd, "rb") as f_obj:
        argv = f_obj.read()
    os.remove(reg_average_cmd)

    expected_argv = "{} {} -avg {} {} {} -omp 1".format(
        get_custom_path("reg_average"),
        os.path.join(os.getcwd(), "avg_out.txt"),
        one_file,
        two_file,
        three_file,
    )

    assert argv.decode("utf-8") == expected_argv

    # Test Reg Average: average list
    nr_average_3 = RegAverage()
    one_file = example_data("TransformParameters.0.txt")
    two_file = example_data("ants_Affine.txt")
    three_file = example_data("elastix.txt")
    nr_average_3.inputs.avg_lts_files = [one_file, two_file, three_file]
    nr_average_3.inputs.omp_core_val = 1
    generated_cmd = nr_average_3.cmdline

    # Read the reg_average_cmd
    reg_average_cmd = os.path.join(os.getcwd(), "reg_average_cmd")
    with open(reg_average_cmd, "rb") as f_obj:
        argv = f_obj.read()
    os.remove(reg_average_cmd)

    expected_argv = "{} {} -avg_lts {} {} {} -omp 1".format(
        get_custom_path("reg_average"),
        os.path.join(os.getcwd(), "avg_out.txt"),
        one_file,
        two_file,
        three_file,
    )

    assert argv.decode("utf-8") == expected_argv

    # Test Reg Average: average ref
    nr_average_4 = RegAverage()
    ref_file = example_data("anatomical.nii")
    one_file = example_data("im1.nii")
    two_file = example_data("im2.nii")
    three_file = example_data("im3.nii")
    trans1_file = example_data("roi01.nii")
    trans2_file = example_data("roi02.nii")
    trans3_file = example_data("roi03.nii")
    nr_average_4.inputs.warp_files = [
        trans1_file,
        one_file,
        trans2_file,
        two_file,
        trans3_file,
        three_file,
    ]
    nr_average_4.inputs.avg_ref_file = ref_file
    nr_average_4.inputs.omp_core_val = 1
    generated_cmd = nr_average_4.cmdline

    # Read the reg_average_cmd
    reg_average_cmd = os.path.join(os.getcwd(), "reg_average_cmd")
    with open(reg_average_cmd, "rb") as f_obj:
        argv = f_obj.read()
    os.remove(reg_average_cmd)

    expected_argv = "{} {} -avg_tran {} -omp 1 {} {} {} {} {} {}".format(
        get_custom_path("reg_average"),
        os.path.join(os.getcwd(), "avg_out.nii.gz"),
        ref_file,
        trans1_file,
        one_file,
        trans2_file,
        two_file,
        trans3_file,
        three_file,
    )

    assert argv.decode("utf-8") == expected_argv

    # Test Reg Average: demean3
    nr_average_5 = RegAverage()
    ref_file = example_data("anatomical.nii")
    one_file = example_data("im1.nii")
    two_file = example_data("im2.nii")
    three_file = example_data("im3.nii")
    aff1_file = example_data("TransformParameters.0.txt")
    aff2_file = example_data("ants_Affine.txt")
    aff3_file = example_data("elastix.txt")
    trans1_file = example_data("roi01.nii")
    trans2_file = example_data("roi02.nii")
    trans3_file = example_data("roi03.nii")
    nr_average_5.inputs.warp_files = [
        aff1_file,
        trans1_file,
        one_file,
        aff2_file,
        trans2_file,
        two_file,
        aff3_file,
        trans3_file,
        three_file,
    ]
    nr_average_5.inputs.demean3_ref_file = ref_file
    nr_average_5.inputs.omp_core_val = 1
    generated_cmd = nr_average_5.cmdline

    # Read the reg_average_cmd
    reg_average_cmd = os.path.join(os.getcwd(), "reg_average_cmd")
    with open(reg_average_cmd, "rb") as f_obj:
        argv = f_obj.read()
    os.remove(reg_average_cmd)

    expected_argv = "{} {} -demean3 {} -omp 1 {} {} {} {} {} {} {} {} {}".format(
        get_custom_path("reg_average"),
        os.path.join(os.getcwd(), "avg_out.nii.gz"),
        ref_file,
        aff1_file,
        trans1_file,
        one_file,
        aff2_file,
        trans2_file,
        two_file,
        aff3_file,
        trans3_file,
        three_file,
    )

    assert argv.decode("utf-8") == expected_argv


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_transform"),
    reason="niftyreg is not installed. reg_transform not found.",
)
def test_reg_transform_def():
    """tests for reg_transform interface"""
    # Create a reg_transform object
    nr_transform = RegTransform()

    # Check if the command is properly defined
    assert nr_transform.cmd == get_custom_path("reg_transform")

    # Assign some input data
    trans_file = example_data("warpfield.nii")
    nr_transform.inputs.def_input = trans_file
    nr_transform.inputs.omp_core_val = 4

    cmd_tmp = "{cmd} -omp 4 -def {trans_file} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        trans_file=trans_file,
        out_file=os.path.join(os.getcwd(), "warpfield_trans.nii.gz"),
    )

    assert nr_transform.cmdline == expected_cmd

    # Test reg_transform: def ref
    nr_transform_2 = RegTransform(omp_core_val=4)
    ref_file = example_data("im1.nii")
    trans_file = example_data("warpfield.nii")
    nr_transform_2.inputs.ref1_file = ref_file
    nr_transform_2.inputs.def_input = trans_file

    cmd_tmp = "{cmd} -ref {ref_file} -omp 4 -def {trans_file} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        ref_file=ref_file,
        trans_file=trans_file,
        out_file=os.path.join(os.getcwd(), "warpfield_trans.nii.gz"),
    )

    assert nr_transform_2.cmdline == expected_cmd

    # Test reg_transform: comp nii
    nr_transform_3 = RegTransform(omp_core_val=4)
    ref_file = example_data("im1.nii")
    trans_file = example_data("warpfield.nii")
    trans2_file = example_data("anatomical.nii")
    nr_transform_3.inputs.ref1_file = ref_file
    nr_transform_3.inputs.comp_input2 = trans2_file
    nr_transform_3.inputs.comp_input = trans_file

    cmd_tmp = "{cmd} -ref {ref_file} -omp 4 -comp {trans1} {trans2} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        ref_file=ref_file,
        trans1=trans_file,
        trans2=trans2_file,
        out_file=os.path.join(os.getcwd(), "warpfield_trans.nii.gz"),
    )

    assert nr_transform_3.cmdline == expected_cmd

    # Test reg_transform: comp txt
    nr_transform_4 = RegTransform(omp_core_val=4)
    aff1_file = example_data("ants_Affine.txt")
    aff2_file = example_data("elastix.txt")
    nr_transform_4.inputs.comp_input2 = aff2_file
    nr_transform_4.inputs.comp_input = aff1_file

    cmd_tmp = "{cmd} -omp 4 -comp {aff1} {aff2} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        aff1=aff1_file,
        aff2=aff2_file,
        out_file=os.path.join(os.getcwd(), "ants_Affine_trans.txt"),
    )

    assert nr_transform_4.cmdline == expected_cmd

    # Test reg_transform: comp
    nr_transform_5 = RegTransform(omp_core_val=4)
    trans_file = example_data("warpfield.nii")
    aff_file = example_data("elastix.txt")
    nr_transform_5.inputs.comp_input2 = trans_file
    nr_transform_5.inputs.comp_input = aff_file

    cmd_tmp = "{cmd} -omp 4 -comp {aff} {trans} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        aff=aff_file,
        trans=trans_file,
        out_file=os.path.join(os.getcwd(), "elastix_trans.nii.gz"),
    )

    assert nr_transform_5.cmdline == expected_cmd

    # Test reg_transform: flirt
    nr_transform_6 = RegTransform(omp_core_val=4)
    aff_file = example_data("elastix.txt")
    ref_file = example_data("im1.nii")
    in_file = example_data("im2.nii")
    nr_transform_6.inputs.flirt_2_nr_input = (aff_file, ref_file, in_file)

    cmd_tmp = "{cmd} -omp 4 -flirtAff2NR {aff} {ref} {in_file} {out_file}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_transform"),
        aff=aff_file,
        ref=ref_file,
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), "elastix_trans.txt"),
    )

    assert nr_transform_6.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd="reg_measure"),
    reason="niftyreg is not installed. reg_measure not found.",
)
def test_reg_measure():
    """tests for reg_measure interface"""
    # Create a reg_measure object
    nr_measure = RegMeasure()

    # Check if the command is properly defined
    assert nr_measure.cmd == get_custom_path("reg_measure")

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_measure.run()

    # Assign some input data
    ref_file = example_data("im1.nii")
    flo_file = example_data("im2.nii")
    nr_measure.inputs.ref_file = ref_file
    nr_measure.inputs.flo_file = flo_file
    nr_measure.inputs.measure_type = "lncc"
    nr_measure.inputs.omp_core_val = 4

    cmd_tmp = "{cmd} -flo {flo} -lncc -omp 4 -out {out} -ref {ref}"
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path("reg_measure"),
        flo=flo_file,
        out="im2_lncc.txt",
        ref=ref_file,
    )

    assert nr_measure.cmdline == expected_cmd
