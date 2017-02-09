# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyseg import (no_niftyseg, get_custom_path,
                                        FillLesions)
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyseg(cmd='seg_FillLesions'))
def test_seg_filllesions():

    # Create a node object
    seg_fill = FillLesions()

    # Check if the command is properly defined
    yield assert_equal, seg_fill.cmd, get_custom_path('seg_FillLesions')

    # Assign some input data
    in_file = example_data('im1.nii')
    seg_fill.inputs.in_file = in_file
    seg_fill.inputs.lesion_mask = in_file

    expected_cmd = '{cmd} -i {in_file} -l {lesion_mask} -o {out_file}'.format(
                cmd=get_custom_path('seg_FillLesions'),
                in_file=in_file,
                lesion_mask=in_file,
                out_file=os.path.join(os.getcwd(), 'im1_lesions_filled.nii'))

    yield assert_equal, seg_fill.cmdline, expected_cmd
