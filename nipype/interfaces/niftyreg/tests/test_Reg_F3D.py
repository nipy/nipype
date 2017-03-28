# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import no_niftyreg, get_custom_path, RegF3D
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyreg(cmd='reg_f3d'))
def test_reg_f3d():

    # Create a reg_f3d object
    nr = RegF3D()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_f3d')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    rmask_file = example_data('mask.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.rmask_file = rmask_file
    nr.inputs.omp_core_val = 4
    nr.inputs.vel_flag = True
    nr.inputs.be_val = 0.1
    nr.inputs.le_val = 0.1

    cmd_tmp = '{cmd} -be 0.100000 -cpp {cpp} -flo {flo} -le 0.100000 -omp 4 \
-ref {ref} -res {res} -rmask {rmask} -vel'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_f3d'),
        cpp=os.path.join(os.getcwd(), 'im2_cpp.nii.gz'),
        flo=flo_file,
        ref=ref_file,
        res=os.path.join(os.getcwd(), 'im2_res.nii.gz'),
        rmask=rmask_file)

    assert nr.cmdline == expected_cmd
