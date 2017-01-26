# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, DwiTool
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyfit(cmd='dwi_tool'))
def test_dwi_tool():
    # Create a reg_aladin object
    test_node = DwiTool()

    # Check if the command is properly defined
    yield assert_equal, test_node.cmd, get_custom_path('dwi_tool')

    # Assign some input data
    in_file = example_data('diffusion.nii')
    test_node.inputs.source_file = in_file

    cmd_tmp = '{cmd} -famap {famap} -logdti2 {logdti2} -mdmap {mdmap} \
-rgbmap {rgbmap} -source {in_file}  -v1map {v1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_dwi'),
        in_file=in_file,
        famap=os.path.join(os.getcwd(), 'diffusion_famap.nii.gz'),
        logdti2=os.path.join(os.getcwd(), 'diffusion_logdti2.nii.gz'),
        mdmap=os.path.join(os.getcwd(), 'diffusion_mdmap.nii.gz'),
        rgbmap=os.path.join(os.getcwd(), 'diffusion_rgbmap.nii.gz'),
        v1map=os.path.join(os.getcwd(), 'diffusion_v1map.nii.gz'))

    yield assert_equal, test_node.cmdline, expected_cmd
