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
# Description: <Enthought util package component>
#------------------------------------------------------------------------------
""" A thin visual divider. """


# Major package imports.
import wx


class Divider(wx.StaticLine):
    """ A thin visual divider. """

    def __init__(self, parent, id, **kw):
        """ Creates a divider. """

        # Base-class constructor.
        wx.StaticLine.__init__(self, parent, id, style=wx.LI_HORIZONTAL, **kw)

        # Create the widget!
        self._create_widget()

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self):
        """ Creates the widget. """

        self.SetSize((1, 1))

        return

#### EOF ######################################################################
