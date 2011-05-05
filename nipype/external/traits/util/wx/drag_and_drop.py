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
""" Drag and drop utilities. """

# Standard library imports.
import inspect

# Major package imports.
import wx


class Clipboard:
    """ The clipboard is used when dragging and dropping Python objects. """

    # fixme: This obviously only works within a single process!
    pass


clipboard = Clipboard()
clipboard.drop_source = None
clipboard.source      = None
clipboard.data        = None


class FileDropTarget(wx.FileDropTarget):
    """ Drop target for files. """

    def __init__(self, handler):
        """ Constructor. """

        # Base-class constructor.
        wx.FileDropTarget.__init__(self)

        self.handler = handler

        return

    def OnDropFiles(self, x, y, filenames):
        """ Called when the files have been dropped. """

        for filename in filenames:
            self.handler(x, y, filename)

        # Return True to accept the data, False to veto it.
        return True


# The data format for Python objects!
PythonObject = wx.CustomDataFormat('PythonObject')


class PythonDropSource(wx.DropSource):
    """ Drop source for Python objects. """

    def __init__(self, source, data, handler=None, allow_move=True):
        """ Creates a new drop source.

        A drop source should be created for *every* drag operation.

        If allow_move is False then the operation will default to
        a copy and only copy operations will be allowed.
        """

        # The handler can either be a function that will be called when
        # the data has been dropped onto the target, or an instance that
        # supports the 'on_dropped' method.
        self.handler = handler
        self.allow_move = allow_move

        # Put the data to be dragged on the clipboard.
        clipboard.data = data
        clipboard.source = source
        clipboard.drop_source = self

        # Create our own data format and use it in a custom data object.
        data_object = wx.CustomDataObject(PythonObject)
        data_object.SetData('dummy')

        # And finally, create the drop source and begin the drag
        # and drop opperation.
        wx.DropSource.__init__(self, source)
        self.SetData(data_object)
        if allow_move:
            flags = wx.Drag_DefaultMove | wx.Drag_AllowMove
        else:
            flags = wx.Drag_CopyOnly
        self.result = self.DoDragDrop(flags)

        return

    def on_dropped(self, drag_result):
        """ Called when the data has been dropped. """

        if self.handler is not None:
            if hasattr(self.handler, 'on_dropped'):
                # For backward compatibility we accept handler functions
                # with either 1 or 3 args, including self.  If there are
                # 3 args then we pass the data and the drag_result.
                args = inspect.getargspec(self.handler.on_dropped)[0]
                if len(args) == 3:
                    self.handler.on_dropped(clipboard.data, drag_result)
                else:
                    self.handler.on_dropped()
            else:
                #print self.handler

                # In this case we assume handler is a function.
                # For backward compatibility we accept handler functions
                # with either 0 or 2 args.  If there are 2 args then
                # we pass the data and drag_result
                args = inspect.getargspec(self.handler)[0]
                if len(args)==2:
                    self.handler(clipboard.data, drag_result)
                else:
                    self.handler()

        return


