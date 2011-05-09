import logging

from enthought.preferences.api import PreferencesHelper
from traits.api import Bool, Str, Trait


class LoggerPreferences(PreferencesHelper):
    """ The persistent service exposing the Logger plugin's API.
    """

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
    smtp_server = Str()
    to_address = Str()
    from_address = Str()

    # The path to the preferences node that contains the preferences.
    preferences_path = Str('traits.logger')
