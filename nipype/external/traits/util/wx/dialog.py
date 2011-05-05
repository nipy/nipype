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
""" Dialog utilities. """


# Major package imports.
import wx

# A file dialog wildcard for Python files.
WILDCARD_PY = "Python files (*.py)|*.py|"

# A file dialog wildcard for text files.
WILDCARD_TXT = "Text files (*.txt)|*.txt|"

# A file dialog wildcard for all files.
WILDCARD_ALL = "All files (*.*)|*.*"

# A file dialog wildcard for Zip archives.
WILDCARD_ZIP = "Zip files (*.zip)|*.zip|"


class OpenFileDialog(wx.FileDialog):
    """ An open-file dialog. """

    def __init__(self, parent=None, **kw):
        """ Constructor. """

        style = wx.OPEN | wx.HIDE_READONLY

        # Base-class constructor.
        wx.FileDialog.__init__(self, parent, "Open", style=style, **kw)

        return

class OpenDirDialog(wx.DirDialog):
    """ An open-directory dialog. """

    def __init__(self, parent=None, **kw):
        """ Constructor. """

        style = wx.OPEN | wx.HIDE_READONLY | wx.DD_NEW_DIR_BUTTON

        # Base-class constructor.
        wx.DirDialog.__init__(self, parent, "Open", style=style, **kw)

        return

class SaveFileAsDialog(wx.FileDialog):
    """ A save-file dialog. """

    def __init__(self, parent=None, **kw):
        """ Constructor. """

        style = wx.SAVE | wx.OVERWRITE_PROMPT

        # Base-class constructor.
        wx.FileDialog.__init__(self, parent, "Save As", style=style, **kw)

        return


def confirmation(parent, message, title=None, default=wx.NO_DEFAULT):
    """ Displays a confirmation dialog. """

    dialog = wx.MessageDialog(
        parent,
        message,
        _get_title(title, parent, 'Confirmation'),
        wx.YES_NO | default | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP
    )

    result = dialog.ShowModal()
    dialog.Destroy()

    return result

def yes_no_cancel(parent, message, title=None, default=wx.NO_DEFAULT):
    """ Displays a Yes/No/Cancel dialog. """

    dialog = wx.MessageDialog(
        parent,
        message,
        _get_title(title, parent, 'Confirmation'),
        wx.YES_NO | wx.CANCEL | default | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP
    )

    result = dialog.ShowModal()
    dialog.Destroy()

    return result

def information(parent, message, title=None):
    """ Displays a modal information dialog. """

    dialog = wx.MessageDialog(
        parent,
        message,
        _get_title(title, parent, 'Information'),
        wx.OK | wx.ICON_INFORMATION | wx.STAY_ON_TOP
    )

    dialog.ShowModal()
    dialog.Destroy()

    return

def warning(parent, message, title=None):
    """ Displays a modal warning dialog. """

    dialog = wx.MessageDialog(
        parent,
        message,
        _get_title(title, parent, 'Warning'),
        wx.OK | wx.ICON_EXCLAMATION | wx.STAY_ON_TOP
    )

    dialog.ShowModal()
    dialog.Destroy()

    return

def error(parent, message, title=None):
    """ Displays a modal error dialog. """

    dialog = wx.MessageDialog(
        parent,
        message,
        _get_title(title, parent, 'Error'),
        wx.OK | wx.ICON_ERROR | wx.STAY_ON_TOP
    )

    dialog.ShowModal()
    dialog.Destroy()

    return

def _get_title(title, parent, default):
    """ Get a sensible title for a dialog! """

    if title is None:
        if parent is not None:
            title = parent.GetTitle()

        else:
            title = default

    return title

#### EOF ######################################################################
