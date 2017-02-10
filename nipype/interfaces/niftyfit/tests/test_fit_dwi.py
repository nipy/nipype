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

    cmd_tmp = '{cmd} -bval {bval} -bvallowthreshold 20.000000 -bvec {bvec} \
-error {error} -famap {fa} -mcmap {mc} -mdmap {md} -res {res} -rgbmap {rgb} \
-rotsform 0 -source {in_file} -syn {syn} -tenmap2 {ten2} -v1map {v1}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_dwi'),
        in_file=in_file,
        bval=bval_file,
        bvec=bvec_file,
        error=os.path.join(os.getcwd(), 'dwifit_error.nii.gz'),
        fa=os.path.join(os.getcwd(), 'dwifit_famap.nii.gz'),
        mc=os.path.join(os.getcwd(), 'dwifit_mcmap.nii.gz'),
        md=os.path.join(os.getcwd(), 'dwifit_mdmap.nii.gz'),
        res=os.path.join(os.getcwd(), 'dwifit_resmap.nii.gz'),
        rgb=os.path.join(os.getcwd(), 'dwifit_rgbmap.nii.gz'),
        syn=os.path.join(os.getcwd(), 'dwifit_syn.nii.gz'),
        ten2=os.path.join(os.getcwd(), 'dwifit_tenmap2.nii.gz'),
        v1=os.path.join(os.getcwd(), 'dwifit_v1map.nii.gz'))

    assert test_node.cmdline == expected_cmd
