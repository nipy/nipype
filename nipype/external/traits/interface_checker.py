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
#  Author: Martin Chilvers
#  Date:   03/20/2008
#
#------------------------------------------------------------------------------

""" An attempt at type-safe casting.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

from types import FunctionType

from inspect import getargspec, getmro

from .has_traits import HasTraits

#-------------------------------------------------------------------------------
#  Logging:
#-------------------------------------------------------------------------------

import logging

logger = logging.getLogger( __name__ )

#-------------------------------------------------------------------------------
#  Constants:
#-------------------------------------------------------------------------------

# Message templates for interface errors.
BAD_SIGNATURE  = ("The '%s' class signature for the '%s' method is different "
                  "from that of the '%s' interface.")
MISSING_METHOD = ("The '%s' class does not implement the '%s' method of the "
                  "'%s' interface.")
MISSING_TRAIT  = ("The '%s' class does not implement the %s trait(s) of the "
                  "'%s' interface.")

#-------------------------------------------------------------------------------
#  'InterfaceError' class:
#-------------------------------------------------------------------------------

class InterfaceError ( Exception ):
    """ The exception raised if a class does not really implement an interface.
    """
    pass

#-------------------------------------------------------------------------------
#  'InterfaceChecker' class:
#-------------------------------------------------------------------------------

class InterfaceChecker ( HasTraits ):
    """ Checks that interfaces are actually implemented.
    """

    #---------------------------------------------------------------------------
    #  'InterfaceChecker' interface:
    #---------------------------------------------------------------------------

    def check_implements ( self, cls, interfaces, error_mode ):
        """ Checks that the class implements the specified interfaces.

            'interfaces' can be a single interface or a list of interfaces.
        """
        # If a single interface was specified then turn it into a list:
        try:
            iter( interfaces )
        except TypeError:
            interfaces = [ interfaces ]

        # If the class has traits then check that it implements all traits and
        # methods on the specified interfaces:
        if issubclass( cls, HasTraits ):
            for interface in interfaces:
                if not self._check_has_traits_class( cls, interface,
                                                     error_mode ):
                    return False

        # Otherwise, just check that the class implements all methods on the
        # specified interface:
        else:
            for interface in interfaces:
                if not self._check_non_has_traits_class( cls, interface,
                                                         error_mode ):
                    return False

        return True

    #---------------------------------------------------------------------------
    #  Private interface:
    #---------------------------------------------------------------------------

    def _check_has_traits_class ( self, cls, interface, error_mode ):
        """ Checks that a 'HasTraits' class implements an interface.
        """
        return (self._check_traits(  cls, interface, error_mode ) and
                self._check_methods( cls, interface, error_mode ))

    def _check_non_has_traits_class ( self, cls, interface, error_mode ):
        """ Checks that a non-'HasTraits' class implements an interface.
        """
        return self._check_methods( cls, interface, error_mode )

    def _check_methods ( self, cls, interface, error_mode ):
        """ Checks that a class implements the methods on an interface.
        """
        cls_methods       = self._get_public_methods( cls )
        interface_methods = self._get_public_methods( interface )

        for name in interface_methods:
            if name not in cls_methods:
                return self._handle_error( MISSING_METHOD %
                           ( self._class_name( cls ), name,
                             self._class_name( interface ) ), error_mode )


            # Check that the method signatures are the same:
            cls_argspec       = getargspec( cls_methods[ name ] )
            interface_argspec = getargspec( interface_methods[ name ] )

            if cls_argspec != interface_argspec:
                return self._handle_error( BAD_SIGNATURE %
                           ( self._class_name( cls ), name,
                             self._class_name( interface ) ), error_mode )

        return True

    def _check_traits ( self, cls, interface, error_mode ):
        """ Checks that a class implements the traits on an interface.
        """
        missing = set( interface.class_traits() ).difference(
                  set( cls.class_traits() ) )

        if len( missing ) > 0:
            return self._handle_error( MISSING_TRAIT %
                       ( self._class_name( cls ), `list( missing )`[1:-1],
                         self._class_name( interface ) ), error_mode )

        return True

    def _get_public_methods ( self, cls ):
        """ Returns all public methods on a class.

            Returns a dictionary containing all public methods keyed by name.
        """
        public_methods = {}
        for c in getmro( cls ):
            # Stop when we get to 'HasTraits'!:
            if c is HasTraits:
                break

            for name, value in c.__dict__.items():
                if ((not name.startswith( '_' )) and
                    (type( value ) is FunctionType)):
                    public_methods[ name ] = value

        return public_methods

    def _class_name ( self, cls ):
        return cls.__name__

    def _handle_error ( self, msg, error_mode ):
        if error_mode > 1:
            raise InterfaceError( msg )

        if error_mode == 1:
            logger.warning( msg )

        return False


# A default interface checker:
checker = InterfaceChecker()

def check_implements ( cls, interfaces, error_mode = 0 ):
    """ Checks that the class implements the specified interfaces.

        'interfaces' can be a single interface or a list of interfaces.
    """
    return checker.check_implements( cls, interfaces, error_mode )

