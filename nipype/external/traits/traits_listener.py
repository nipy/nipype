#-------------------------------------------------------------------------------
#
#  Copyright (c) 2007, Enthought, Inc.
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
#  Date:   03/05/2007
#
#-------------------------------------------------------------------------------

""" Defines classes used to implement and manage various trait listener
    patterns.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import re
import string
import weakref
from weakref import WeakKeyDictionary
from string import whitespace
from types import MethodType

from .has_traits import HasPrivateTraits
from .trait_base import Undefined, Uninitialized
from .traits import Property
from .trait_types import Str, Int, Bool, Instance, List, Enum, Any
from .trait_errors import TraitError
from .trait_notifiers import TraitChangeNotifyWrapper

#---------------------------------------------------------------------------
#  Constants:
#---------------------------------------------------------------------------

# The name of the dictionary used to store active listeners
TraitsListener = '__traits_listener__'

# End of String marker
EOS = '\0'

# Types of traits that can be listened to

ANYTRAIT_LISTENER = '_register_anytrait'
SIMPLE_LISTENER   = '_register_simple'
LIST_LISTENER     = '_register_list'
DICT_LISTENER     = '_register_dict'
SET_LISTENER      = '_register_set'

# Mapping from trait default value types to listener types
type_map = {
    5: LIST_LISTENER,
    6: DICT_LISTENER,
    9: SET_LISTENER
}

# Listener types:
ANY_LISTENER = 0
SRC_LISTENER = 1
DST_LISTENER = 2

ListenerType = {
    0: ANY_LISTENER,
    1: DST_LISTENER,
    2: DST_LISTENER,
    3: SRC_LISTENER,
    4: SRC_LISTENER
}

# Invalid destination ( object, name ) reference marker (i.e. ambiguous):
INVALID_DESTINATION = ( None, None )

# Regular expressions used by the parser:
simple_pat = re.compile( r'^([a-zA-Z_]\w*)(\.|:)([a-zA-Z_]\w*)$' )
name_pat   = re.compile( r'([a-zA-Z_]\w*)\s*(.*)' )

# Characters valid in a traits name:
name_chars = string.ascii_letters + string.digits + '_'

#-------------------------------------------------------------------------------
# Utility functions:
#-------------------------------------------------------------------------------

def indent ( text, first_line = True, n = 1, width = 4 ):
    """ Indent lines of text.

    Parameters
    ----------
    text : str
        The text to indent.
    first_line : bool, optional
        If False, then the first line will not be indented.
    n : int, optional
        The level of indentation.
    width : int, optional
        The number of spaces in each level of indentation.

    Returns
    -------
    indented : str
    """
    lines = text.split( '\n' )
    if not first_line:
        first = lines[0]
        lines = lines[1:]

    spaces = ' ' * (width * n)
    lines2 = [ spaces + x for x in lines ]

    if not first_line:
        lines2.insert( 0, first )

    indented = '\n'.join( lines2 )

    return indented

#-------------------------------------------------------------------------------
#  Metadata filters:
#-------------------------------------------------------------------------------

def is_not_none ( value ): return (value is not None)
def is_none ( value ):     return (value is None)
def not_event ( value ):   return (value != 'event')

#-------------------------------------------------------------------------------
#  'ListenerBase' class:
#-------------------------------------------------------------------------------

class ListenerBase ( HasPrivateTraits ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # The handler to be called when any listened to trait is changed:
    #handler = Any

    # The dispatch mechanism to use when invoking the handler:
    #dispatch = Str

    # Does the handler go at the beginning (True) or end (False) of the
    # notification handlers list?
    #priority = Bool( False )

    # The next level (if any) of ListenerBase object to be called when any of
    # our listened to traits is changed:
    #next = Instance( ListenerBase )

    # The type of handler being used:
    #type = Enum( ANY_LISTENER, SRC_LISTENER, DST_LISTENER )

    # Should changes to this item generate a notification to the handler?
    # notify = Bool

    # Should registering listeners for items reachable from this listener item
    # be deferred until the associated trait is first read or set?
    # deferred = Bool

    #---------------------------------------------------------------------------
    #  Registers new listeners:
    #---------------------------------------------------------------------------

    def register ( self, new ):
        """ Registers new listeners.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Unregisters any existing listeners:
    #---------------------------------------------------------------------------

    def unregister ( self, old ):
        """ Unregisters any existing listeners.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Handles a trait change for a simple trait:
    #---------------------------------------------------------------------------

    def handle ( self, object, name, old, new ):
        """ Handles a trait change for a simple trait.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Handles a trait change for a list trait:
    #---------------------------------------------------------------------------

    def handle_list ( self, object, name, old, new ):
        """ Handles a trait change for a list trait.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Handles a trait change for a list traits items:
    #---------------------------------------------------------------------------

    def handle_list_items ( self, object, name, old, new ):
        """ Handles a trait change for a list traits items.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Handles a trait change for a dictionary trait:
    #---------------------------------------------------------------------------

    def handle_dict ( self, object, name, old, new ):
        """ Handles a trait change for a dictionary trait.
        """
        raise NotImplementedError

    #---------------------------------------------------------------------------
    #  Handles a trait change for a dictionary traits items:
    #---------------------------------------------------------------------------

    def handle_dict_items ( self, object, name, old, new ):
        """ Handles a trait change for a dictionary traits items.
        """
        raise NotImplementedError

