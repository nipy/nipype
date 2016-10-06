# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegResample)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_resample'))
def test_reg_resample_res():

    # Create a reg_resample object
    nr = RegResample()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_resample')

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.trans_file = trans_file
    nr.inputs.inter_val = 'LIN'
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_resample') + ' ' + '-flo ' + flo_file + ' ' + '-inter 1 -omp 4 ' +\
                   '-ref ' + ref_file + ' ' + '-trans ' + trans_file + ' ' +\
                   '-res ' + os.getcwd() + os.sep + 'im2_res.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd


@skipif(no_niftyreg(cmd='reg_resample'))
def test_reg_resample_blank():

    # Create a reg_resample object
    nr = RegResample()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_resample')

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'blank'
    nr.inputs.inter_val = 'LIN'
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_resample') + ' ' + '-flo ' + flo_file + ' ' + '-inter 1 -omp 4 ' +\
                   '-ref ' + ref_file + ' ' + '-trans ' + trans_file + ' ' +\
                   '-blank ' + os.getcwd() + os.sep + 'im2_blank.nii.gz'
    yield assert_equal, nr.cmdline, expected_cmd
