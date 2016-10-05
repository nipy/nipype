# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegJacobian)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jac():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_jacobian')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_jacobian') + ' -omp 4 ' + '-ref ' + ref_file + ' ' +\
                   '-trans ' + trans_file + ' -jac ' + os.getcwd() + os.sep + 'warpfield_jac.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jacM():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_jacobian')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'jacM'
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_jacobian') + ' -omp 4 ' + '-ref ' + ref_file + ' ' +\
                   '-trans ' + trans_file + ' -jacM ' + os.getcwd() + os.sep + 'warpfield_jacM.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jacL():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_jacobian')

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'jacL'
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_jacobian') + ' -omp 4 ' + '-ref ' + ref_file + ' ' +\
                   '-trans ' + trans_file + ' -jacL ' + os.getcwd() + os.sep + 'warpfield_jacL.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd
