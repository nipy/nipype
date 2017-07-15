# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via dask

"""
from __future__ import print_function, division, unicode_literals, absolute_import

from .base import PluginBase


class DaskPlugin(PluginBase):
    """
    Base class for plugins
    """

    def run(self, graph, config, updatehash=False):
        pass
