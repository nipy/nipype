# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via dask

"""
from __future__ import print_function, division, unicode_literals, absolute_import

from dask.distributed import Client

from .base import PluginBase


class DaskPlugin(PluginBase):
    """
    Base class for plugins
    """

    def __init__(self, plugin_args=None):
        if IPython_not_loaded:
            raise ImportError('Please install ipyparallel to use this plugin.')
        super(DaskPlugin, self).__init__(plugin_args=plugin_args)
        valid_args = ('scheduler_file', 'scheduler_ip')
        self.client_args = {arg: plugin_args[arg]
                            for arg in valid_args if arg in plugin_args}
        self.daskclient = Client(**self.client_args)

    def run(self, graph, config, updatehash=False):
        pass
