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

""" Tests to help find out if we can do type-safe casting. """

from __future__ import absolute_import

# Standard library imports.
import unittest

# Enthought library imports.
from ..api import Adapter, HasTraits, Instance, Int, Interface, adapts, implements

# Local imports.
from ..interface_checker import InterfaceError, check_implements

# Make sure implicit interface checking is turned off, so that we can make the
# checks explicitly:
from .. import has_traits
has_traits.CHECK_INTERFACES = 0


class InterfaceCheckerTestCase(unittest.TestCase):
    """ Tests to help find out if we can do type-safe casting. """

    ###########################################################################
    # 'TestCase' interface.
    ###########################################################################

    def setUp(self):
        """ Prepares the test fixture before each test method is called. """

        return

    def tearDown(self):
        """ Called immediately after each test method has been called. """

        return

    ###########################################################################
    # Tests.
    ###########################################################################

    def test_non_traits_class(self):
        """ non-traits class """

        class IFoo(Interface):
            def foo(self):
                pass

        # A class that *does* implement the interface.
        class Foo(object):
            implements(IFoo)

            def foo(self):
                pass

        # The checker will raise an exception if the class does not implement
        # the interface.
        check_implements(Foo, IFoo, 2)

        return

    def test_single_interface(self):
        """ single interface """

        class IFoo(Interface):
            x = Int

        # A class that *does* implement the interface.
        class Foo(HasTraits):
            implements(IFoo)

            x = Int

        # The checker will raise an exception if the class does not implement
        # the interface.
        check_implements(Foo, IFoo, 2)

        return

    def test_single_interface_with_invalid_method_signature(self):
        """ single interface with invalid method signature """

        class IFoo(Interface):
            def foo(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo)

            # Extra argument!
            def foo(self, x):
                pass

        self.failUnlessRaises(InterfaceError, check_implements, Foo, IFoo, 2)

        return

    def test_single_interface_with_missing_trait(self):
        """ single interface with missing trait """

        class IFoo(Interface):
            x = Int

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo)


        self.failUnlessRaises(InterfaceError, check_implements, Foo, IFoo, 2)

        return

    def test_single_interface_with_missing_method(self):
        """ single interface with missing method """

        class IFoo(Interface):
            def method(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo)


        self.failUnlessRaises(InterfaceError, check_implements, Foo, IFoo, 2)

        return

    def test_multiple_interfaces(self):
        """ multiple interfaces """

        class IFoo(Interface):
            x = Int

        class IBar(Interface):
            y = Int

        class IBaz(Interface):
            z = Int

        # A class that *does* implement the interface.
        class Foo(HasTraits):
            implements(IFoo, IBar, IBaz)

            x = Int
            y = Int
            z = Int

        # The checker will raise an exception if the class does not implement
        # the interface.
        check_implements(Foo, [IFoo, IBar, IBaz], 2)

        return

    def test_multiple_interfaces_with_invalid_method_signature(self):
        """ multiple interfaces with invalid method signature """

        class IFoo(Interface):
            def foo(self):
                pass

        class IBar(Interface):
            def bar(self):
                pass

        class IBaz(Interface):
            def baz(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo, IBar, IBaz)

            def foo(self):
                pass

            def bar(self):
                pass

            # Extra argument!
            def baz(self, x):
                pass

        self.failUnlessRaises(
            InterfaceError, check_implements, Foo, [IFoo, IBar, IBaz], 2
        )

        return

    def test_multiple_interfaces_with_missing_trait(self):
        """ multiple interfaces with missing trait """

        class IFoo(Interface):
            x = Int

        class IBar(Interface):
            y = Int

        class IBaz(Interface):
            z = Int

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo, IBar, IBaz)

            x = Int
            y = Int

        self.failUnlessRaises(
            InterfaceError, check_implements, Foo, [IFoo, IBar, IBaz], 2
        )

        return

    def test_multiple_interfaces_with_missing_method(self):
        """ multiple interfaces with missing method """

        class IFoo(Interface):
            def foo(self):
                pass

        class IBar(Interface):
            def bar(self):
                pass

        class IBaz(Interface):
            def baz(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IFoo, IBar, IBaz)

            def foo(self):
                pass

            def bar(self):
                pass

        self.failUnlessRaises(
            InterfaceError, check_implements, Foo, [IFoo, IBar, IBaz], 2
        )

        return

    def test_inherited_interfaces(self):
        """ inherited interfaces """

        class IFoo(Interface):
            x = Int

        class IBar(IFoo):
            y = Int

        class IBaz(IBar):
            z = Int

        # A class that *does* implement the interface.
        class Foo(HasTraits):
            implements(IBaz)

            x = Int
            y = Int
            z = Int

        # The checker will raise an exception if the class does not implement
        # the interface.
        check_implements(Foo, IBaz, 2)

        return

    def test_inherited_interfaces_with_invalid_method_signature(self):
        """ inherited with invalid method signature """

        class IFoo(Interface):
            def foo(self):
                pass

        class IBar(IFoo):
            def bar(self):
                pass

        class IBaz(IBar):
            def baz(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IBaz)

            def foo(self):
                pass

            def bar(self):
                pass

            # Extra argument!
            def baz(self, x):
                pass

        self.failUnlessRaises(InterfaceError, check_implements, Foo, IBaz, 2)

        return

    def test_inherited_interfaces_with_missing_trait(self):
        """ inherited interfaces with missing trait """

        class IFoo(Interface):
            x = Int

        class IBar(IFoo):
            y = Int

        class IBaz(IBar):
            z = Int

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IBaz)

            x = Int
            y = Int

        self.failUnlessRaises(InterfaceError, check_implements, Foo, IBaz, 2)

        return

    def test_inherited_interfaces_with_missing_method(self):
        """ inherited interfaces with missing method """

        class IFoo(Interface):
            def foo(self):
                pass

        class IBar(IFoo):
            def bar(self):
                pass

        class IBaz(IBar):
            def baz(self):
                pass

        # A class that does *not* implement the interface.
        class Foo(HasTraits):
            implements(IBaz)

            def foo(self):
                pass

            def bar(self):
                pass

        self.failUnlessRaises(InterfaceError, check_implements, Foo, IBaz, 2)

        return

    # Make sure interfaces and adaptation etc still work with the 'HasTraits'
    # version of 'Interface'!
    def test_instance(self):
        """ instance """

        class IFoo(Interface):
            pass

        class Foo(HasTraits):
            implements(IFoo)

        class Bar(HasTraits):
            foo = Instance(IFoo)

        b = Bar(foo=Foo())

        return

    def test_callable(self):
        """ callable """

        class IFoo(Interface):
            pass

        class Foo(HasTraits):
            implements(IFoo)

        f = Foo()
        self.assertEqual(f, IFoo(f))

        return

    def test_adaptation(self):
        """ adaptation """

        class IFoo(Interface):
            pass

        class Foo(HasTraits):
            pass

        class FooToIFooAdapter(Adapter):
            adapts(Foo, IFoo)

        f = Foo()

        # Make sure adaptation works.
        i_foo = IFoo(f)

        self.assertNotEqual(None, i_foo)
        self.assertEqual(FooToIFooAdapter, type(i_foo))

        return


# Entry point for stand-alone testing.
if __name__ == '__main__':
    unittest.main()

