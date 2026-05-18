# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Hand-written tests for nipype.interfaces.t1prep.preprocess."""

import os
import sys

import pytest

from nipype.interfaces.t1prep import T1Prep, T1PrepSegment


@pytest.fixture
def in_t1(tmp_path):
    f = tmp_path / "sub-01_T1w.nii.gz"
    f.write_bytes(b"")
    return str(f)


def test_T1Prep_cmd_uses_current_interpreter():
    t = T1Prep()
    assert t.cmd.startswith(sys.executable + " -m t1prep.t1prep")


def test_T1Prep_cmdline(in_t1):
    t = T1Prep()
    t.inputs.in_files = [in_t1]
    t.inputs.bids = True
    t.inputs.out_dir = "/tmp/derivatives"
    assert t.cmdline == (
        f"{sys.executable} -m t1prep.t1prep --bids --out-dir /tmp/derivatives "
        f"{in_t1}"
    )


def test_T1Prep_list_outputs_default_to_input_dir(in_t1):
    t = T1Prep()
    t.inputs.in_files = [in_t1]
    outs = t._list_outputs()
    parent = os.path.dirname(os.path.abspath(in_t1))
    assert outs["out_dir"] == parent
    assert outs["mri_dir"] == os.path.join(parent, "mri")
    assert outs["surf_dir"] == os.path.join(parent, "surf")
    assert outs["report_dir"] == os.path.join(parent, "report")
    assert outs["label_dir"] == os.path.join(parent, "label")


def test_T1Prep_list_outputs_respects_out_dir(in_t1, tmp_path):
    t = T1Prep()
    t.inputs.in_files = [in_t1]
    t.inputs.out_dir = str(tmp_path / "out")
    outs = t._list_outputs()
    assert outs["out_dir"] == str(tmp_path / "out")
    assert outs["mri_dir"] == str(tmp_path / "out" / "mri")


def test_T1Prep_skullstrip_xor(in_t1):
    """Setting both skullstrip_only and skip_skullstrip must raise."""
    t = T1Prep()
    t.inputs.in_files = [in_t1]
    t.inputs.skullstrip_only = True
    with pytest.raises(OSError):
        t.inputs.skip_skullstrip = True


def test_T1PrepSegment_cmd_uses_current_interpreter():
    s = T1PrepSegment()
    assert s.cmd == f"{sys.executable} -m t1prep.segment"


def test_T1PrepSegment_cmdline(in_t1, tmp_path):
    s = T1PrepSegment()
    s.inputs.in_file = in_t1
    s.inputs.mri_dir = str(tmp_path / "mri")
    s.inputs.report_dir = str(tmp_path / "report")
    s.inputs.label_dir = str(tmp_path / "label")
    s.inputs.surf = True
    s.inputs.gz = True
    cmd = s.cmdline
    assert cmd.startswith(f"{sys.executable} -m t1prep.segment ")
    assert "--gz" in cmd
    assert "--surf" in cmd
    assert f"--input {in_t1}" in cmd or f"--input '{in_t1}'" in cmd
    assert "--mri-dir" in cmd
    assert "--report-dir" in cmd
    assert "--label-dir" in cmd


def test_T1PrepSegment_list_outputs_absolute(in_t1, tmp_path):
    s = T1PrepSegment()
    s.inputs.in_file = in_t1
    s.inputs.mri_dir = "mri"
    s.inputs.report_dir = "report"
    s.inputs.label_dir = "label"
    outs = s._list_outputs()
    assert outs["mri_dir"] == os.path.abspath("mri")
    assert outs["report_dir"] == os.path.abspath("report")
    assert outs["label_dir"] == os.path.abspath("label")
