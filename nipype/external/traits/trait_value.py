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
#  Author:        David C. Morrill
#  Original Date: 04/01/2008
#
#------------------------------------------------------------------------------

""" Defines the TraitValue class, used for creating special, dynamic trait
    values.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

from .trait_base import Undefined
from .traits import CTrait
from .has_traits import HasTraits, HasPrivateTraits
from .trait_errors import TraitError
from .trait_types import Tuple, Dict, Any, Str, Instance, Event, Callable
from .trait_handlers import TraitType, _read_only, _write_only, _arg_count

#-------------------------------------------------------------------------------
#  'BaseTraitValue' class:
#-------------------------------------------------------------------------------

class BaseTraitValue ( HasPrivateTraits ):

    # Subclasses can define this trait as a property:
    # value = Property

    #-- Public Methods ---------------------------------------------------------

    def as_ctrait ( self, original_trait ):
        """ Returns the low-level C-based trait for this TraitValue.
        """
        notifiers = original_trait._notifiers( 0 )

        if self._ctrait is not None:
            if (notifiers is None) or (len( notifiers ) == 0):
                return self._ctrait

            trait = CTrait( 0 )
            trait.clone( self._ctrait )
        else:
            trait = self._as_ctrait( original_trait )

        if ((trait     is not None) and
            (notifiers is not None) and
            (len( notifiers ) > 0)):
            trait._notifiers( 1 ).extend( notifiers )

        return trait

    #-- Private Methods --------------------------------------------------------

    def _as_ctrait ( self, original_trait ):
        """ Returns the low-level C-based trait for this TraitValue.
        """
        value_trait = self.trait( 'value' )
        if value_trait is None:
            return None

        if value_trait.type != 'property':
            raise TraitError( "Invalid TraitValue specified." )

        metadata = { 'type':         'property',
                     '_trait_value': self }

        getter, setter, validate = value_trait.property()
        read_only = (getter is _read_only)
        if not read_only:
            getter = self._getter
            metadata[ 'transient' ] =  True

        if setter is not _write_only:
            if read_only:
                setter = self._read_only_setter
            else:
                setter = self._setter
            metadata[ 'transient' ] =  True

        return self._property_trait( getter, setter, validate, metadata )

    def _property_trait ( self, getter, setter, validate, metadata ):
        """ Returns a properly constructed 'property' trait.
        """
        n = 0
        if validate is not None:
            n = _arg_count( validate )

        trait = CTrait( 4 )
        trait.property( getter,   _arg_count( getter ),
                        setter,   _arg_count( setter ),
                        validate, n )

        trait.value_allowed(  True )
        trait.value_property( True )
        trait.__dict__ = metadata

        return trait

    def _getter ( self, object, name ):
        return self.value

    def _setter ( self, object, name, value ):
        old_value  = self.value
        self.value = value
        new_value  = self.value
        if new_value != old_value:
            object.trait_property_changed( name, old_value, new_value )

    def _read_only_setter ( self, object, name, value ):
        self.value = value
        object.trait_property_changed( name, Undefined, value )

#-------------------------------------------------------------------------------
#  'TraitValue' class:
#-------------------------------------------------------------------------------

class TraitValue ( BaseTraitValue ):

    # The callable used to define a default value:
    default = Callable

    # The positional arguments to pass to the callable default value:
    args = Tuple

    # The keyword arguments to pass to the callable default value:
    kw = Dict

    # The trait to use as the new trait type:
    type = Any

    # The object to delegate the new value to:
    delegate = Instance( HasTraits )

    # The name of the trait on the delegate object to get the new value from:
    name = Str

    #-- Private Methods --------------------------------------------------------

    def _as_ctrait ( self, original_trait ):
        """ Returns the low-level C-based trait for this TraitValue.
        """
        if self.default is not None:
            trait = CTrait( 0 )
            trait.clone( original_trait )
            if original_trait.__dict__ is not None:
                trait.__dict__ = original_trait.__dict__.copy()

            trait.default_value( 7, ( self.default, self.args, self.kw ) )

        elif self.type is not None:
            type = self.type
            try:
                rc = issubclass( type, TraitType )
            except:
                rc = False

            if rc:
                type = type( *self.args, **self.kw )

            if not isinstance( type, TraitType ):
                raise TraitError( ("The 'type' attribute of a TraitValue "
                    "instance must be a TraitType instance or subclass, but a "
                    "value of %s was specified.") % self.trait )

            self._ctrait = trait = type.as_ctrait()
            trait.value_allowed( True )

        elif self.delegate is None:
            return None

        else:
            if self.name == '':
                raise TraitError( "You must specify a non-empty string "
                    "value for the 'name' attribute when using the "
                    "'delegate' trait of a TraitValue instance." )

            metadata = { 'type':         'property',
                         '_trait_value': self,
                         'transient':    True }

            getter   = self._delegate_getter
            setter   = self._delegate_setter
            validate = None

            self.add_trait( 'value', Event() )
            self.delegate.on_trait_change( self._delegate_modified, self.name )

            trait = self._property_trait( getter, setter, validate, metadata )

        return trait

    def _delegate_getter ( self, object, name ):
        return getattr( self.delegate, self.name )

    def _delegate_setter ( self, object, name, value ):
        setattr( self.delegate, self.name, value )

    #-- Traits Event Handlers --------------------------------------------------

    def _delegate_modified ( self ):
        self.value = True

#-- Helper Function Definitions ------------------------------------------------

def SyncValue ( delegate, name ):
    return TraitValue( delegate = delegate, name = name )

def TypeValue ( type ):
    return TraitValue( type = type )

def DefaultValue ( default, args = (), kw = {} ):
    return TraitValue( default = default, args = args, kw = kw )

#-------------------------------------------------------------------------------
#  Tell the C-based traits module about the 'BaseTraitValue' class:
#-------------------------------------------------------------------------------

from . import ctraits
ctraits._value_class( BaseTraitValue )

