#!/usr/bin/env python
import pytest
import sys
from contextlib import contextmanager

from io import StringIO
from ...utils import nipype_cmd


@contextmanager
def capture_sys_output():
    caputure_out, capture_err = StringIO(), StringIO()
    current_out, current_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = caputure_out, capture_err
        yield caputure_out, capture_err
    finally:
        sys.stdout, sys.stderr = current_out, current_err


class TestNipypeCMD:
    maxDiff = None

    def test_main_returns_2_on_empty(self):
        with pytest.raises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(["nipype_cmd"])

        exit_exception = cm.value
        assert exit_exception.code == 2

        msg = """usage: nipype_cmd [-h] module interface
nipype_cmd: error: the following arguments are required: module, interface
"""

        assert stderr.getvalue() == msg
        assert stdout.getvalue() == ""

    def test_main_returns_0_on_help(self):
        with pytest.raises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(["nipype_cmd", "-h"])

        exit_exception = cm.value
        assert exit_exception.code == 0

        assert stderr.getvalue() == ""
        if sys.version_info >= (3, 10):
            options = "options"
        else:
            options = "optional arguments"
        assert (
            stdout.getvalue()
            == f"""usage: nipype_cmd [-h] module interface

Nipype interface runner

positional arguments:
  module      Module name
  interface   Interface name

{options}:
  -h, --help  show this help message and exit
"""
        )

    def test_list_nipy_interfacesp(self):
        with pytest.raises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(["nipype_cmd", "nipype.interfaces.nipy"])

        # repeat twice in case nipy raises warnings
        with pytest.raises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(["nipype_cmd", "nipype.interfaces.nipy"])
        exit_exception = cm.value
        assert exit_exception.code == 0

        assert stderr.getvalue() == ""
        assert (
            stdout.getvalue()
            == """Available Interfaces:
\tComputeMask
\tEstimateContrast
\tFitGLM
\tSimilarity
\tSpaceTimeRealigner
"""
        )
