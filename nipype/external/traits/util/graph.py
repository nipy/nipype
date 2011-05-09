#-----------------------------------------------------------------------------
#
#  Copyright (c) 2005, Enthought, Inc.
#  All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#
#-----------------------------------------------------------------------------

""" Graph algorithms.

A graph is represented by a dictionary which represents the adjacency relation,
where node ``a`` has an arc to node ``b`` if and only if ``b in d[a]``.
"""

import __builtin__
from itertools import chain

from .cbook import flatten
from .dict import map_items, map_values

class CyclicGraph(Exception):
    """
    Exception for cyclic graphs.
    """
    def __init__(self):
        Exception.__init__(self, "Graph is cyclic")


def topological_sort(graph):
    """
    Returns the nodes in the graph in topological order.
    """
    discovered = {}
    explored = {}
    order = []
    def explore(node):
        children = graph.get(node, [])
        for child in children:
            if child in explored:
                pass
            elif child in discovered:
                raise CyclicGraph()
            else:
                discovered[child] = 1
                explore(child)
        explored[node] = 1
        order.append(node)

    for node in graph.keys():
        if node not in explored:
            explore(node)
    order.reverse()
    return order


def closure(graph, sorted=True):
    """
    Returns the transitive closure of the graph.
    If sorted is True then the successor nodes will
    be sorted into topological order.
    """
    order = topological_sort(graph)
    # Map nodes to their index in the topologically sorted list for later use.
    idxorder = {}
    for i, obj in enumerate(order):
        idxorder[obj] = i
    reachable = {}
    for i in range(len(order)-1, -1, -1):
        node = order[i]
        # We are going through in reverse topological order so we
        # are guaranteed that all of the children of the node
        # are already in reachable
        # We are using dicts to emulate sets for speed in Python 2.3.
        node_reachable = {}
        for child in graph.get(node, []):
            node_reachable[child] = 1
            node_reachable.update(reachable[child])
        reachable[node] = node_reachable
    # Now, build the return graph by doing a topological sort of
    # each reachable set, if required
    retval = {}
    for node, node_reachable in reachable.items():
        if not sorted:
            retval[node] = node_reachable.keys()
        else:
            # Create a tuple list so the faster built-in sort
            # comparator can be used.
            tmp = []
            reachable_list = node_reachable.keys()
            for n in reachable_list:
                tmp.append((idxorder[n], n))
            tmp.sort()
            reachable_list = [x[1] for x in tmp]
            retval[node] = reachable_list
    return retval

def reverse(graph):
    """
    Returns the reverse of a graph, that is the graph made when all
    of the edges are reversed.
    """
    retval = {}
    for node, successors in graph.items():
        # Make sure we keep isolated nodes, too.
        if node not in retval:
            retval[node] = []
        for s in successors:
            retval.setdefault(s, []).append(node)
    return retval

def map(f, graph):
    ''' Maps function f over the nodes in graph.

        >>> map(str, { 1:[2,3] })
        {'1': ['2', '3']}
    '''
    return map_items(lambda k,v: (f(k), __builtin__.map(f,v)), graph)

# FIXME Implement graphs with sets of values instead of lists of values
def eq(g1, g2):
    return map_values(set, g1) == map_values(set, g2)

def reachable_graph(graph, nodes):
    ''' Return the subgraph of the given graph reachable from the given nodes.

        >>> reachable_graph({'a':'bc', 'b':'c' }, 'a')
        {'a': 'bc', 'b': 'c'}
        >>> reachable_graph({'a':'bc', 'b':'c' }, 'b')
        {'b': 'c'}
        >>> reachable_graph({'a':'bc', 'b':'c' }, 'c')
        {}
    '''
    ret = {}
    closed = closure(graph)
    for n in chain(nodes, flatten([ closed[n] for n in nodes ])):
        if n in graph.keys():
            ret[n] = graph[n]
    return ret

if __name__ == "__main__":
    g = {1:[2,3],
         2:[3,4],
         6:[3],
         4:[6]}
    print topological_sort(g)
    print closure(g)

#### EOF ######################################################################
