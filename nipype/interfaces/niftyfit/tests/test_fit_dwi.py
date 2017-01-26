# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitDwi
from nipype.testing import assert_equal, skipif, example_data


@skipif(no_niftyfit(cmd='fit_dwi'))
def test_fit_dwi():
    # Create a reg_aladin object
    test_node = FitDwi()

    # Check if the command is properly defined
    yield assert_equal, test_node.cmd, get_custom_path('fit_dwi')

    # Assign some input data
    in_file = example_data('diffusion.nii')
    bval_file = example_data('bvals')
    bvec_file = example_data('bvecs')
    test_node.inputs.source_file = in_file
    test_node.inputs.bval_file = bval_file
    test_node.inputs.bvec_file = bvec_file

    cmd_tmp = '{cmd} -bval {bval} -bvec {bvec} -famap {famap} -mcmap \
{mcmap} -mdmap {mdmap} -res {resmap} -rgbmap {rgbmap} \
-source {in_file} -syn {syn} -tenmap2 {tenmap} -v1map \
{v1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_dwi'),
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        famap=os.path.join(os.getcwd(), 'diffusion_famap.nii.gz'),
        mcmap=os.path.join(os.getcwd(), 'diffusion_mcmap.nii.gz'),
        mdmap=os.path.join(os.getcwd(), 'diffusion_mdmap.nii.gz'),
        resmap=os.path.join(os.getcwd(), 'diffusion_resmap.nii.gz'),
        rgbmap=os.path.join(os.getcwd(), 'diffusion_rgbmap.nii.gz'),
        syn=os.path.join(os.getcwd(), 'diffusion_syn.nii.gz'),
        tenmap=os.path.join(os.getcwd(), 'diffusion_tenmap2.nii.gz'),
        v1map=os.path.join(os.getcwd(), 'diffusion_v1map.nii.gz'))

    yield assert_equal, test_node.cmdline, expected_cmd
