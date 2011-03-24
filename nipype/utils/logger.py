# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import logging.handlers
import os

from nipype.utils.config import config

#Sets up logging for pipeline and nodewrapper execution
LOG_FILENAME = os.path.join(config.get('logging','log_directory'),
                            'pypeline.log')
logging.basicConfig()
logger = logging.getLogger('workflow')
fmlogger = logging.getLogger('filemanip')
iflogger = logging.getLogger('interface')
hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                            maxBytes=config.get('logging','log_size'),
                                            backupCount=config.get('logging','log_rotate'))
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
