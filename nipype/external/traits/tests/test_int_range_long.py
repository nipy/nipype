#-------------------------------------------------------------------------------
#
#  Copyright (c) 2007, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in /LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import unittest

from ..api import HasTraits, Int, Range, Long, TraitError

class A(HasTraits):
    i = Int
    l = Long
    r = Range(2L, 9223372036854775807L)


class TraitIntRangeLong(unittest.TestCase):
    def test_int(self):
        "Test to make sure it is illegal to set an Int trait to a long value"
        a = A()
        a.i = 1
        self.assertRaises(TraitError, a.set, i=10L)

    def test_long(self):
        "Test if it is legal to set a Long trait to an int value"
        a = A()
        a.l = 10
        a.l = 100L

    def test_range(self):
        "Test a range trait with longs being set to an int value"
        a = A()
        a.r = 256
        a.r = 20L
        self.assertRaises(TraitError, a.set, r=1L)
        self.assertRaises(TraitError, a.set, r=9223372036854775808L)

if __name__ == '__main__':
    unittest.main()
