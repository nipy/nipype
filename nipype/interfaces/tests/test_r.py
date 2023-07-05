# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
from nipype.interfaces import r

no_r = r.no_r


@pytest.mark.skipif(no_r, reason="R is not available")
def test_cmdline(tmp_path):
    default_script_file = str(tmp_path / "testscript")
    ri = r.RCommand(script="1 + 1", script_file=default_script_file, rfile=False)
    r_cmd = r.get_r_command()

    assert ri.cmdline == r_cmd + (' -e "1 + 1"')

    assert ri.inputs.script == "1 + 1"
    assert ri.inputs.script_file == default_script_file
    assert not os.path.exists(ri.inputs.script_file), "scriptfile should not exist"
    assert not os.path.exists(
        default_script_file
    ), "default scriptfile should not exist."


@pytest.mark.skipif(no_r, reason="R is not available")
def test_run_interface(tmpdir):
    cwd = tmpdir.chdir()
    default_script_file = r.RInputSpec().script_file

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
    cwd.chdir()


@pytest.mark.skipif(no_r, reason="R is not available")
def test_set_rcmd(tmpdir):
    cwd = tmpdir.chdir()
    default_script_file = r.RInputSpec().script_file

    ri = r.RCommand()
    _default_r_cmd = ri._cmd
    ri.set_default_r_cmd("foo")
    assert not os.path.exists(default_script_file), "scriptfile should not exist."
    assert ri._cmd == "foo"
    ri.set_default_r_cmd(_default_r_cmd)
    cwd.chdir()
