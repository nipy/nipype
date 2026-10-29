# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

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
    assert eddy.cmd == "eddy_correct"

    # test raising error with mandatory args absent
    with pytest.raises(ValueError):
        eddy.run()

    # .inputs based parameters setting
    eddy.inputs.in_file = filelist[0]
    eddy.inputs.out_file = "foo_eddc.nii"
    eddy.inputs.ref_num = 100
    assert eddy.cmdline == "eddy_correct %s foo_eddc.nii 100" % filelist[0]

    # .run based parameter setting
    eddy2 = fsl.EddyCorrect(in_file=filelist[0], out_file="foo_ec.nii", ref_num=20)
    assert eddy2.cmdline == "eddy_correct %s foo_ec.nii 20" % filelist[0]

    # test arguments for opt_map
    # eddy_correct class doesn't have opt_map{}


@pytest.fixture
def eddy_env(monkeypatch):
    """Control the executables on PATH and the FSL version seen by Eddy."""

    def _setup(binaries=(), version=None):
        monkeypatch.setattr(
            fsl, "which", lambda name: f"/fsl/bin/{name}" if name in binaries else None
        )
        monkeypatch.setattr(fsl.Info, "version", staticmethod(lambda: version))

    return _setup


@pytest.mark.parametrize(
    "use_cuda, binaries, expected",
    [
        (True, ("eddy_cuda", "eddy", "eddy_cpu"), "eddy_cuda"),
        (True, ("eddy", "eddy_cpu"), "eddy"),
        (True, (), "eddy"),
        (False, ("eddy_cuda", "eddy", "eddy_cpu", "eddy_openmp"), "eddy_cpu"),
        (False, ("eddy", "eddy_openmp"), "eddy_openmp"),
        (False, ("eddy",), "eddy_openmp"),
    ],
)
def test_eddy_cmd_selection(eddy_env, use_cuda, binaries, expected):
    eddy_env(binaries)
    eddy = fsl.Eddy(use_cuda=use_cuda)
    assert eddy.cmd == expected


def test_eddy_cmd_follows_use_cuda(eddy_env):
    eddy_env(("eddy_cuda", "eddy_cpu"))
    eddy = fsl.Eddy()
    assert eddy.cmd == "eddy_cpu"
    eddy.inputs.use_cuda = True
    assert eddy.cmd == "eddy_cuda"
    eddy.inputs.use_cuda = False
    assert eddy.cmd == "eddy_cpu"


@pytest.mark.parametrize(
    "version, use_cuda, has_nthr",
    [
        ("6.0.7.17", False, True),
        ("6.0.7.8", False, True),
        ("6.0.7.7", False, False),
        ("6.0.5", False, False),
        (None, False, False),
        ("6.0.7.17", True, False),
    ],
)
def test_eddy_nthr(eddy_env, version, use_cuda, has_nthr):
    eddy_env(("eddy_cpu", "eddy_cuda"), version)
    eddy = fsl.Eddy(use_cuda=use_cuda)
    eddy.inputs.num_threads = 4
    if use_cuda:
        assert eddy.inputs.num_threads == 1
    assert (f"--nthr={eddy.inputs.num_threads}" in eddy._parse_inputs()) == has_nthr
    assert eddy.inputs.environ["OMP_NUM_THREADS"] == str(eddy.inputs.num_threads)


def test_eddy_num_threads_not_hashed(eddy_env):
    eddy_env(("eddy_cpu",), "6.0.7.17")
    eddy = fsl.Eddy()
    eddy.inputs.num_threads = 2
    _, hash2 = eddy.inputs.get_hashval()
    eddy.inputs.num_threads = 8
    _, hash8 = eddy.inputs.get_hashval()
    assert hash2 == hash8
