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
""" A null log handler. """


# Standard library imports.
import logging


class NullHandler(logging.Handler):
    """ A null log handler.

    This is a quick hack so that we can start to refactor the 'logger'
    module since it used to add actual handlers at module load time.

    Now we only add this handler so that people using just the ETS library and
    not one of our applications won't see the warning about 'no handlers'.

    """

    ###########################################################################
    # 'Handler' interface.
    ###########################################################################

    def emit(self, record):
        """ Emits a log record. """

        pass

#### EOF ######################################################################
