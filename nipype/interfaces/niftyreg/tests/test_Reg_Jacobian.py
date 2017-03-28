# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path,
                                        RegJacobian)
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jac():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_jacobian')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -ref {ref} -trans {trans} -jac {jac}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_jacobian'),
        ref=ref_file,
        trans=trans_file,
        jac=os.path.join(os.getcwd(), 'warpfield_jac.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jac_m():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_jacobian')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'jacM'
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -ref {ref} -trans {trans} -jacM {jac}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_jacobian'),
        ref=ref_file,
        trans=trans_file,
        jac=os.path.join(os.getcwd(), 'warpfield_jacM.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_jacobian'))
def test_reg_jacobian_jac_l():

    # Create a reg_jacobian object
    nr = RegJacobian()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_jacobian')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    trans_file = example_data('warpfield.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.trans_file = trans_file
    nr.inputs.type = 'jacL'
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -omp 4 -ref {ref} -trans {trans} -jacL {jac}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_jacobian'),
        ref=ref_file,
        trans=trans_file,
        jac=os.path.join(os.getcwd(), 'warpfield_jacL.nii.gz'))

    assert nr.cmdline == expected_cmd
