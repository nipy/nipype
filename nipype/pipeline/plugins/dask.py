# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via dask

"""
from __future__ import print_function, division, unicode_literals, absolute_import

import dask.distributed as dd

from .base import PluginBase


def run_node(node, updatehash, *args):
    """Function to execute node.run(), catch and log any errors and
    return the result dictionary

    Parameters
    ----------
    node : nipype Node instance
        the node to run
    updatehash : boolean
        flag for updating hash

    Returns
    -------
    result : dictionary
        dictionary containing the node runtime results and stats
    """

    # Init variables
    result = dict(result=None, traceback=None)

    # Try and execute the node via node.run()
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype, eval, etr)
        result['result'] = node.result

    # Return the result dictionary
    return result


class DaskPlugin(PluginBase):
    """
    Base class for plugins
    """

    def __init__(self, plugin_args=None):
        super(DaskPlugin, self).__init__(plugin_args=plugin_args)
        self.client = dd.client(**plugin_args)
        self.dask_get = dd.get

    def run(self, graph, config, updatehash=False):
        edges = graph.edges()
        dask_graph = {}
        for node in graph.nodes():
            parents = [edge[0].fullname for edge in edges if edge[1] is node]
            edges = [edge for edge in edges if edge[1] is not node]

            dask_graph[node.fullname] = (partial(run_node, node, updatehash), parents)

        self.dask_get(dask_graph, 'final')
