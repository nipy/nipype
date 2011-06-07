# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import logging
import logging.handlers
import os

from nipype.utils.config import config
import sys

#Sets up logging for pipeline and nodewrapper execution
LOG_FILENAME = os.path.join(config.get('logging','log_directory'),
                            'pypeline.log')
logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger('workflow')
fmlogger = logging.getLogger('filemanip')
iflogger = logging.getLogger('interface')
hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                            maxBytes=int(config.get('logging',
                                                                    'log_size')),
                                            backupCount=int(config.get('logging',
                                                                       'log_rotate')))
formatter = logging.Formatter(fmt='%(asctime)s,%(msecs)d %(name)-2s '\
                                  '%(levelname)-2s:\n\t %(message)s',
                              datefmt='%y%m%d-%H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.getLevelName(config.get('logging','workflow_level')))
fmlogger.addHandler(hdlr)
fmlogger.setLevel(logging.getLevelName(config.get('logging','filemanip_level')))
iflogger.addHandler(hdlr)
iflogger.setLevel(logging.getLevelName(config.get('logging','interface_level')))

def logdebug_dict_differences(dold, dnew, prefix=""):
    """Helper to log what actually changed from old to new values of
    dictionaries.

    typical use -- log difference for hashed_inputs
    """
    # Compare against hashed_inputs
    # Keys: should rarely differ
    new_keys = set(dnew.keys())
    old_keys = set(dold.keys())
    if len(new_keys - old_keys):
        logger.debug("%s not previously seen: %s"
                     % (prefix, new_keys - old_keys))
    if len(old_keys - new_keys):
        logger.debug("%s not presently seen: %s"
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
        logger.debug("%s values differ in fields: %s" % (prefix, ", ".join(msgs)))
