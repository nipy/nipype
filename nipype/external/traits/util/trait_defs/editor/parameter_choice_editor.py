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
#  Define a new Choice editor
#
#  Written by: Lowell G. Vaughn
#
#  Date: 01/04/2005
#
#  Symbols defined: ParameterChoiceEditorFactory
#
#  (c) Copyright 2005 by Enthought, Inc.
#
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  imports:
#-------------------------------------------------------------------------------

import wx

from traitsui.wx.editor import Editor
from traitsui.editor_factory import EditorFactory as WxEditorFactory
from traits.api import Any, HasTraits, Int

class ChoiceEditorModel(HasTraits):
    "An interface for model for use with the ChoiceEditorFactory"
    def __init__(self, object):
        pass

    def get_labels(self):
        return []

    def get_object(self, index):
        return None

    def index_of(self, obj):
        return 0

class ParameterChoiceEditorFactory (WxEditorFactory):
    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------
    model_class = Any
    width=Int(100)

    def __init__(self, *args, **kwargs):
        #self.model_class = kwargs['model_class']
        # print self.model_class
        WxEditorFactory.__init__(self, *args, **kwargs)

    #---------------------------------------------------------------------------
    #  Performs any initialization needed after all constructor traits have
    #  been set:
    #---------------------------------------------------------------------------
    def init(self, *args):
        pass

    #---------------------------------------------------------------------------
    #  'Editor' factory methods:
    #---------------------------------------------------------------------------

    def simple_editor ( self, ui, object, name, description, parent ):
        model = self.model_class(object)
        # model.__init__(object)
        return SimpleEditor( parent,
                             factory     = self,
                             ui          = ui,
                             object      = object,
                             model       = model,
                             name        = name,
                             description = description,
                             width       = self.width )

    def custom_editor ( self, ui, object, name, description, parent ):
        model = self.model_class.__new__(self.model_class, object)
        model.__init__(object)
        return SimpleEditor( parent,
                             factory     = self,
                             ui          = ui,
                             object      = object,
                             model       = model,
                             name        = name,
                             description = description,
                             width       = self.width )


#-------------------------------------------------------------------------------
#  'SimpleEditor' class:
#-------------------------------------------------------------------------------

class SimpleEditor ( Editor ):
    model = Any
    width = Int(100)

#    def __init__(self, *args, **kwargs):
#        self.model = kwargs['model']
#        # print self.model
#        Editor.__init__(self, *args, **kwargs)
    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        self.control = wx.Choice( parent, -1, wx.Point( 0, 0 ),
                                  wx.Size( self.width, 20 ), self.model.get_labels() )
        wx.EVT_CHOICE( parent, self.control.GetId(), self.update_object )
        self.update_editor()

    #---------------------------------------------------------------------------
    #  Handles the user selecting a new value from the combo box:
    #---------------------------------------------------------------------------

    def update_object ( self, event ):
        """ Handles the user selecting a new value from the combo box.
        """
        self.value = self.model.get_object(event.GetSelection())

    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ Updates the editor when the object trait changes external to the
            editor.
        """
        #print ("Update Editor")
        idx = self.model.index_of(self.value)
        try:
            self.control.SetSelection( idx )
        except:
            #print "Pass"
            pass


