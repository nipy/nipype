# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
import nipype.interfaces.matlab as mlab

matlab_cmd = mlab.get_matlab_command()
no_matlab = matlab_cmd is None
if not no_matlab:
    mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


def clean_workspace_and_get_default_script_file():
    # Make sure things are clean.
    default_script_file = mlab.MatlabInputSpec().script_file
    if os.path.exists(default_script_file):
        os.remove(
            default_script_file
        )  # raise Exception('Default script file needed for tests; please remove %s!' % default_script_file)
    return default_script_file


@pytest.mark.skipif(no_matlab, reason="matlab is not available")
def test_cmdline():
    default_script_file = clean_workspace_and_get_default_script_file()

    mi = mlab.MatlabCommand(script="whos", script_file="testscript", mfile=False)

    assert mi.cmdline == matlab_cmd + (
        ' -nodesktop -nosplash -singleCompThread -r "fprintf(1,'
        "'Executing code at %s:\\n',datestr(now));ver,try,"
        "whos,catch ME,fprintf(2,'MATLAB code threw an "
        "exception:\\n');fprintf(2,'%s\\n',ME.message);if "
        "length(ME.stack) ~= 0, fprintf(2,'File:%s\\nName:%s\\n"
        "Line:%d\\n',ME.stack.file,ME.stack.name,"
        'ME.stack.line);, end;end;;exit"'
    )

    assert mi.inputs.script == "whos"
    assert mi.inputs.script_file == "testscript"
    assert not os.path.exists(mi.inputs.script_file), "scriptfile should not exist"
    assert not os.path.exists(
        default_script_file
    ), "default scriptfile should not exist."


@pytest.mark.skipif(no_matlab, reason="matlab is not available")
def test_mlab_inputspec():
    default_script_file = clean_workspace_and_get_default_script_file()
    spec = mlab.MatlabInputSpec()
    for k in [
        "paths",
        "script",
        "nosplash",
        "mfile",
        "logfile",
        "script_file",
        "nodesktop",
    ]:
        assert k in spec.copyable_trait_names()
    assert spec.nodesktop
    assert spec.nosplash
    assert spec.mfile
    assert spec.script_file == default_script_file


@pytest.mark.skipif(no_matlab, reason="matlab is not available")
def test_mlab_init():
    default_script_file = clean_workspace_and_get_default_script_file()

    assert mlab.MatlabCommand._cmd == "matlab"
    assert mlab.MatlabCommand.input_spec == mlab.MatlabInputSpec

    assert mlab.MatlabCommand().cmd == matlab_cmd
    mc = mlab.MatlabCommand(matlab_cmd="foo_m")
    assert mc.cmd == "foo_m"


@pytest.mark.skipif(no_matlab, reason="matlab is not available")
def test_run_interface(tmpdir):
    default_script_file = clean_workspace_and_get_default_script_file()

    mc = mlab.MatlabCommand(matlab_cmd="foo_m")
    assert not os.path.exists(default_script_file), "scriptfile should not exist 1."
    with pytest.raises(ValueError):
        mc.run()  # script is mandatory
    assert not os.path.exists(default_script_file), "scriptfile should not exist 2."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    mc.inputs.script = "a=1;"
    assert not os.path.exists(default_script_file), "scriptfile should not exist 3."
    with pytest.raises(IOError):
        mc.run()  # foo_m is not an executable
    assert os.path.exists(default_script_file), "scriptfile should exist 3."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    cwd = tmpdir.chdir()

    # bypasses ubuntu dash issue
    mc = mlab.MatlabCommand(script="foo;", paths=[tmpdir.strpath], mfile=True)
    assert not os.path.exists(default_script_file), "scriptfile should not exist 4."
    with pytest.raises(OSError):
        mc.run()
    assert os.path.exists(default_script_file), "scriptfile should exist 4."
    if os.path.exists(default_script_file):  # cleanup
        os.remove(default_script_file)

    # bypasses ubuntu dash issue
    res = mlab.MatlabCommand(script="a=1;", paths=[tmpdir.strpath], mfile=True).run()
    assert res.runtime.returncode == 0
    assert os.path.exists(default_script_file), "scriptfile should exist 5."
    cwd.chdir()


@pytest.mark.skipif(no_matlab, reason="matlab is not available")
def test_set_matlabcmd():
    default_script_file = clean_workspace_and_get_default_script_file()

    mi = mlab.MatlabCommand()
    mi.set_default_matlab_cmd("foo")
    assert not os.path.exists(default_script_file), "scriptfile should not exist."
    assert mi._default_matlab_cmd == "foo"
    mi.set_default_matlab_cmd(matlab_cmd)
