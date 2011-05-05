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

from numpy import arange, array

import traits.util.numeric as N


class test_numeric(unittest.TestCase):

    def test_safe_take(self):
        a = array((1,2,3,4,2,2,7))
        b = array((2,2,2))
        indices = array((1,4,5))
        x = N.safe_take(a,indices)
        self.assert_((x == b).all())

        a = 2
        indices = array((0))
        x = N.safe_take(a,indices)
        self.assert_(x == a)

    def test_safe_copy(self):
        a = arange(1,4,1)
        x = N.safe_copy(a)
        self.assert_((x == a).all())

        a = 4.1
        x = N.safe_copy(a)
        self.assert_(x == a)

    def test_safe_min(self):
        a = array((1,2,3,4,5,-6,-7))
        x = N.safe_min(a)
        self.assert_(x == -7)

        a = 5.
        x = N.safe_min(a)
        self.assert_(x == 5.)

    def test_safe_max(self):
        a = array((1,2,3,4,5,-6,-7))
        x = N.safe_max(a)
        self.assert_(x == 5)

        a = 5.
        x = N.safe_max(a)
        self.assert_(x == 5.)

    def test_safe_len(self):
        a = array((1,2,3,4,5,-6,-7))
        x = N.safe_len(a)
        self.assert_(x == 7)

        a = 5.
        x = N.safe_len(a)
        self.assert_(x == 1)


if __name__ == "__main__":
    unittest.main()
