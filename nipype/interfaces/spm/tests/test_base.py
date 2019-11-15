# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import numpy as np

import pytest
from nipype.testing.fixtures import create_files_in_directory

import nipype.interfaces.spm.base as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab
from nipype.interfaces.spm.base import SPMCommandInputSpec
from nipype.interfaces.base import traits

mlab.MatlabCommand.set_default_matlab_cmd(os.getenv("MATLABCMD", "matlab"))


def test_scan_for_fnames(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    names = spm.scans_for_fnames(filelist, keep4d=True)
    assert names[0] == filelist[0]
    assert names[1] == filelist[1]


save_time = False
if not save_time:

    @pytest.mark.skipif(no_spm(), reason="spm is not installed")
    def test_spm_path():
        spm_path = spm.Info.path()
        if spm_path is not None:
            assert isinstance(spm_path, (str, bytes))
            assert "spm" in spm_path.lower()


def test_use_mfile():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    assert dc.inputs.mfile


def test_find_mlab_cmd_defaults():
    saved_env = dict(os.environ)

    class TestClass(spm.SPMCommand):
        pass

    # test without FORCE_SPMMCR, SPMMCRCMD set
    for varname in ["FORCE_SPMMCR", "SPMMCRCMD"]:
        try:
            del os.environ[varname]
        except KeyError:
            pass
    dc = TestClass()
    assert dc._use_mcr is None
    assert dc._matlab_cmd is None
    # test with only FORCE_SPMMCR set
    os.environ["FORCE_SPMMCR"] = "1"
    dc = TestClass()
    assert dc._use_mcr
    assert dc._matlab_cmd is None
    # test with both, FORCE_SPMMCR and SPMMCRCMD set
    os.environ["SPMMCRCMD"] = "spmcmd"
    dc = TestClass()
    assert dc._use_mcr
    assert dc._matlab_cmd == "spmcmd"
    # restore environment
    os.environ.clear()
    os.environ.update(saved_env)


@pytest.mark.skipif(no_spm(), reason="spm is not installed")
def test_cmd_update():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    dc.inputs.matlab_cmd = "foo"
    assert dc.mlab._cmd == "foo"


def test_cmd_update2():
    class TestClass(spm.SPMCommand):
        _jobtype = "jobtype"
        _jobname = "jobname"
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    assert dc.jobtype == "jobtype"
    assert dc.jobname == "jobname"


def test_reformat_dict_for_savemat():
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    out = dc._reformat_dict_for_savemat({"a": {"b": {"c": []}}})
    assert out == [{"a": [{"b": [{"c": []}]}]}]


def test_generate_job(create_files_in_directory):
    class TestClass(spm.SPMCommand):
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    out = dc._generate_job()
    assert out == ""
    # struct array
    contents = {"contents": [1, 2, 3, 4]}
    out = dc._generate_job(contents=contents)
    assert out == (
        ".contents(1) = 1;\n.contents(2) = 2;"
        "\n.contents(3) = 3;\n.contents(4) = 4;\n"
    )
    # cell array of strings
    filelist, outdir = create_files_in_directory
    names = spm.scans_for_fnames(filelist, keep4d=True)
    contents = {"files": names}
    out = dc._generate_job(prefix="test", contents=contents)
    assert out == "test.files = {...\n'a.nii';...\n'b.nii';...\n};\n"
    # string assignment
    contents = "foo"
    out = dc._generate_job(prefix="test", contents=contents)
    assert out == "test = 'foo';\n"
    # cell array of vectors
    contents = {"onsets": np.array((1,), dtype=object)}
    contents["onsets"][0] = [1, 2, 3, 4]
    out = dc._generate_job(prefix="test", contents=contents)
    assert out == "test.onsets = {...\n[1, 2, 3, 4];...\n};\n"


def test_bool():
    class TestClassInputSpec(SPMCommandInputSpec):
        test_in = include_intercept = traits.Bool(field="testfield")

    class TestClass(spm.SPMCommand):
        input_spec = TestClassInputSpec
        _jobtype = "jobtype"
        _jobname = "jobname"

    dc = TestClass()  # dc = derived_class
    dc.inputs.test_in = True
    out = dc._make_matlab_command(dc._parse_inputs())
    assert out.find("jobs{1}.spm.jobtype.jobname.testfield = 1;") > 0, 1
    dc.inputs.use_v8struct = False
    out = dc._make_matlab_command(dc._parse_inputs())
    assert out.find("jobs{1}.jobtype{1}.jobname{1}.testfield = 1;") > 0, 1


def test_make_matlab_command(create_files_in_directory):
    class TestClass(spm.SPMCommand):
        _jobtype = "jobtype"
        _jobname = "jobname"
        input_spec = spm.SPMCommandInputSpec

    dc = TestClass()  # dc = derived_class
    filelist, outdir = create_files_in_directory
    contents = {"contents": [1, 2, 3, 4]}
    script = dc._make_matlab_command([contents])
    assert "jobs{1}.spm.jobtype.jobname.contents(3) = 3;" in script
    dc.inputs.use_v8struct = False
    script = dc._make_matlab_command([contents])
    assert "jobs{1}.jobtype{1}.jobname{1}.contents(3) = 3;" in script
