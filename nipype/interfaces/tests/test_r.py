# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
from nipype.interfaces import r

no_r = r.no_r


def clean_workspace_and_get_default_script_file():
    # Make sure things are clean.
    default_script_file = r.RInputSpec().script_file
    if os.path.exists(default_script_file):
        os.remove(
            default_script_file
        )  # raise Exception('Default script file needed for tests; please remove %s!' % default_script_file)
    return default_script_file


@pytest.mark.skipif(no_r, reason="R is not available")
def test_cmdline():
    default_script_file = clean_workspace_and_get_default_script_file()

    ri = r.RCommand(script="1 + 1", script_file="testscript", rfile=False)

    assert ri.cmdline == r_cmd + (
        ' -e "1 + 1"'
    )

    assert ri.inputs.script == "1 + 1"
    assert ri.inputs.script_file == "testscript"
    assert not os.path.exists(ri.inputs.script_file), "scriptfile should not exist"
    assert not os.path.exists(
        default_script_file
    ), "default scriptfile should not exist."

@pytest.mark.skipif(no_r, reason="R is not available")
def test_r_init():
    default_script_file = clean_workspace_and_get_default_script_file()

    assert r.RCommand._cmd == "R"
    assert r.RCommand.input_spec == r.RInputSpec

    assert r.RCommand().cmd == r_cmd
    rc = r.RCommand(r_cmd="foo_m")
    assert rc.cmd == "foo_m"


@pytest.mark.skipif(no_r, reason="R is not available")
def test_run_interface(tmpdir):
    default_script_file = clean_workspace_and_get_default_script_file()

    rc = r.RCommand(r_cmd="foo_m")
    assert not os.path.exists(default_script_file), "scriptfile should not exist 1."
    with pytest.raises(ValueError):
        rc.run()  # script is mandatory
    assert not os.path.exists(default_script_file), "scriptfile should not exist 2."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    rc.inputs.script = "a=1;"
    assert not os.path.exists(default_script_file), "scriptfile should not exist 3."
    with pytest.raises(IOError):
        rc.run()  # foo_m is not an executable
    assert os.path.exists(default_script_file), "scriptfile should exist 3."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    cwd = tmpdir.chdir()

    # bypasses ubuntu dash issue
    rc = r.RCommand(script="foo;", rfile=True)
    assert not os.path.exists(default_script_file), "scriptfile should not exist 4."
    with pytest.raises(RuntimeError):
        rc.run()
    assert os.path.exists(default_script_file), "scriptfile should exist 4."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    # bypasses ubuntu dash issue
    res = r.RCommand(script="a=1;", rfile=True).run()
    assert res.runtime.returncode == 0
    assert os.path.exists(default_script_file), "scriptfile should exist 5."
    cwd.chdir()


@pytest.mark.skipif(no_r, reason="R is not available")
def test_set_rcmd():
    default_script_file = clean_workspace_and_get_default_script_file()

    ri = r.RCommand()
    _default_r_cmd = ri._default_r_cmd
    ri.set_default_r_cmd("foo")
    assert not os.path.exists(default_script_file), "scriptfile should not exist."
    assert ri._default_r_cmd == "foo"
    ri.set_default_r_cmd(_default_r_cmd)
