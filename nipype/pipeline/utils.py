# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Utility routines for workflow graphs
"""

from copy import deepcopy
from glob import glob
import logging
import os
import re

import numpy as np
from nipype.utils.misc import package_check
package_check('networkx', '1.3')
import networkx as nx

from nipype.interfaces.base import CommandLine, isdefined, Undefined
from nipype.utils.filemanip import fname_presuffix, FileNotFoundError
from nipype.utils.config import config

logger = logging.getLogger('workflow')

try:
    dfs_preorder = nx.dfs_preorder
except AttributeError:
    dfs_preorder = nx.dfs_preorder_nodes
    logger.debug('networkx 1.4 dev or higher detected')

try:
    from os.path import relpath
except ImportError:
    import os
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
                raise ValueError("Cannot mix UNC and non-UNC paths (%s and%s)" %
                                                                    (path, start))
            else:
                raise ValueError("path is on drive %s, start on drive %s"
                                             % (path_list[0], start_list[0]))
        # Work out how much of the filepath is shared by start and path.
        for i in range(min(len(start_list), len(path_list))):
            if start_list[i].lower() != path_list[i].lower():
                break
        else:
            i += 1

        rel_list = [op.pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return os.curdir
        return op.join(*rel_list)

def modify_paths(object, relative=True, basedir=None):
    """Modify filenames in a data structure to either full paths or relative paths
    """
    if not basedir:
        basedir = os.getcwd()
    if isinstance(object, dict):
        out = {}
        for key, val in sorted(object.items()):
            if isdefined(val):
                out[key] = modify_paths(val, relative=relative,
                                        basedir=basedir)
    elif isinstance(object, (list,tuple)):
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
                    if config.getboolean('execution','use_relative_paths'):
                        out = relpath(object,start=basedir)
                    else:
                        out = object
                else:
                    out = os.path.abspath(os.path.join(basedir,object))
                if not os.path.exists(out):
                    raise FileNotFoundError('File %s not found'%out)
            else:
                out = object
    return out

def get_print_name(node):
    """Get the name of the node

    For example, a node containing an instance of interfaces.fsl.BET
    would be called nodename.BET.fsl
    
    """
    name = node.name
    if hasattr(node, '_interface'):
        pkglist = node._interface.__class__.__module__.split('.')
        interface = node._interface.__class__.__name__
        destclass = ''
        if len(pkglist) > 2:
            destclass = '.%s'%pkglist[2]
        name = '.'.join([node.name, interface]) + destclass
    return name
    
def _create_dot_graph(graph, show_connectinfo=False):
    """Create a graph that can be pickled.

    Ensures that edge info is pickleable.
    """
    logger.debug('creating dot graph')
    pklgraph = nx.DiGraph()
    for edge in graph.edges():
        data = graph.get_edge_data(*edge)
        srcname = get_print_name(edge[0])
        destname = get_print_name(edge[1])
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
                ipstrip = 'in'+replacefunk(inport)
                opstrip = 'out'+replacefunk(outport)
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
            interface = n._interface.__class__.__name__
            if len(pkglist) > 2:
                srcpackage = pkglist[2]
        srchierarchy = '.'.join(nodename.split('.')[1:-1])
        nodenamestr = '{ %s | %s | %s }'% (nodename.split('.')[-1], srcpackage, srchierarchy)
        text += ['%s [label="%s|%s|%s"];' % (nodename.replace('.', ''),
                                             inputstr, nodenamestr,
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
        for child_paths in walk(tail, level+1, path, usename):
            yield child_paths

def get_levels(G):
    levels = {}
    for n in nx.topological_sort(G):
        levels[n] = 0
        for pred in G.predecessors_iter(n):
            levels[n] = max(levels[n], levels[pred]+1)
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
    ids = [n._hierarchy+n._id for n in supernodes]
    if len(np.unique(ids)) != len(ids):
        # This should trap the problem of miswiring when multiple iterables are
        # used at the same level. The use of the template below for naming
        # updates to nodes is the general solution.
        raise Exception('Execution graph does not have a unique set of node names. Please rerun the workflow')
    edgeinfo = {}
    for n in subgraph.nodes():
        nidx = ids.index(n._hierarchy+n._id)
        for edge in supergraph.in_edges_iter(supernodes[nidx]):
                #make sure edge is not part of subgraph
            if edge[0] not in subgraph.nodes():
                if n._hierarchy+n._id not in edgeinfo.keys():
                    edgeinfo[n._hierarchy+n._id] = []
                edgeinfo[n._hierarchy+n._id].append((edge[0],
                                       supergraph.get_edge_data(*edge)))
    supergraph.remove_nodes_from(nodes)
    # Add copies of the subgraph depending on the number of iterables
    count = 0
    for i, params in enumerate(walk(iterables.items())):
        count += 1
    template = '.%s%%0%dd'%(prefix, np.ceil(np.log10(count)))
    for i, params in enumerate(walk(iterables.items())):
        Gc = deepcopy(subgraph)
        ids = [n._hierarchy+n._id for n in Gc.nodes()]
        nodeidx = ids.index(nodeid)
        rootnode = Gc.nodes()[nodeidx]
        paramstr = ''
        for key, val in sorted(params.items()):
            paramstr = '_'.join((paramstr, _get_valid_pathstr(key),
                                 _get_valid_pathstr(str(val)))) #.replace(os.sep, '_')))
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
            if node._hierarchy+node._id in edgeinfo.keys():
                for info in edgeinfo[node._hierarchy+node._id]:
                    supergraph.add_edges_from([(info[0], node, info[1])])
            node._id += template%i
    return supergraph

def generate_expanded_graph(graph_in):
    """Generates an expanded graph based on node parameterization
    
    Parameterization is controlled using the `iterables` field of the
    pipeline elements.  Thus if there are two nodes with iterables a=[1,2]
    and b=[3,4] this procedure will generate a graph with sub-graphs
    parameterized as (a=1,b=3), (a=1,b=4), (a=2,b=3) and (a=2,b=4). 
    """
    logger.debug("PE: expanding iterables")
    moreiterables = True
    # convert list of tuples to dict fields
    for node in graph_in.nodes():
        if isinstance(node.iterables, tuple):
            node.iterables = [node.iterables]
    for node in graph_in.nodes():
        if isinstance(node.iterables, list):
            node.iterables = dict(map(lambda(x):(x[0], lambda:x[1]),
                                      node.iterables))
    allprefixes = list('0abcdefghijklmnopqrstuvwxyz')
    iterable_prefix = '0'
    while moreiterables:
        nodes = nx.topological_sort(graph_in)
        nodes.reverse()
        inodes = [node for node in nodes if node.iterables is not None]
        if inodes:
            node = inodes[0]
            iterables = node.iterables.copy()
            iterable_prefix = allprefixes[allprefixes.index(iterable_prefix)+1]
            logger.debug('node: %s iterables: %s'%(node, iterables))
            #nx.write_dot(graph_in, '%s_pre.dot'%node)
            node.iterables = None
            node._id += ('.' + iterable_prefix + 'I')
            subnodes = [s for s in dfs_preorder(graph_in, node)]
            logger.debug(('subnodes:' , subnodes))
            subgraph = graph_in.subgraph(subnodes)
            graph_in = _merge_graphs(graph_in, subnodes,
                                     subgraph, node._hierarchy+node._id,
                                     iterables, iterable_prefix)
            #nx.write_dot(graph_in, '%s_post.dot'%node)
        else:
            moreiterables = False
    for node in graph_in.nodes():
        if node.parameterization:
           node.parameterization = [param for _, param in sorted(node.parameterization)]
    logger.debug("PE: expanding iterables ... done")
    return graph_in

def export_graph(graph_in, base_dir=None, show = False, use_execgraph=False,
                 show_connectinfo=False, dotfilename='graph.dot', format='png'):
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
    logger.info('Creating detailed dot file: %s'%outfname)
    _write_detailed_dot(graph, outfname)
    cmd = 'dot -T%s -O %s' % (format, outfname)
    res = CommandLine(cmd).run()
    if res.runtime.returncode:
        logger.warn('dot2png: %s', res.runtime.stderr)
    pklgraph = _create_dot_graph(graph, show_connectinfo)
    outfname = fname_presuffix(dotfilename,
                               suffix='.dot',
                               use_ext=False,
                               newpath=base_dir)
    nx.write_dot(pklgraph, outfname)
    logger.info('Creating dot file: %s' % outfname)
    cmd = 'dot -T%s -O %s' % (format, outfname)
    res = CommandLine(cmd).run()
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
    logger.info('Converting dotfile: %s to %s format'%(dotfilename, format))

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
    elif isinstance(object, (list,tuple)):
        for val in object:
            if isdefined(val):
                out.extend(walk_outputs(val))
    else:
        if isdefined(object) and isinstance(object, str):
            if os.path.islink(object) or os.path.isfile(object):
                out = [(filename,'f') for filename in get_all_files(object)]
            elif os.path.isdir(object):
                out = [(object,'d')]
    return out

def walk_files(cwd):
    for path, _, files in os.walk(cwd):
        for f in files:
            yield os.path.join(path, f)

def clean_working_directory(outputs, cwd, inputs, needed_outputs,
                            files2keep=None, dirs2keep=None):
    """Removes all files not needed for further analysis from the directory
    """
    if not needed_outputs:
        return outputs
    # build a list of needed files
    output_files = []
    outputdict = outputs.get()
    for output in needed_outputs:
        output_files.extend(walk_outputs(outputdict[output]))
    needed_files = [path for path, type in output_files if type == 'f']
    input_files = []
    inputdict = inputs.get()
    input_files.extend(walk_outputs(inputdict))
    needed_files += [path for path, type in input_files if type == 'f']
    for extra in ['_0x*.json', 'provenance.xml', 'pyscript*.m',
                  'command.txt', 'result*.pklz', '_inputs.pklz']:
        needed_files.extend(glob(os.path.join(cwd, extra)))
    if files2keep:
        needed_files.extend(filename_to_list(files2keep))
    needed_dirs = [path for path, type in output_files if type == 'd']
    if dirs2keep:
        needed_dirs.extend(filename_to_list(dirs2keep))
    for extra in ['_nipype', '_report']:
        needed_dirs.extend(glob(os.path.join(cwd, extra)))
    logger.debug('Needed files: %s'%(';'.join(needed_files)))
    logger.debug('Needed dirs: %s'%(';'.join(needed_dirs)))
    files2remove = []
    for f in walk_files(cwd):
        if f not in needed_files:
            if len(needed_dirs) == 0:
                files2remove.append(f)
            elif not any([f.startswith(dirname) for dirname in needed_dirs]):
                files2remove.append(f)
    logger.debug('Removing files: %s'%(';'.join(files2remove)))
    for f in files2remove:
        os.remove(f)
    for key in outputs.copyable_trait_names():
        if key not in needed_outputs:
            setattr(outputs, key, Undefined)
    return outputs

def merge_dict(d1, d2, merge=lambda x,y:y):
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
    for k,v in d2.iteritems():
        if k in result:
            result[k] = merge_dict(result[k], v, merge=merge)
        else:
            result[k] = v
    return result
