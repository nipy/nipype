# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegF3D)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_f3d'))
def test_reg_f3d():

    # Create a reg_f3d object
    nr = RegF3D()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_f3d')

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    rmask_file = example_data('mask.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.rmask_file = rmask_file
    nr.inputs.omp_core_val = 4
    nr.inputs.vel_flag = True
    nr.inputs.be_val = 0.1
    nr.inputs.le_val = 0.1

    expected_cmd = get_custom_path('reg_f3d') + ' ' + '-be 0.100000 ' +\
                   '-cpp ' + os.getcwd() + os.sep + 'im2_cpp.nii.gz ' +'-flo ' + flo_file + ' ' +\
                   '-le 0.100000 ' + '-omp 4 ' + '-ref ' + ref_file + ' ' +\
                   '-res ' + os.getcwd() + os.sep + 'im2_res.nii.gz ' + '-rmask ' + rmask_file + ' ' + '-vel'
    yield assert_equal, nr.cmdline, expected_cmd
