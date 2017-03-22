# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyseg import no_niftyseg, get_custom_path, EM
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyseg(cmd='seg_EM'))
def test_seg_em():

    # Create a node object
    seg_em = EM()

    # Check if the command is properly defined
    assert seg_em.cmd == get_custom_path('seg_EM')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        seg_em.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    seg_em.inputs.in_file = in_file
    seg_em.inputs.no_prior = 4

    cmd_tmp = '{cmd} -in {in_file} -nopriors 4 -bc_out {bc_out} -out \
{out_file} -out_outlier {out_outlier}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('seg_EM'),
        in_file=in_file,
        out_file=os.path.join(os.getcwd(), 'im1_em.nii'),
        bc_out=os.path.join(os.getcwd(), 'im1_bc_em.nii'),
        out_outlier=os.path.join(os.getcwd(), 'im1_outlier_em.nii'))

    assert seg_em.cmdline == expected_cmd
