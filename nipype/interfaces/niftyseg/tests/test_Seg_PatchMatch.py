# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        PatchMatch)
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyseg(cmd='seg_PatchMatch'))
def test_seg_patchmatch():

    # Create a reg_aladin object
    seg_patchmatch = PatchMatch()

    # Check if the command is properly defined
    yield assert_equal, seg_patchmatch.cmd, get_custom_path('seg_PatchMatch')

    # Assign some input data
    in_file = example_data('im1.nii')
    seg_patchmatch.inputs.in_file = in_file
    seg_patchmatch.inputs.mask_file = in_file
    seg_patchmatch.inputs.database_file = in_file

    cmd_tmp = '{cmd} -i {in_file} -m {mask_file} -db {db} -o {out_file}'
    expected_cmd = cmd_tmp.format(
                        cmd=get_custom_path('seg_PatchMatch'),
                        in_file=in_file,
                        mask_file=in_file,
                        db=in_file,
                        out_file=os.path.join(os.getcwd(), 'im1_pm.nii'))

    yield assert_equal, seg_patchmatch.cmdline, expected_cmd
