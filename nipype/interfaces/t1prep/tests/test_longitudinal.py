# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.longitudinal."""

import os
import sys

import pytest

from nipype.interfaces.t1prep import T1PrepRealignLongitudinal


@pytest.fixture
def in_files(tmp_path):
    paths = []
    for ses in ("01", "02", "03"):
        f = tmp_path / f"sub-01_ses-{ses}_T1w.nii.gz"
        f.write_bytes(b"")
        paths.append(str(f))
    return paths


def test_T1PrepRealignLongitudinal_cmd_uses_current_interpreter():
    ra = T1PrepRealignLongitudinal()
    assert ra.cmd == f"{sys.executable} -m t1prep.realign_longitudinal"


def test_T1PrepRealignLongitudinal_cmdline(in_files, tmp_path):
    ra = T1PrepRealignLongitudinal()
    ra.inputs.in_files = in_files
    ra.inputs.out_dir = str(tmp_path / "out")
    ra.inputs.save_resampled = True
    ra.inputs.iterations = 5
    cmd = ra.cmdline
    assert "--inputs" in cmd
    for p in in_files:
        assert p in cmd
    assert "--out-dir" in cmd
    assert f"{tmp_path}/out" in cmd or f"'{tmp_path}/out'" in cmd
    assert "--save-resampled" in cmd
    assert "--iterations 5" in cmd


def test_T1PrepRealignLongitudinal_list_outputs(in_files, tmp_path):
    ra = T1PrepRealignLongitudinal()
    ra.inputs.in_files = in_files
    ra.inputs.out_dir = "rel/out"
    outs = ra._list_outputs()
    assert outs["out_dir"] == os.path.abspath("rel/out")
