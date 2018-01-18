# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from builtins import object
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import logging
from warnings import warn
import os
import sys
from .misc import str2bool

try:
    from ..external.cloghandler import ConcurrentRotatingFileHandler as \
        RFHandler
except ImportError:
    # Next 2 lines are optional:  issue a warning to the user
    warn("ConcurrentLogHandler not installed. Using builtin log handler")
    from logging.handlers import RotatingFileHandler as RFHandler


class Logging(object):
    """Nipype logging class
    """
    fmt = ('%(asctime)s,%(msecs)d %(name)-2s '
           '%(levelname)-2s:\n\t %(message)s')
    datefmt = '%y%m%d-%H:%M:%S'

    def __init__(self, config):
        self._config = config
        logging.basicConfig(
            format=self.fmt, datefmt=self.datefmt, stream=sys.stdout)
        # logging.basicConfig(stream=sys.stdout)
        self._logger = logging.getLogger('workflow')
        self._utlogger = logging.getLogger('utils')
        self._fmlogger = logging.getLogger('filemanip')
        self._iflogger = logging.getLogger('interface')

        self.loggers = {
            'workflow': self._logger,
            'utils': self._utlogger,
            'filemanip': self._fmlogger,
            'interface': self._iflogger
        }
        self._hdlr = None
        self.update_logging(self._config)

    def enable_file_logging(self):
        config = self._config
        LOG_FILENAME = os.path.join(
            config.get('logging', 'log_directory'), 'pypeline.log')
        hdlr = RFHandler(
            LOG_FILENAME,
            maxBytes=int(config.get('logging', 'log_size')),
            backupCount=int(config.get('logging', 'log_rotate')))
        formatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
        hdlr.setFormatter(formatter)
        self._logger.addHandler(hdlr)
        self._utlogger.addHandler(hdlr)
        self._iflogger.addHandler(hdlr)
        self._fmlogger.addHandler(hdlr)
        self._hdlr = hdlr

    def disable_file_logging(self):
        if self._hdlr:
            self._logger.removeHandler(self._hdlr)
            self._utlogger.removeHandler(self._hdlr)
            self._iflogger.removeHandler(self._hdlr)
            self._fmlogger.removeHandler(self._hdlr)
            self._hdlr = None

    def update_logging(self, config):
        self._config = config
        self.disable_file_logging()
        self._logger.setLevel(
            logging.getLevelName(config.get('logging', 'workflow_level')))
        self._utlogger.setLevel(
            logging.getLevelName(config.get('logging', 'utils_level')))
        self._iflogger.setLevel(
            logging.getLevelName(config.get('logging', 'interface_level')))
        if str2bool(config.get('logging', 'log_to_file')):
            self.enable_file_logging()

    def getLogger(self, name):
        if name == 'filemanip':
            warn('The "filemanip" logger has been deprecated and replaced by '
                 'the "utils" logger as of nipype 1.0')
        if name in self.loggers:
            return self.loggers[name]
        return None

    def getLevelName(self, name):
        return logging.getLevelName(name)

    def logdebug_dict_differences(self, dold, dnew, prefix=""):
        """Helper to log what actually changed from old to new values of
        dictionaries.

        typical use -- log difference for hashed_inputs
        """
        from .misc import dict_diff
        self._logger.warning(
            "logdebug_dict_differences has been deprecated, please use "
            "nipype.utils.misc.dict_diff.")
        self._logger.debug(dict_diff(dold, dnew))
