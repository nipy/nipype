#-------------------------------------------------------------------------------
#
#  Test the 'add_trait_listener', 'remove_trait_listener' interface to
#  the HasTraits class.
#
#  Written by: David C. Morrill
#
#  Date: 09/07/2005
#
#  (c) Copyright 2005 by Enthought, Inc.
#
#  Copyright (c) 2007, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  ListenEventsicense included in /LICENSE.txt and may be redistributed
#  only under the conditions described in the aforementioned license.  The
#  license is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#

#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import unittest

from ..api import HasTraits, Str, Int, Float

#-------------------------------------------------------------------------------
#  'GenerateEvents' class:
#-------------------------------------------------------------------------------

class GenerateEvents ( HasTraits ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    name   = Str
    age    = Int
    weight = Float

#-------------------------------------------------------------------------------
#  'ListenEvents' class:
#-------------------------------------------------------------------------------

events = {} # dict of events

class ListenEvents ( HasTraits ):

    #---------------------------------------------------------------------------
    #  'GenerateEvents' event interface:
    #  the events are stored in the dict 'events'
    #---------------------------------------------------------------------------

    def _name_changed ( self, object, name, old, new ):
        events["_name_changed"] = (name, old, new)

    def _age_changed ( self, object, name, old, new ):
        events["_age_changed"] = (name, old, new)

    def _weight_changed ( self, object, name, old, new ):
        events["_weight_changed"] = (name, old, new)

    def alt_name_changed ( self, object, name, old, new ):
        events["alt_name_changed"] = (name, old, new)

    def alt_weight_changed ( self, object, name, old, new ):
        events["alt_weight_changed"] = (name, old, new)

#-------------------------------------------------------------------------------
#  unit test class:
#-------------------------------------------------------------------------------

class Test_Listeners ( unittest.TestCase ):

    def test(self):
        global events

        # FIXME: comparing floats
        ge = GenerateEvents()
        le = ListenEvents()

        # Starting test: No Listeners
        ge.set( name = 'Joe', age = 22, weight = 152.0 )

        # Adding default listener
        ge.add_trait_listener( le )
        events = {}
        ge.set( name = 'Mike', age = 34, weight = 178.0 )
        self.assertEqual(events, {
            '_age_changed': ('age', 22, 34),
            '_weight_changed': ('weight', 152.0, 178.0),
            '_name_changed': ('name', 'Joe', 'Mike'),
            })

        # Adding alternate listener
        ge.add_trait_listener( le, 'alt' )
        events = {}
        ge.set( name = 'Gertrude', age = 39, weight = 108.0 )
        self.assertEqual(events, {
            '_age_changed': ('age', 34, 39),
            '_name_changed': ('name', 'Mike', 'Gertrude'),
            '_weight_changed': ('weight', 178.0, 108.0),
            'alt_name_changed': ('name', 'Mike', 'Gertrude'),
            'alt_weight_changed': ('weight', 178.0, 108.0),
            })

        # Removing default listener
        ge.remove_trait_listener( le )
        events = {}
        ge.set( name = 'Sally', age = 46, weight = 118.0 )
        self.assertEqual(events, {
            'alt_name_changed': ('name', 'Gertrude', 'Sally'),
            'alt_weight_changed': ('weight', 108.0, 118.0),
            })

        # Removing alternate listener
        ge.remove_trait_listener( le, 'alt' )
        events = {}
        ge.set( name = 'Ralph', age = 29, weight = 198.0 )
        self.assertEqual(events, {})



# Run the unit tests (if invoked from the command line):
if __name__ == '__main__':
    unittest.main()
