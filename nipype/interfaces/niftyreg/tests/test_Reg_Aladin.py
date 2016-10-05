# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegAladin)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_aladin'))
def test_reg_aladin():

    # Create a reg_aladin object
    nr = RegAladin()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_aladin')

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    rmask_file = example_data('mask.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.rmask_file = rmask_file
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_aladin') + ' ' + '-aff ' + os.getcwd() + os.sep + 'im2_aff.txt ' +\
                   '-flo ' + flo_file + ' ' + '-omp 4 ' + '-ref ' + ref_file + ' ' +\
                   '-res ' + os.getcwd() + os.sep + 'im2_res.nii.gz ' + '-rmask ' + rmask_file
    yield assert_equal, nr.cmdline, expected_cmd
