# -*- coding: utf-8 -*-
import os
import shlex

import pytest

from ..synth import SynthMorphApply, SynthMorphReg, SynthSeg, SynthStrip
from ....interfaces.base import isdefined


@pytest.fixture
def nifti(tmp_path):
    """Two empty files in the working directory, referred to by relative name."""
    os.chdir(tmp_path)
    for name in ("moving.nii", "fixed.nii"):
        (tmp_path / name).write_bytes(b"")
    return "moving.nii", "fixed.nii"


def _args(interface):
    return shlex.split(interface.cmdline)


def test_synthstrip_cmdline(nifti):
    node = SynthStrip(in_file=nifti[0], mask_file="mask.nii", border=2, no_csf=True)
    assert _args(node) == [
        "mri_synthstrip",
        "-b",
        "2.00",
        "-i",
        "moving.nii",
        "-m",
        "mask.nii",
        "--no-csf",
        "-o",
        "moving_brain.nii",
    ]
    outputs = node._list_outputs()
    assert outputs["mask_file"] == os.path.abspath("mask.nii")
    assert outputs["out_file"] == os.path.abspath("moving_brain.nii")


def test_synthstrip_gpu_threads_exclusive(nifti):
    with pytest.raises(Exception):
        SynthStrip(in_file=nifti[0], use_gpu=True, num_threads=2).cmdline


def test_synthseg_cmdline(nifti):
    node = SynthSeg(
        in_file=nifti[0], parcellation=True, crop=[160, 160, 160], volume_file="v.csv"
    )
    assert _args(node) == [
        "mri_synthseg",
        "--crop",
        "160",
        "160",
        "160",
        "--i",
        "moving.nii",
        "--o",
        "moving_segmentation.nii",
        "--parc",
        "--cpu",
        "--vol",
        "v.csv",
    ]
    outputs = node._list_outputs()
    assert outputs["volume_file"] == os.path.abspath("v.csv")
    assert not isdefined(outputs.get("qc_file", None))


@pytest.mark.parametrize(
    "model, ext", [("joint", ".nii.gz"), ("deform", ".nii.gz"), ("rigid", ".lta")]
)
def test_synthmorph_reg_default_transforms(nifti, tmp_path, model, ext):
    node = SynthMorphReg(in_file=nifti[0], reference=nifti[1], model=model)
    outputs = node._list_outputs()
    assert outputs["warp_file"] == str(tmp_path / f"moving_warp_file{ext}")
    assert outputs["inv_warp_file"] == str(tmp_path / f"moving_inv_warp_file{ext}")
    args = _args(node)
    assert args[:2] == ["mri_synthmorph", "register"]
    assert args[-2:] == [nifti[0], nifti[1]]
    assert args[args.index("-m") + 1] == model
    assert args[args.index("-t") + 1] == outputs["warp_file"]
    assert args[args.index("-T") + 1] == outputs["inv_warp_file"]


def test_synthmorph_reg_user_transform(nifti, tmp_path):
    node = SynthMorphReg(in_file=nifti[0], reference=nifti[1], warp_file="w.nii.gz")
    assert node._list_outputs()["warp_file"] == str(tmp_path / "w.nii.gz")


def test_synthmorph_apply_cmdline(nifti):
    node = SynthMorphApply(
        warp_file=nifti[1], in_file=nifti[0], method="nearest", out_type="uint8"
    )
    assert _args(node) == [
        "mri_synthmorph",
        "apply",
        "-m",
        "nearest",
        "-t",
        "uint8",
        "fixed.nii",
        "moving.nii",
        "moving_registered.nii",
    ]


def test_synthseg_cpu_by_default_gpu_on_request(nifti):
    assert "--cpu" in _args(SynthSeg(in_file=nifti[0]))
    assert "--cpu" not in _args(SynthSeg(in_file=nifti[0], use_gpu=True))
    args = _args(SynthSeg(in_file=nifti[0], num_threads=4))
    assert args[args.index("--threads") + 1] == "4"
    assert "--cpu" in args


@pytest.mark.parametrize(
    "interface, flag, kwargs",
    [
        (SynthStrip, "--gpu", {}),
        (SynthMorphReg, "-g", {"reference": "fixed.nii"}),
    ],
)
def test_gpu_is_opt_in(nifti, interface, flag, kwargs):
    assert flag not in _args(interface(in_file=nifti[0], **kwargs))
    assert flag in _args(interface(in_file=nifti[0], use_gpu=True, **kwargs))
