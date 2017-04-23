# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import no_niftyreg, get_custom_path, RegTools
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyreg(cmd='reg_tools'))
def test_reg_tools_mul():

    # Create a reg_tools object
    nr = RegTools()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_tools')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    nr.inputs.in_file = in_file
    nr.inputs.mul_val = 4
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -in {in_file} -mul 4.0 -omp 4 -out {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_tools'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_tools.nii.gz'))

    assert nr.cmdline == expected_cmd


@skipif(no_niftyreg(cmd='reg_tools'))
def test_reg_tools_iso():

    # Create a reg_tools object
    nr = RegTools()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_tools')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    nr.inputs.in_file = in_file
    nr.inputs.iso_flag = True
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -in {in_file} -iso -omp 4 -out {out_file}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_tools'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_tools.nii.gz'))

    assert nr.cmdline == expected_cmd
