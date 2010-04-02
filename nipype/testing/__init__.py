"""Simple utility to pull in all the testing functions we're likely to use.
"""

import numpy as np
from distutils.version import LooseVersion

from nose.tools import (assert_true, assert_false, assert_not_equal,
                        assert_raises)
from nose import SkipTest

from numpy.testing import *
if LooseVersion(np.__version__) >= '1.2':
    from numpy.testing.decorators import *
else:
    from nipype.testing.numpytesting.decorators import *

from utils import *
from enthought.traits.api import TraitError

