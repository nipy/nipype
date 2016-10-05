# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path, RegMeasure)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyreg(cmd='reg_measure'))
def test_reg_measure():

    # Create a reg_measure object
    nr = RegMeasure()

    # Check if the command is properly defined
    yield assert_equal, nr.cmd, get_custom_path('reg_measure')

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.measure_type = 'lncc'
    nr.inputs.omp_core_val = 4

    expected_cmd = get_custom_path('reg_measure') + ' ' + '-flo ' + flo_file + ' ' + '-lncc ' + '-omp 4 '+\
                   '-out ' + os.getcwd() + os.sep + 'im2_lncc.txt ' + '-ref ' + ref_file
    yield assert_equal, nr.cmdline, expected_cmd
