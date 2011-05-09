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
# Description: <Enthought logger package component>
#------------------------------------------------------------------------------

# Standard library imports.
import logging

# Enthought library imports.
from pyface.api import Dialog
from traits.api import Any, Str, Tuple


# Setup a logger for this module.
logger = logging.getLogger(__name__)


priority_levels = ['Low', 'Medium', 'High', 'Critical']


class QualityAgentView(Dialog):

    size = Tuple((700, 900))
    title = Str('Quality Agent')

    # The associated LoggerService.
    service = Any()

    msg = Str('')
    subject = Str('Untitled Error Report')
    to_address = Str()
    cc_address = Str('')
    from_address = Str()
    smtp_server = Str()
    priority = Str(priority_levels[2])
    comments = Str('None')
    include_userdata = Any

    ###########################################################################
    # Protected 'Dialog' interface.
    ###########################################################################

    # fixme: Ideally, this should be passed in; this topic ID belongs to the
    #        Enlib help project/plug-in.
    help_id = 'enlib|HID_Quality_Agent_Dlg'

    def _create_dialog_area(self, parent):
        """ Creates the main content of the dialog. """
        import wx

        parent.SetSizeHints(minW=300, minH=575)

        # Add the main panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(parent, -1)
        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)


        # Add a descriptive label at the top ...
        label = wx.StaticText(panel, -1, "Send a comment or bug report ...")
        sizer.Add(label, 0, wx.ALL, border=5)

        # Add the stack trace view ...
        error_panel = self._create_error_panel(panel)
        sizer.Add(error_panel, 1, wx.ALL|wx.EXPAND|wx.CLIP_CHILDREN, border=5)

        # Update the layout:
        sizer.Fit(panel)

        # Add the error report view ...
        report_panel = self._create_report_panel(panel)
        sizer.Add(report_panel, 2, wx.ALL|wx.EXPAND|wx.CLIP_CHILDREN, border=5)

        # Update the layout:
        sizer.Fit(panel)

        return panel


    def _create_buttons(self, parent):
        """ Creates the buttons. """
        import wx

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 'Send' button.
        send = wx.Button(parent, wx.ID_OK, "Send")
        wx.EVT_BUTTON(parent, wx.ID_OK, self._on_send)
        sizer.Add(send)
        send.SetDefault()

        # 'Cancel' button.
        cancel = wx.Button(parent, wx.ID_CANCEL, "Cancel")
        wx.EVT_BUTTON(parent, wx.ID_CANCEL, self._wx_on_cancel)
        sizer.Add(cancel, 0, wx.LEFT, 10)

        # 'Help' button.
        if len(self.help_id) > 0:
            help = wx.Button(parent, wx.ID_HELP, "Help")
            wx.EVT_BUTTON(parent, wx.ID_HELP, self._wx_on_help)
            sizer.Add(help, 0, wx.LEFT, 10)

        return sizer

    def _on_help(self, event):
        """Called when the 'Help' button is pressed. """

        hp = self.service.application.get_service('enthought.help.IHelp')
        hp.library.show_topic(self.help_id)

        return


    ### Utility methods #######################################################

    def _create_error_panel(self, parent):
        import wx

        box = wx.StaticBox(parent, -1, "Message:")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Print the stack trace
        label2 = wx.StaticText(parent, -1,"The following information will be included in the report:")
        sizer.Add(label2, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.CLIP_CHILDREN, border=5)

        details = wx.TextCtrl(parent, -1, self.msg, size=(-1,75),
                              style=wx.TE_MULTILINE |
                                    wx.TE_READONLY |
                                    wx.HSCROLL |
                                    wx.VSCROLL |
                                    wx.TE_RICH2 |
                                    wx.CLIP_CHILDREN)
        details.SetSizeHints(minW=-1, minH=75)
        # Set the font to not be proportional
        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)
        details.SetStyle(0, len(self.msg), wx.TextAttr(font=font))
        sizer.Add(details, 1, wx.EXPAND|wx.ALL|wx.CLIP_CHILDREN, 5)


        return sizer


    def _create_report_panel(self, parent):
        import wx

        box = wx.StaticBox(parent, -1, "Report Information:")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # Add email info ...
        sizer.Add(self._create_email_info(parent), 0, wx.ALL|wx.EXPAND, 5)

        # Add priority combo:
        sizer.Add(self._create_priority_combo(parent), 0, wx.ALL|wx.RIGHT, 5)

        # Extra comments from the user:
        label3 = wx.StaticText(parent, -1, "Additional Comments:")
        sizer.Add(label3, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.CLIP_CHILDREN, 5)

        comments_field = wx.TextCtrl(parent, -1, self.comments, size=(-1,75),
                                     style=wx.TE_MULTILINE |
                                           wx.TE_RICH2 |
                                           wx.CLIP_CHILDREN)
        comments_field.SetSizeHints(minW=-1, minH=75)
        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL)
        comments_field.SetStyle(0, len(self.comments), wx.TextAttr(font=font))
        sizer.Add(comments_field, 1, wx.ALL|wx.EXPAND|wx.CLIP_CHILDREN, 5)
        wx.EVT_TEXT(parent, comments_field.GetId(), self._on_comments)

        # Include the project combobox?
        if len(self.service.mail_files) > 0:
            sizer.Add(self._create_project_upload(parent), 0, wx.ALL, border=5)

        return sizer


    def _create_email_info(self, parent):
        import wx

        # Layout setup ..
        sizer = wx.FlexGridSizer(5,2,10,10)
        sizer.AddGrowableCol(1)

        title_label = wx.StaticText(parent, -1, "Subject:")
        sizer.Add(title_label , 0, wx.ALL|wx.ALIGN_RIGHT)
        title_field = wx.TextCtrl(parent, -1, self.subject, wx.Point(-1,-1))
        sizer.Add(title_field, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.CLIP_CHILDREN)
        wx.EVT_TEXT(parent, title_field.GetId(), self._on_subject)

        to_label = wx.StaticText(parent, -1, "To:")
        sizer.Add(to_label , 0, wx.ALL|wx.ALIGN_RIGHT)
        to_field = wx.TextCtrl(parent, -1, self.to_address)
        sizer.Add(to_field, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.CLIP_CHILDREN)
        wx.EVT_TEXT(parent, to_field.GetId(), self._on_to)

        cc_label = wx.StaticText(parent, -1, "Cc:")
        sizer.Add(cc_label, 0, wx.ALL|wx.ALIGN_RIGHT)
        cc_field = wx.TextCtrl(parent, -1, "")
        sizer.Add(cc_field, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.CLIP_CHILDREN)
        wx.EVT_TEXT(parent, cc_field.GetId(), self._on_cc)

        from_label = wx.StaticText(parent, -1, "From:")
        sizer.Add(from_label, 0, wx.ALL|wx.ALIGN_RIGHT)
        from_field = wx.TextCtrl(parent, -1, self.from_address)
        sizer.Add(from_field, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.CLIP_CHILDREN)
        wx.EVT_TEXT(parent, from_field.GetId(), self._on_from)

        smtp_label = wx.StaticText(parent, -1, "SMTP Server:")
        sizer.Add(smtp_label, 0, wx.ALL|wx.ALIGN_RIGHT)
        smtp_server_field = wx.TextCtrl(parent, -1, self.smtp_server)
        sizer.Add(smtp_server_field, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT|wx.CLIP_CHILDREN)
        wx.EVT_TEXT(parent, smtp_server_field.GetId(), self._on_smtp_server)

        return sizer


    def _create_priority_combo(self, parent):
        import wx

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(parent, -1, "How critical is this issue?")
        sizer.Add(label, 0, wx.ALL, border=0)

        cb = wx.ComboBox(parent, -1, self.priority,
                         wx.Point(90, 50), wx.Size(95, -1),
                         priority_levels, wx.CB_READONLY)
        sizer.Add(cb, 1, wx.EXPAND|wx.LEFT|wx.CLIP_CHILDREN, border=10)

        wx.EVT_COMBOBOX(parent, cb.GetId(), self._on_priority)

        return sizer


    def _create_project_upload(self, parent):
        import wx

        id = wx.NewId()
        cb = wx.CheckBox(parent, id, "Include Workspace Files (will increase email size)        ",
                                wx.Point(65, 80), wx.Size(-1, 20), wx.NO_BORDER)
        wx.EVT_CHECKBOX(parent, id, self._on_project)

        return cb


    ## UI Listeners ###########################################################

    def _on_subject(self, event):
        self.subject = event.GetEventObject().GetValue()


    def _on_to(self, event):
        self.to_address = event.GetEventObject().GetValue()


    def _on_cc(self, event):
        self.cc_address = event.GetEventObject().GetValue()


    def _on_from(self, event):
        self.from_address = event.GetEventObject().GetValue()


    def _on_smtp_server(self, event):
        self.smtp_server = event.GetEventObject().GetValue()


    def _on_priority(self, event):
        self.priority = event.GetEventObject().GetStringSelection()


    def _on_comments(self, event):
        self.comments = event.GetEventObject().GetValue()


    def _on_project(self, event):
        self.include_userdata = event.Checked()
        cb = event.GetEventObject()

        if event.Checked():
            cb.SetLabel("Include Workspace Files (approx. %.2f MBytes)" % self._compute_project_size())
        else:
            cb.SetLabel("Include Workspace Files (will increase email size)")
        return

    def _on_send(self, event):
        import wx
        # Disable the Send button while we go through the possibly
        # time-consuming email-sending process.
        button = event.GetEventObject()
        button.Enable(0)

        fromaddr, toaddrs, ccaddrs = self._create_email_addresses()
        message = self._create_email(fromaddr, toaddrs, ccaddrs)

        self.service.send_bug_report(self.smtp_server, fromaddr, toaddrs,
            ccaddrs, message)

        # save the user's preferences
        self.service.preferences.smtp_server = self.smtp_server
        self.service.preferences.to_address = self.to_address
        self.service.preferences.from_address = self.from_address

        # finally we close the dialog
        self._wx_on_ok(event)

        return

    ## Private ################################################################

    def _create_email_addresses(self):
        # utility function map addresses from ui into the standard format
        # FIXME: We should use standard To: header parsing instead of this ad
        # hoc whitespace-only approach.
        fromaddr = self.from_address
        if "" == fromaddr.strip():
            fromaddr = "anonymous"
        toaddrs = self.to_address.split()
        ccaddrs = self.cc_address.split()

        return fromaddr, toaddrs, ccaddrs


    def _compute_project_size(self):
        # determine size of email in MBytes
        fromaddr, toaddrs, ccaddrs = self._create_email_addresses()
        message = self._create_email(fromaddr, toaddrs, ccaddrs)
        return len(message.as_string()) / (2.0**20)


    def _create_email(self, fromaddr, toaddrs, ccaddrs):
        return self.service.create_email_message(
            fromaddr, toaddrs, ccaddrs,
            self.subject,
            self.priority,
            self.include_userdata,
            self.msg,
            self.comments,
        )

    def _to_address_default(self):
        return self.service.preferences.to_address

    def _from_address_default(self):
        return self.service.preferences.from_address

    def _smtp_server_default(self):
        return self.service.preferences.smtp_server

####### EOF #############################################################
