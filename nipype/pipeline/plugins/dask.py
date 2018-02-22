# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Parallel workflow execution via dask

"""
from __future__ import print_function, division, unicode_literals, absolute_import

import sys
from traceback import format_exception
from functools import partial
from dask.dot import dot_graph
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
    result = {'traceback': None}

    if hasattr(node, 'get_subnodes'):
        subnodes = node.get_subnodes()
        dask_graph = {
            snode.fullname: (partial(run_node, snode, updatehash), [])
            for snode in subnodes}
        resources = {snode.fullname: {'MEM': snode._interface.estimated_memory_gb,
                                      'CPU': snode._interface.num_threads}
                     for snode in subnodes}
        client = dd.get_client()
        dd.secede()  # Give up our worker status
        client.get(dask_graph, list(dask_graph.keys()), resources=resources)  # Wait
        # Fall of the end, to let MapNode collate and save results

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
        if plugin_args is None:
            plugin_args = {}
        valid_args = ('scheduler_file', 'scheduler_ip')
        client_args = {arg: plugin_args[arg]
                       for arg in valid_args if arg in plugin_args}
        self.daskclient = dd.Client(**client_args)

    def run(self, graph, config, updatehash=False):
        edges = graph.edges()
        dask_graph = {}
        resources = {}
        leafs = []
        for node in graph.nodes():
            parents = [edge[0].fullname for edge in edges if edge[1] is node]
            edges = [edge for edge in edges if edge[1] is not node]
            if graph.successors(node) == []:
                leafs.append(node.fullname)

            dask_graph[node.fullname] = (partial(run_node, node, updatehash),
                                         parents)
            resources[node.fullname] = {'MEM': node._interface.estimated_memory_gb,
                                        'CPU': node._interface.num_threads}

        dot_graph(dask_graph)
        self.daskclient.get(dask_graph, leafs, resources=resources)
