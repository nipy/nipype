# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegTransform)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_def():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    trans_file = example_data('warpfield.nii')
    nr.inputs.def_input = trans_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -omp 4 ' +\
                   '-def ' + trans_file + ' ' + os.getcwd() + os.sep + 'warpfield_trans.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_def_ref():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref1_file = ref_file
    nr.inputs.def_input = trans_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -ref ' + ref_file + ' -omp 4 ' +\
                   '-def ' + trans_file + ' ' + os.getcwd() + os.sep + 'warpfield_trans.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp_nii():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    trans2_file = example_data('anatomical.nii')
    nr.inputs.ref1_file = ref_file
    nr.inputs.comp_input2 = trans2_file
    nr.inputs.comp_input = trans_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -ref ' + ref_file + ' -omp 4 ' +\
                   '-comp ' + trans_file + ' ' + trans2_file + ' ' + os.getcwd() + os.sep + 'warpfield_trans.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp_txt():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    aff1_file = example_data('ants_Affine.txt')
    aff2_file = example_data('elastix.txt')
    nr.inputs.comp_input2 = aff2_file
    nr.inputs.comp_input = aff1_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -omp 4 ' +\
                   '-comp ' + aff1_file + ' ' + aff2_file + ' ' + os.getcwd() + os.sep + 'ants_Affine_trans.txt'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_comp():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    trans_file = example_data('warpfield.nii')
    aff_file = example_data('elastix.txt')
    nr.inputs.comp_input2 = trans_file
    nr.inputs.comp_input = aff_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -omp 4 ' +\
                   '-comp ' + aff_file + ' ' + trans_file + ' ' + os.getcwd() + os.sep + 'elastix_trans.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_transform'))
def test_reg_transform_flirt():

    # Create a reg_transform object
    nr = RegTransform()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_transform')

    # Assign some input data
    aff_file = example_data('elastix.txt')
    ref_file = example_data('im1.nii')
    in_file = example_data('im2.nii')
    nr.inputs.flirt_2_nr_input = (aff_file, ref_file, in_file)
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_transform') + ' -omp 4 ' +\
                   '-flirtAff2NR ' + '%s %s %s' % (aff_file, ref_file, in_file) + ' ' +\
                   os.getcwd() + os.sep + 'elastix_trans.txt'
    yield assert_equal, nr.cmdline, expected_cmd
