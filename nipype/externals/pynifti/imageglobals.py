# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
''' Defaults for images and headers '''

import logging

error_level = 40
log_level = 30
logger = logging.getLogger('nifti.global')
logger.addHandler(logging.StreamHandler())
