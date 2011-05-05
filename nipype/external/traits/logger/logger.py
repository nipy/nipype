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
""" Convenience functions for creating logging handlers etc. """


# Standard library imports.
import logging
from logging.handlers import RotatingFileHandler

# Enthought library imports.
from traits.util.api import deprecated

# Local imports.
from log_queue_handler import LogQueueHandler


# The default logging level.
LEVEL = logging.DEBUG

# The default formatter.
FORMATTER = logging.Formatter('%(levelname)s|%(asctime)s|%(message)s')


class LogFileHandler(RotatingFileHandler):
    """ The default log file handler.
    """

    def __init__(self, path, maxBytes=1000000, backupCount=3, level=None,
        formatter=None):
        RotatingFileHandler.__init__(
            self, path, maxBytes=maxBytes, backupCount=3
        )

        if level is None:
            level = LEVEL
        if formatter is None:
            formatter = FORMATTER
        # Set our default formatter and log level.
        self.setFormatter(formatter)
        self.setLevel(level)

@deprecated('use "LogFileHandler"')
def create_log_file_handler(path, maxBytes=1000000, backupCount=3, level=None,
    formatter=None):
    """ Creates a log file handler.

    This is just a convenience function to make it easy to create the same
    kind of handlers across applications.

    It sets the handler's formatter to the default formatter, and its logging
    level to the default logging level.

    """
    if level is None:
        level = LEVEL
    if formatter is None:
        formatter = FORMATTER

    handler = RotatingFileHandler(
        path, maxBytes=maxBytes, backupCount=backupCount
    )

    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler


def add_log_queue_handler(logger, level=None, formatter=None):
    """ Adds a queueing log handler to a logger.
    """
    if level is None:
        level = LEVEL
    if formatter is None:
        formatter = FORMATTER

    # Add the handler to the root logger.
    log_queue_handler = LogQueueHandler()
    log_queue_handler.setLevel(level)
    log_queue_handler.setFormatter(formatter)
    logger.addHandler(log_queue_handler)
    return log_queue_handler


#### EOF ######################################################################
