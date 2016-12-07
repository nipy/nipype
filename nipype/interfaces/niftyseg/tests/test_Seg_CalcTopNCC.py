# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        CalcTopNCC)
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyseg(cmd='seg_CalcTopNCC'))
def test_seg_patchmatch():

    # Create a reg_aladin object
    calctopncc = CalcTopNCC()

    # Check if the command is properly defined
    yield assert_equal, calctopncc.cmd, get_custom_path('seg_CalcTopNCC')

    # Assign some input data
    in_file = example_data('im1.nii')
    calctopncc.inputs.in_file = in_file
    calctopncc.inputs.num_templates = 2
    calctopncc.inputs.in_templates = [in_file, in_file]
    calctopncc.inputs.top_templates = 1

    cmd_tmp = '{cmd} -target {in_file} -templates 2 {file1} {file2} -n 1'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_CalcTopNCC'),
                        in_file=in_file,
                        file1=in_file,
                        file2=in_file)
    # out_file=os.path.join(os.getcwd(), 'im1_pm.nii'))

    yield assert_equal, calctopncc.cmdline, expected_cmd
