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
""" Classes to provide a switcher. """


# Major package imports.
import wx
from wx.lib.scrolledpanel import ScrolledPanel as wxScrolledPanel

# Enthought library imports.
from traits.api import HasTraits, Int


class SwitcherModel(HasTraits):
    """ Base class for switcher models. """

    # The index of the selected 'page'.
    selected = Int(-1)

    def __init__(self):
        """ Creates a new switcher model. """

        # The items to display in the switcher control.
        self.items = [] # (str label, object value)

        return

    ###########################################################################
    # 'SwitcherModel' interface.
    ###########################################################################

    def create_page(self, parent, index):
        """ Creates a page for the switcher panel. """

        raise NotImplementedError


class SwitcherControl(wx.Panel):
    """ The default switcher control (a combo box). """

    def __init__(self, parent, id, model, label=None, **kw):
        """ Creates a new switcher control. """

        # Base-class constructor.
        wx.Panel.__init__(self, parent, id, **kw)

        # The switcher model that we are a controller for.
        self.model = model

        # The optional label.
        self.label = label

        # Create the widget!
        self._create_widget(model, label)

        # Listen for when the selected item in the model is changed.
        model.on_trait_change(self._on_selected_changed, 'selected')

        return

    ###########################################################################
    # Trait event handlers.
    ###########################################################################

    def _on_selected_changed(self, selected):
        """ Called when the selected item in the model is changed. """

        self.combo.SetSelection(selected)

        return

    ###########################################################################
    # wx event handlers.
    ###########################################################################

    def _on_combobox(self, event):
        """ Called when the combo box selection is changed. """

        combo = event.GetEventObject()

        # Update the model.
        self.model.selected = combo.GetSelection()

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self, model, label):
        """ Creates the widget."""

        self.sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        ##self.SetBackgroundColour("light grey")

        # Switcher combo.
        sizer.Add(self._combo(self, model, label), 1, wx.EXPAND)

        # Resize the panel to match the sizer's minimal size.
        sizer.Fit(self)

        return

    def _combo(self, parent, model, label):
        """ Creates the switcher combo. """

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Label.
        if label is not None:
            text = wx.StaticText(parent, -1, label)
            sizer.Add(text, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # Combo.
        self.combo = combo = wx.ComboBox(
            parent,
            -1,
            style=wx.CB_DROPDOWN | wx.CB_READONLY
        )
        sizer.Add(combo, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, 5)

        # Ask the model for the available options.
        items = model.items
        if len(items) > 0:
            for name, data in model.items:
                combo.Append(name, data)

        # Listen for changes to the selected item.
        wx.EVT_COMBOBOX(self, combo.GetId(), self._on_combobox)

        # If the model's selected variable has been set ...
        if model.selected != -1:
            combo.SetSelection(model.selected)

        return sizer


class SwitcherPanel(wxScrolledPanel):
    """ The default switcher panel. """

    def __init__(self, parent, id, model, label=None, cache=True, **kw):

        # Base-class constructor.
        wxScrolledPanel.__init__(self, parent, id, **kw)
        self.SetupScrolling()

        # The switcher model that we are a panel for.
        self.model = model

        # Should we cache pages as we create them?
        self.cache = cache

        # The page cache (if caching was requested).
        self._page_cache = {}

        # The currently displayed page.
        self.current = None

        # Create the widget!
        self._create_widget(model, label)

        # Listen for when the selected item in the model is changed.
        #model.on_trait_change(self._on_selected_changed, 'selected')

        return

    ###########################################################################
    # 'SwitcherPanel' interface.
    ###########################################################################

    def show_page(self, index):
        """ Shows the page at the specified index. """

        self._show_page(index)

        return

    ###########################################################################
    # Trait event handlers.
    ###########################################################################

    def _on_selected_changed(self, selected):
        """ Called when the selected item in the model is changed. """

        self._show_page(selected)

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self, model, label):
        """ Creates the widget. """

        self.sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        ##self.SetBackgroundColour('red')

        #if model.selected != -1:
        #    self._show_page(model.selected)

        # Nothing to add here as we add the panel contents lazily!
        pass

        # Resize the panel to match the sizer's minimal size.
        sizer.Fit(self)

        return

    def _show_page(self, index):
        """ Shows the page at the specified index. """

        # If a page is already displayed then hide it.
        if self.current is not None:
            current_size = self.current.GetSize()
            self.current.Show(False)
            self.sizer.Remove(self.current)

        # Is the page in the cache?
        page = self._page_cache.get(index)
        if not self.cache or page is None:
            # If not then ask our panel factory to create it.
            page = self.model.create_page(self, index)

            # Add it to the cache!
            self._page_cache[index] = page

        #if self.current is not None:
        #    page.SetSize(current_size)

        # Display the page.
        self.sizer.Add(page, 15, wx.EXPAND, 5)
        page.Show(True)

        self.current = page

        # Force a new layout of the sizer's children but KEEPING the current
        # dimension.
        self.sizer.Layout()
        #self.sizer.Fit(self)
        #self.SetupScrolling()

        return


class Switcher(wx.Panel):
    """ A switcher. """

    def __init__(self, parent, id, model, label=None, **kw):
        """ Create a new switcher. """

        # Base-class constructor.
        wx.Panel.__init__(self, parent, id, **kw)

        # The model that we are a switcher for.
        self.model = model

        # Create the widget!
        self._create_widget(model, label)

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_widget(self, model, label):
        """ Creates the widget. """

        self.sizer = sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        # Switcher control.
        self.control = control = SwitcherControl(self, -1, model, label)
        sizer.Add(control, 0, wx.EXPAND)

        # Switcher panel.
        self.panel = panel = SwitcherPanel(self, -1, model, label)
        sizer.Add(panel, 1, wx.EXPAND)

        # Resize the panel to match the sizer's minimal size.
        sizer.Fit(self)

        return

#### EOF ######################################################################
