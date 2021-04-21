# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The testing directory contains a small set of imaging files to be
used for doctests only.
"""

import os

# Discover directory path
filepath = os.path.abspath(__file__)
basedir = os.path.dirname(filepath)

funcfile = os.path.join(basedir, "data", "functional.nii")
anatfile = os.path.join(basedir, "data", "structural.nii")
template = funcfile
transfm = funcfile

from . import decorators
from .utils import package_check, TempFATFS

skipif = decorators.dec.skipif


def example_data(infile="functional.nii"):
    """returns path to empty example data files for doc tests
    it will raise an exception if filename is not in the directory"""

    filepath = os.path.abspath(__file__)
    basedir = os.path.dirname(filepath)
    outfile = os.path.join(basedir, "data", infile)
    if not os.path.exists(outfile):
        raise IOError("%s empty data file does NOT exist" % outfile)

    return outfile