#-------------------------------------------------------------------------------
#  'ListenerItem' class:
#-------------------------------------------------------------------------------

class ListenerItem ( ListenerBase ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # The name of the trait to listen to:
    name = Str

    # The name of any metadata that must be present (or not present):
    metadata_name = Str

    # Does the specified metadata need to be defined (True) or not defined
    # (False)?
    metadata_defined = Bool( True )

    # The handler to be called when any listened-to trait is changed:
    handler = Any

    # A weakref 'wrapped' version of 'handler':
    wrapped_handler_ref = Any

    # The dispatch mechanism to use when invoking the handler:
    dispatch = Str

    # Does the handler go at the beginning (True) or end (False) of the
    # notification handlers list?
    priority = Bool( False )

    # The next level (if any) of ListenerBase object to be called when any of
    # this object's listened-to traits is changed:
    next = Instance( ListenerBase )

    # The type of handler being used:
    type = Enum( ANY_LISTENER, SRC_LISTENER, DST_LISTENER )

    # Should changes to this item generate a notification to the handler?
    notify = Bool( True )

    # Should registering listeners for items reachable from this listener item
    # be deferred until the associated trait is first read or set?
    deferred = Bool( False )

    # Is this an 'any_trait' change listener, or does it create explicit
    # listeners for each individual trait?
    is_any_trait = Bool( False )

    # Is the associated handler a special list handler that handles both
    # 'foo' and 'foo_items' events by receiving a list of 'deleted' and 'added'
    # items as the 'old' and 'new' arguments?
    is_list_handler = Bool( False )

    # A dictionary mapping objects to a list of all current active
    # (*name*, *type*) listener pairs, where *type* defines the type of
    # listener, one of: (SIMPLE_LISTENER, LIST_LISTENER, DICT_LISTENER).
    active = Instance( WeakKeyDictionary, () )

    #-- 'ListenerBase' Class Method Implementations ----------------------------

    #---------------------------------------------------------------------------
    #  String representation:
    #---------------------------------------------------------------------------

    def __repr__ ( self, seen = None ):
        """Returns a string representation of the object.

        Since the object graph may have cycles, we extend the basic __repr__ API
        to include a set of objects we've already seen while constructing
        a string representation. When this method tries to get the repr of
        a ListenerItem or ListenerGroup, we will use the extended API and build
        up the set of seen objects. The repr of a seen object will just be
        '<cycle>'.
        """
        if seen is None:
            seen = set()

        seen.add( self )
        next_repr = 'None'
        next      = self.next
        if next is not None:
            if next in seen:
                next_repr = '<cycle>'
            else:
                next_repr = next.__repr__( seen )

        return """%s(
    name = %r,
    metadata_name = %r,
    metadata_defined = %r,
    is_any_trait = %r,
    dispatch = %r,
    notify = %r,
    is_list_handler = %r,
    type = %r,
    next = %s
')""" % ( self.__class__.__name__, self.name, self.metadata_name,
          self.metadata_defined, self.is_any_trait, self.dispatch, self.notify,
          self.is_list_handler, self.type, indent( next_repr, False ) )

    #---------------------------------------------------------------------------
    #  Registers new listeners:
    #---------------------------------------------------------------------------

    def register ( self, new ):
        """ Registers new listeners.
        """
        # Make sure we actually have an object to set listeners on and that it
        # has not already been registered (cycle breaking):
        if (new is None) or (new is Undefined) or (new in self.active):
            return INVALID_DESTINATION

        # Create a dictionary of {name: trait_values} that match the object's
        # definition for the 'new' object:
        name = self.name
        last = name[-1:]
        if last == '*':
            # Handle the special case of an 'anytrait' change listener:
            if self.is_any_trait:
                try:
                    self.active[ new ] = [ ( '', ANYTRAIT_LISTENER ) ]
                    return self._register_anytrait( new, '', False )
                except TypeError:
                    # This error can occur if 'new' is a list or other object
                    # for which a weakref cannot be created as the dictionary
                    # key for 'self.active':
                    return INVALID_DESTINATION

            # Handle trait matching based on a common name prefix and/or
            # matching trait metadata:
            metadata = self._metadata
            if metadata is None:
                self._metadata = metadata = { 'type': not_event }
                if self.metadata_name != '':
                    if self.metadata_defined:
                        metadata[ self.metadata_name ] = is_not_none
                    else:
                        metadata[ self.metadata_name ] = is_none

            # Get all object traits with matching metadata:
            names = new.trait_names( **metadata )

            # If a name prefix was specified, filter out only the names that
            # start with the specified prefix:
            name = name[:-1]
            if name != '':
                n     = len( name )
                names = [ aname for aname in names if name == aname[ : n ] ]

            # Create the dictionary of selected traits:
            bt     = new.base_trait
            traits = dict( [ ( name, bt( name ) ) for name in names ] )

            # Handle any new traits added dynamically to the object:
            new.on_trait_change( self._new_trait_added, 'trait_added' )
        else:
            # Determine if the trait is optional or not:
            optional = (last == '?')
            if optional:
                name = name[:-1]

            # Else, no wildcard matching, just get the specified trait:
            trait = new.base_trait( name )

            # Try to get the object trait:
            if trait is None:
                # Raise an error if trait is not defined and not optional:

                # fixme: Properties which are lists don't implement the
                # '..._items' sub-trait, which can cause a failure here when
                # used with an editor that sets up listeners on the items...
                if not optional:
                    raise TraitError( "'%s' object has no '%s' trait" % (
                                      new.__class__.__name__, name ) )

                # Otherwise, just skip it:
                traits = {}
            else:
                # Create a result dictionary containing just the single trait:
                traits = { name: trait }

        # For each item, determine its type (simple, list, dict):
        self.active[ new ] = active = []
        for name, trait in traits.items():

            # Determine whether the trait type is simple, list, set or
            # dictionary:
            type    = SIMPLE_LISTENER
            handler = trait.handler
            if handler is not None:
                type = type_map.get( handler.default_value_type,
                                     SIMPLE_LISTENER )

            # Add the name and type to the list of traits being registered:
            active.append( ( name, type ) )

            # Set up the appropriate trait listeners on the object for the
            # current trait:
            value = getattr( self, type )( new, name, False )

        if len( traits ) == 1:
            return value

        return INVALID_DESTINATION

    #---------------------------------------------------------------------------
    #  Unregisters any existing listeners:
    #---------------------------------------------------------------------------

    def unregister ( self, old ):
        """ Unregisters any existing listeners.
        """
        if old is not None and old is not Uninitialized:
            try:
                active = self.active.pop( old, None )
                if active is not None:
                    for name, type in active:
                        getattr( self, type )( old, name, True )
            except TypeError:
                # An error can occur if 'old' is a list or other object for
                # which a weakref cannot be created and used an a key for
                # 'self.active':
                pass

    #---------------------------------------------------------------------------
    #  Handles a trait change for an intermediate link trait:
    #---------------------------------------------------------------------------

    def handle_simple ( self, object, name, old, new ):
        """ Handles a trait change for an intermediate link trait.
        """
        self.next.unregister( old )
        self.next.register( new )

    def handle_dst ( self, object, name, old, new ):
        """ Handles a trait change for an intermediate link trait when the
            notification is for the final destination trait.
        """
        self.next.unregister( old )
        object, name = self.next.register( new )
        if old is not Uninitialized:
            if object is None:
                raise TraitError( "on_trait_change handler signature is "
                         "incompatible with a change to an intermediate trait" )

            wh = self.wrapped_handler_ref()
            if wh is not None:
                wh( object, name, old,
                    getattr( object, name, Undefined ) )

    #---------------------------------------------------------------------------
    #  Handles a trait change for a list (or set) trait:
    #---------------------------------------------------------------------------

    def handle_list ( self, object, name, old, new ):
        """ Handles a trait change for a list (or set) trait.
        """
        if old is not None and old is not Uninitialized:
            unregister = self.next.unregister
            for obj in old:
                unregister( obj )

        register = self.next.register
        for obj in new:
            register( obj )

    #---------------------------------------------------------------------------
    #  Handles a trait change for a list (or set) traits items:
    #---------------------------------------------------------------------------

    def handle_list_items ( self, object, name, old, new ):
        """ Handles a trait change for items of a list (or set) trait.
        """
        self.handle_list( object, name, new.removed, new.added )

    def handle_list_items_special ( self, object, name, old, new ):
        """ Handles a trait change for items of a list (or set) trait with
            notification.
        """
        wh = self.wrapped_handler_ref()
        if wh is not None:
            wh( object, name, new.removed, new.added )

    #---------------------------------------------------------------------------
    #  Handles a trait change for a dictionary trait:
    #---------------------------------------------------------------------------

    def handle_dict ( self, object, name, old, new ):
        """ Handles a trait change for a dictionary trait.
        """
        if old is not Uninitialized:
            unregister = self.next.unregister
            for obj in old.values():
                unregister( obj )

        register = self.next.register
        for obj in new.values():
            register( obj )

    #---------------------------------------------------------------------------
    #  Handles a trait change for a dictionary traits items:
    #---------------------------------------------------------------------------

    def handle_dict_items ( self, object, name, old, new ):
        """ Handles a trait change for items of a dictionary trait.
        """
        self.handle_dict( object, name, new.removed, new.added )

        if len( new.changed ) > 0:
            dict = getattr( object, name )
            unregister = self.next.unregister
            register = self.next.register
            for key, obj in new.changed.items():
                unregister( obj )
                register( dict[ key ] )

    #---------------------------------------------------------------------------
    #  Handles an invalid intermediate trait change to a handler that must be
    #  applied to the final destination object.trait:
    #---------------------------------------------------------------------------

    def handle_error ( self, obj, name, old, new ):
        """ Handles an invalid intermediate trait change to a handler that must
            be applied to the final destination object.trait.
        """
        if old is not None and old is not Uninitialized:
            raise TraitError( "on_trait_change handler signature is "
                              "incompatible with a change to an intermediate trait" )

    #-- Event Handlers ---------------------------------------------------------

    #---------------------------------------------------------------------------
    #  Handles the 'handler' trait being changed:
    #---------------------------------------------------------------------------

    def _handler_changed ( self, handler ):
        """ Handles the **handler** trait being changed.
        """
        if self.next is not None:
            self.next.handler = handler

    #---------------------------------------------------------------------------
    #  Handles the 'wrapped_handler_ref' trait being changed:
    #---------------------------------------------------------------------------

    def _wrapped_handler_ref_changed ( self, wrapped_handler_ref ):
        """ Handles the 'wrapped_handler_ref' trait being changed.
        """
        if self.next is not None:
            self.next.wrapped_handler_ref = wrapped_handler_ref

    #---------------------------------------------------------------------------
    #  Handles the 'dispatch' trait being changed:
    #---------------------------------------------------------------------------

    def _dispatch_changed ( self, dispatch ):
        """ Handles the **dispatch** trait being changed.
        """
        if self.next is not None:
            self.next.dispatch = dispatch

    #---------------------------------------------------------------------------
    #  Handles the 'priority' trait being changed:
    #---------------------------------------------------------------------------

    def _priority_changed ( self, priority ):
        """ Handles the **priority** trait being changed.
        """
        if self.next is not None:
            self.next.priority = priority

    #-- Private Methods --------------------------------------------------------

    #---------------------------------------------------------------------------
    #  Registers any 'anytrait' listener:
    #---------------------------------------------------------------------------

    def _register_anytrait ( self, object, name, remove ):
        """ Registers any 'anytrait' listener.
        """
        handler = self.handler()
        if handler is not Undefined:
            object._on_trait_change( handler, remove   = remove,
                                              dispatch = self.dispatch,
                                              priority = self.priority )

        return ( object, name )

    #---------------------------------------------------------------------------
    #  Registers a handler for a simple trait:
    #---------------------------------------------------------------------------

    def _register_simple ( self, object, name, remove ):
        """ Registers a handler for a simple trait.
        """
        next = self.next
        if next is None:
            handler = self.handler()
            if handler is not Undefined:
                object._on_trait_change( handler, name,
                                         remove   = remove,
                                         dispatch = self.dispatch,
                                         priority = self.priority )

            return ( object, name )

        tl_handler = self.handle_simple
        if self.notify:
            if self.type == DST_LISTENER:
                if self.dispatch != 'same':
                    raise TraitError( "Trait notification dispatch type '%s' "
                      "is not compatible with handler signature and "
                      "extended trait name notification style" % self.dispatch )
                tl_handler = self.handle_dst
            else:
                handler = self.handler()
                if handler is not Undefined:
                    object._on_trait_change( handler, name,
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

        object._on_trait_change( tl_handler, name,
                                 remove   = remove,
                                 dispatch = 'extended',
                                 priority = self.priority )

        if remove:
            return next.unregister( getattr( object, name ) )

        if not self.deferred:
            return next.register( getattr( object, name ) )

        return ( object, name )

    #---------------------------------------------------------------------------
    #  Registers a handler for a list trait:
    #---------------------------------------------------------------------------

    def _register_list ( self, object, name, remove ):
        """ Registers a handler for a list trait.
        """
        next = self.next
        if next is None:
            handler = self.handler()
            if handler is not Undefined:
                object._on_trait_change( handler, name,
                                         remove   = remove,
                                         dispatch = self.dispatch,
                                         priority = self.priority )

                if self.is_list_handler:
                    object._on_trait_change( self.handle_list_items_special,
                                             name + '_items',
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

                elif self.type == ANY_LISTENER:
                    object._on_trait_change( handler, name + '_items',
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

            return ( object, name )

        tl_handler       = self.handle_list
        tl_handler_items = self.handle_list_items
        if self.notify:
            if self.type == DST_LISTENER:
                tl_handler = tl_handler_items = self.handle_error
            else:
                handler = self.handler()
                if handler is not Undefined:
                    object._on_trait_change( handler, name,
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

                    if self.is_list_handler:
                        object._on_trait_change( self.handle_list_items_special,
                                               name + '_items',
                                               remove   = remove,
                                               dispatch = self.dispatch,
                                               priority = self.priority )
                    elif self.type == ANY_LISTENER:
                        object._on_trait_change( handler, name + '_items',
                                                 remove   = remove,
                                                 dispatch = self.dispatch,
                                                 priority = self.priority )

        object._on_trait_change( tl_handler, name,
                                 remove   = remove,
                                 dispatch = 'extended',
                                 priority = self.priority )

        object._on_trait_change( tl_handler_items, name + '_items',
                                 remove   = remove,
                                 dispatch = 'extended',
                                 priority = self.priority )

        if remove:
            handler = next.unregister
        elif self.deferred:
            return INVALID_DESTINATION
        else:
            handler = next.register

        for obj in getattr( object, name ):
            handler( obj )

        return INVALID_DESTINATION

    # Handle 'sets' the same as 'lists':
    # Note: Currently the behavior of sets is almost identical to that of lists,
    # so we are able to share the same code for both. This includes some 'duck
    # typing' that occurs with the TraitListEvent and TraitSetEvent, that define
    # 'removed' and 'added' attributes that behave similarly enough (from the
    # point of view of this module) that they can be treated as equivalent. If
    # the behavior of sets ever diverges from that of lists, then this code may
    # need to be changed.
    _register_set = _register_list

    #---------------------------------------------------------------------------
    #  Registers a handler for a dictionary trait:
    #---------------------------------------------------------------------------

    def _register_dict ( self, object, name, remove ):
        """ Registers a handler for a dictionary trait.
        """
        next = self.next
        if next is None:
            handler = self.handler()
            if handler is not Undefined:
                object._on_trait_change( handler, name,
                                         remove   = remove,
                                         dispatch = self.dispatch,
                                         priority = self.priority )

                if self.type == ANY_LISTENER:
                    object._on_trait_change( handler, name + '_items',
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

            return ( object, name )

        tl_handler       = self.handle_dict
        tl_handler_items = self.handle_dict_items
        if self.notify:
            if self.type == DST_LISTENER:
                tl_handler = tl_handler_items = self.handle_error
            else:
                handler = self.handler()
                if handler is not Undefined:
                    object._on_trait_change( handler, name,
                                             remove   = remove,
                                             dispatch = self.dispatch,
                                             priority = self.priority )

                    if self.type == ANY_LISTENER:
                        object._on_trait_change( handler, name + '_items',
                                                 remove   = remove,
                                                 dispatch = self.dispatch,
                                                 priority = self.priority )

        object._on_trait_change( tl_handler, name,
                                 remove   = remove,
                                 dispatch = self.dispatch,
                                 priority = self.priority )

        object._on_trait_change( tl_handler_items, name + '_items',
                                 remove   = remove,
                                 dispatch = self.dispatch,
                                 priority = self.priority )

        if remove:
            handler = next.unregister
        elif self.deferred:
            return INVALID_DESTINATION
        else:
            handler = next.register

        for obj in getattr( object, name ).values():
            handler( obj )

        return INVALID_DESTINATION

    #---------------------------------------------------------------------------
    #  Handles new traits being added to an object being monitored:
    #---------------------------------------------------------------------------

    def _new_trait_added ( self, object, name, new_trait ):
        """ Handles new traits being added to an object being monitored.
        """
        # Set if the new trait matches our prefix and metadata:
        if new_trait.startswith( self.name[:-1] ):
            trait = object.base_trait( new_trait )
            for meta_name, meta_eval in self._metadata.items():
                if not meta_eval( getattr( trait, meta_name ) ):
                    return

            # Determine whether the trait type is simple, list, set or
            # dictionary:
            type    = SIMPLE_LISTENER
            handler = trait.handler
            if handler is not None:
                type = type_map.get( handler.default_value_,
                                 SIMPLE_LISTENER )

            # Add the name and type to the list of traits being registered:
            self.active[ object ].append( ( new_trait, type ) )

            # Set up the appropriate trait listeners on the object for the
            # new trait:
            getattr( self, type )( object, new_trait, False )

#-------------------------------------------------------------------------------
#  'ListenerGroup' class:
#-------------------------------------------------------------------------------

def _set_value ( self, name, value ):
    for item in self.items:
        setattr( item, name, value )

def _get_value ( self, name ):
    # Use the attribute on the first item. If there are no items, return None.
    if self.items:
        return getattr( self.items[0], name )
    else:
        return None

ListProperty = Property( fget = _get_value, fset = _set_value )

class ListenerGroup ( ListenerBase ):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # The handler to be called when any listened-to trait is changed
    handler = Property

    # A weakref 'wrapped' version of 'handler':
    wrapped_handler_ref = Property

    # The dispatch mechanism to use when invoking the handler:
    dispatch = Property

    # Does the handler go at the beginning (True) or end (False) of the
    # notification handlers list?
    priority = ListProperty

    # The next level (if any) of ListenerBase object to be called when any of
    # this object's listened-to traits is changed
    next = ListProperty

    # The type of handler being used:
    type = ListProperty

    # Should changes to this item generate a notification to the handler?
    notify = ListProperty

    # Should registering listeners for items reachable from this listener item
    # be deferred until the associated trait is first read or set?
    deferred = ListProperty

    # The list of ListenerBase objects in the group
    items = List( ListenerBase )

    #-- Property Implementations -----------------------------------------------

    def _set_handler ( self, handler ):
        if self._handler is None:
            self._handler = handler
            for item in self.items:
                item.handler = handler

    def _set_wrapped_handler_ref ( self, wrapped_handler_ref ):
        if self._wrapped_handler_ref is None:
            self._wrapped_handler_ref = wrapped_handler_ref
            for item in self.items:
                item.wrapped_handler_ref = wrapped_handler_ref

    def _set_dispatch ( self, dispatch ):
        if self._dispatch is None:
            self._dispatch = dispatch
            for item in self.items:
                item.dispatch = dispatch

    #-- 'ListenerBase' Class Method Implementations ----------------------------

    #---------------------------------------------------------------------------
    #  String representation:
    #---------------------------------------------------------------------------

    def __repr__ ( self, seen = None ):
        """Returns a string representation of the object.

        Since the object graph may have cycles, we extend the basic __repr__ API
        to include a set of objects we've already seen while constructing
        a string representation. When this method tries to get the repr of
        a ListenerItem or ListenerGroup, we will use the extended API and build
        up the set of seen objects. The repr of a seen object will just be
        '<cycle>'.
        """
        if seen is None:
            seen = set()

        seen.add( self )

        lines = [ '%s(items = [' % self.__class__.__name__ ]

        for item in self.items:
            lines.extend( indent( item.__repr__( seen ), True ).split( '\n' ) )
            lines[-1] += ','

        lines.append( '])' )

        return '\n'.join( lines )

    #---------------------------------------------------------------------------
    #  Registers new listeners:
    #---------------------------------------------------------------------------

    def register ( self, new ):
        """ Registers new listeners.
        """
        for item in self.items:
            item.register( new )

        return INVALID_DESTINATION

    #---------------------------------------------------------------------------
    #  Unregisters any existing listeners:
    #---------------------------------------------------------------------------

    def unregister ( self, old ):
        """ Unregisters any existing listeners.
        """
        for item in self.items:
            item.unregister( old )

#-------------------------------------------------------------------------------
#  'ListenerParser' class:
#-------------------------------------------------------------------------------

class ListenerParser ( HasPrivateTraits ):

    #-------------------------------------------------------------------------------
    #  Trait definitions:
    #-------------------------------------------------------------------------------

    # The string being parsed
    text = Str

    # The length of the string being parsed.
    len_text = Int

    # The current parse index within the string
    index = Int

    # The next character from the string being parsed
    next = Property

    # The next Python attribute name within the string:
    name = Property

    # The next non-whitespace character
    skip_ws = Property

    # Backspaces to the last character processed
    backspace = Property

    # The ListenerBase object resulting from parsing **text**
    listener = Instance( ListenerBase )

    #-- Property Implementations -----------------------------------------------

    def _get_next ( self ):
        index       = self.index
        self.index += 1
        if index >= self.len_text:
            return EOS

        return self.text[ index ]

    def _get_backspace ( self ):
        self.index = max( 0, self.index - 1 )

    def _get_skip_ws ( self ):
        while True:
            c = self.next
            if c not in whitespace:
                return c

    def _get_name ( self ):
        match = name_pat.match( self.text, self.index - 1 )
        if match is None:
            return ''

        self.index = match.start( 2 )

        return match.group( 1 )

    #-- object Method Overrides ------------------------------------------------

    def __init__ ( self, text = '', **traits ):
        self.text = text
        super( ListenerParser, self ).__init__( **traits )

    #-- Private Methods --------------------------------------------------------

    #---------------------------------------------------------------------------
    #  Parses the text and returns the appropriate collection of ListenerBase
    #  objects described by the text:
    #---------------------------------------------------------------------------

    def parse ( self ):
        """ Parses the text and returns the appropriate collection of
            ListenerBase objects described by the text.
        """
        # Try a simple case of 'name1.name2'. The simplest case of a single
        # Python name never triggers this parser, so we don't try to make that
        # a shortcut too. Whitespace should already have been stripped from the
        # start and end.

        # TODO: The use of regexes should be used throughout all of the parsing
        # functions to speed up all aspects of parsing.
        match = simple_pat.match( self.text )
        if match is not None:
            return ListenerItem(
                       name   = match.group( 1 ),
                       notify = match.group(2) == '.',
                       next   = ListenerItem( name = match.group( 3 ) ) )

        return self.parse_group( EOS )

    #---------------------------------------------------------------------------
    #  Parses the contents of a group:
    #---------------------------------------------------------------------------

    def parse_group ( self, terminator = ']' ):
        """ Parses the contents of a group.
        """
        items = []
        while True:
            items.append( self.parse_item( terminator ) )

            c = self.skip_ws
            if c is terminator:
                break

            if c != ',':
                if terminator == EOS:
                    self.error( "Expected ',' or end of string" )
                else:
                    self.error( "Expected ',' or '%s'" % terminator )

        if len( items ) == 1:
            return items[0]

        return ListenerGroup( items = items )

    #---------------------------------------------------------------------------
    #  Parses a single, complete listener item/group string:
    #---------------------------------------------------------------------------

    def parse_item ( self, terminator ):
        """ Parses a single, complete listener item or group string.
        """
        c = self.skip_ws
        if c == '[':
            result = self.parse_group()
            c      = self.skip_ws
        else:
            name = self.name
            if name != '':
                c = self.next

            result = ListenerItem( name = name )

            if c in '+-':
                result.name += '*'
                result.metadata_defined = (c == '+')
                cn = self.skip_ws
                result.metadata_name = metadata = self.name
                if metadata != '':
                    cn = self.skip_ws

                result.is_any_trait = ((c == '-') and (name == '') and
                                       (metadata == ''))
                c = cn

                if result.is_any_trait and (not ((c == terminator) or
                    ((c == ',') and (terminator == ']')))):
                    self.error( "Expected end of name" )
            elif c == '?':
                if len( name ) == 0:
                    self.error( "Expected non-empty name preceding '?'" )
                result.name += '?'
                c = self.skip_ws

        cycle = (c == '*')
        if cycle:
            c = self.skip_ws

        if c in '.:':
            result.notify = (c == '.')
            next = self.parse_item( terminator )
            if cycle:
                last = result
                while last.next is not None:
                    last = last.next
                last.next = lg = ListenerGroup( items = [ next, result ] )
                result    = lg
            else:
                result.next = next

            return result

        if c == '[':
            if (self.skip_ws == ']') and (self.skip_ws == terminator):
                self.backspace
                result.is_list_handler = True
            else:
                self.error( "Expected '[]' at the end of an item" )
        else:
            self.backspace

        if cycle:
            result.next = result

        return result

    #---------------------------------------------------------------------------
    #  Parses the metadata portion of a listener item:
    #---------------------------------------------------------------------------

    def parse_metadata ( self, item ):
        """ Parses the metadata portion of a listener item.
        """
        self.skip_ws
        item.metadata_name = name = self.name
        if name == '':
            self.backspace

    #---------------------------------------------------------------------------
    #  Raises a syntax error:
    #---------------------------------------------------------------------------

    def error ( self, msg ):
        """ Raises a syntax error.
        """
        raise TraitError( "%s at column %d of '%s'" %
                          ( msg, self.index, self.text ) )

    #-- Event Handlers ---------------------------------------------------------

    #---------------------------------------------------------------------------
    #  Handles the 'text' trait being changed:
    #---------------------------------------------------------------------------

    def _text_changed ( self ):
        self.index    = 0
        self.len_text = len( self.text )
        self.listener = self.parse()

#-------------------------------------------------------------------------------
#  'ListenerNotifyWrapper' class:
#-------------------------------------------------------------------------------

class ListenerNotifyWrapper ( TraitChangeNotifyWrapper ):

    #-- TraitChangeNotifyWrapper Method Overrides ------------------------------

    def __init__ ( self, handler, owner, id, listener, target=None):
        self.type     = ListenerType.get( self.init( handler,
                                    weakref.ref( owner, self.owner_deleted ), target ) )
        self.id       = id
        self.listener = listener

    def listener_deleted ( self, ref ):
        owner = self.owner()
        if owner is not None:
            dict      = owner.__dict__.get( TraitsListener )
            listeners = dict.get( self.id )
            listeners.remove( self )
            if len( listeners ) == 0:
                del dict[ self.id ]
                if len( dict ) == 0:
                    del owner.__dict__[ TraitsListener ]
                # fixme: Is the following line necessary, since all registered
                # notifiers should be getting the same 'listener_deleted' call:
                self.listener.unregister( owner )

        self.object = self.owner = self.listener = None

    def owner_deleted ( self, ref ):
        self.object = self.owner = None

#-------------------------------------------------------------------------------
#  'ListenerHandler' class:
#-------------------------------------------------------------------------------

class ListenerHandler ( object ):

    def __init__ ( self, handler ):
        if type( handler ) is MethodType:
            object = handler.im_self
            if object is not None:
                self.object = weakref.ref( object, self.listener_deleted )
                self.name   = handler.__name__

                return

        self.handler = handler

    def __call__ ( self ):
        result = getattr( self, 'handler', None )
        if result is not None:
            return result

        return getattr( self.object(), self.name )

    def listener_deleted ( self, ref ):
        self.handler = Undefined

