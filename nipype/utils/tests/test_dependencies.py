"""Tests for dependency inspection command arguments."""

from unittest import mock

import pytest

from nipype.utils import filemanip


@pytest.mark.parametrize(
    "platform, tool_args",
    [("darwin", ["otool", "-L"]), ("linux", ["ldd"])],
)
@pytest.mark.parametrize("returncode", [0, 1])
def test_get_dependencies_passes_resolved_path_without_shell(
    platform, tool_args, returncode
):
    name = "imaging tool;literal"
    executable = "/tmp/Imaging Tools/imaging tool;literal"
    environ = {"PATH": "/tmp/Imaging Tools"}
    process = mock.Mock()
    process.stdout = b"dependencies\n"
    process.returncode = returncode
    with (
        mock.patch.object(filemanip.sys, "platform", platform),
        mock.patch.object(filemanip, "which", return_value=executable) as which,
        mock.patch.object(filemanip.sp, "run", return_value=process) as run,
    ):
        result = filemanip.get_dependencies(name, environ)

    which.assert_called_once_with(name, env=environ)
    run.assert_called_once_with(
        tool_args + [executable],
        stdout=filemanip.sp.PIPE,
        stderr=filemanip.sp.PIPE,
        shell=False,
        env=environ,
        check=False,
    )
    assert result == b"dependencies"


@pytest.mark.parametrize("missing", [False, True])
def test_get_dependencies_preserves_failure_result(missing):
    executable = None if missing else "/tmp/Imaging Tools/tool"
    with (
        mock.patch.object(filemanip.sys, "platform", "linux"),
        mock.patch.object(filemanip, "which", return_value=executable),
        mock.patch.object(
            filemanip.sp, "run", side_effect=OSError("unavailable")
        ) as run,
    ):
        result = filemanip.get_dependencies("tool", {})

    command = ["ldd"] if missing else ["ldd", executable]
    assert result == f"{command!r} failed"
    assert run.call_count == (0 if missing else 1)
