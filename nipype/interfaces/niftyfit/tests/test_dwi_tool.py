# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, DwiTool
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyfit(cmd='dwi_tool'))
def test_dwi_tool():
    # Create a node object
    test_node = DwiTool()

    # Check if the command is properly defined
    assert test_node.cmd == get_custom_path('dwi_tool')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        test_node.run()

    # Assign some input data
    in_file = example_data('diffusion.nii')
    bval_file = example_data('bvals')
    bvec_file = example_data('bvecs')
    b0_file = example_data('b0.nii')
    mask_file = example_data('mask.nii')
    test_node.inputs.source_file = in_file
    test_node.inputs.mask_file = mask_file
    test_node.inputs.bval_file = bval_file
    test_node.inputs.bvec_file = bvec_file
    test_node.inputs.b0_file = b0_file
    test_node.inputs.dti_flag = True

    cmd_tmp = '{cmd} -source {in_file} -bval {bval} -bvec {bvec} -b0 {b0} \
-mask {mask} -dti -famap {fa} -logdti2 {log} -mcmap {mc} -mdmap {md} \
-rgbmap {rgb} -syn {syn} -v1map {v1}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('dwi_tool'),
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        b0=b0_file,
        mask=mask_file,
        fa=os.path.join(os.getcwd(), 'diffusion_famap.nii.gz'),
        log=os.path.join(os.getcwd(), 'diffusion_logdti2.nii.gz'),
        mc=os.path.join(os.getcwd(), 'diffusion_mcmap.nii.gz'),
        md=os.path.join(os.getcwd(), 'diffusion_mdmap.nii.gz'),
        rgb=os.path.join(os.getcwd(), 'diffusion_rgbmap.nii.gz'),
        syn=os.path.join(os.getcwd(), 'diffusion_syn.nii.gz'),
        v1=os.path.join(os.getcwd(), 'diffusion_v1map.nii.gz'))

    assert test_node.cmdline == expected_cmd
