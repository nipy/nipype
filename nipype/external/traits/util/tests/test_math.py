#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#------------------------------------------------------------------------------
import unittest

import numpy
import traits.util.math as M


class test_math(unittest.TestCase):

    def test_is_monotonic(self):
        a = numpy.array((1,2,3,4,5,6,7))
        self.assert_(M.is_monotonic(a) == True)
        a = numpy.array((1,2,3,-1000,5,6,7))
        self.assert_(M.is_monotonic(a) == False)
        a = numpy.array((1))
        self.assert_(M.is_monotonic(a) == False)

    def test_brange(self):
        a = numpy.arange(1,5,1)
        b = M.brange(1,4,1)
        self.assert_(numpy.allclose(a, b))


if __name__ == "__main__":
    unittest.main()