class PythonDropTarget(wx.PyDropTarget):
    """ Drop target for Python objects. """

    def __init__(self, handler):
        """ Constructor

        The handler can be either a function that will be called when
        *any* data is dropped onto the target, or an instance that supports
        the 'wx_drag_over' and 'wx_dropped_on' methods. The latter case
        allows the target to veto the drop.

        """

        # Base-class constructor.
        super(PythonDropTarget, self).__init__()

        # The handler can either be a function that will be called when
        # any data is dropped onto the target, or an instance that supports
        # the 'wx_drag_over' and 'wx_dropped_on' methods. The latter case
        # allows the target to veto the drop.
        self.handler = handler

        # Specify the type of data we will accept.
        self.data_object = wx.DataObjectComposite()
        self.data = wx.CustomDataObject(PythonObject)
        self.data_object.Add(self.data, preferred = True)
        self.file_data = wx.FileDataObject()
        self.data_object.Add(self.file_data)
        self.SetDataObject(self.data_object)

        return

    def OnData(self, x, y, default_drag_result):
        """ Called when OnDrop returns True. """

        # First, if we have a source in the clipboard and the source
        # doesn't allow moves then change the default to copy
        if clipboard.drop_source is not None and \
           not clipboard.drop_source.allow_move:
            default_drag_result = wx.DragCopy
        elif clipboard.drop_source is None:
            # This means we might be receiving a file; try to import
            # the right packages to nicely handle a file drop.  If those
            # packages can't be imported, then just pass through.
            if self.GetData():
                try:
                    from enthought.io import File
                    from enthought.naming.api import Binding

                    names = self.file_data.GetFilenames()
                    files = []
                    bindings = []
                    for name in names:
                        f = File(name)
                        files.append(f)
                        bindings.append(Binding(name = name, obj = f))
                    clipboard.data = files
                    clipboard.node = bindings
                except ImportError:
                    pass

        # Pass the object on the clipboard it to the handler.
        #
        # fixme: We allow 'wx_dropped_on' and 'on_drop' because both Dave
        # and Martin want different things! Unify!
        if hasattr(self.handler, 'wx_dropped_on'):
            drag_result = self.handler.wx_dropped_on(
                x, y, clipboard.data, default_drag_result
            )

        elif hasattr(self.handler, 'on_drop'):
            drag_result = self.handler.on_drop(
                x, y, clipboard.data, default_drag_result
            )

        else:
            self.handler(x, y, clipboard.data)
            drag_result = default_drag_result

        # Let the source of the drag/drop know that the operation is complete.
        drop_source = clipboard.drop_source
        if drop_source is not None:
            drop_source.on_dropped(drag_result)

        # Clean out the drop source!
        clipboard.drop_source = None

        # The return value tells the source what to do with the original data
        # (move, copy, etc.).  In this case we just return the suggested value
        # given to us.
        return default_drag_result

    # Some virtual methods that track the progress of the drag.
    def OnDragOver(self, x, y, default_drag_result):
        """ Called when a data object is being dragged over the target. """

        # First, if we have a source in the clipboard and the source
        # doesn't allow moves then change the default to copy
        data = clipboard.data
        if clipboard.drop_source is None:

            if not hasattr(self.handler, 'wx_drag_any'):
                # this is probably a file being dragged in, so just return
                return default_drag_result

            data = None

        elif not clipboard.drop_source.allow_move:
            default_drag_result = wx.DragCopy

        # The value returned here tells the source what kind of visual feedback
        # to give.  For example, if wxDragCopy is returned then only the copy
        # cursor will be shown, even if the source allows moves.  You can use
        # the passed in (x,y) to determine what kind of feedback to give.
        # In this case we return the suggested value which is based on whether
        # the Ctrl key is pressed.
        #
        # fixme: We allow 'wx_drag_over' and 'on_drag_over' because both Dave
        # and Martin want different things! Unify!
        if hasattr(self.handler, 'wx_drag_any'):
            drag_result = self.handler.wx_drag_any(
                x, y, data, default_drag_result
            )

        elif hasattr(self.handler, 'wx_drag_over'):
            drag_result = self.handler.wx_drag_over(
                x, y, data, default_drag_result
            )

        elif hasattr(self.handler, 'on_drag_over'):
            drag_result = self.handler.on_drag_over(
                x, y, data, default_drag_result
            )

        else:
            drag_result = default_drag_result

        return drag_result

    def OnLeave(self):
        """ Called when the mouse leaves the drop target. """

        if hasattr(self.handler, 'wx_drag_leave'):
            self.handler.wx_drag_leave(clipboard.data)

        return

    def OnDrop(self, x, y):
        """ Called when the user drops a data object on the target.

        Return 'False' to veto the operation.

        """

        return True

#### EOF #####################################################################
