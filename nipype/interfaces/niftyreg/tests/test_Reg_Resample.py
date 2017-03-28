# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path,
                                        RegResample)
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyreg(cmd='reg_resample'))
def test_reg_resample_res():

    # Create a reg_resample object
    nr = RegResample()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_resample')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.trans_file = trans_file
    nr.inputs.inter_val = 'LIN'
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -flo {flo} -inter 1 -omp 4 -ref {ref} -trans {trans} \
-res {res}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_resample'),
        flo=flo_file,
        ref=ref_file,
        trans=trans_file,
        res=os.path.join(os.getcwd(), 'im2_res.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_resample'))
def test_reg_resample_blank():

    # Create a reg_resample object
    nr = RegResample()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_resample')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'blank'
    nr.inputs.inter_val = 'LIN'
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -flo {flo} -inter 1 -omp 4 -ref {ref} -trans {trans} \
-blank {blank}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_resample'),
        flo=flo_file,
        ref=ref_file,
        trans=trans_file,
        blank=os.path.join(os.getcwd(), 'im2_blank.nii.gz'))

    assert nr.cmdline == expected_cmd
