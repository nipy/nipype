# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Package contains interfaces for using existing functionality in other packages

Requires Packages to be installed
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
__docformat__ = 'restructuredtext'

from .io import DataGrabber, DataSink, SelectFiles, BIDSDataGrabber
from .utility import IdentityInterface, Rename, Function, Select, Merge
