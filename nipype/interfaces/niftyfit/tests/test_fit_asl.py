# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitAsl
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyfit(cmd='fit_asl'))
def test_fit_asl():
    # Create a reg_aladin object
    test_node = FitAsl()

    # Check if the command is properly defined
    yield assert_equal, test_node.cmd, get_custom_path('fit_asl')

    # Assign some input data
    in_file = example_data('im1.nii')
    test_node.inputs.source_file = in_file

    cmd_tmp = '{cmd} -cbf {cbf} -error {error} -source {in_file} -syn {syn}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_asl'),
        in_file=in_file,
        cbf=os.path.join(os.getcwd(), 'im1_cbf.nii.gz'),
        error=os.path.join(os.getcwd(), 'im1_error.nii.gz'),
        syn=os.path.join(os.getcwd(), 'im1_syn.nii.gz'))

    yield assert_equal, test_node.cmdline, expected_cmd
