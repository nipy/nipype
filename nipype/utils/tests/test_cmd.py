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
    
    def test_list_nipy_interfacesp(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy'])
        
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)
        
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(),
"""Available Interfaces:
	SpaceTimeRealigner
	Similarity
	ComputeMask
	FitGLM
	EstimateContrast
	FmriRealign4d
""")

    def test_run_4d_realign_without_arguments(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy', 'FmriRealign4d'])
        
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)
        
        self.assertEqual(stderr.getvalue(),
"""usage: nipype_cmd nipype.interfaces.nipy FmriRealign4d [-h]
                                                       [--between_loops BETWEEN_LOOPS]
                                                       [--ignore_exception IGNORE_EXCEPTION]
                                                       [--loops LOOPS]
                                                       [--slice_order SLICE_ORDER]
                                                       [--speedup SPEEDUP]
                                                       [--start START]
                                                       [--time_interp TIME_INTERP]
                                                       [--tr_slices TR_SLICES]
                                                       in_file tr
nipype_cmd nipype.interfaces.nipy FmriRealign4d: error: too few arguments
""")
        self.assertEqual(stdout.getvalue(), '')
        
    def test_run_4d_realign_help(self):
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (stdout, stderr):
                nipype_cmd.main(['nipype_cmd', 'nipype.interfaces.nipy', 'FmriRealign4d', '-h'])
        
        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 0)
        
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(stdout.getvalue(),
"""usage: nipype_cmd nipype.interfaces.nipy FmriRealign4d [-h]
                                                       [--between_loops BETWEEN_LOOPS]
                                                       [--ignore_exception IGNORE_EXCEPTION]
                                                       [--loops LOOPS]
                                                       [--slice_order SLICE_ORDER]
                                                       [--speedup SPEEDUP]
                                                       [--start START]
                                                       [--time_interp TIME_INTERP]
                                                       [--tr_slices TR_SLICES]
                                                       in_file tr

Run FmriRealign4d

positional arguments:
  in_file               File to realign
  tr                    TR in seconds

optional arguments:
  -h, --help            show this help message and exit
  --between_loops BETWEEN_LOOPS
                        loops used to realign different runs
  --ignore_exception IGNORE_EXCEPTION
                        Print an error message instead of throwing an
                        exception in case the interface fails to run
  --loops LOOPS         loops within each run
  --slice_order SLICE_ORDER
                        0 based slice order. This would be equivalent to
                        enteringnp.argsort(spm_slice_order) for this field.
                        This effectsinterleaved acquisition. This field will
                        be deprecated infuture Nipy releases and be replaced
                        by actual sliceacquisition times.
  --speedup SPEEDUP     successive image sub-sampling factors for acceleration
  --start START         time offset into TR to align slices to
  --time_interp TIME_INTERP
                        Assume smooth changes across time e.g., fmri series.
                        If you don't want slice timing correction set this to
                        undefined
  --tr_slices TR_SLICES
                        TR slices
""")


if __name__ == '__main__':
    unittest.main()