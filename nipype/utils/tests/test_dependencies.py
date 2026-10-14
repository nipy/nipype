"""Tests for dependency inspection command arguments."""

from unittest import mock

import pytest

from nipype.utils import filemanip


@pytest.mark.parametrize(
    "platform, tool_args",
    [("darwin", ["otool", "-L"]), ("linux", ["ldd"])],
)
def test_get_dependencies_passes_resolved_path_without_shell(platform, tool_args):
    name = "imaging tool;literal"
    executable = "/tmp/Imaging Tools/imaging tool;literal"
    environ = {"PATH": "/tmp/Imaging Tools"}
    process = mock.Mock()
    process.communicate.return_value = (b"dependencies\n", b"")
    with (
        mock.patch.object(filemanip.sys, "platform", platform),
        mock.patch.object(filemanip, "which", return_value=executable) as which,
        mock.patch.object(filemanip.sp, "Popen", return_value=process) as popen,
    ):
        result = filemanip.get_dependencies(name, environ)

    which.assert_called_once_with(name, env=environ)
    popen.assert_called_once_with(
        tool_args + [executable],
        stdout=filemanip.sp.PIPE,
        stderr=filemanip.sp.PIPE,
        shell=False,
        env=environ,
    )
    assert result == b"dependencies"
