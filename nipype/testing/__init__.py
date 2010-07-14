# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Simple utility to pull in all the testing functions we're likely to use.
"""

import os

import numpy as np
from distutils.version import LooseVersion

from nose.tools import (assert_true, assert_false, assert_not_equal,
                        assert_raises)
from nose import SkipTest, with_setup

if LooseVersion(np.__version__) >= '1.2':
    from numpy.testing import *
    from numpy.testing.decorators import *
else:
    from numpytesting import *
    from numpytesting.decorators import *

from utils import *
from enthought.traits.api import TraitError

# import Fernando's lightunit for parametric tests
from lightunit import ParametricTestCase, parametric

# import datasets for doctests
filepath = os.path.abspath(__file__)
basedir = os.path.dirname(filepath)


funcfile = os.path.join(basedir, 'data', 'functional.nii')
anatfile = funcfile
template = funcfile
transfm = funcfile

def example_data(infile='functional.nii'):
    """returns path to empty example data files for doc tests
    it will raise an exception if filename is not in the directory"""
   
    filepath = os.path.abspath(__file__)
    basedir = os.path.dirname(filepath)
    outfile = os.path.join(basedir, 'data', infile)
    if not os.path.exists(outfile):
        raise IOError('%s empty data file does NOT exist'%(outfile))
    
    return outfile 
