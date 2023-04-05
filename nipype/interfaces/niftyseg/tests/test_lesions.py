# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from ...niftyreg import get_custom_path
from ...niftyreg.tests.test_regutils import no_nifty_tool
from .. import FillLesions


@pytest.mark.skipif(
    no_nifty_tool(cmd="seg_FillLesions"), reason="niftyseg is not installed"
)
def test_seg_filllesions():
    # Create a node object
    seg_fill = FillLesions()

    # Check if the command is properly defined
    cmd = get_custom_path("seg_FillLesions", env_dir="NIFTYSEGDIR")
    assert seg_fill.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        seg_fill.run()

    # Assign some input data
    in_file = example_data("im1.nii")
    lesion_mask = example_data("im2.nii")
    seg_fill.inputs.in_file = in_file
    seg_fill.inputs.lesion_mask = lesion_mask

    expected_cmd = "{cmd} -i {in_file} -l {lesion_mask} -o {out_file}".format(
        cmd=cmd,
        in_file=in_file,
        lesion_mask=lesion_mask,
        out_file="im1_lesions_filled.nii.gz",
    )

    assert seg_fill.cmdline == expected_cmd
