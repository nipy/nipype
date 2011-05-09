#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought pyface package component>
#------------------------------------------------------------------------------
""" A log handler that allows filtering of messages by origin. """


# Standard library imports.
import logging, inspect, os

# Local imports.
#
# fixme: This module was just copied over from 'enthought.envisage.core' (so
# that we don't rely on Envisage here!). Where should this module go?
from util import get_module_name


class FilteringHandler(logging.Handler):
    """ A log handler that allows filtering of messages by origin.

    Example
    -------
    ::

        from traits.logger.api import DebugHandler, logger

        handler = FilteringHandler(
            include = {
                'enthought.envisage.core' : True
            },

            exclude = {
                'enthought.envisage.core.application' : False
            }
        )

        logger.addHandler(handler)

    Notes
    -----

    The boolean value specified for each name in the include and exclude
    dictionaries indicates whether or not the include or exclude should pertain
    to any sub-packages and modules.

    The above example includes all log messages from anything contained in, or
    under the 'enthought.envisage.core' package, EXCEPT for any log messages
    from the 'enthought.envisage.core.application' module.

    """

    ###########################################################################
    # 'object' interface.
    ###########################################################################

    def __init__(self, include=None, exclude=None):
        """ Creates a new handler. """

        # Base class constructor.
        logging.Handler.__init__(self)

        # Packages or modules to include.
        self.include = include is not None and include or {}

        # Packages or modules to exclude.
        self.exclude = exclude is not None and exclude or {}

        return

    ###########################################################################
    # 'Handler' interface.
    ###########################################################################

    def emit(self, record):
        """ Emits a log record. """

        # Get the name of the module that the logger was called from.
        module_name = self._get_module_name()

        if len(self.include) == 0 or self._include(module_name):
            if len(self.exclude) == 0 or not self._exclude(module_name):
                self.filtered_emit(record)

        return

    ###########################################################################
    # 'Handler' interface.
    ###########################################################################

    def filtered_emit(self, record):
        """ Emits a log record if it has not been filtered. """

        print record.getMessage()

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _get_module_name(self):
        """ Returns the module that the logger was actually called from. """

        # fixem: Ahem.... what can I say... this gets us to the actual caller!
        frame = inspect.currentframe()
        frame = frame.f_back.f_back.f_back.f_back.f_back.f_back.f_back

        # This returns a tuple containing the last 5 elements of the frame
        # record which are:-
        #
        # - the filename
        # - the line number
        # - the function name
        # - the list of lines of context from the source code
        # - the index of the current line within that list
        filename, lineno, funcname, source, index = inspect.getframeinfo(frame)

        # The plugin definition's location is the directory containing the
        # module that it is defined in.
        self.location = os.path.dirname(filename)

        # We can't use 'inspect.getmodulename' here as it gets confused because
        # of our import hook in Envisage 8^(
        #
        # e.g. for the core plugin definition:-
        #
        # using inspect -> 'core_plugin_definition'
        # using ours    -> 'enthought.envisage.core.core_plugin_definition'
        return get_module_name(filename)

    def _include(self, module_name):
        """ Is the module name in the include set? """

        for item, include_children in self.include.items():
            if item == module_name:
                include = True
                break

            elif include_children and self._is_child_of(item, module_name):
                include = True
                break

        else:
            include = False

        return include

    def _exclude(self, module_name):
        """ Is the module name in the exclude set? """

        for item, exclude_children in self.exclude.items():
            if item == module_name:
                exclude = True
                break

            elif exclude_children and self._is_child_of(item, module_name):
                exclude = True
                break

        else:
            exclude = False

        return exclude

    def _is_child_of(self, x, y):
        """ Is 'y' a child symbol of 'x'?

        e.g.

        'foo.bar.baz' (y) is a child of 'foo.bar' (x)

        """

        if y.startswith(x):
            x_atoms = x.split('.')
            y_atoms = y.split('.')

            is_child_of = y_atoms[:len(x_atoms)] == x_atoms

        else:
            is_child_of = False

        return is_child_of

#### EOF ######################################################################
