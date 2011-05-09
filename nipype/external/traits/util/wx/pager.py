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
""" A pager contains a set of pages, but only shows one at a time. """


# Major package imports.
import wx
from wx.lib.scrolledpanel import wxScrolledPanel


class Pager(wxScrolledPanel):
    """ A pager contains a set of pages, but only shows one at a time. """


    def __init__(self, parent, wxid, **kw):
        """ Creates a new pager. """

        # Base-class constructor.
        wxScrolledPanel.__init__(self, parent, wxid, **kw)
        self.SetupScrolling()

        # The pages in the pager!
        self._pages = {} # { str name : wx.Window page }

        # The page that is currently displayed.
        self._current_page = None

        # Create the widget!
        self._create_widget()

        return

    ###########################################################################
    # 'Pager' interface.
    ###########################################################################

    def add_page(self, name, page):
        """ Adds a page with the specified name. """

        self._pages[name] = page

        # Make the pager panel big enought ot hold the biggest page.
        #
        # fixme: I have a feeling this needs some testing!
        sw, sh = self.GetSize()
        pw, ph = page.GetSize()
        self.SetSize((max(sw, pw), max(sh, ph)))

        # All pages are added as hidden.  Use 'show_page' to make a page
        # visible.
        page.Show(False)

        return page

    def show_page(self, name):
        """ Shows the page with the specified name. """

        # Hide the current page (if one is displayed).
        if self._current_page is not None:
            self._hide_page(self._current_page)

        # Show the specified page.
        page = self._show_page(self._pages[name])

        # Resize the panel to match the sizer's minimal size.
        self._sizer.Fit(self)

        return page

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self):
        """ Creates the widget. """

        self._sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        return

    def _hide_page(self, page):
        """ Hides the specified page. """

        page.Show(False)
        self._sizer.Remove(page)

        return

    def _show_page(self, page):
        """ Shows the specified page. """

        page.Show(True)
        self._sizer.Add(page, 1, wx.EXPAND)

        self._current_page = page

        return page

#### EOF ######################################################################
