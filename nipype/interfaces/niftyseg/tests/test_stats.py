# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import pytest

from ....testing import example_data
from ...niftyreg import get_custom_path
from ...niftyreg.tests.test_regutils import no_nifty_tool
from .. import UnaryStats, BinaryStats


@pytest.mark.skipif(no_nifty_tool(cmd="seg_stats"), reason="niftyseg is not installed")
def test_unary_stats():
    """Test for the seg_stats interfaces"""
    # Create a node object
    unarys = UnaryStats()

    # Check if the command is properly defined
    cmd = get_custom_path("seg_stats", env_dir="NIFTYSEGDIR")
    assert unarys.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        unarys.run()

    # Assign some input data
    in_file = example_data("im1.nii")
    unarys.inputs.in_file = in_file
    unarys.inputs.operation = "a"

    expected_cmd = f"{cmd} {in_file} -a"

    assert unarys.cmdline == expected_cmd


@pytest.mark.skipif(no_nifty_tool(cmd="seg_stats"), reason="niftyseg is not installed")
def test_binary_stats():
    """Test for the seg_stats interfaces"""
    # Create a node object
    binarys = BinaryStats()

    # Check if the command is properly defined
    cmd = get_custom_path("seg_stats", env_dir="NIFTYSEGDIR")
    assert binarys.cmd == cmd

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        binarys.run()

    # Assign some input data
    in_file = example_data("im1.nii")
    binarys.inputs.in_file = in_file
    binarys.inputs.operand_value = 2
    binarys.inputs.operation = "sa"

    expected_cmd = f"{cmd} {in_file} -sa 2.00000000"

    assert binarys.cmdline == expected_cmd
