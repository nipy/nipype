#-------------------------------------------------------------------------------
#
#  Unit test case for testing interfaces and adaptation.
#
#  Written by: David C. Morrill
#
#  Date: 4/10/2007
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

""" Unit test case for testing interfaces and adaptation.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import unittest

from ..api import (HasTraits, Interface, Adapter, Instance, Int, List,
        TraitError, AdaptedTo, adapts, implements)

#-------------------------------------------------------------------------------
#  Test 'Interface' definitions:
#-------------------------------------------------------------------------------

class IFoo(Interface):

    def get_foo(self):
        """ Returns the current foo. """

class IFooPlus(IFoo):

    def get_foo_plus(self):
        """ Returns even more foo. """

class IAverage(Interface):

    def get_average(self):
        """ Returns the average value for the object. """

class IList(Interface):

    def get_list(self):
        """ Returns the list value for the object. """

#-------------------------------------------------------------------------------
#  Test 'model' classes:
#-------------------------------------------------------------------------------

class Sample ( HasTraits ):

    s1 = Int( 1, sample = True )
    s2 = Int( 2, sample = True )
    s3 = Int( 3, sample = True )
    i1 = Int( 4 )
    i2 = Int( 5 )
    i3 = Int( 6 )

class SampleList ( HasTraits ):

    implements( IList )

    data = List( Int, [ 10, 20, 30 ] )

    def get_list ( self ):
        return self.data

class SampleAverage ( HasTraits ):

    implements( IList, IAverage )

    data = List( Int, [ 100, 200, 300 ] )

    def get_list ( self ):
        return self.data

    def get_average ( self ):
        value = self.get_list()
        if len( value ) == 0:
            return 0.0

        average = 0.0
        for item in value:
            average += item
        return (average / len( value ))

class SampleBad ( HasTraits ):

    pass

#-------------------------------------------------------------------------------
#  Test interfaces class:
#-------------------------------------------------------------------------------

class TraitsHolder ( HasTraits ):

    a_no      = Instance( IAverage, adapt = 'no' )
    a_yes     = Instance( IAverage, adapt = 'yes' )
    a_default = Instance( IAverage, adapt = 'default' )
    l_yes     = AdaptedTo( IList )
    f_yes     = AdaptedTo( IFoo )
    fp_yes    = AdaptedTo( IFooPlus )

#-------------------------------------------------------------------------------
#  Test 'adapter' definitions:
#-------------------------------------------------------------------------------

class SampleListAdapter ( Adapter ):

    adapts( Sample, IList )

    def get_list ( self ):
        obj = self.adaptee
        return [ getattr( obj, name )
                 for name in obj.trait_names( sample = True ) ]

class ListAverageAdapter ( Adapter ):

    adapts( IList, IAverage )

    def get_average ( self ):
        value = self.adaptee.get_list()
        if len( value ) == 0:
            return 0.0

        average = 0.0
        for item in value:
            average += item
        return (average / len( value ))

class SampleFooAdapter ( HasTraits ):

    adapts( Sample, IFoo )

    object = Instance( Sample )

    def __init__ ( self, object ):
        self.object = object

    def get_foo ( self ):
        object = self.object
        return (object.s1 + object.s2 + object.s3)

class FooPlusAdapter ( object ):

    def __init__ ( self, obj ):
        self.obj = obj

    def get_foo ( self ):
        return self.obj.get_foo()

    def get_foo_plus ( self ):
        return (self.obj.get_foo() + 1)

adapts( FooPlusAdapter, IFoo, IFooPlus )

#-------------------------------------------------------------------------------
#  'InterfacesTest' unit test class:
#-------------------------------------------------------------------------------

class InterfacesTest ( unittest.TestCase ):

    #---------------------------------------------------------------------------
    #  Individual unit test methods:
    #---------------------------------------------------------------------------

    def test_implements_none ( self ):
        class Test ( HasTraits ):
            implements()

    def test_implements_one ( self ):
        class Test ( HasTraits ):
            implements( IFoo )

    def test_implements_multi ( self ):
        class Test ( HasTraits ):
            implements( IFoo, IAverage, IList )

    def test_implements_extended ( self ):
        """ Ensure that subclasses of Interfaces imply the superinterface.
        """
        class Test ( HasTraits ):
            implements( IFooPlus )

        ta = TraitsHolder()
        ta.f_yes = Test()

    def test_implements_bad ( self ):
        self.assertRaises( TraitError, self.implements_bad )

    def test_instance_adapt_no ( self ):
        ta = TraitsHolder()

        # Verify that SampleAverage() does not raise an error (it is an instance
        # of the IAverage interface).
        try:
            ta.a_no = SampleAverage()
        except TraitError:
            self.fail("Setting instance of interface should not require " \
                      "adaptation")

        # These are not instances of the IAverage interface, and therefore
        # cannot be set to the trait.
        self.assertRaises( TraitError, ta.set, a_no = SampleList() )
        self.assertRaises( TraitError, ta.set, a_no = Sample() )
        self.assertRaises( TraitError, ta.set, a_no = SampleBad() )

    def test_instance_adapt_yes ( self ):
        ta = TraitsHolder()

        ta.a_yes = object = SampleAverage()
        self.assertEqual( ta.a_yes.get_average(), 200.0 )
        self.assert_( isinstance( ta.a_yes,  SampleAverage ) )
        self.assertFalse( hasattr(ta, 'a_yes_') )

        ta.a_yes = object = SampleList()
        self.assertEqual( ta.a_yes.get_average(), 20.0 )
        self.assert_( isinstance( ta.a_yes,  ListAverageAdapter ) )
        self.assertFalse( hasattr(ta, 'a_yes_') )

        ta.l_yes = object = Sample()
        result = ta.l_yes.get_list()
        self.assertEqual( len( result ), 3 )
        for n in [ 1, 2, 3 ]:
            self.assert_( n in result )
        self.assert_( isinstance( ta.l_yes,  SampleListAdapter ) )
        self.assertEqual( ta.l_yes_, object )

        ta.a_yes = object = Sample()
        self.assertEqual( ta.a_yes.get_average(), 2.0 )
        self.assert_( isinstance( ta.a_yes, ListAverageAdapter ) )
        self.assertFalse( hasattr(ta, 'a_yes_') )

        self.assertRaises( TraitError, ta.set, a_yes = SampleBad() )

        ta.f_yes = object = Sample()
        self.assertEqual( ta.f_yes.get_foo(), 6 )
        self.assert_( isinstance( ta.f_yes, SampleFooAdapter ) )
        self.assertEqual( ta.f_yes_, object )

        ta.fp_yes = object = Sample( s1 = 5, s2 = 10, s3 = 15 )
        self.assertEqual( ta.fp_yes.get_foo(), 30 )
        self.assertEqual( ta.fp_yes.get_foo_plus(), 31 )
        self.assert_( isinstance( ta.fp_yes, FooPlusAdapter ) )
        self.assertEqual( ta.fp_yes_, object )

    def test_instance_adapt_default ( self ):
        ta = TraitsHolder()

        ta.a_default = object = SampleAverage()
        self.assertEqual( ta.a_default.get_average(), 200.0 )
        self.assert_( isinstance( ta.a_default, SampleAverage ) )
        self.assertFalse( hasattr(ta, 'a_default_') )

        ta.a_default = object = SampleList()
        self.assertEqual( ta.a_default.get_average(), 20.0 )
        self.assert_( isinstance( ta.a_default, ListAverageAdapter ) )
        self.assertFalse( hasattr(ta, 'a_default_') )

        ta.a_default = object = Sample()
        self.assertEqual( ta.a_default.get_average(), 2.0 )
        self.assert_( isinstance( ta.a_default, ListAverageAdapter ) )
        self.assertFalse( hasattr(ta, 'a_default_') )

        ta.a_default = object = SampleBad()
        self.assertEqual( ta.a_default, None )
        self.assertFalse( hasattr(ta, 'a_default_') )

    #-- Helper Methods ---------------------------------------------------------

    def implements_bad ( self ):
        class Test ( HasTraits ):
            implements( Sample )

# Run the unit tests (if invoked from the command line):
if __name__ == '__main__':
    unittest.main()
