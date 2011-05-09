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
#-------------------------------------------------------------------------------
#
#-------------------------------------------------------------------------------

import types
from string import atof
import wx
from wx.grid import PyGridCellRenderer

#-------------------------------------------------------------------------------

class DefaultRenderer(PyGridCellRenderer):
    """ This renderer provides the default representation of an
    Enthought spreadsheet cell.
    """

    selected_cells = wx.Brush(wx.Colour(255,255,200), wx.SOLID)
    normal_cells = wx.Brush("white", wx.SOLID)
    odd_cells = wx.Brush(wx.Colour(240,240,240), wx.SOLID)
    error_cells = wx.Brush(wx.Colour(255,122,122), wx.SOLID)
    warn_cells = wx.Brush(wx.Colour(255,242,0), wx.SOLID)

    def __init__(self, color="black", font="ARIAL", fontsize=8):
        PyGridCellRenderer.__init__(self)
        self.color = color
        self.foundary = font
        self.fontsize = fontsize
        self.font = wx.Font(fontsize, wx.DEFAULT, wx.NORMAL, wx.NORMAL,0, font)

    def Clone(self):
        return DefaultRenderer(self.color, self.foundary, self.fontsize)

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        self.DrawBackground(grid, attr, dc, rect, row, col, isSelected);
        self.DrawForeground(grid, attr, dc, rect, row, col, isSelected);
        dc.DestroyClippingRegion()
        return

    def DrawBackground(self, grid, attr, dc, rect, row, col, isSelected):
        """ Erases whatever is already in the cell by drawing over it.
        """
        # We have to set the clipping region on the grid's DC,
        # otherwise the text will spill over to the next cell
        dc.SetClippingRect(rect)

        # overwrite anything currently in the cell ...
        dc.SetBackgroundMode(wx.SOLID)

        dc.SetPen(wx.Pen(wx.WHITE, 1, wx.SOLID))

        if isSelected:
            dc.SetBrush(DefaultRenderer.selected_cells)
        elif row%2:
            dc.SetBrush(DefaultRenderer.normal_cells)
        else:
            dc.SetBrush(DefaultRenderer.odd_cells)

        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        return

    def DrawForeground(self, grid, attr, dc, rect, row, col, isSelected):
        """ Draws the cell (text) on top of the existing background color.
        """
        dc.SetBackgroundMode(wx.TRANSPARENT)
        text = grid.model.GetValue(row, col)
        dc.SetTextForeground(self.color)
        dc.SetFont(self.font)
        dc.DrawText(self.FormatText(text), rect.x+1, rect.y+1)

        self.DrawEllipses(grid, attr, dc, rect, row, col, isSelected);
        return

    def FormatText(self, text):
        """ Formats numbers to 3 decimal places.
        """
        try:
            text = '%0.3f' % atof(text)
        except:
            pass

        return text

    def DrawEllipses(self, grid, attr, dc, rect, row, col, isSelected):
        """ Adds three dots "..." to indicate the cell is truncated.
        """
        text = grid.model.GetValue(row, col)
        if not isinstance(text, basestring):
            msg = 'Problem appending "..." to cell: %d %d' % (row, col)
            raise TypeError, msg

        width, height = dc.GetTextExtent(text)
        if width > rect.width-2:
            width, height = dc.GetTextExtent("...")
            x = rect.x+1 + rect.width-2 - width
            dc.DrawRectangle(x, rect.y+1, width+1, height)
            dc.DrawText("...", x, rect.y+1)
        return

    def GetBestSize88(self, grid, attr, dc, row, col):
        """ This crashes the app - hmmmm. """
        size = PyGridCellRenderer.GetBestSize(self, grid, attr, dc, row, col)
        print '-----------------------------', size
        return size
#-------------------------------------------------------------------------------
