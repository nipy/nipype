# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path,
                                        RegTransform)
from nipype.testing import skipif, example_data
import os


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_def():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    trans_file = example_data('warpfield.nii')
    nr.inputs.def_input = trans_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -def {trans_file} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        trans_file=trans_file,
        out_file=os.path.join(os.getcwd(), 'warpfield_trans.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_def_ref():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref1_file = ref_file
    nr.inputs.def_input = trans_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -ref {ref_file} -omp 4 -def {trans_file} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        ref_file=ref_file,
        trans_file=trans_file,
        out_file=os.path.join(os.getcwd(), 'warpfield_trans.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp_nii():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    trans2_file = example_data('anatomical.nii')
    nr.inputs.ref1_file = ref_file
    nr.inputs.comp_input2 = trans2_file
    nr.inputs.comp_input = trans_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -ref {ref_file} -omp 4 -comp {trans1} {trans2} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        ref_file=ref_file,
        trans1=trans_file,
        trans2=trans2_file,
        out_file=os.path.join(os.getcwd(), 'warpfield_trans.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp_txt():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    aff1_file = example_data('ants_Affine.txt')
    aff2_file = example_data('elastix.txt')
    nr.inputs.comp_input2 = aff2_file
    nr.inputs.comp_input = aff1_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -comp {aff1} {aff2} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        aff1=aff1_file,
        aff2=aff2_file,
        out_file=os.path.join(os.getcwd(), 'ants_Affine_trans.txt'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    trans_file = example_data('warpfield.nii')
    aff_file = example_data('elastix.txt')
    nr.inputs.comp_input2 = trans_file
    nr.inputs.comp_input = aff_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -comp {aff} {trans} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        aff=aff_file,
        trans=trans_file,
        out_file=os.path.join(os.getcwd(), 'elastix_trans.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_flirt():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_transform')

    # Assign some input data
    aff_file = example_data('elastix.txt')
    ref_file = example_data('im1.nii')
    in_file = example_data('im2.nii')
    nr.inputs.flirt_2_nr_input = (aff_file, ref_file, in_file)
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -flirtAff2NR {aff} {ref} {in_file} {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_transform'),
        aff=aff_file,
        ref=ref_file,
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'elastix_trans.txt'))

    assert nr.cmdline == expected_cmd
