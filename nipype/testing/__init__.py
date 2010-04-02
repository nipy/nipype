"""Simple utility to pull in all the testing functions we're likely to use.
"""

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

