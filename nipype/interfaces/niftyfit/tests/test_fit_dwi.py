# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitDwi
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyfit(cmd='fit_dwi'))
def test_fit_dwi():

    # Create a node object
    test_node = FitDwi()

    # Check if the command is properly defined
    assert test_node.cmd == get_custom_path('fit_dwi')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        test_node.run()

    # Assign some input data
    in_file = example_data('diffusion.nii')
    bval_file = example_data('bvals')
    bvec_file = example_data('bvecs')
    test_node.inputs.source_file = in_file
    test_node.inputs.bval_file = bval_file
    test_node.inputs.bvec_file = bvec_file
    test_node.inputs.dti_flag = True

    cmd_tmp = '{cmd} -source {in_file} -bval {bval} -bvec {bvec} -dti \
-error {error} -famap {fa} -mcmap {mc} -mdmap {md} -nodiff {nodiff} \
-res {res} -rgbmap {rgb} -syn {syn} -tenmap2 {ten2} \
-tenmap {ten} -v1map {v1}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_dwi'),
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        error=os.path.join(os.getcwd(), 'diffusion_error.nii.gz'),
        fa=os.path.join(os.getcwd(), 'diffusion_famap.nii.gz'),
        mc=os.path.join(os.getcwd(), 'diffusion_mcmap.nii.gz'),
        md=os.path.join(os.getcwd(), 'diffusion_mdmap.nii.gz'),
        nodiff=os.path.join(os.getcwd(), 'diffusion_no_diff.nii.gz'),
        res=os.path.join(os.getcwd(), 'diffusion_resmap.nii.gz'),
        rgb=os.path.join(os.getcwd(), 'diffusion_rgbmap.nii.gz'),
        syn=os.path.join(os.getcwd(), 'diffusion_syn.nii.gz'),
        ten2=os.path.join(os.getcwd(), 'diffusion_tenmap2.nii.gz'),
        v1=os.path.join(os.getcwd(), 'diffusion_v1map.nii.gz'),
        ten=os.path.join(os.getcwd(), 'diffusion_tenmap.nii.gz'))

    assert test_node.cmdline == expected_cmd
