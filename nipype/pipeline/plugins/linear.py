# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Local serial workflow execution
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os

import networkx as nx
from .base import (PluginBase, logger, report_crash, report_nodes_not_run,
                   str2bool)
from ..engine.utils import dfs_preorder, topological_sort


class LinearPlugin(PluginBase):
    """Execute workflow in series
    """

    def run(self, graph, config, updatehash=False):
        """Executes a pre-defined pipeline in a serial order.

        Parameters
        ----------

        graph : networkx digraph
            defines order of execution
        """

        if not isinstance(graph, nx.DiGraph):
            raise ValueError('Input must be a networkx digraph object')
        logger.info("Running serially.")
        old_wd = os.getcwd()
        notrun = []
        donotrun = []
        nodes, _ = topological_sort(graph)
        for node in nodes:
            try:
                if node in donotrun:
                    continue
                if self._status_callback:
                    self._status_callback(node, 'start')
                node.run(updatehash=updatehash)
                if self._status_callback:
                    self._status_callback(node, 'end')
            except:
                os.chdir(old_wd)
                if str2bool(config['execution']['stop_on_first_crash']):
                    raise
                # bare except, but i really don't know where a
                # node might fail
                crashfile = report_crash(node)
                # remove dependencies from queue
                subnodes = [s for s in dfs_preorder(graph, node)]
                notrun.append(
                    dict(node=node, dependents=subnodes, crashfile=crashfile))
                donotrun.extend(subnodes)
                if self._status_callback:
                    self._status_callback(node, 'exception')
        report_nodes_not_run(notrun)
