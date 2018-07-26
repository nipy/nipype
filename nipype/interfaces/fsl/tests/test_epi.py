# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
from nipype.testing.fixtures import create_files_in_directory

import nipype.interfaces.fsl.epi as fsl
from nipype.interfaces.fsl import no_fsl


# test eddy_correct
@pytest.mark.skipif(no_fsl(), reason="fsl is not installed")
def test_eddy_correct2(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    eddy = fsl.EddyCorrect()

    # make sure command gets called
    assert eddy.cmd == 'eddy_correct'

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        eddy.run()

    # .inputs based parameters setting
    eddy.inputs.in_file = filelist[0]
    eddy.inputs.out_file = 'foo_eddc.nii'
    eddy.inputs.ref_num = 100
    assert eddy.cmdline == 'eddy_correct %s foo_eddc.nii 100' % filelist[0]

    # .run based parameter setting
    eddy2 = fsl.EddyCorrect(
        in_file=filelist[0], out_file='foo_ec.nii', ref_num=20)
    assert eddy2.cmdline == 'eddy_correct %s foo_ec.nii 20' % filelist[0]

    # test arguments for opt_map
    # eddy_correct class doesn't have opt_map{}
