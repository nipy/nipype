# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from ...niftyreg import get_custom_path

from ..asl import FitAsl
from ...niftyreg.tests.test_regutils import no_nifty_tool


@pytest.mark.skipif(
    no_nifty_tool(cmd='fit_asl'), reason="niftyfit is not installed")
def test_fit_asl():
    """ Testing FitAsl interface."""
    # Create the test node
    fit_asl = FitAsl()

    # Check if the command is properly defined
    cmd = get_custom_path('fit_asl', env_dir='NIFTYFIT_DIR')
    assert fit_asl.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        fit_asl.run()

    # Tests on the interface:
    # Runs cbf fitting assuming all tissue is GM!
    in_file = example_data('asl.nii.gz')
    fit_asl.inputs.source_file = in_file

    cmd_tmp = '{cmd} -source {in_file} -cbf {cbf} -error {error} -syn {syn}'
    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        cbf='asl_cbf.nii.gz',
        error='asl_error.nii.gz',
        syn='asl_syn.nii.gz',
    )

    assert fit_asl.cmdline == expected_cmd

    # Runs cbf fitting using IR/SR T1 data to estimate the local T1 and uses
    # the segmentation data to fit tissue specific blood flow parameters
    # (lambda,transit times,T1)
    fit_asl2 = FitAsl(sig=True)
    in_file = example_data('asl.nii.gz')
    t1map = example_data('T1map.nii.gz')
    seg = example_data('segmentation0.nii.gz')
    fit_asl2.inputs.source_file = in_file
    fit_asl2.inputs.t1map = t1map
    fit_asl2.inputs.seg = seg

    cmd_tmp = '{cmd} -source {in_file} -cbf {cbf} -error {error} \
-seg {seg} -sig -syn {syn} -t1map {t1map}'

    expected_cmd = cmd_tmp.format(
        cmd=cmd,
        in_file=in_file,
        t1map=t1map,
        seg=seg,
        cbf='asl_cbf.nii.gz',
        error='asl_error.nii.gz',
        syn='asl_syn.nii.gz',
    )

    assert fit_asl2.cmdline == expected_cmd
