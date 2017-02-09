# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        UnaryMaths, BinaryMaths)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyseg(cmd='seg_maths'))
def test_seg_maths():

    # Create a node object
    unarym = UnaryMaths()

    # Check if the command is properly defined
    yield assert_equal, unarym.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    unarym.inputs.in_file = in_file
    unarym.inputs.operation = 'otsu'

    expected_cmd = '{cmd} {in_file} -otsu {out_file}'.format(
                        cmd=get_custom_path('seg_maths'),
                        in_file=in_file,
                        out_file=os.path.join(os.getcwd(), 'im1_otsu.nii'))

    yield assert_equal, unarym.cmdline, expected_cmd

    # Create a node object
    binarym = BinaryMaths()

    # Check if the command is properly defined
    yield assert_equal, binarym.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    binarym.inputs.in_file = in_file
    binarym.inputs.operand_value = 2.0
    binarym.inputs.operation = 'sub'

    expected_cmd = '{cmd} {in_file} -sub 2.00000000 {out_file}'.format(
                        cmd=get_custom_path('seg_maths'),
                        in_file=in_file,
                        out_file=os.path.join(os.getcwd(), 'im1_maths.nii'))

    yield assert_equal, binarym.cmdline, expected_cmd
