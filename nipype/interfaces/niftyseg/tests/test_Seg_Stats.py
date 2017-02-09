# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        UnaryStats, BinaryStats)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyseg(cmd='seg_stats'))
def test_unary_stats():

    # Create a node object
    unarys = UnaryStats()

    # Check if the command is properly defined
    yield assert_equal, unarys.cmd, get_custom_path('seg_stats')

    # Assign some input data
    in_file = example_data('im1.nii')
    unarys.inputs.in_file = in_file
    unarys.inputs.operation = 'a'

    expected_cmd = '{cmd} {in_file} -a'.format(
        cmd=get_custom_path('seg_stats'),
        in_file=in_file)

    yield assert_equal, unarys.cmdline, expected_cmd


@skipif(no_niftyseg(cmd='seg_stats'))
def test_binary_stats():
    # Create a node object
    binarys = BinaryStats()

    # Check if the command is properly defined
    yield assert_equal, binarys.cmd, get_custom_path('seg_stats')

    # Assign some input data
    in_file = example_data('im1.nii')
    binarys.inputs.in_file = in_file
    binarys.inputs.operand_value = 2
    binarys.inputs.operation = 'sa'

    expected_cmd = '{cmd} {in_file} -sa 2.00000000'.format(
        cmd=get_custom_path('seg_stats'),
        in_file=in_file)

    yield assert_equal, binarys.cmdline, expected_cmd
