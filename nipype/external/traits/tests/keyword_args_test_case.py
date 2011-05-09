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

from ..api import HasTraits, Instance, Int

import unittest

class Bar(HasTraits):
    b = Int(3)

class Foo(HasTraits):
   bar = Instance(Bar)

class KeyWordArgsTest(unittest.TestCase):
   def test_using_kw(self):
      bar = Bar(b=5)
      foo = Foo(bar=bar)
      self.assertEqual(foo.bar.b, 5)

   def test_not_using_kw(self):
      foo = Foo()
      self.assertEqual(foo.bar, None)
