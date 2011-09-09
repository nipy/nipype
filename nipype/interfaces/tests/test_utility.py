# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import shutil
from tempfile import mkdtemp

from nipype.testing import assert_equal, assert_true
from nipype.interfaces import utility

def test_rename():
    tempdir = os.path.realpath(mkdtemp())
    origdir = os.getcwd()
    os.chdir(tempdir)

    # Test very simple rename
    _ = open("file.txt","w").close()
    rn = utility.Rename(in_file="file.txt", format_string="test_file1.txt")
    res = rn.run()
    outfile = os.path.join(tempdir, "test_file1.txt")
    yield assert_equal, res.outputs.out_file, outfile
    yield assert_true, os.path.exists(outfile)

    # Now a string-formatting version
    rn = utility.Rename(in_file="file.txt", format_string="%(field1)s_file%(field2)d",keep_ext=True)
    # Test .input field creation
    yield assert_true, hasattr(rn.inputs, "field1")
    yield assert_true, hasattr(rn.inputs, "field2")
    # Set the inputs
    rn.inputs.field1 = "test"
    rn.inputs.field2 = 2
    res = rn.run()
    outfile = os.path.join(tempdir, "test_file2.txt")
    yield assert_equal, res.outputs.out_file, outfile
    yield assert_true, os.path.exists(outfile)

    # Clean up
    os.chdir(origdir)
    shutil.rmtree(tempdir)
