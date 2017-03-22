# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import no_niftyseg, get_custom_path, CalcTopNCC
from nipype.testing import skipif, example_data
import pytest


@skipif(no_niftyseg(cmd='seg_CalcTopNCC'))
def test_seg_calctopncc():

    # Create a node object
    calctopncc = CalcTopNCC()

    # Check if the command is properly defined
    assert calctopncc.cmd == get_custom_path('seg_CalcTopNCC')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        calctopncc.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    file1 = example_data('im2.nii')
    file2 = example_data('im3.nii')
    calctopncc.inputs.in_file = in_file
    calctopncc.inputs.num_templates = 2
    calctopncc.inputs.in_templates = [file1, file2]
    calctopncc.inputs.top_templates = 1

    cmd_tmp = '{cmd} -target {in_file} -templates 2 {file1} {file2} -n 1'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_CalcTopNCC'),
        in_file=in_file,
        file1=file1,
        file2=file2)

    assert calctopncc.cmdline == expected_cmd
