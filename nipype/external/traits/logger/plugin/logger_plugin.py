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
""" Logger plugin.
"""

# Standard library imports.
import logging

# Enthought library imports.
from enthought.envisage.api import ExtensionPoint, Plugin
from traits.logger.log_queue_handler import LogQueueHandler
from traits.api import Callable, List

# Local imports.
from logger_preferences import LoggerPreferences
from logger_service import LoggerService


ID = 'traits.logger'
ILOGGER = ID + '.plugin.logger_service.LoggerService'

class LoggerPlugin(Plugin):
    """ Logger plugin.
    """

    id = ID
    name = 'Logger plugin'

    #### Extension points for this plugin ######################################

    MAIL_FILES = 'traits.logger.plugin.mail_files'

    mail_files = ExtensionPoint(
        List(Callable), id=MAIL_FILES, desc="""

        This extension point allows you to contribute functions which will be
        called to add project files to the zip file that the user mails back
        with bug reports from the Quality Agent.

        The function will be passed a zipfile.ZipFile object.

        """
    )

    #### Contributions to extension points made by this plugin #################

    PREFERENCES = 'enthought.envisage.preferences'
    PREFERENCES_PAGES = 'enthought.envisage.ui.workbench.preferences_pages'
    VIEWS = 'enthought.envisage.ui.workbench.views'

    preferences = List(contributes_to=PREFERENCES)
    preferences_pages = List(contributes_to=PREFERENCES_PAGES)
    views = List(contributes_to=VIEWS)


    def _preferences_default(self):
        return ['pkgfile://%s/plugin/preferences.ini' % ID]

    def _preferences_pages_default(self):
        from traits.logger.plugin.view.logger_preferences_page import \
            LoggerPreferencesPage
        return [LoggerPreferencesPage]

    def _views_default(self):
        return [self._logger_view_factory]


    #### Plugin interface ######################################################

    def start(self):
        """ Starts the plugin.
        """
        preferences = LoggerPreferences()
        service = LoggerService(application=self.application,
            preferences=preferences)
        formatter = logging.Formatter('%(levelname)s|%(asctime)s|%(message)s')
        handler = LogQueueHandler()
        handler.setLevel(preferences.level_)
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(preferences.level_)
        service.handler = handler
        self.application.register_service(ILOGGER, service)

    def stop(self):
        """ Stops the plugin.
        """
        service = self.application.get_service(ILOGGER)
        service.save_preferences()


    #### LoggerPlugin private interface ########################################

    def _logger_view_factory(self, **traits):
        from traits.logger.plugin.view.logger_view import LoggerView
        service = self.application.get_service(ILOGGER)
        view = LoggerView(service=service, **traits)
        # Record the created view on the service.
        service.plugin_view = view
        return view


#### EOF ######################################################################
