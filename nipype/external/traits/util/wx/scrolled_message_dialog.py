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
from wx.lib.layoutf import Layoutf

class ScrolledMessageDialog(wx.Dialog):
    def __init__(self, parent, msg, caption, pos = wx.DefaultPosition, size = (500,300)):

        wx.Dialog.__init__(self, parent, -1, caption, pos, size)
        x, y = pos
        if x == -1 and y == -1:
            self.CenterOnScreen(wx.BOTH)

        text = wx.TextCtrl(self, -1, msg, wx.DefaultPosition, wx.DefaultSize,
                             wx.TE_READONLY |
                             wx.TE_MULTILINE |
                             wx.HSCROLL |
                             wx.TE_RICH2
                             )

        font = wx.Font(8, wx.MODERN, wx.NORMAL, wx.NORMAL)
        text.SetStyle(0, len(msg), wx.TextAttr(font=font))

        ok = wx.Button(self, wx.ID_OK, "OK")
        text.SetConstraints(Layoutf('t=t5#1;b=t5#2;l=l5#1;r=r5#1', (self,ok)))
        ok.SetConstraints(Layoutf('b=b5#1;x%w50#1;w!80;h!25', (self,)))

        self.SetAutoLayout(1)
        self.Layout()


