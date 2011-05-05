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

try:
    from enthought.units.unit_parser import unit_parser
except ImportError:
    unit_parser = None

from default_renderer import DefaultRenderer

class UnitRenderer(DefaultRenderer):

    def DrawForeground(self, grid, attr, dc, rect, row, col, isSelected):
        dc.SetBackgroundMode(wx.TRANSPARENT)
        text = grid.model.GetValue(row, col)
        #print 'Rendering ', row, col, text, text.__class__
        dc.SetFont(self.font)
        dc.DrawText(text, rect.x+1, rect.y+1)

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

        text = grid.model.GetValue(row, col)

        if isSelected:
            dc.SetBrush(DefaultRenderer.selected_cells)
        elif unit_parser and unit_parser.parse_unit(text).is_valid():
            dc.SetBrush(DefaultRenderer.normal_cells)
        else:
            dc.SetBrush(DefaultRenderer.error_cells)

        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        return
#-------------------------------------------------------------------------------

class MultiUnitRenderer(DefaultRenderer):

    def __init__( self, color="black", font="ARIAL", fontsize=8,
                  suppress_warnings=False):

        self.suppress_warnings = suppress_warnings
        DefaultRenderer.__init__( self, color, font, fontsize )

    def DrawForeground(self, grid, attr, dc, rect, row, col, isSelected):
        dc.SetBackgroundMode(wx.TRANSPARENT)
        text = grid.model.GetValue(row, col)
        dc.SetFont(self.font)
        dc.DrawText(text, rect.x+1, rect.y+1)

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

        text = grid.model.GetValue(row, col)
        if unit_parser:
            this_unit = unit_parser.parse_unit(text, self.suppress_warnings)
        else:
            this_unit = None

        # Todo - clean up this hardcoded logic/column position mess

        family = grid.model.GetValue(row, 6)

        # AI units of 'impedance ((kg/s)*(g/cc))' creates list of 3, not 2!
        try:
            family, other_text = family[:-1].split('(')
        except:
            family, other_text = family[:-1].split(' ')

        if unit_parser:
            other_unit = unit_parser.parse_unit(other_text, self.suppress_warnings)
            dimensionally_equivalent = this_unit.can_convert(other_unit)
        else:
            other_unit = None
            dimensionally_equivalent = False

        if isSelected:
            dc.SetBrush(DefaultRenderer.selected_cells)
        elif not this_unit or not this_unit.is_valid():
            dc.SetBrush(DefaultRenderer.error_cells)
        elif not dimensionally_equivalent:
            dc.SetBrush(DefaultRenderer.warn_cells)
        else:
            dc.SetBrush(DefaultRenderer.normal_cells)

        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)
        return
