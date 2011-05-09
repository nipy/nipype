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
import wx

class ProgressDialog(wx.ProgressDialog):

    def __init__(self, *args, **kwds):

        wx.ProgressDialog.__init__(self, *args, **kwds)

    def SetButtonLabel(self, title):
        """ Change the Cancel button label to something else eg Stop."""
        button = self.FindWindowById(wx.ID_CANCEL)
        button.SetLabel(title)

        return
