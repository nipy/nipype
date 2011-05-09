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

import logging

from enthought.preferences.ui.api import PreferencesPage
from traits.api import Bool, Trait, Str
from traitsui.api import EnumEditor, Group, Item, View

class LoggerPreferencesPage(PreferencesPage):
    """ A preference page for the logger plugin.
    """

    #### 'PreferencesPage' interface ##########################################

    # The page's category (e.g. 'General/Appearance'). The empty string means
    # that this is a top-level page.
    category = ''

    # The page's help identifier (optional). If a help Id *is* provided then
    # there will be a 'Help' button shown on the preference page.
    help_id = ''

    # The page name (this is what is shown in the preferences dialog.
    name = 'Logger'

    # The path to the preferences node that contains the preferences.
    preferences_path = 'traits.logger'


    #### Preferences ###########################################################

    # The log levels
    level = Trait('Info',
        {'Debug'    : logging.DEBUG,
         'Info'     : logging.INFO,
         'Warning'  : logging.WARNING,
         'Error'    : logging.ERROR,
         'Critical' : logging.CRITICAL,
        },
        is_str = True,
    )

    enable_agent = Bool(False)
    smtp_server = Str
    to_address = Str
    from_address = Str


    # The view used to change the plugin preferences
    traits_view = View(
        Group(
            Group(
                Item(
                    name='level',
                    editor=EnumEditor(
                        values={
                            'Debug'    : '1:Debug',
                            'Info'     : '2:Info',
                            'Warning'  : '3:Warning',
                            'Error'    : '4:Error' ,
                            'Critical' : '5:Critical',
                        },
                    ),
                    style='simple',
                ),
                label='Logger Settings',
                show_border=True,
            ),
            Group(Item(name='10')),
            Group(
                Group(
                    Group(Item(name='enable_agent', label='Enable quality agent'), show_left=False),
                    Group(Item(name='smtp_server', label='SMTP server'),
                          Item(name='from_address'),
                          Item(name='to_address'), enabled_when='enable_agent==True')),
                label='Quality Agent Settings',
                show_border=True,
            ),
        ),
    )


#### EOF ######################################################################
