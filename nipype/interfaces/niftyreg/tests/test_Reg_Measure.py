# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyreg import (no_niftyreg, get_custom_path,
                                        RegMeasure)
from nipype.testing import skipif, example_data
import pytest
import os


@skipif(no_niftyreg(cmd='reg_measure'))
def test_reg_measure():

    # Create a reg_measure object
    nr = RegMeasure()

    # Check if the command is properly defined
    assert nr.cmd == get_custom_path('reg_measure')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        nr.run()

    # Assign some input data
    ref_file = example_data('im1.nii')
    flo_file = example_data('im2.nii')
    nr.inputs.ref_file = ref_file
    nr.inputs.flo_file = flo_file
    nr.inputs.measure_type = 'lncc'
    nr.inputs.omp_core_val = 4

    cmd_tmp = '{cmd} -flo {flo} -lncc -omp 4 -out {out} -ref {ref}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('reg_measure'),
        flo=flo_file,
        out=os.path.join(os.getcwd(), 'im2_lncc.txt'),
        ref=ref_file)

    assert nr.cmdline == expected_cmd
