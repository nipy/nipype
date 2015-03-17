#!/usr/bin/env python

from StringIO import StringIO
import unittest, sys
from nipype.utils import nipype_cmd
from contextlib import contextmanager

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
        
        self.assertEqual(stderr.getvalue(), 
"""usage: runfiles.py [-h] module interface
runfiles.py: error: too few arguments
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
"""usage: runfiles.py [-h] module interface\n\nNipype interface runner

positional arguments:
  module      Module name
  interface   Interface name

optional arguments:
  -h, --help  show this help message and exit
""")

if __name__ == '__main__':
    unittest.main()