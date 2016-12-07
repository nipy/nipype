# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, DwiTool
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyfit(cmd='dwi_tool'))
def test_seg_em():

    # Create a reg_aladin object
    test_node = DwiTool()

    # Check if the command is properly defined
    yield assert_equal, test_node.cmd, get_custom_path('dwi_tool')

    # Assign some input data
    in_file = example_data('diffusion.nii')
    test_node.inputs.source_file = in_file

    cmd_tmp = '{cmd} -famap dwifit__famap -logdti2 dwifit__logdti2 -mdmap \
dwifit__mdmap -rgbmap dwifit__rgbmap -source {in_file}  -v1map dwifit__v1map'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('dwi_tool'),
        in_file=in_file)

    yield assert_equal, test_node.cmdline, expected_cmd
