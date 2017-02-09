# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        UnaryMaths, BinaryMaths,
                                        BinaryMathsInteger, TupleMaths,
                                        Merge)
from nipype.testing import (assert_equal, skipif, example_data)


@skipif(no_niftyseg(cmd='seg_maths'))
def test_unary_maths():

    # Create a node object
    unarym = UnaryMaths()

    # Check if the command is properly defined
    yield assert_equal, unarym.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    unarym.inputs.in_file = in_file
    unarym.inputs.operation = 'otsu'
    unarym.inputs.output_datatype = 'float'

    expected_cmd = '{cmd} {in_file} -otsu {out_file} -odt float'.format(
        cmd=get_custom_path('seg_maths'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_otsu.nii'))

    yield assert_equal, unarym.cmdline, expected_cmd


@skipif(no_niftyseg(cmd='seg_maths'))
def test_binary_maths():

    # Create a node object
    binarym = BinaryMaths()

    # Check if the command is properly defined
    yield assert_equal, binarym.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    binarym.inputs.in_file = in_file
    binarym.inputs.operand_value = 2.0
    binarym.inputs.operation = 'sub'
    binarym.inputs.output_datatype = 'float'

    cmd_tmp = '{cmd} {in_file} -sub 2.00000000 {out_file} -odt float'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_maths'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_sub.nii'))

    yield assert_equal, binarym.cmdline, expected_cmd


@skipif(no_niftyseg(cmd='seg_maths'))
def test_int_binary_maths():

    # Create a node object
    ibinarym = BinaryMathsInteger()

    # Check if the command is properly defined
    yield assert_equal, ibinarym.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    ibinarym.inputs.in_file = in_file
    ibinarym.inputs.operand_value = 2
    ibinarym.inputs.operation = 'dil'
    ibinarym.inputs.output_datatype = 'float'

    expected_cmd = '{cmd} {in_file} -dil 2 {out_file} -odt float'.format(
        cmd=get_custom_path('seg_maths'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_dil.nii'))

    yield assert_equal, ibinarym.cmdline, expected_cmd


@skipif(no_niftyseg(cmd='seg_maths'))
def test_tuple_maths():

    # Create a node object
    tuplem = TupleMaths()

    # Check if the command is properly defined
    yield assert_equal, tuplem.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    op_file = example_data('im2.nii')
    tuplem.inputs.in_file = in_file
    tuplem.inputs.operation = 'lncc'
    tuplem.inputs.operand_file1 = op_file
    tuplem.inputs.operand_value2 = 2.0
    tuplem.inputs.output_datatype = 'float'

    cmd_tmp = '{cmd} {in_file} -lncc {op} 2.00000000 {out_file} -odt float'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_maths'),
        in_file=in_file,
        op=op_file,
        out_file=os.path.join(os.getcwd(), 'im1_lncc.nii'))

    yield assert_equal, tuplem.cmdline, expected_cmd


@skipif(no_niftyseg(cmd='seg_maths'))
def test_merge():

    # Create a node object
    merge = Merge()

    # Check if the command is properly defined
    yield assert_equal, merge.cmd, get_custom_path('seg_maths')

    # Assign some input data
    in_file = example_data('im1.nii')
    file1 = example_data('im2.nii')
    file2 = example_data('im3.nii')
    merge.inputs.in_file = in_file
    merge.inputs.merge_files = [file1, file2]
    merge.inputs.dimension = 2
    merge.inputs.output_datatype = 'float'

    cmd_tmp = '{cmd} {in_file} -merge 2 2 {f1} {f2} {out_file} -odt float'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_maths'),
        in_file=in_file,
        f1=file1,
        f2=file2,
        out_file=os.path.join(os.getcwd(), 'im1_merged.nii'))

    yield assert_equal, merge.cmdline, expected_cmd
