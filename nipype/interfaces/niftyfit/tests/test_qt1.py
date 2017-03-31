# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import pytest

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitQt1
from nipype.testing import example_data


@pytest.mark.skipif(no_niftyfit(cmd='fit_qt1'),
                    reason="niftyfit is not installed")
def test_fit_qt1():
    """ Testing FitQt1 interface."""
    # Create a node object
    fit_qt1 = FitQt1()

    # Check if the command is properly defined
    assert fit_qt1.cmd == get_custom_path('fit_qt1')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        fit_qt1.run()

    # Regular test:
    in_file = example_data('TI4D.nii.gz')
    fit_qt1.inputs.source_file = in_file

    cmd_tmp = '{cmd} -source {in_file} -comp {comp} -error {error} -m0map \
{map0} -mcmap {cmap} -res {res} -syn {syn} -t1map {t1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_qt1'),
        in_file=in_file,
        comp=os.path.join(os.getcwd(), 'TI4D_comp.nii.gz'),
        map0=os.path.join(os.getcwd(), 'TI4D_m0map.nii.gz'),
        error=os.path.join(os.getcwd(), 'TI4D_error.nii.gz'),
        cmap=os.path.join(os.getcwd(), 'TI4D_mcmap.nii.gz'),
        res=os.path.join(os.getcwd(), 'TI4D_res.nii.gz'),
        t1map=os.path.join(os.getcwd(), 'TI4D_t1map.nii.gz'),
        syn=os.path.join(os.getcwd(), 'TI4D_syn.nii.gz')
    )

    assert fit_qt1.cmdline == expected_cmd

    # Runs T1 fitting to inversion and saturation recovery data (NLSQR)
    fit_qt1_2 = FitQt1(tis=[1, 2, 5], ir_flag=True)
    in_file = example_data('TI4D.nii.gz')
    fit_qt1_2.inputs.source_file = in_file

    cmd_tmp = '{cmd} -source {in_file} -IR -TIs 1.0 2.0 5.0 \
-comp {comp} -error {error} -m0map {map0} -mcmap {cmap} -res {res} \
-syn {syn} -t1map {t1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_qt1'),
        in_file=in_file,
        comp=os.path.join(os.getcwd(), 'TI4D_comp.nii.gz'),
        map0=os.path.join(os.getcwd(), 'TI4D_m0map.nii.gz'),
        error=os.path.join(os.getcwd(), 'TI4D_error.nii.gz'),
        cmap=os.path.join(os.getcwd(), 'TI4D_mcmap.nii.gz'),
        res=os.path.join(os.getcwd(), 'TI4D_res.nii.gz'),
        t1map=os.path.join(os.getcwd(), 'TI4D_t1map.nii.gz'),
        syn=os.path.join(os.getcwd(), 'TI4D_syn.nii.gz')
    )

    assert fit_qt1_2.cmdline == expected_cmd

    # Runs T1 fitting to spoiled gradient echo (SPGR) data (NLSQR)
    fit_qt1_3 = FitQt1(flips=[2, 4, 8], spgr=True)
    in_file = example_data('TI4D.nii.gz')
    fit_qt1_3.inputs.source_file = in_file

    cmd_tmp = '{cmd} -source {in_file} -comp {comp} -error {error} \
-flips 2.0 4.0 8.0 -m0map {map0} -mcmap {cmap} -res {res} -SPGR -syn {syn} \
-t1map {t1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_qt1'),
        in_file=in_file,
        comp=os.path.join(os.getcwd(), 'TI4D_comp.nii.gz'),
        map0=os.path.join(os.getcwd(), 'TI4D_m0map.nii.gz'),
        error=os.path.join(os.getcwd(), 'TI4D_error.nii.gz'),
        cmap=os.path.join(os.getcwd(), 'TI4D_mcmap.nii.gz'),
        res=os.path.join(os.getcwd(), 'TI4D_res.nii.gz'),
        t1map=os.path.join(os.getcwd(), 'TI4D_t1map.nii.gz'),
        syn=os.path.join(os.getcwd(), 'TI4D_syn.nii.gz')
    )

    assert fit_qt1_3.cmdline == expected_cmd
