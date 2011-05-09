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

# Standard library imports
from datetime import datetime
import logging

# Enthought library imports.
from pyface.api import ImageResource, clipboard
from pyface.workbench.api import TraitsUIView
from traits.api import Button, Instance, List, Property, Str, \
    cached_property, on_trait_change
from traitsui.api import View, Group, Item, CodeEditor, \
    TabularEditor, spring
from traitsui.tabular_adapter import TabularAdapter

# Local imports
from traits.logger.agent.quality_agent_view import QualityAgentView
from traits.logger.plugin import view
from traits.logger.plugin.logger_service import LoggerService

# Constants
_IMAGE_MAP = { logging.DEBUG: ImageResource('debug'),
               logging.INFO: ImageResource('info'),
               logging.WARNING: ImageResource('warning'),
               logging.ERROR: ImageResource('error'),
               logging.CRITICAL: ImageResource('crit_error') }


class LogRecordAdapter(TabularAdapter):
    """ A TabularEditor adapter for logging.LogRecord objects.
    """

    columns = [ ('Level', 'level'), ('Date', 'date'), ('Time', 'time'),
                ('Message', 'message') ]
    column_widths = [ 80, 100, 120, -1 ]

    level_image = Property
    level_text = Property(Str)
    date_text = Property(Str)
    time_text = Property(Str)
    message_text = Property(Str)

    def get_width(self, object, trait, column):
        return self.column_widths[column]

    def _get_level_image(self):
        return _IMAGE_MAP[self.item.levelno]

    def _get_level_text(self):
        return self.item.levelname.capitalize()

    def _get_date_text(self):
        dt = datetime.fromtimestamp(self.item.created)
        return dt.date().isoformat()

    def _get_time_text(self):
        dt = datetime.fromtimestamp(self.item.created)
        return dt.time().isoformat()

    def _get_message_text(self):
        # Just display the first line of multiline messages, like stacktraces.
        msg = self.item.getMessage()
        msgs = msg.strip().split('\n')
        if len(msgs) > 1:
            suffix = '... [double click for details]'
        else:
            suffix = ''
        abbrev_msg = msgs[0] + suffix
        return abbrev_msg


class LoggerView(TraitsUIView):
    """ The Workbench View showing the list of log items.
    """

    id = Str('traits.logger.plugin.view.logger_view.LoggerView')
    name = Str('Logger')
    service = Instance(LoggerService)

    log_records = List(Instance(logging.LogRecord))
    formatted_records = Property(Str, depends_on='log_records')

    activated = Instance(logging.LogRecord)
    activated_text = Property(Str, depends_on='activated')
    reset_button = Button("Reset Logs")
    show_button = Button("Complete Text Log")
    copy_button = Button("Copy Log to Clipboard")


    code_editor = CodeEditor(lexer='null',
                             show_line_numbers=False)
    log_records_editor = TabularEditor(adapter=LogRecordAdapter(),
                                       editable=False,
                                       activated='activated')
    trait_view = View(Group(Item('log_records',
                                 editor=log_records_editor),
                            Group(Item('reset_button'),
                                  spring,
                                  Item('show_button'),
                                  Item('copy_button'),
                                  orientation='horizontal',
                                  show_labels=False),
                            show_labels=False))

    ###########################################################################
    # LogQueueHandler view interface
    ###########################################################################

    def update(self, force=False):
        """ Update 'log_records' if our handler has new records or 'force' is
            set.
        """
        service = self.service
        if service.handler.has_new_records() or force:
            self.log_records = [ rec for rec in service.handler.get()
                                 if rec.levelno >= service.preferences.level_ ]

    ###########################################################################
    # Private interface
    ###########################################################################

    @on_trait_change('service.preferences.level_')
    def _update_log_records(self):
        self.service.handler._view = self
        self.update(force=True)

    def _reset_button_fired(self):
        self.service.handler.reset()
        self.log_records = []

    def _show_button_fired(self):
        self.edit_traits(view=View(Item('formatted_records',
                                        editor=self.code_editor,
                                        style='readonly',
                                        show_label=False),
                                   width=800, height=600, resizable=True,
                                   buttons=[ 'OK' ],
                                   title='Complete Text Log'))

    def _copy_button_fired(self):
        clipboard.text_data = self.formatted_records

    @cached_property
    def _get_formatted_records(self):
        return '\n'.join([ self.service.handler.formatter.format(record)
                           for record in self.log_records ])

    def _activated_changed(self):
        if self.activated is None:
            return
        msg = self.activated.getMessage()
        if self.service.preferences.enable_agent:
            dialog = QualityAgentView(msg=msg, service=self.service)
            dialog.open()
        else:
            self.edit_traits(view=View(Item('activated_text',
                                            editor=self.code_editor,
                                            style='readonly',
                                            show_label=False),
                                       width=800, height=600, resizable=True,
                                       buttons=[ 'OK' ],
                                       title='Log Message Detail'))

    @cached_property
    def _get_activated_text(self):
        if self.activated is None:
            return ''
        else:
            return self.activated.getMessage()

#### EOF ######################################################################
