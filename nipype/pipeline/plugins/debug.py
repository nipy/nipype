# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Debug plugin
"""

from .base import (PluginBase, logger)
from ..utils import (nx)

class DebugPlugin(PluginBase):
    """Execute workflow in series
    """

    def __init__(self, plugin_args=None):
        super(DebugPlugin, self).__init__(plugin_args=plugin_args)
        if plugin_args and "callable" in plugin_args and \
            hasattr(plugin_args['callable'], '__call__'):
            self._callable = plugin_args['callable']
        else:
            raise ValueError('plugin_args must contain a callable function')


    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline in a serial order.

        Parameters
        ----------

        graph : networkx digraph
            defines order of execution
        """

        if not isinstance(graph, nx.DiGraph):
            raise ValueError('Input must be a networkx digraph object')
        logger.info("Executing debug plugin")
        for node in nx.topological_sort(graph):
            self._callable(node, graph)

