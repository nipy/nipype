#-------------------------------------------------------------------------------
#
#  Copyright (c) 2010, Enthought, Inc.
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



""" Test whether HasTraits objects with cycles can be garbage collected.
"""

# Standard library imports
import unittest

# Enthought library imports
from traits.api import HasTraits, Instance, Int

class TestCase(unittest.TestCase):
    """ Tests the 'target' argument for on_traits_change. """

    def test_simple(self):
        """ Tests a simple dynamic trait change handler. """
        class Test(HasTraits):
            i = Int

        # Create objects
        obj = Test()
        target = HasTraits()

        # Set up to count changes in i
        self.count = 0
        def count_notifies():
            self.count += 1
        obj.on_trait_change(count_notifies, "i", target=target)

        # Change the trait
        obj.i = 10
        # Delete the target and change it again
        del target
        obj.i = 0
        # The count should be 1
        self.assertEqual(self.count, 1)

    def test_extended(self):
        """ Tests a dynamic trait change handler using extended names. """

        class Child(HasTraits):
            i = Int

        class Parent(HasTraits):
            child = Instance(Child)

        # Create objects
        parent = Parent(child=Child())
        target = HasTraits()

        # Set up to count changes in i
        self.count = 0
        def count_notifies():
            self.count += 1
        parent.on_trait_change(count_notifies, "child:i", target=target)

        # Change the trait
        parent.child.i = 10
        # Delete the target and change it again
        del target
        parent.child.i = 0
        # The count should be 1
        self.assertEqual(self.count, 1)

if __name__ == '__main__':
    unittest.main()








