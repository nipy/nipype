# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Local serial workflow execution
"""

import os
from .base import PluginBase, logger, report_crash, report_nodes_not_run, str2bool
from ..engine.utils import topological_sort


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
        import networkx as nx

        try:
            dfs_preorder = nx.dfs_preorder
        except AttributeError:
            dfs_preorder = nx.dfs_preorder_nodes

        if not isinstance(graph, nx.DiGraph):
            raise ValueError("Input must be a networkx digraph object")
        logger.info("Running serially.")
        old_wd = os.getcwd()
        notrun = []
        donotrun = []
        nodes, _ = topological_sort(graph)
        for node in nodes:
            endstatus = "end"
            try:
                if node in donotrun:
                    continue
                if self._status_callback:
                    self._status_callback(node, "start")
                node.run(updatehash=updatehash)
            except:
                endstatus = "exception"
                # bare except, but i really don't know where a
                # node might fail
                crashfile = report_crash(node)
                if str2bool(config["execution"]["stop_on_first_crash"]):
                    raise
                # remove dependencies from queue
                subnodes = [s for s in dfs_preorder(graph, node)]
                notrun.append(
                    {"node": node, "dependents": subnodes, "crashfile": crashfile}
                )
                donotrun.extend(subnodes)
                # Delay raising the crash until we cleaned the house
                if str2bool(config["execution"]["stop_on_first_crash"]):
                    os.chdir(old_wd)  # Return wherever we were before
                    report_nodes_not_run(notrun)  # report before raising
                    raise
            finally:
                if self._status_callback:
                    self._status_callback(node, endstatus)

        os.chdir(old_wd)  # Return wherever we were before
        report_nodes_not_run(notrun)
