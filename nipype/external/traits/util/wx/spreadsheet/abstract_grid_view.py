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
from numpy import arange

import wx
from wx.grid import Grid, PyGridTableBase
from wx.grid import PyGridCellRenderer
from wx.grid import GridCellTextEditor, GridCellStringRenderer
from wx.grid import GridCellFloatRenderer, GridCellFloatEditor

from wx.lib.mixins.grid import GridAutoEditMixin


class ComboboxFocusHandler(wx.EvtHandler):
    """ Workaround for combobox focus problems in wx 2.6."""

    # This is copied from enthought/pyface/grid.combobox_focus_handler.py.
    # Since this was the only thing that traits.util.wx needed from pyface,
    # and it's a temporary workaround for an outdated version of wx, we're just
    # copying it here instead of introducing a dependency on a large package.

    def __init__(self):
        wx.EvtHandler.__init__(self)
        wx.EVT_KILL_FOCUS(self, self._on_kill_focus)
        return

    def _on_kill_focus(self, evt):

        # this is pretty egregious. somehow the combobox gives up focus
        # as soon as it starts up, causing the grid to remove the editor.
        # so we just don't let it give up focus. i suspect this will cause
        # some other problem down the road, but it seems to work for now.
        # fixme: remove this h*ck once the bug is fixed in wx.
        editor = evt.GetEventObject()
        if isinstance(editor, wx._controls.ComboBox) and \
               evt.GetWindow() is None:
            return
        evt.Skip()
        return


class AbstractGridView(Grid):
    """ Enthought's default spreadsheet view.

    Uses a virtual data source.

    THIS CLASS IS NOT LIMITED TO ONLY DISPLAYING LOG DATA!
    """

    def __init__(self, parent, ID=-1, **kw):

        Grid.__init__(self, parent, ID, **kw)

        # We have things set up to edit on a single click - so we have to select
        # an initial cursor location that is off of the screen otherwise a cell
        # will be in edit mode as soon as the grid fires up.
        self.moveTo = [1000,1]
        self.edit = False

        # this seems like a busy idle ...
        wx.EVT_IDLE(self, self.OnIdle)

        # Enthought specific display controls ...
        self.init_labels()
        self.init_data_types()
        self.init_handlers()

        wx.grid.EVT_GRID_EDITOR_CREATED(self, self._on_editor_created)

        return


    # needed to handle problem in wx 2.6 with combobox cell editors
    def _on_editor_created(self, evt):

        editor = evt.GetControl()
        editor.PushEventHandler(ComboboxFocusHandler())

        evt.Skip()
        return

    def init_labels(self):
        self.SetLabelFont(wx.Font(self.GetFont().GetPointSize(),
                                  wx.SWISS, wx.NORMAL, wx.BOLD))
        self.SetGridLineColour("blue")
        self.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        return

    def init_data_types(self):
        """ If the model says a cell is of a specified type, the grid uses
        the specific renderer and editor set in this method.
        """
        self.RegisterDataType("LogData", GridCellFloatRenderer(precision=3), GridCellFloatEditor())

        return

    def init_handlers(self):

        wx.grid.EVT_GRID_CELL_LEFT_CLICK(self, self.OnCellLeftClick)
        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(self, self.OnCellRightClick)
        wx.grid.EVT_GRID_CELL_LEFT_DCLICK(self, self.OnCellLeftDClick)
        wx.grid.EVT_GRID_CELL_RIGHT_DCLICK(self, self.OnCellRightDClick)

        wx.grid.EVT_GRID_LABEL_LEFT_CLICK(self, self.OnLabelLeftClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_CLICK(self, self.OnLabelRightClick)
        wx.grid.EVT_GRID_LABEL_LEFT_DCLICK(self, self.OnLabelLeftDClick)
        wx.grid.EVT_GRID_LABEL_RIGHT_DCLICK(self, self.OnLabelRightDClick)

        wx.grid.EVT_GRID_ROW_SIZE(self, self.OnRowSize)
        wx.grid.EVT_GRID_COL_SIZE(self, self.OnColSize)

        wx.grid.EVT_GRID_RANGE_SELECT(self, self.OnRangeSelect)
        wx.grid.EVT_GRID_CELL_CHANGE(self, self.OnCellChange)
        wx.grid.EVT_GRID_SELECT_CELL(self, self.OnSelectCell)

        wx.grid.EVT_GRID_EDITOR_SHOWN(self, self.OnEditorShown)
        wx.grid.EVT_GRID_EDITOR_HIDDEN(self, self.OnEditorHidden)
        wx.grid.EVT_GRID_EDITOR_CREATED(self, self.OnEditorCreated)

        return

    def SetColLabelsVisible(self, show=True):
        """ This only works if you 'hide' then 'show' the labels.
        """
        if not show:
            self._default_col_label_size = self.GetColLabelSize()
            self.SetColLabelSize(0)
        else:
            self.SetColLabelSize(self._default_col_label_size)
        return

    def SetRowLabelsVisible(self, show=True):
        """ This only works if you 'hide' then 'show' the labels.
        """
        if not show:
            self._default_row_label_size = self.GetRowLabelSize()
            self.SetRowLabelSize(0)
        else:
            self.SetRowLabelSize(self._default_row_label_size)
        return

    def SetTable(self, table, *args):
        """ Some versions of wxPython do not return the correct
        table - hence we store our own copy here - weak ref?
        todo - does this apply to Enthought?
        """
        self._table = table
        return Grid.SetTable(self, table, *args)

    def GetTable(self):
        # Terminate editing of the current cell to force an update of the table
        self.DisableCellEditControl()
        return self._table

    def Reset(self):
        """ Resets the view based on the data in the table.

        Call this when rows are added or destroyed.
        """
        self._table.ResetView(self)

    def OnCellLeftClick(self, evt):
        evt.Skip()

    def OnCellRightClick(self, evt):
        #print self.GetDefaultRendererForCell(evt.GetRow(), evt.GetCol())
        evt.Skip()

    def OnCellLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()
        evt.Skip()

    def OnCellRightDClick(self, evt):
        evt.Skip()

    def OnLabelLeftClick(self, evt):
        evt.Skip()

    def OnLabelRightClick(self, evt):
        evt.Skip()

    def OnLabelLeftDClick(self, evt):
        evt.Skip()

    def OnLabelRightDClick(self, evt):
        evt.Skip()

    def OnRowSize(self, evt):
        evt.Skip()

    def OnColSize(self, evt):
        evt.Skip()

    def OnRangeSelect(self, evt):
        #if evt.Selecting():
        #    print "OnRangeSelect: top-left %s, bottom-right %s\n" % (evt.GetTopLeftCoords(), evt.GetBottomRightCoords())
        evt.Skip()

    def OnCellChange(self, evt):
        evt.Skip()

    def OnIdle(self, evt):
        """ Immediately jumps into editing mode, bypassing the usual select mode
        of a spreadsheet. See also self.OnSelectCell().
        """

        if self.edit == True:
            if self.CanEnableCellControl():
                self.EnableCellEditControl()
            self.edit = False

        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None

        evt.Skip()

    def OnSelectCell(self, evt):

        """ Immediately jumps into editing mode, bypassing the usual select mode
        of a spreadsheet. See also self.OnIdle().
        """
        self.edit = True
        evt.Skip()

    def OnEditorShown(self, evt):
        evt.Skip()

    def OnEditorHidden(self, evt):
        evt.Skip()

    def OnEditorCreated(self, evt):
        evt.Skip()
#-------------------------------------------------------------------------------
