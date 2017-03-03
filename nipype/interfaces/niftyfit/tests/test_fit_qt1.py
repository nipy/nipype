# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.niftyfit import no_niftyfit, get_custom_path, FitQt1
from nipype.testing import skipif, example_data
import os
import pytest


@skipif(no_niftyfit(cmd='fit_qt1'))
def test_fit_qt1():
    # Create a node object
    test_node = FitQt1()

    # Check if the command is properly defined
    assert test_node.cmd == get_custom_path('fit_qt1')

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        test_node.run()

    # Assign some input data
    in_file = example_data('im1.nii')
    test_node.inputs.source_file = in_file

    cmd_tmp = '{cmd} -source {in_file} -comp {comp} -error {error} -m0map \
{map0} -mcmap {cmap} -res {res} -syn {syn} -t1map {t1map}'
    expected_cmd = cmd_tmp.format(
        cmd=get_custom_path('fit_qt1'),
        in_file=in_file,
        comp=os.path.join(os.getcwd(), 'im1_comp.nii.gz'),
        map0=os.path.join(os.getcwd(), 'im1_m0map.nii.gz'),
        error=os.path.join(os.getcwd(), 'im1_error.nii.gz'),
        cmap=os.path.join(os.getcwd(), 'im1_mcmap.nii.gz'),
        res=os.path.join(os.getcwd(), 'im1_res.nii.gz'),
        t1map=os.path.join(os.getcwd(), 'im1_t1map.nii.gz'),
        syn=os.path.join(os.getcwd(), 'im1_syn.nii.gz'))

    assert test_node.cmdline == expected_cmd
