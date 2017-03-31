# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import no_niftyseg, get_custom_path, PatchMatch
from nipype.testing import example_data
import os
import pytest


@pytest.mark.skipif(no_niftyseg(cmd='seg_PatchMatch'),
                    reason="niftyseg is not installed")
def test_seg_patchmatch():

    # Create a node object
    seg_patchmatch = PatchMatch()

    # Check if the command is properly defined
    assert seg_patchmatch.cmd == get_custom_path('seg_PatchMatch')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        seg_patchmatch.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    mask_file = example_data('im2.nii')
    db_file = example_data('db.xml')
    seg_patchmatch.inputs.in_file = in_file
    seg_patchmatch.inputs.mask_file = mask_file
    seg_patchmatch.inputs.database_file = db_file

    cmd_tmp = '{cmd} -i {in_file} -m {mask_file} -db {db} -o {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_PatchMatch'),
        in_file=in_file,
        mask_file=mask_file,
        db=db_file,
        out_file=os.path.join(os.getcwd(), 'im1_pm.nii')
    )

    assert seg_patchmatch.cmdline == expected_cmd
