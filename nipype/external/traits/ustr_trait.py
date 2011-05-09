#------------------------------------------------------------------------------
#
#  Copyright (c) 2008, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#  Author: David C. Morrill
#  Date:   08/21/2008
#
#------------------------------------------------------------------------------

""" Defines the UStr type and HasUniqueStrings mixin class for efficiently
    creating lists of objects containing traits whose string values must be
    unique within the list.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

from .trait_base import is_str
from .has_traits import HasTraits
from .trait_value import TraitValue, TypeValue
from .trait_types import List
from .trait_handlers import TraitType, NoDefaultSpecified

#-------------------------------------------------------------------------------
#  'UStr' class:
#-------------------------------------------------------------------------------

class UStr ( TraitType ):
    """ Trait type that ensures that a value assigned to a trait is unique
        within the list it belongs to.
    """
    # The type value to assign to restore the original list item type when a
    # list item is removed from the monitored list:
    str_type = TraitValue()

    # The informational text describing the trait:
    info_text = 'a unique string'

    def __init__ ( self, owner, list_name, str_name,
                         default_value = NoDefaultSpecified, **metadata ):
        """ Initializes the type.
        """
        super( UStr, self ).__init__( default_value, **metadata )

        self.owner     = owner
        self.list_name = list_name
        self.str_name  = str_name
        self.ustr_type = TypeValue( self )
        self.names     = dict( [ ( getattr( item, str_name ), item )
                                 for item in getattr( owner, list_name ) ] )
        self.roots     = {}
        self.available = {}
        owner.on_trait_change( self._items_modified, list_name + '[]' )

    def validate ( self, object, name, value ):
        """ Ensures that a value being assigned to a trait is a unique string.
        """
        if isinstance( value, basestring ):
            names    = self.names
            old_name = getattr( object, name )
            if names.get( old_name ) is object:
                self._remove( old_name )

            if value not in names:
                names[ value ] = object
                return value

            available = self.available.get( value )
            while True:
                if available is None:
                    new_value = None
                    break

                index = available.pop()
                if len( available ) == 0:
                    del self.available[ value ]
                    available = None

                new_value = '%s_%d' % ( value, index )
                if new_value not in names:
                    break

            if new_value is None:
                self.roots[ value ] = index = \
                    self.roots.setdefault( value, 1 ) + 1
                new_value = '%s_%d' % ( value, index )

            names[ new_value ] = object
            return new_value

        self.error( object, name, value )

    def _remove ( self, name ):
        """ Removes a specified name.
        """
        self.names.pop( name, None )
        col = name.rfind( '_' )
        if col >= 0:
            try:
                index  = int( name[ col + 1: ] )
                prefix = name[ : col ]
                if prefix in self.roots:
                    if prefix not in self.available:
                        self.available[ prefix ] = set()
                    self.available[ prefix ].add( index )
            except:
                pass

    def _items_modified ( self, object, name, removed, added ):
        """ Handles items being added to or removed from the monitored list.
        """
        str_name  = self.str_name
        str_type  = self.str_type
        ustr_type = self.ustr_type

        for item in removed:
            setattr( item, str_name, str_type )
            self._remove( getattr( item, str_name ) )

        for item in added:
            setattr( item, str_name, ustr_type )
            setattr( item, str_name, getattr( item, str_name ) )

#-------------------------------------------------------------------------------
#  'HasUniqueStrings' class:
#-------------------------------------------------------------------------------

class HasUniqueStrings ( HasTraits ):
    """ Mixin or base class for objects containing lists with items containing
        string valued traits that must be unique.

        List traits within the class that contain items which have string traits
        which must be unique should indicate this by attaching metadata of the
        form::

            unique_string = 'trait1, trait2, ..., traitn'

        where each 'traiti' value is the name of a trait within each list item
        that must contain unique string data.

        For example::

            usa = List( State, unique_string = 'name, abbreviation' )
    """

    #-- Private Traits ---------------------------------------------------------

    # List of UStr traits that have been attached to object list traits:
    _ustr_traits = List

    #-- HasTraits Object Initializer -------------------------------------------

    def traits_init ( self ):
        """ Adds any UStrMonitor objects to list traits with 'unique_string'
            metadata.
        """
        super( HasUniqueStrings, self ).traits_init()

        for name, trait in self.traits( unique_string = is_str ).items():
            for str_name in trait.unique_string.split( ',' ):
                self._ustr_traits.append( UStr( self, name, str_name.strip() ) )

            items = getattr( self, name )
            if len( items ) > 0:
                setattr( self, name, [] )
                setattr( self, name, items )

