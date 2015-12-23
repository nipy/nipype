#!/usr/bin/env python

from future import standard_library
standard_library.install_aliases()

import unittest
import sys
from contextlib import contextmanager

from nipype.external.six import PY2, PY3, StringIO
from nipype.utils import nipype_cmd


@contextmanager
def capture_sys_output():
    caputure_out, capture_err = StringIO(), StringIO()
    current_out, current_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = caputure_out, capture_err
        yield caputure_out, capture_err
    finally:
        sys.stdout, sys.stderr = current_out, current_err


class TestNipypeCMD(unittest.TestCase):

    def test_main_returns_2_on_empty(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd'])

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)

        if PY2:
            self.assertEqual(stderr.getvalue(),
                             """usage: nipype_cmd [-h] module interface
nipype_cmd: error: too few arguments
""")
        elif PY3:
            self.assertEqual(stderr.getvalue(),
                             """usage: nipype_cmd [-h] module interface
nipype_cmd: error: the following arguments are required: module, interface
""")

        self.assertEqual(stdout.getvalue(), '')

    def test_main_returns_0_on_help(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', '-h'])

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(),
                         """usage: nipype_cmd [-h] module interface

Nipype interface runner

positional arguments:
  module      Module name
  interface   Interface name

optional arguments:
  -h, --help  show this help message and exit
""")

    def test_list_nipy_interfacesp(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy'])

        # repeat twice in case nipy raises warnings
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy'])
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)

        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(),
                         """Available Interfaces:
	ComputeMask
	EstimateContrast
	FitGLM
	FmriRealign4d
	Similarity
	SpaceTimeRealigner
""")

    def test_run_4d_realign_without_arguments(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy', 'FmriRealign4d'])

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)

        error_message = """usage: nipype_cmd nipype.interfaces.nipy FmriRealign4d [-h]
                                                       [--between_loops [BETWEEN_LOOPS [BETWEEN_LOOPS ...]]]
                                                       [--ignore_exception]
                                                       [--loops [LOOPS [LOOPS ...]]]
                                                       [--slice_order SLICE_ORDER]
                                                       [--speedup [SPEEDUP [SPEEDUP ...]]]
                                                       [--start START]
                                                       [--time_interp TIME_INTERP]
                                                       [--tr_slices TR_SLICES]
                                                       in_file [in_file ...]
                                                       tr"""

        if PY2:
            error_message += """
nipype_cmd nipype.interfaces.nipy FmriRealign4d: error: too few arguments
"""
        elif PY3:
            error_message += """
nipype_cmd nipype.interfaces.nipy FmriRealign4d: error: the following arguments are required: in_file, tr
"""

        self.assertEqual(stderr.getvalue(), error_message)
        self.assertEqual(stdout.getvalue(), '')

    def test_run_4d_realign_help(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy', 'FmriRealign4d', '-h'])

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)

        self.assertEqual(stderr.getvalue(), '')
        self.assertTrue("Run FmriRealign4d" in stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
