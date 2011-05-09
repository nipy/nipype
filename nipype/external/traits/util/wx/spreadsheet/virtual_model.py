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
from wx.grid import Grid, PyGridTableBase, GridCellAttr, GridTableMessage, GridCellFloatRenderer
from wx.grid import GRIDTABLE_NOTIFY_ROWS_DELETED, GRIDTABLE_NOTIFY_ROWS_APPENDED
from wx.grid import GRIDTABLE_NOTIFY_COLS_DELETED, GRIDTABLE_NOTIFY_COLS_APPENDED
from wx.grid import GRIDTABLE_REQUEST_VIEW_GET_VALUES
from wx.grid import GRID_VALUE_BOOL
from wx import ALIGN_LEFT, ALIGN_CENTRE, Colour

from default_renderer import DefaultRenderer

class VirtualModel(PyGridTableBase):
    """
    A custom wxGrid Table that expects a user supplied data source.
    THIS CLASS IS NOT LIMITED TO ONLY DISPLAYING LOG DATA!
    """
    def __init__(self, data, column_names):
        """data is currently a list of the form
        [(rowname, dictionary),
        dictionary.get(colname, None) returns the data for a cell
        """
        ##print 'Initializing virtual model'
        PyGridTableBase.__init__(self)
        self.set_data_source(data)
        self.colnames = column_names
        #self.renderers = {"DEFAULT_RENDERER":DefaultRenderer()}
        #self.editors = {}

        # we need to store the row length and col length to see if the table has changed size
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

#-------------------------------------------------------------------------------
# Implement/override the methods from PyGridTableBase
#-------------------------------------------------------------------------------

    def GetNumberCols(self):
        return len(self.colnames)

    def GetNumberRows(self):
        return len(self._data)

    def GetColLabelValue(self, col):
        return self.colnames[col]

    def GetRowLabelValue(self, row):
        return self._data[row][0]

    def GetValue(self, row, col):
        return str(self._data[row][1].get(self.GetColLabelValue(col), ""))

    def GetRawValue(self, row, col):
        return self._data[row][1].get(self.GetColLabelValue(col), "")

    def SetValue(self, row, col, value):
        print 'Setting value %d %d %s' % (row, col, value)
        print 'Before ', self.GetValue(row, col)
        self._data[row][1][self.GetColLabelValue(col)] = value
        print 'After ', self.GetValue(row, col)

    ''' def GetTypeName(self, row, col):
        if col == 2 or col == 6:
            res = "MeasurementUnits"
        elif col == 7:
            res = GRID_VALUE_BOOL
        else:
            res = self.base_GetTypeName(row, col)
        # print 'asked for type of col ', col, ' ' ,res
        return res'''

#-------------------------------------------------------------------------------
# Accessors for the Enthought data model (a dict of dicts)
#-------------------------------------------------------------------------------
    def get_data_source(self):
        """ The data structure we provide the data in.
        """
        return self._data

    def set_data_source(self, source):
        self._data = source
        return

#-------------------------------------------------------------------------------
# Methods controlling updating and editing of cells in grid
#-------------------------------------------------------------------------------

    def ResetView(self, grid):
        """
        (wxGrid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        ##print 'VirtualModel.reset_view'
        grid.BeginBatch()
        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), GRIDTABLE_NOTIFY_ROWS_DELETED, GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), GRIDTABLE_NOTIFY_COLS_DELETED, GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:
            if new < current:
                msg = GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)
        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

        # update the renderers
        # self._updateColAttrs(grid)
        # self._updateRowAttrs(grid) too expensive to use on a large grid

        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()


    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = GridTableMessage(self, GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

    def GetAttr88(self, row, col, someExtraParameter ):
        print 'Overridden GetAttr ', row, col
        """Part of a workaround to avoid use of attributes, queried by _PropertyGrid's IsCurrentCellReadOnly"""
        #property = self.GetPropertyForCoordinate( row, col )
        #object = self.GetObjectForCoordinate( row, col )
        #if property.ReadOnly( object ):
        attr = GridCellAttr()
        attr.SetReadOnly( 1 )
        return attr
        #return None


    def _updateColAttrs88(self, grid):
        """
        wxGrid -> update the column attributes to add the
        appropriate renderer given the column name.
        """
        for col, colname in enumerate(self.colnames):
            attr = GridCellAttr()
            #attr.SetAlignment(ALIGN_LEFT, ALIGN_CENTRE)
            if colname in self.renderers:
                # renderer = self.plugins[colname](self)
                renderer = self.renderers[colname]
                #if renderer.colSize:
                #    grid.SetColSize(col, renderer.colSize)
                #if renderer.rowSize:
                #    grid.SetDefaultRowSize(renderer.rowSize)
                # attr.SetReadOnly(False)
                # attr.SetRenderer(renderer)
            else:
                renderer = self.renderers["DEFAULT_RENDERER"] # .Clone()

            attr.SetRenderer(renderer)

            """else:
                #renderer = GridCellFloatRenderer(6,2)
                #attr.SetReadOnly(True)
                #attr.SetRenderer(renderer)"""

            if colname in self.editors:
                editor = self.editors[colname]
                attr.SetEditor(editor)

            grid.SetColAttr(col, attr)
        return

#------------------------------------------------------------------------------
# code to manipulate the table (non wx related)
#------------------------------------------------------------------------------

    def AppendRow(self, row):
        """ Append a tupe containing (name, data)
        """
        name, data = row
        print 'Appending ', name
        self._data.append(row)
        '''entry = {}
        for name in self.colnames:
            entry[name] = "Appended_%i"%row
        return'''

    def DeleteCols88(self, cols):
        """
        cols -> delete the columns from the dataset
        cols hold the column indices
        """
        # we'll cheat here and just remove the name from the
        # list of column names.  The data will remain but
        # it won't be shown
        deleteCount = 0
        cols = cols[:]
        cols.sort()
        for i in cols:
            self.colnames.pop(i-deleteCount)
            # we need to advance the delete count
            # to make sure we delete the right columns
            deleteCount += 1
        if not len(self.colnames):
            self.data = []

    def DeleteRow(self, row):
        name, data = row
        print 'Deleting ', name
        self._data.remove(row)

    def DeleteRows88(self, rows):
        """
        rows -> delete the rows from the dataset
        rows hold the row indices
        """
        deleteCount = 0
        rows = rows[:]
        rows.sort()
        for i in rows:
            self._data.pop(i-deleteCount)
            # we need to advance the delete count
            # to make sure we delete the right rows
            deleteCount += 1

    def SortColumn88(self, col):
        """
        to do - never tested
        tried to rename data to _data and _data to _tmp_data
        col -> sort the data based on the column indexed by col
        """
        name = self.colnames[col]
        _tmp_data = []
        for row in self._data:
            rowname, entry = row
            _tmp_data.append((entry.get(name, None), row))

        _tmp_data.sort()
        self._data = []
        for sortvalue, row in _tmp_data:
            self._data.append(row)
