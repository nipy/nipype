# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegTools)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_tools'))
def test_reg_tools_mul():

    # Create a reg_tools object
    nr = RegTools()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_tools')

    # Assign some input data
    in_file = example_data('im1.nii')
    nr.inputs.in_file = in_file
    nr.inputs.mul_val = 4
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_tools') + ' ' + '-in ' + in_file + ' -mul 4.0 ' +\
                   '-omp 4 ' + '-out ' + os.getcwd() + os.sep + 'im1_tools.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd

@skipif(no_niftyreg(cmd='reg_tools'))
def test_reg_tools_iso():

    # Create a reg_tools object
    nr = RegTools()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_tools')

    # Assign some input data
    in_file = example_data('im1.nii')
    nr.inputs.in_file = in_file
    nr.inputs.iso_flag = True
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_tools') + ' ' + '-in ' + in_file + ' -iso ' +\
                   '-omp 4 ' + '-out ' + os.getcwd() + os.sep + 'im1_tools.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd
