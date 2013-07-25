# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Utility routines for workflow graphs
"""

from copy import deepcopy
from glob import glob
from collections import defaultdict
import os
import pickle
import pwd
import re
from uuid import uuid1

import numpy as np
from nipype.utils.misc import package_check

package_check('networkx', '1.3')
import json
from socket import gethostname, getfqdn

import networkx as nx

from ..utils.filemanip import (fname_presuffix, FileNotFoundError,
                               filename_to_list)
from ..utils.misc import create_function_from_source, str2bool
from ..interfaces.base import CommandLine, isdefined, Undefined, Bunch
from ..interfaces.base import pm as prov, safe_encode
from ..interfaces.utility import IdentityInterface

from .. import __version__ as nipype_version
from .. import get_info
from .. import logging, config
logger = logging.getLogger('workflow')

try:
    dfs_preorder = nx.dfs_preorder
except AttributeError:
    dfs_preorder = nx.dfs_preorder_nodes
    logger.debug('networkx 1.4 dev or higher detected')

try:
    from os.path import relpath
except ImportError:
    import os.path as op

    def relpath(path, start=None):
        """Return a relative version of a path"""
        if start is None:
            start = os.curdir
        if not path:
            raise ValueError("no path specified")
        start_list = op.abspath(start).split(op.sep)
        path_list = op.abspath(path).split(op.sep)
        if start_list[0].lower() != path_list[0].lower():
            unc_path, rest = op.splitunc(path)
            unc_start, rest = op.splitunc(start)
            if bool(unc_path) ^ bool(unc_start):
                raise ValueError(("Cannot mix UNC and non-UNC paths "
                                  "(%s and %s)") % (path, start))
            else:
                raise ValueError("path is on drive %s, start on drive %s"
                                 % (path_list[0], start_list[0]))
        # Work out how much of the filepath is shared by start and path.
        for i in range(min(len(start_list), len(path_list))):
            if start_list[i].lower() != path_list[i].lower():
                break
        else:
            i += 1

        rel_list = [op.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return os.curdir
        return op.join(*rel_list)


def modify_paths(object, relative=True, basedir=None):
    """Convert paths in data structure to either full paths or relative paths

    Supports combinations of lists, dicts, tuples, strs

    Parameters
    ----------

    relative : boolean indicating whether paths should be set relative to the
               current directory
    basedir : default os.getcwd()
              what base directory to use as default
    """
    if not basedir:
        basedir = os.getcwd()
    if isinstance(object, dict):
        out = {}
        for key, val in sorted(object.items()):
            if isdefined(val):
                out[key] = modify_paths(val, relative=relative,
                                        basedir=basedir)
    elif isinstance(object, (list, tuple)):
        out = []
        for val in object:
            if isdefined(val):
                out.append(modify_paths(val, relative=relative,
                                        basedir=basedir))
        if isinstance(object, tuple):
            out = tuple(out)
    else:
        if isdefined(object):
            if isinstance(object, str) and os.path.isfile(object):
                if relative:
                    if config.getboolean('execution', 'use_relative_paths'):
                        out = relpath(object, start=basedir)
                    else:
                        out = object
                else:
                    out = os.path.abspath(os.path.join(basedir, object))
                if not os.path.exists(out):
                    raise FileNotFoundError('File %s not found' % out)
            else:
                out = object
    return out


def get_print_name(node, simple_form=True):
    """Get the name of the node

    For example, a node containing an instance of interfaces.fsl.BET
    would be called nodename.BET.fsl

    """
    name = node.fullname
    if hasattr(node, '_interface'):
        pkglist = node._interface.__class__.__module__.split('.')
        interface = node._interface.__class__.__name__
        destclass = ''
        if len(pkglist) > 2:
            destclass = '.%s' % pkglist[2]
        if simple_form:
            name = node.fullname + destclass
        else:
            name = '.'.join([node.fullname, interface]) + destclass
    if simple_form:
        parts = name.split('.')
        if len(parts) > 2:
            return ' ('.join(parts[1:])+')'
        elif len(parts) == 2:
            return parts[1]
    return name


def _create_dot_graph(graph, show_connectinfo=False, simple_form=True):
    """Create a graph that can be pickled.

    Ensures that edge info is pickleable.
    """
    logger.debug('creating dot graph')
    pklgraph = nx.DiGraph()
    for edge in graph.edges():
        data = graph.get_edge_data(*edge)
        srcname = get_print_name(edge[0], simple_form=simple_form)
        destname = get_print_name(edge[1], simple_form=simple_form)
        if show_connectinfo:
            pklgraph.add_edge(srcname, destname, l=str(data['connect']))
        else:
            pklgraph.add_edge(srcname, destname)
    return pklgraph


def _write_detailed_dot(graph, dotfilename):
    """Create a dot file with connection info

    digraph structs {
    node [shape=record];
    struct1 [label="<f0> left|<f1> mid\ dle|<f2> right"];
    struct2 [label="<f0> one|<f1> two"];
    struct3 [label="hello\nworld |{ b |{c|<here> d|e}| f}| g | h"];
    struct1:f1 -> struct2:f0;
    struct1:f0 -> struct2:f1;
    struct1:f2 -> struct3:here;
    }
    """
    text = ['digraph structs {', 'node [shape=record];']
    # write nodes
    edges = []
    replacefunk = lambda x: x.replace('_', '').replace('.', ''). \
        replace('@', '').replace('-', '')
    for n in nx.topological_sort(graph):
        nodename = str(n)
        inports = []
        for u, v, d in graph.in_edges_iter(nbunch=n, data=True):
            for cd in d['connect']:
                if isinstance(cd[0], str):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                inport = cd[1]
                ipstrip = 'in' + replacefunk(inport)
                opstrip = 'out' + replacefunk(outport)
                edges.append('%s:%s:e -> %s:%s:w;' % (str(u).replace('.', ''),
                                                      opstrip,
                                                      str(v).replace('.', ''),
                                                      ipstrip))
                if inport not in inports:
                    inports.append(inport)
        inputstr = '{IN'
        for ip in sorted(inports):
            inputstr += '|<in%s> %s' % (replacefunk(ip), ip)
        inputstr += '}'
        outports = []
        for u, v, d in graph.out_edges_iter(nbunch=n, data=True):
            for cd in d['connect']:
                if isinstance(cd[0], str):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                if outport not in outports:
                    outports.append(outport)
        outputstr = '{OUT'
        for op in sorted(outports):
            outputstr += '|<out%s> %s' % (replacefunk(op), op)
        outputstr += '}'
        srcpackage = ''
        if hasattr(n, '_interface'):
            pkglist = n._interface.__class__.__module__.split('.')
            if len(pkglist) > 2:
                srcpackage = pkglist[2]
        srchierarchy = '.'.join(nodename.split('.')[1:-1])
        nodenamestr = '{ %s | %s | %s }' % (nodename.split('.')[-1],
                                            srcpackage,
                                            srchierarchy)
        text += ['%s [label="%s|%s|%s"];' % (nodename.replace('.', ''),
                                             inputstr,
                                             nodenamestr,
                                             outputstr)]
    # write edges
    for edge in sorted(edges):
        text.append(edge)
    text.append('}')
    filep = open(dotfilename, 'wt')
    filep.write('\n'.join(text))
    filep.close()
    return text


# Graph manipulations for iterable expansion
def _get_valid_pathstr(pathstr):
    """Remove disallowed characters from path

    Removes:  [][ (){}?:<>#!|"';]
    Replaces: ',' -> '.'
    """
    pathstr = pathstr.replace(os.sep, '..')
    pathstr = re.sub(r'''[][ (){}?:<>#!|"';]''', '', pathstr)
    pathstr = pathstr.replace(',', '.')
    return pathstr


def walk(children, level=0, path=None, usename=True):
    """Generate all the full paths in a tree, as a dict.
    """
    # Entry point
    if level == 0:
        path = {}
    # Exit condition
    if not children:
        yield path.copy()
        return
    # Tree recursion
    head, tail = children[0], children[1:]
    name, func = head
    for child in func():
        # We can use the arg name or the tree level as a key
        if usename:
            path[name] = child
        else:
            path[level] = child
        # Recurse into the next level
        for child_paths in walk(tail, level + 1, path, usename):
            yield child_paths


def evaluate_connect_function(function_source, args, first_arg):
    func = create_function_from_source(function_source)
    try:
        output_value = func(first_arg,
                            *list(args))
    except NameError as e:
        if e.args[0].startswith("global name") and \
                e.args[0].endswith("is not defined"):
            e.args = (e.args[0],
                      ("Due to engine constraints all imports have to be done "
                       "inside each function definition"))
        raise e
    return output_value


def get_levels(G):
    levels = {}
    for n in nx.topological_sort(G):
        levels[n] = 0
        for pred in G.predecessors_iter(n):
            levels[n] = max(levels[n], levels[pred] + 1)
    return levels


def _merge_graphs(supergraph, nodes, subgraph, nodeid, iterables, prefix):
    """Merges two graphs that share a subset of nodes.

    If the subgraph needs to be replicated for multiple iterables, the
    merge happens with every copy of the subgraph. Assumes that edges
    between nodes of supergraph and subgraph contain data.

    Parameters
    ----------
    supergraph : networkx graph
    Parent graph from which subgraph was selected
    nodes : networkx nodes
    Nodes of the parent graph from which the subgraph was initially
    constructed.
    subgraph : networkx graph
    A subgraph that contains as a subset nodes from the supergraph.
    These nodes connect the subgraph to the supergraph
    nodeid : string
    Identifier of a node for which parameterization has been sought
    iterables : dict of functions
    see `pipeline.NodeWrapper` for iterable requirements

    Returns
    -------
    Returns a merged graph containing copies of the subgraph with
    appropriate edge connections to the supergraph.

    """
    # Retrieve edge information connecting nodes of the subgraph to other
    # nodes of the supergraph.
    supernodes = supergraph.nodes()
    ids = [n._hierarchy + n._id for n in supernodes]
    if len(np.unique(ids)) != len(ids):
        # This should trap the problem of miswiring when multiple iterables are
        # used at the same level. The use of the template below for naming
        # updates to nodes is the general solution.
        raise Exception(("Execution graph does not have a unique set of node "
                         "names. Please rerun the workflow"))
    edgeinfo = {}
    for n in subgraph.nodes():
        nidx = ids.index(n._hierarchy + n._id)
        for edge in supergraph.in_edges_iter(supernodes[nidx]):
                #make sure edge is not part of subgraph
            if edge[0] not in subgraph.nodes():
                if n._hierarchy + n._id not in edgeinfo.keys():
                    edgeinfo[n._hierarchy + n._id] = []
                edgeinfo[n._hierarchy + n._id].append((edge[0],
                                               supergraph.get_edge_data(*edge)))
    supergraph.remove_nodes_from(nodes)
    # Add copies of the subgraph depending on the number of iterables
    iterable_params = list(walk(iterables.items()))
    # If there are no iterable subgraphs, then return
    if not iterable_params:
        return supergraph
    # Make an iterable subgraph node id template
    count = len(iterable_params)
    template = '.%s%%0%dd' % (prefix, np.ceil(np.log10(count)))
    # Copy the iterable subgraphs
    for i, params in enumerate(iterable_params):
        Gc = deepcopy(subgraph)
        ids = [n._hierarchy + n._id for n in Gc.nodes()]
        nodeidx = ids.index(nodeid)
        rootnode = Gc.nodes()[nodeidx]
        paramstr = ''
        for key, val in sorted(params.items()):
            paramstr = '_'.join((paramstr, _get_valid_pathstr(key),
                                 _get_valid_pathstr(str(val))))
            rootnode.set_input(key, val)
        levels = get_levels(Gc)
        for n in Gc.nodes():
            """
            update parameterization of the node to reflect the location of
            the output directory.  For example, if the iterables along a
            path of the directed graph consisted of the variables 'a' and
            'b', then every node in the path including and after the node
            with iterable 'b' will be placed in a directory
            _a_aval/_b_bval/.
            """
            path_length = levels[n]
            # enter as negative numbers so that earlier iterables with longer
            # path lengths get precedence in a sort
            paramlist = [(-path_length, paramstr)]
            if n.parameterization:
                n.parameterization = paramlist + n.parameterization
            else:
                n.parameterization = paramlist
        supergraph.add_nodes_from(Gc.nodes())
        supergraph.add_edges_from(Gc.edges(data=True))
        for node in Gc.nodes():
            if node._hierarchy + node._id in edgeinfo.keys():
                for info in edgeinfo[node._hierarchy + node._id]:
                    supergraph.add_edges_from([(info[0], node, info[1])])
            node._id += template % i
    return supergraph


def _connect_nodes(graph, srcnode, destnode, connection_info):
    """Add a connection between two nodes
    """
    data = graph.get_edge_data(srcnode, destnode, default=None)
    if not data:
        data = {'connect': connection_info}
        graph.add_edges_from([(srcnode, destnode, data)])
    else:
        data['connect'].extend(connection_info)


def _remove_identity_nodes(graph, keep_iterables=False):
    """Remove identity nodes from an execution graph
    """
    identity_nodes = []
    for node in nx.topological_sort(graph):
        if isinstance(node._interface, IdentityInterface):
            if keep_iterables and getattr(node, 'iterables') is not None:
                pass
            else:
                identity_nodes.append(node)
    if identity_nodes:
        for node in identity_nodes:
            portinputs = {}
            portoutputs = {}
            for u, _, d in graph.in_edges_iter(node, data=True):
                for src, dest in d['connect']:
                    portinputs[dest] = (u, src)
            for _, v, d in graph.out_edges_iter(node, data=True):
                for src, dest in d['connect']:
                    if isinstance(src, tuple):
                        srcport = src[0]
                    else:
                        srcport = src
                    if srcport not in portoutputs:
                        portoutputs[srcport] = []
                    portoutputs[srcport].append((v, dest, src))
            if not portoutputs:
                pass
            elif not portinputs:
                for key, connections in portoutputs.items():
                    for destnode, inport, src in connections:
                        value = getattr(node.inputs, key)
                        if isinstance(src, tuple):
                            value = evaluate_connect_function(src[1], src[2],
                                                              value)
                        destnode.set_input(inport, value)
            else:
                for key, connections in portoutputs.items():
                    for destnode, inport, src in connections:
                        if key not in portinputs:
                            value = getattr(node.inputs, key)
                            if isinstance(src, tuple):
                                value = evaluate_connect_function(src[1],
                                                                  src[2],
                                                                  value)
                            destnode.set_input(inport, value)
                        else:
                            srcnode, srcport = portinputs[key]
                            if isinstance(srcport, tuple) and isinstance(src,
                                                                         tuple):
                                raise ValueError(("Does not support two inline "
                                                  "functions in series (\'%s\' "
                                                  "and \'%s\'). Please use a "
                                                  "Function node") %
                                            (srcport[1].split("\\n")[0][6:-1],
                                             src[1].split("\\n")[0][6:-1]))
                            connect = graph.get_edge_data(srcnode,
                                                          destnode,
                                                       default={'connect': []})
                            if isinstance(src, tuple):
                                connect['connect'].append(((srcport,
                                                            src[1],
                                                            src[2]),
                                                           inport))
                            else:
                                connect = {'connect': [(srcport, inport)]}
                            old_connect = graph.get_edge_data(srcnode,
                                                              destnode,
                                                        default={'connect': []})
                            old_connect['connect'] += connect['connect']
                            graph.add_edges_from([(srcnode, destnode,
                                                   old_connect)])
            graph.remove_nodes_from([node])
    return graph


def generate_expanded_graph(graph_in):
    """Generates an expanded graph based on node parameterization

    Parameterization is controlled using the `iterables` field of the
    pipeline elements.  Thus if there are two nodes with iterables a=[1,2]
    and b=[3,4] this procedure will generate a graph with sub-graphs
    parameterized as (a=1,b=3), (a=1,b=4), (a=2,b=3) and (a=2,b=4).
    """
    logger.debug("PE: expanding iterables")
    graph_in = _remove_identity_nodes(graph_in, keep_iterables=True)
    # convert list of tuples to dict fields
    for node in graph_in.nodes_iter():
        if isinstance(node.iterables, tuple):
            node.iterables = [node.iterables]
    for node in graph_in.nodes_iter():
        if isinstance(node.iterables, list):
            node.iterables = dict(map(lambda(x): (x[0],
                                                  lambda: x[1]),
                                      node.iterables))
    allprefixes = list('abcdefghijklmnopqrstuvwxyz')

    # the iterable nodes
    inodes = _iterable_nodes(graph_in)
    # while there is an iterable node, expand the iterable node's
    # subgraphs
    while inodes:
        inode = inodes[0]
        iterables = inode.iterables.copy()
        inode.iterables = None
        logger.debug('node: %s iterables: %s' % (inode, iterables))

        # the join successor nodes of the current iterable node
        jnodes = [node for node in graph_in.nodes_iter()
            if hasattr(node, 'joinsource') and inode.name == node.joinsource]

        # excise the join in-edges
        jedge_dict = {}
        for jnode in jnodes:
            for src, dest, data in graph_in.in_edges_iter(jnode, True):
                jedge_dict[src.name] = (dest.name, data)
                graph_in.remove_edge(src, dest)
                logger.debug("Excised the %s -> %s join node in-edge."
                             % (src, dest))

        # collect the subnodes to expand
        subnodes = [s for s in dfs_preorder(graph_in, inode)]
        prior_prefix = []
        for s in subnodes:
            prior_prefix.extend(re.findall('\.(.)I', s._id))
        prior_prefix = sorted(prior_prefix)
        if not len(prior_prefix):
            iterable_prefix = 'a'
        else:
            if prior_prefix[-1] == 'z':
                raise ValueError('Too many iterables in the workflow')
            iterable_prefix =\
            allprefixes[allprefixes.index(prior_prefix[-1]) + 1]
        logger.debug(('subnodes:', subnodes))

        # append a suffix to the iterable node id
        inode._id += ('.' + iterable_prefix + 'I')

        # merge the iterated subgraphs
        subgraph = graph_in.subgraph(subnodes)
        graph_in = _merge_graphs(graph_in, subnodes,
                                 subgraph, inode._hierarchy + inode._id,
                                 iterables, iterable_prefix)

        # reconnect the join nodes
        if jnodes:
            # the {node name: replicated nodes} dictionary
            node_name_dict = defaultdict(list)
            for node in graph_in.nodes_iter():
                node_name_dict[node.name].append(node)
            # preserve the node iteration order by sorting on the node id
            for nodes in node_name_dict.values():
                nodes.sort(key=str)
            # for each join in-edge, connect every expanded source node
            # which matches on the in-edge source name to the destination
            # join node. Qualify each edge connect join field name by
            # appending the next join slot index, e.g. the connect
            # from two expanded nodes from field 'out_file' to join
            # field 'in' are qualified as ('out_file', 'in1') and
            # ('out_file', 'in2'), resp. This preserves connection port
            # integrity.
            for src_name, tgt in jedge_dict.iteritems():
                dest_name, edge_data = tgt
                dests = node_name_dict[dest_name]
                if not dests:
                    raise Exception("The execution graph does not contain"
                                    " the join node: %s" % dest_name)
                elif len(dests) > 1:
                    raise Exception("The execution graph contains more than"
                                    " one join node named %s: %s"
                                    % (dest_name, dests))
                else:
                    dest = dests[0]
                for src in node_name_dict[src_name]:
                    newdata = deepcopy(edge_data)
                    connects = newdata['connect']
                    join_fields = [field for _, field in connects
                        if field in dest.joinfield]
                    slot_dict = dest._add_join_item_fields()
                    for idx, connect in enumerate(connects):
                        src_field, dest_field = connect
                        # qualify a join destination field name
                        if dest_field in slot_dict:
                            slot_field = slot_dict[dest_field]
                            connects[idx] = (src_field, slot_field)
                            logger.debug("Qualified the %s -> %s join field"
                                         " %s as %s." %
                                         (src, dest, dest_field, slot_field))
                    graph_in.add_edge(src, dest, newdata)
                    logger.debug("Connected the join node %s subgraph to the"
                                 " expanded join point %s" % (dest, src))

        #nx.write_dot(graph_in, '%s_post.dot' % node)
        # the remaining iterable nodes
        inodes = _iterable_nodes(graph_in)

    for node in graph_in.nodes():
        if node.parameterization:
            node.parameterization = [param for _, param in
                                     sorted(node.parameterization)]
    logger.debug("PE: expanding iterables ... done")
    return _remove_identity_nodes(graph_in)

def _iterable_nodes(graph_in):
    """ Returns the iterable nodes in the given graph
    
    The nodes are sorted in reverse topological order.
    """
    nodes = nx.topological_sort(graph_in)
    nodes.reverse()
    return [node for node in nodes if node.iterables is not None]
    
def export_graph(graph_in, base_dir=None, show=False, use_execgraph=False,
                 show_connectinfo=False, dotfilename='graph.dot', format='png',
                 simple_form=True):
    """ Displays the graph layout of the pipeline

    This function requires that pygraphviz and matplotlib are available on
    the system.

    Parameters
    ----------

    show : boolean
    Indicate whether to generate pygraphviz output fromn
    networkx. default [False]

    use_execgraph : boolean
    Indicates whether to use the specification graph or the
    execution graph. default [False]

    show_connectioninfo : boolean
    Indicates whether to show the edge data on the graph. This
    makes the graph rather cluttered. default [False]
    """
    graph = deepcopy(graph_in)
    if use_execgraph:
        graph = generate_expanded_graph(graph)
        logger.debug('using execgraph')
    else:
        logger.debug('using input graph')
    if base_dir is None:
        base_dir = os.getcwd()
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    outfname = fname_presuffix(dotfilename,
                               suffix='_detailed.dot',
                               use_ext=False,
                               newpath=base_dir)
    logger.info('Creating detailed dot file: %s' % outfname)
    _write_detailed_dot(graph, outfname)
    cmd = 'dot -T%s -O %s' % (format, outfname)
    res = CommandLine(cmd, terminal_output='allatonce').run()
    if res.runtime.returncode:
        logger.warn('dot2png: %s', res.runtime.stderr)
    pklgraph = _create_dot_graph(graph, show_connectinfo, simple_form)
    outfname = fname_presuffix(dotfilename,
                               suffix='.dot',
                               use_ext=False,
                               newpath=base_dir)
    nx.write_dot(pklgraph, outfname)
    logger.info('Creating dot file: %s' % outfname)
    cmd = 'dot -T%s -O %s' % (format, outfname)
    res = CommandLine(cmd, terminal_output='allatonce').run()
    if res.runtime.returncode:
        logger.warn('dot2png: %s', res.runtime.stderr)
    if show:
        pos = nx.graphviz_layout(pklgraph, prog='dot')
        nx.draw(pklgraph, pos)
        if show_connectinfo:
            nx.draw_networkx_edge_labels(pklgraph, pos)


def format_dot(dotfilename, format=None):
    cmd = 'dot -T%s -O %s' % (format, dotfilename)
    CommandLine(cmd).run()
    logger.info('Converting dotfile: %s to %s format' % (dotfilename, format))


def make_output_dir(outdir):
    """Make the output_dir if it doesn't exist.

    Parameters
    ----------
    outdir : output directory to create

    """
    if not os.path.exists(os.path.abspath(outdir)):
        logger.debug("Creating %s" % outdir)
        os.makedirs(outdir)
    return outdir


def get_all_files(infile):
    files = [infile]
    if infile.endswith(".img"):
        files.append(infile[:-4] + ".hdr")
        files.append(infile[:-4] + ".mat")
    if infile.endswith(".img.gz"):
        files.append(infile[:-7] + ".hdr.gz")
    return files


def walk_outputs(object):
    """Extract every file and directory from a python structure
    """
    out = []
    if isinstance(object, dict):
        for key, val in sorted(object.items()):
            if isdefined(val):
                out.extend(walk_outputs(val))
    elif isinstance(object, (list, tuple)):
        for val in object:
            if isdefined(val):
                out.extend(walk_outputs(val))
    else:
        if isdefined(object) and isinstance(object, basestring):
            if os.path.islink(object) or os.path.isfile(object):
                out = [(filename, 'f') for filename in get_all_files(object)]
            elif os.path.isdir(object):
                out = [(object, 'd')]
    return out


def walk_files(cwd):
    for path, _, files in os.walk(cwd):
        for f in files:
            yield os.path.join(path, f)


def clean_working_directory(outputs, cwd, inputs, needed_outputs, config,
                            files2keep=None, dirs2keep=None):
    """Removes all files not needed for further analysis from the directory
    """
    if not outputs:
        return
    outputs_to_keep = outputs.get().keys()
    if needed_outputs and \
       str2bool(config['execution']['remove_unnecessary_outputs']):
        outputs_to_keep = needed_outputs
    # build a list of needed files
    output_files = []
    outputdict = outputs.get()
    for output in outputs_to_keep:
        output_files.extend(walk_outputs(outputdict[output]))
    needed_files = [path for path, type in output_files if type == 'f']
    if str2bool(config['execution']['keep_inputs']):
        input_files = []
        inputdict = inputs.get()
        input_files.extend(walk_outputs(inputdict))
        needed_files += [path for path, type in input_files if type == 'f']
    for extra in ['_0x*.json', 'provenance.*', 'pyscript*.m',
                  'command.txt', 'result*.pklz', '_inputs.pklz', '_node.pklz']:
        needed_files.extend(glob(os.path.join(cwd, extra)))
    if files2keep:
        needed_files.extend(filename_to_list(files2keep))
    needed_dirs = [path for path, type in output_files if type == 'd']
    if dirs2keep:
        needed_dirs.extend(filename_to_list(dirs2keep))
    for extra in ['_nipype', '_report']:
        needed_dirs.extend(glob(os.path.join(cwd, extra)))
    logger.debug('Needed files: %s' % (';'.join(needed_files)))
    logger.debug('Needed dirs: %s' % (';'.join(needed_dirs)))
    files2remove = []
    if str2bool(config['execution']['remove_unnecessary_outputs']):
        for f in walk_files(cwd):
            if f not in needed_files:
                if len(needed_dirs) == 0:
                    files2remove.append(f)
                elif not any([f.startswith(dname) for dname in needed_dirs]):
                    files2remove.append(f)
    else:
        if not str2bool(config['execution']['keep_inputs']):
            input_files = []
            inputdict = inputs.get()
            input_files.extend(walk_outputs(inputdict))
            input_files = [path for path, type in input_files if type == 'f']
            for f in walk_files(cwd):
                if f in input_files and f not in needed_files:
                    files2remove.append(f)
    logger.debug('Removing files: %s' % (';'.join(files2remove)))
    for f in files2remove:
        os.remove(f)
    for key in outputs.copyable_trait_names():
        if key not in outputs_to_keep:
            setattr(outputs, key, Undefined)
    return outputs


def merge_dict(d1, d2, merge=lambda x, y: y):
    """
    Merges two dictionaries, non-destructively, combining
    values on duplicate keys as defined by the optional merge
    function.  The default behavior replaces the values in d1
    with corresponding values in d2.  (There is no other generally
    applicable merge strategy, but often you'll have homogeneous
    types in your dicts, so specifying a merge technique can be
    valuable.)

    Examples:

    >>> d1 = {'a': 1, 'c': 3, 'b': 2}
    >>> merge_dict(d1, d1)
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge_dict(d1, d1, lambda x,y: x+y)
    {'a': 2, 'c': 6, 'b': 4}

    """
    if not isinstance(d1, dict):
        return merge(d1, d2)
    result = dict(d1)
    if d2 is None:
        return result
    for k, v in d2.iteritems():
        if k in result:
            result[k] = merge_dict(result[k], v, merge=merge)
        else:
            result[k] = v
    return result


def write_prov(graph, filename=None, format='turtle'):
    """Write W3C PROV Model JSON file
    """
    if not filename:
        filename = os.path.join(os.getcwd(), 'workflow_provenance')
    foaf = prov.Namespace("foaf", "http://xmlns.com/foaf/0.1/")
    dcterms = prov.Namespace("dcterms", "http://purl.org/dc/terms/")
    nipype = prov.Namespace("nipype", "http://nipy.org/nipype/terms/")

    # create a provenance container
    g = prov.ProvBundle()

    # Set the default _namespace name
    #g.set_default_namespace(nipype.get_uri())
    g.add_namespace(foaf)
    g.add_namespace(dcterms)
    g.add_namespace(nipype)

    get_id = lambda: nipype[uuid1().hex]

    user_agent = g.agent(get_id(),
                         {prov.PROV["type"]: prov.PROV["Person"],
                          prov.PROV["label"]: pwd.getpwuid(os.geteuid()).pw_name,
                          foaf["name"]: safe_encode(pwd.getpwuid(os.geteuid()).pw_name)})
    agent_attr = {prov.PROV["type"]: prov.PROV["SoftwareAgent"],
                  prov.PROV["label"]: "Nipype",
                  foaf["name"]: safe_encode("Nipype")}
    for key, value in get_info().items():
        agent_attr.update({nipype[key]: safe_encode(value)})
    software_agent = g.agent(get_id(), agent_attr)

    processes = []
    nodes = graph.nodes()
    for idx, node in enumerate(nodes):
        result = node.result
        classname = node._interface.__class__.__name__
        _, hashval, _, _ = node.hash_exists()
        if isinstance(result.runtime, list):
            startTime = None
            endTime = None
            for runtime in result.runtime:
                newStartTime = getattr(runtime, 'startTime')
                if startTime:
                    if newStartTime < startTime:
                        startTime = newStartTime
                else:
                    startTime = newStartTime
                newEndTime = getattr(runtime, 'endTime')
                if endTime:
                    if newEndTime > endTime:
                        endTime = newEndTime
                else:
                    endTime = newEndTime
            attrs = {foaf["host"]: gethostname(),
                     prov.PROV["type"]: nipype[classname],
                     prov.PROV["label"]: '_'.join((classname,
                                                   node.name)),
                     nipype['hashval']: hashval}
            process = g.activity(uuid1().hex, startTime,
                                 endTime, attrs)
            process.add_extra_attributes({prov.PROV["type"]: nipype["MapNode"]})
            # add info about sub processes
            for runtime in result.runtime:
                attrs = {foaf["host"]: runtime.hostname,
                         prov.PROV["type"]: nipype[classname],
                         prov.PROV["label"]: '_'.join((classname,
                                                       node.name)),
                         #nipype['hashval']: hashval,
                         nipype['duration']: runtime.duration,
                         nipype['working_directory']: runtime.cwd,
                         nipype['return_code']: runtime.returncode,
                         nipype['platform']: runtime.platform,
                         }
                try:
                    attrs.update({nipype['command']: runtime.cmdline})
                    attrs.update({nipype['command_path']: runtime.command_path})
                    attrs.update({nipype['dependencies']: runtime.dependencies})
                except AttributeError:
                    pass
                process_sub = g.activity(uuid1().hex, runtime.startTime,
                                     runtime.endTime, attrs)
                process_sub.add_extra_attributes({prov.PROV["type"]: nipype["Node"]})
                g.wasAssociatedWith(process_sub, user_agent, None, None,
                                    {prov.PROV["Role"]: "LoggedInUser"})
                g.wasAssociatedWith(process_sub, software_agent, None, None,
                                    {prov.PROV["Role"]: prov.PROV["SoftwareAgent"]})
                g.wasInformedBy(process_sub, process)
                # environment
                id = uuid1().hex
                environ = g.entity(id)
                environ.add_extra_attributes({prov.PROV['type']: nipype['environment'],
                                              prov.PROV['label']: "environment",
                                              nipype['environ_json']: json.dumps(runtime.environ)})
                g.used(process_sub, id)
        else:
            runtime = result.runtime
            attrs = {foaf["host"]: runtime.hostname,
                     prov.PROV["type"]: nipype[classname],
                     prov.PROV["label"]: '_'.join((classname,
                                                   node.name)),
                     nipype['hashval']: hashval,
                     nipype['duration']: runtime.duration,
                     nipype['working_directory']: runtime.cwd,
                     nipype['return_code']: runtime.returncode,
                     nipype['platform']: runtime.platform,
                     }
            try:
                attrs.update({nipype['command']: runtime.cmdline})
                attrs.update({nipype['command_path']: runtime.command_path})
                attrs.update({nipype['dependencies']: runtime.dependencies})
            except AttributeError:
                pass
            process = g.activity(uuid1().hex, runtime.startTime,
                                 runtime.endTime, attrs)
            process.add_extra_attributes({prov.PROV["type"]: nipype["Node"]})
            # environment
            id = uuid1().hex
            environ = g.entity(id)
            environ.add_extra_attributes({prov.PROV['type']: nipype['environment'],
                                          prov.PROV['label']: "environment",
                                          nipype['environ_json']: json.dumps(runtime.environ)})
            g.used(process, id)
        processes.append(process)
        g.wasAssociatedWith(process, user_agent, None, None,
                {prov.PROV["Role"]: "LoggedInUser"})
        g.wasAssociatedWith(process, software_agent, None, None,
                {prov.PROV["Role"]: prov.PROV["SoftwareAgent"]})
        for inidx, inputval in enumerate(sorted(node.inputs.get().items())):
            if isdefined(inputval[1]):
                inport = inputval[0]
                used_ports = []
                for _, _, d in graph.in_edges_iter([node], data=True):
                    for _, dest in d['connect']:
                        used_ports.append(dest)
                if inport not in used_ports:
                    param = g.entity(uuid1().hex,
                                     {prov.PROV["type"]: nipype['input'],
                                      prov.PROV["label"]: inport,
                                      nipype['port']: inport,
                                      prov.PROV["value"]: str(inputval[1])
                                      })
                    g.used(process, param)

    # add dependencies (edges)
    # add artifacts (files)
    counter = 0
    for idx, node in enumerate(nodes):
        if node.result.outputs is None:
            continue
        if isinstance(node.result.outputs, Bunch):
            outputs = node.result.outputs.dictcopy()
        else:
            outputs = node.result.outputs.get()
        used_ports = {}
        for _, v, d in graph.out_edges_iter([node], data=True):
            for src, dest in d['connect']:
                if isinstance(src, tuple):
                    srcname = src[0]
                else:
                    srcname = src
                if srcname not in used_ports:
                    used_ports[srcname] = []
                used_ports[srcname].append((v, dest))
        for outidx, nameval in enumerate(sorted(outputs.items())):
            if not isdefined(nameval[1]):
                continue
            artifact = g.entity(uuid1().hex,
                                {prov.PROV["type"]: nipype['artifact'],
                                 prov.PROV["label"]: nameval[0],
                                 nipype['port']: nameval[0],
                                 prov.PROV["value"]: str(nameval[1])
                                 })
            g.wasGeneratedBy(artifact, processes[idx])
            if nameval[0] in used_ports:
                for destnode, portname in used_ports[nameval[0]]:
                    counter += 1
                    # Used: Artifact->Process
                    attrs = {prov.PROV["label"]: portname}
                    g.used(processes[nodes.index(destnode)], artifact,
                           other_attributes=attrs)
    # Process->Process
    for idx, edgeinfo in enumerate(graph.in_edges_iter()):
        g.wasStartedBy(processes[nodes.index(edgeinfo[1])],
                       starter=processes[nodes.index(edgeinfo[0])])
    # write provenance
    try:
        if format in ['turtle', 'all']:
            g.rdf().serialize(filename + '.ttl', format='turtle')
    except (ImportError, NameError):
        format = 'all'
    finally:
        if format in ['provn', 'all']:
            with open(filename + '.provn', 'wt') as fp:
                fp.writelines(g.get_provn())
        if format in ['json', 'all']:
            with open(filename + '.json', 'wt') as fp:
                prov.json.dump(g, fp, cls=prov.ProvBundle.JSONEncoder)
    return g
