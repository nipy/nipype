# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from .. import (get_custom_path, RegAladin, RegF3D)
from .test_regutils import no_nifty_tool


@pytest.mark.skipif(
    no_nifty_tool(cmd='reg_aladin'),
    reason="niftyreg is not installed. reg_aladin not found.")
def test_reg_aladin():
    """ tests for reg_aladin interface"""
    # Create a reg_aladin object
    nr_aladin = RegAladin()

    # Check if the command is properly defined
    assert nr_aladin.cmd == get_custom_path('reg_aladin')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_aladin.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    rmask_file = example_data('mask.nii')
    nr_aladin.inputs.ref_file = ref_file
    nr_aladin.inputs.flo_file = flo_file
    nr_aladin.inputs.rmask_file = rmask_file
    nr_aladin.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -aff {aff} -flo {flo} -omp 4 -ref {ref} -res {res} \
-rmask {rmask}'

    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_aladin'),
        aff='im2_aff.txt',
        flo=flo_file,
        ref=ref_file,
        res='im2_res.nii.gz',
        rmask=rmask_file,
    )

    assert nr_aladin.cmdline == expected_cmd


@pytest.mark.skipif(
    no_nifty_tool(cmd='reg_f3d'),
    reason="niftyreg is not installed. reg_f3d not found.")
def test_reg_f3d():
    """ tests for reg_f3d interface"""
    # Create a reg_f3d object
    nr_f3d = RegF3D()

    # Check if the command is properly defined
    assert nr_f3d.cmd == get_custom_path('reg_f3d')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr_f3d.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    rmask_file = example_data('mask.nii')
    nr_f3d.inputs.ref_file = ref_file
    nr_f3d.inputs.flo_file = flo_file
    nr_f3d.inputs.rmask_file = rmask_file
    nr_f3d.inputs.omp_core_val = 4
    nr_f3d.inputs.vel_flag = True
    nr_f3d.inputs.be_val = 0.1
    nr_f3d.inputs.le_val = 0.1

    cmd_tmp = '{cmd} -be 0.100000 -cpp {cpp} -flo {flo} -le 0.100000 -omp 4 \
-ref {ref} -res {res} -rmask {rmask} -vel'

    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_f3d'),
        cpp='im2_cpp.nii.gz',
        flo=flo_file,
        ref=ref_file,
        res='im2_res.nii.gz',
        rmask=rmask_file,
    )

    assert nr_f3d.cmdline == expected_cmd
