# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        STEPS)
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyseg(cmd='seg_LabFusion'))
def test_seg_patchmatch():

    # Create a node object
    steps = STEPS()

    # Check if the command is properly defined
    yield assert_equal, steps.cmd, get_custom_path('seg_LabFusion')

    # Assign some input data
    in_file = example_data('im1.nii')
    steps.inputs.in_file = in_file
    steps.inputs.kernel_size = 2
    steps.inputs.warped_seg_file = in_file
    steps.inputs.warped_img_file = in_file
    steps.inputs.template_num = 2

    cmd_tmp = '{cmd} -in {warped_img_file} -STEPS 2.000000 2 {in_file} \
{warped_seg_file} -out {out_file}'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_LabFusion'),
                        warped_img_file=in_file,
                        in_file=in_file,
                        warped_seg_file=in_file,
                        out_file=os.path.join(os.getcwd(), 'im1_steps.nii'))
    # out_file=os.path.join(os.getcwd(), 'im1_pm.nii'))

    yield assert_equal, steps.cmdline, expected_cmd
