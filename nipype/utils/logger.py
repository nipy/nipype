# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import logging
import os
import sys
try:
    from ..external.cloghandler import ConcurrentRotatingFileHandler as \
    RFHandler
except ImportError:
    # Next 2 lines are optional:  issue a warning to the user
    from warnings import warn
    warn("ConcurrentLogHandler not installed. Using builtin log handler")
    from logging.handlers import RotatingFileHandler as RFHandler
from .misc import str2bool
from .config import NipypeConfig

class Logging(object):
    """Nipype logging class
    """
    fmt = ('%(asctime)s,%(msecs)d %(name)-2s '
           '%(levelname)-2s:\n\t %(message)s')
    datefmt = '%y%m%d-%H:%M:%S'
    def __init__(self, config):
        self._config = config
        logging.basicConfig(format=self.fmt, datefmt=self.datefmt,
                            stream=sys.stdout)
        #logging.basicConfig(stream=sys.stdout)
        self._logger = logging.getLogger('workflow')
        self._fmlogger = logging.getLogger('filemanip')
        self._iflogger = logging.getLogger('interface')

        self.loggers = {'workflow': self._logger,
                        'filemanip': self._fmlogger,
                        'interface': self._iflogger}
        self._hdlr = None
        self.update_logging(self._config)

    def enable_file_logging(self):
        config = self._config
        LOG_FILENAME = os.path.join(config.get('logging', 'log_directory'),
                                    'pypeline.log')
        hdlr = RFHandler(LOG_FILENAME,
                         maxBytes=int(config.get('logging', 'log_size')),
                         backupCount=int(config.get('logging',
                                                    'log_rotate')))
        formatter = logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)
        hdlr.setFormatter(formatter)
        self._logger.addHandler(hdlr)
        self._fmlogger.addHandler(hdlr)
        self._iflogger.addHandler(hdlr)
        self._hdlr = hdlr

    def disable_file_logging(self):
        if self._hdlr:
            self._logger.removeHandler(self._hdlr)
            self._fmlogger.removeHandler(self._hdlr)
            self._iflogger.removeHandler(self._hdlr)
            self._hdlr = None

    def update_logging(self, config):
        self._config = config
        self.disable_file_logging()
        self._logger.setLevel(logging.getLevelName(config.get('logging',
                                                              'workflow_level')))
        self._fmlogger.setLevel(logging.getLevelName(config.get('logging',
                                                                'filemanip_level')))
        self._iflogger.setLevel(logging.getLevelName(config.get('logging',
                                                                'interface_level')))
        if str2bool(config.get('logging', 'log_to_file')):
            self.enable_file_logging()

    def getLogger(self, name):
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
        # Compare against hashed_inputs
        # Keys: should rarely differ
        new_keys = set(dnew.keys())
        old_keys = set(dold.keys())
        if len(new_keys - old_keys):
            self._logger.debug("%s not previously seen: %s"
                         % (prefix, new_keys - old_keys))
        if len(old_keys - new_keys):
            self._logger.debug("%s not presently seen: %s"
                         % (prefix, old_keys - new_keys))

        # Values in common keys would differ quite often,
        # so we need to join the messages together
        msgs = []
        for k in new_keys.intersection(old_keys):
            same = False
            try:
                new, old = dnew[k], dold[k]
                same = new == old
                if not same:
                    # Since JSON does not discriminate between lists and
                    # tuples, we might need to cast them into the same type
                    # as the last resort.  And lets try to be more generic
                    same = old.__class__(new) == old
            except Exception, e:
                same = False
            if not same:
                msgs += ["%s: %r != %r"
                         % (k, dnew[k], dold[k])]
        if len(msgs):
            self._logger.debug("%s values differ in fields: %s" % (prefix,
                                                             ", ".join(msgs)))
