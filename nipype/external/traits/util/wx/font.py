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
""" Font utilities. """


# Major package imports.
import wx


def clone_font(font):
    """ Clones the specified font. """

    point_size = font.GetPointSize()
    family = font.GetFamily()
    style = font.GetStyle()
    weight = font.GetWeight()
    underline = font.GetUnderlined()
    face_name = font.GetFaceName()

    clone = wx.Font(
        point_size, family, style, weight, underline, face_name,
    )

    return clone

def set_font_size(window, size):
    """ Recursively sets the font size starting from 'window'. """

    font = window.GetFont()

    clone = clone_font(font)
    clone.SetPointSize(size)

    window.SetFont(clone)

    sizer = window.GetSizer()
    if sizer is not None:
        sizer.Layout()

    window.Refresh()

    for child in window.GetChildren():
        set_font_size(child, size)

    return

def increase_font_size(window, delta=2):
    """ Recursively increases the font size starting from 'window'. """

    font = window.GetFont()

    clone = clone_font(font)
    clone.SetPointSize(font.GetPointSize() + delta)

    window.SetFont(clone)

    sizer = window.GetSizer()
    if sizer is not None:
        sizer.Layout()

    window.Refresh()

    for child in window.GetChildren():
        increase_font_size(child, delta)

    return

def decrease_font_size(window, delta=2):
    """ Recursively decreases the font size starting from 'window'. """

    increase_font_size(window, delta=-2)

    return

def set_bold_font(window):
    """ Set 'window's font to be bold. """

    font = window.GetFont()
    font.SetWeight(wx.BOLD)
    window.SetFont(font)

    return

#### EOF ######################################################################
