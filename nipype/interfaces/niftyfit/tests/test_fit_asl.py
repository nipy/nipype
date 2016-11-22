# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitAsl
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyfit(cmd='fit_asl'))
def test_seg_em():

    # Create a reg_aladin object
    test_node = FitAsl()

    # Check if the command is properly defined
    yield assert_equal, test_node.cmd, get_custom_path('fit_asl')

    # Assign some input data
    in_file = example_data('im1.nii')
    test_node.inputs.source_file = in_file

    cmd_tmp = '{cmd} -cbf im1_cbf -error im1_error -source {in_file} \
-syn im1_syn'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_asl'),
        in_file=in_file)

    yield assert_equal, test_node.cmdline, expected_cmd
