# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Utility routines for workflow graphs"""
import os
import sys
import pickle
from collections import defaultdict
import re
from copy import deepcopy
from glob import glob
from pathlib import Path

from traceback import format_exception
from hashlib import sha1

from functools import reduce

import numpy as np

from ... import logging, config
from ...utils.filemanip import (
    indirectory,
    relpath,
    fname_presuffix,
    ensure_list,
    get_related_files,
    save_json,
    savepkl,
    loadpkl,
    write_rst_header,
    write_rst_dict,
    write_rst_list,
)
from ...utils.misc import str2bool
from ...utils.functions import create_function_from_source
from ...interfaces.base.traits_extension import (
    rebase_path_traits,
    resolve_path_traits,
    OutputMultiPath,
    isdefined,
    Undefined,
)
from ...interfaces.base.support import Bunch, InterfaceResult
from ...interfaces.base import CommandLine
from ...interfaces.utility import IdentityInterface
from ...utils.provenance import ProvStore, pm, nipype_ns, get_id

from inspect import signature

logger = logging.getLogger("nipype.workflow")


def _parameterization_dir(param, maxlen):
    """
    Returns the directory name for the given parameterization string as follows:
        - If the parameterization is longer than maxlen characters, then
          return the SHA-1 hex digest.
        - Otherwise, return the parameterization unchanged.
    """
    if len(param) > maxlen:
        return sha1(param.encode()).hexdigest()
    return param


def save_hashfile(hashfile, hashed_inputs):
    """Store a hashfile"""
    try:
        save_json(hashfile, hashed_inputs)
    except (OSError, TypeError):
        err_type = sys.exc_info()[0]
        if err_type is TypeError:
            # XXX - SG current workaround is to just
            # create the hashed file and not put anything
            # in it
            with open(hashfile, "w") as fd:
                fd.writelines(str(hashed_inputs))

            logger.debug("Unable to write a particular type to the json file")
        else:
            logger.critical("Unable to open the file in write mode: %s", hashfile)


def nodelist_runner(nodes, updatehash=False, stop_first=False):
    """
    A generator that iterates and over a list of ``nodes`` and
    executes them.

    """
    for i, node in nodes:
        err = None
        result = None
        try:
            result = node.run(updatehash=updatehash)
        except Exception:
            if stop_first:
                raise

            result = node.result
            err = []
            if result.runtime and hasattr(result.runtime, "traceback"):
                err = [result.runtime.traceback]

            err += format_exception(*sys.exc_info())
            err = "\n".join(err)
        finally:
            yield i, result, err


def write_node_report(node, result=None, is_mapnode=False):
    """Write a report file for a node."""
    if not str2bool(node.config["execution"]["create_report"]):
        return

    cwd = node.output_dir()
    report_file = Path(cwd) / "_report" / "report.rst"
    report_file.parent.mkdir(exist_ok=True, parents=True)

    lines = [
        write_rst_header("Node: %s" % get_print_name(node), level=0),
        write_rst_list(["Hierarchy : %s" % node.fullname, "Exec ID : %s" % node._id]),
        write_rst_header("Original Inputs", level=1),
        write_rst_dict(node.inputs.trait_get()),
    ]

    if result is None:
        logger.debug('[Node] Writing pre-exec report to "%s"', report_file)
        report_file.write_text("\n".join(lines), encoding='utf-8')
        return

    logger.debug('[Node] Writing post-exec report to "%s"', report_file)
    lines += [
        write_rst_header("Execution Inputs", level=1),
        write_rst_dict(node.inputs.trait_get()),
        write_rst_header("Execution Outputs", level=1),
    ]

    outputs = result.outputs
    if outputs is None:
        lines += ["None"]
        report_file.write_text("\n".join(lines), encoding='utf-8')
        return

    if isinstance(outputs, Bunch):
        lines.append(write_rst_dict(outputs.dictcopy()))
    elif outputs:
        lines.append(write_rst_dict(outputs.trait_get()))
    else:
        lines += ["Outputs object was empty."]

    if is_mapnode:
        lines.append(write_rst_header("Subnode reports", level=1))
        nitems = len(ensure_list(getattr(node.inputs, node.iterfield[0])))
        subnode_report_files = []
        for i in range(nitems):
            subnode_file = (
                Path(cwd)
                / "mapflow"
                / ("_%s%d" % (node.name, i))
                / "_report"
                / "report.rst"
            )
            subnode_report_files.append("subnode %d : %s" % (i, subnode_file))

        lines.append(write_rst_list(subnode_report_files))
        report_file.write_text("\n".join(lines), encoding='utf-8')
        return

    lines.append(write_rst_header("Runtime info", level=1))
    # Init rst dictionary of runtime stats
    rst_dict = {
        "hostname": result.runtime.hostname,
        "duration": result.runtime.duration,
        "working_dir": result.runtime.cwd,
        "prev_wd": getattr(result.runtime, "prevcwd", "<not-set>"),
    }

    for prop in ("cmdline", "mem_peak_gb", "cpu_percent"):
        if hasattr(result.runtime, prop):
            rst_dict[prop] = getattr(result.runtime, prop)

    lines.append(write_rst_dict(rst_dict))

    # Collect terminal output
    if hasattr(result.runtime, "merged"):
        lines += [
            write_rst_header("Terminal output", level=2),
            write_rst_list(result.runtime.merged),
        ]
    if hasattr(result.runtime, "stdout"):
        lines += [
            write_rst_header("Terminal - standard output", level=2),
            write_rst_list(result.runtime.stdout),
        ]
    if hasattr(result.runtime, "stderr"):
        lines += [
            write_rst_header("Terminal - standard error", level=2),
            write_rst_list(result.runtime.stderr),
        ]

    # Store environment
    if hasattr(result.runtime, "environ"):
        lines += [
            write_rst_header("Environment", level=2),
            write_rst_dict(result.runtime.environ),
        ]

    report_file.write_text("\n".join(lines), encoding='utf-8')


def write_report(node, report_type=None, is_mapnode=False):
    """Write a report file for a node - DEPRECATED"""
    if report_type not in ("preexec", "postexec"):
        logger.warning('[Node] Unknown report type "%s".', report_type)
        return

    write_node_report(
        node,
        is_mapnode=is_mapnode,
        result=node.result if report_type == "postexec" else None,
    )


def save_resultfile(result, cwd, name, rebase=None):
    """Save a result pklz file to ``cwd``."""
    if rebase is None:
        rebase = config.getboolean("execution", "use_relative_paths")

    cwd = os.path.abspath(cwd)
    resultsfile = os.path.join(cwd, "result_%s.pklz" % name)
    logger.debug("Saving results file: '%s'", resultsfile)

    if result.outputs is None:
        logger.warning("Storing result file without outputs")
        savepkl(resultsfile, result)
        return
    try:
        output_names = result.outputs.copyable_trait_names()
    except AttributeError:
        logger.debug("Storing non-traited results, skipping rebase of paths")
        savepkl(resultsfile, result)
        return

    if not rebase:
        savepkl(resultsfile, result)
        return

    backup_traits = {}
    try:
        with indirectory(cwd):
            # All the magic to fix #2944 resides here:
            for key in output_names:
                old = getattr(result.outputs, key)
                if isdefined(old):
                    if result.outputs.trait(key).is_trait_type(OutputMultiPath):
                        old = result.outputs.trait(key).handler.get_value(
                            result.outputs, key
                        )
                    backup_traits[key] = old
                    val = rebase_path_traits(result.outputs.trait(key), old, cwd)
                    setattr(result.outputs, key, val)
        savepkl(resultsfile, result)
    finally:
        # Restore resolved paths from the outputs dict no matter what
        for key, val in list(backup_traits.items()):
            setattr(result.outputs, key, val)


def load_resultfile(results_file, resolve=True):
    """
    Load InterfaceResult file from path.

    Parameters
    ----------
    results_file : pathlike
        Path to an existing pickle (``result_<interface name>.pklz``) created with
        ``save_resultfile``.
        Raises ``FileNotFoundError`` if ``results_file`` does not exist.
    resolve : bool
        Determines whether relative paths will be resolved to absolute (default is ``True``).

    Returns
    -------
    result : InterfaceResult
        A Nipype object containing the runtime, inputs, outputs and other interface information
        such as a traceback in the case of errors.

    """
    results_file = Path(results_file)
    if not results_file.exists():
        raise FileNotFoundError(results_file)

    result = loadpkl(results_file)
    if resolve and getattr(result, "outputs", None):
        try:
            outputs = result.outputs.get()
        except TypeError:  # This is a Bunch
            logger.debug("Outputs object of loaded result %s is a Bunch.", results_file)
            return result

        logger.debug("Resolving paths in outputs loaded from results file.")
        for trait_name, old in list(outputs.items()):
            if isdefined(old):
                if result.outputs.trait(trait_name).is_trait_type(OutputMultiPath):
                    old = result.outputs.trait(trait_name).handler.get_value(
                        result.outputs, trait_name
                    )
                value = resolve_path_traits(
                    result.outputs.trait(trait_name), old, results_file.parent
                )
                setattr(result.outputs, trait_name, value)
    return result


def strip_temp(files, wd):
    """Remove temp from a list of file paths"""
    out = []
    for f in files:
        if isinstance(f, list):
            out.append(strip_temp(f, wd))
        else:
            out.append(f.replace(os.path.join(wd, "_tempinput"), wd))
    return out


def _write_inputs(node):
    lines = []
    nodename = node.fullname.replace(".", "_")
    for key, _ in list(node.inputs.items()):
        val = getattr(node.inputs, key)
        if isdefined(val):
            if isinstance(val, (str, bytes)):
                try:
                    func = create_function_from_source(val)
                except RuntimeError:
                    lines.append(f"{nodename}.inputs.{key} = '{val}'")
                else:
                    funcname = [
                        name for name in func.__globals__ if name != "__builtins__"
                    ][0]
                    lines.append(pickle.loads(val))
                    if funcname == nodename:
                        lines[-1] = lines[-1].replace(
                            " %s(" % funcname, " %s_1(" % funcname
                        )
                        funcname = "%s_1" % funcname
                    lines.append("from nipype.utils.functions import getsource")
                    lines.append(f"{nodename}.inputs.{key} = getsource({funcname})")
            else:
                lines.append(f"{nodename}.inputs.{key} = {val}")
    return lines


def format_node(node, format="python", include_config=False):
    """Format a node in a given output syntax."""
    from .nodes import MapNode

    lines = []
    name = node.fullname.replace(".", "_")
    if format == "python":
        klass = node.interface
        importline = f"from {klass.__module__} import {klass.__class__.__name__}"
        comment = "# Node: %s" % node.fullname
        spec = signature(node.interface.__init__)
        filled_args = []
        for param in spec.parameters.values():
            val = getattr(node.interface, f"_{param.name}", None)
            if val is not None:
                filled_args.append(f"{param.name}={val!r}")
        args = ", ".join(filled_args)
        klass_name = klass.__class__.__name__
        if isinstance(node, MapNode):
            nodedef = '{} = MapNode({}({}), iterfield={}, name="{}")'.format(
                name,
                klass_name,
                args,
                node.iterfield,
                name,
            )
        else:
            nodedef = f'{name} = Node({klass_name}({args}), name="{name}")'
        lines = [importline, comment, nodedef]

        if include_config:
            lines = [
                importline,
                "from collections import OrderedDict",
                comment,
                nodedef,
            ]
            lines.append(f"{name}.config = {node.config}")

        if node.iterables is not None:
            lines.append(f"{name}.iterables = {node.iterables}")
        lines.extend(_write_inputs(node))

    return lines


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
                out[key] = modify_paths(val, relative=relative, basedir=basedir)
    elif isinstance(object, (list, tuple)):
        out = []
        for val in object:
            if isdefined(val):
                out.append(modify_paths(val, relative=relative, basedir=basedir))
        if isinstance(object, tuple):
            out = tuple(out)
    else:
        if isdefined(object):
            if isinstance(object, (str, bytes)) and os.path.isfile(object):
                if relative:
                    if config.getboolean("execution", "use_relative_paths"):
                        out = relpath(object, start=basedir)
                    else:
                        out = object
                else:
                    out = os.path.abspath(os.path.join(basedir, object))
                if not os.path.exists(out):
                    raise OSError("File %s not found" % out)
            else:
                out = object
        else:
            raise TypeError(f"Object {object} is undefined")
    return out


def get_print_name(node, simple_form=True):
    """Get the name of the node

    For example, a node containing an instance of interfaces.fsl.BET
    would be called nodename.BET.fsl

    """
    name = node.fullname
    if hasattr(node, "_interface"):
        pkglist = node.interface.__class__.__module__.split(".")
        interface = node.interface.__class__.__name__
        destclass = ""
        if len(pkglist) > 2:
            destclass = ".%s" % pkglist[2]
        if simple_form:
            name = f"{node.fullname}{destclass}"
        else:
            name = f"{node.fullname}.{interface}{destclass}"
    if simple_form:
        parts = name.split(".")
        if len(parts) > 2:
            return " (".join(parts[1:]) + ")"
        elif len(parts) == 2:
            return parts[1]
    return name


def _create_dot_graph(graph, show_connectinfo=False, simple_form=True):
    """Create a graph that can be pickled.

    Ensures that edge info is pickleable.
    """
    logger.debug("creating dot graph")
    import networkx as nx

    pklgraph = nx.DiGraph()
    for edge in graph.edges():
        data = graph.get_edge_data(*edge)
        srcname = get_print_name(edge[0], simple_form=simple_form)
        destname = get_print_name(edge[1], simple_form=simple_form)
        if show_connectinfo:
            pklgraph.add_edge(f'"{srcname}"', f'"{destname}"', l=str(data["connect"]))
        else:
            pklgraph.add_edge(f'"{srcname}"', f'"{destname}"')
    return pklgraph


def _write_detailed_dot(graph, dotfilename):
    r"""
    Create a dot file with connection info ::

        digraph structs {
        node [shape=record];
        struct1 [label="<f0> left|<f1> middle|<f2> right"];
        struct2 [label="<f0> one|<f1> two"];
        struct3 [label="hello\nworld |{ b |{c|<here> d|e}| f}| g | h"];
        struct1:f1 -> struct2:f0;
        struct1:f0 -> struct2:f1;
        struct1:f2 -> struct3:here;
        }
    """
    import networkx as nx

    text = ["digraph structs {", "node [shape=record];"]
    # write nodes
    edges = []
    for n in nx.topological_sort(graph):
        nodename = n.itername
        in_ports = []
        for u, v, d in graph.in_edges(nbunch=n, data=True):
            for cd in d["connect"]:
                if isinstance(cd[0], (str, bytes)):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                in_port = cd[1]
                ipstrip = "in%s" % _replacefunk(in_port)
                opstrip = "out%s" % _replacefunk(outport)
                edges.append(
                    "%s:%s:e -> %s:%s:w;"
                    % (
                        u.itername.replace(".", ""),
                        opstrip,
                        v.itername.replace(".", ""),
                        ipstrip,
                    )
                )
                if in_port not in in_ports:
                    in_ports.append(in_port)
        inputstr = (
            ["{IN"]
            + [f"|<in{_replacefunk(ip)}> {ip}" for ip in sorted(in_ports)]
            + ["}"]
        )
        outports = []
        for u, v, d in graph.out_edges(nbunch=n, data=True):
            for cd in d["connect"]:
                if isinstance(cd[0], (str, bytes)):
                    outport = cd[0]
                else:
                    outport = cd[0][0]
                if outport not in outports:
                    outports.append(outport)
        outputstr = (
            ["{OUT"]
            + [f"|<out{_replacefunk(oport)}> {oport}" for oport in sorted(outports)]
            + ["}"]
        )
        srcpackage = ""
        if hasattr(n, "_interface"):
            pkglist = n.interface.__class__.__module__.split(".")
            if len(pkglist) > 2:
                srcpackage = pkglist[2]
        srchierarchy = ".".join(nodename.split(".")[1:-1])
        nodenamestr = "{{ {} | {} | {} }}".format(
            nodename.split(".")[-1],
            srcpackage,
            srchierarchy,
        )
        text += [
            '%s [label="%s|%s|%s"];'
            % (
                nodename.replace(".", ""),
                "".join(inputstr),
                nodenamestr,
                "".join(outputstr),
            )
        ]
    # write edges
    for edge in sorted(edges):
        text.append(edge)
    text.append("}")
    with open(dotfilename, "w") as filep:
        filep.write("\n".join(text))
    return text


def _replacefunk(x):
    return x.replace("_", "").replace(".", "").replace("@", "").replace("-", "")


# Graph manipulations for iterable expansion
def _get_valid_pathstr(pathstr):
    """Remove disallowed characters from path

    Removes:  [][ (){}?:<>#!|"';]
    Replaces: ',' -> '.'
    """
    if not isinstance(pathstr, (str, bytes)):
        pathstr = str(pathstr)
    pathstr = pathstr.replace(os.sep, "..")
    pathstr = re.sub(r"""[][ (){}?:<>#!|"';]""", "", pathstr)
    pathstr = pathstr.replace(",", ".")
    return pathstr


def expand_iterables(iterables, synchronize=False):
    if synchronize:
        return synchronize_iterables(iterables)
    return list(walk(list(iterables.items())))


def count_iterables(iterables, synchronize=False):
    """Return the number of iterable expansion nodes.

    If synchronize is True, then the count is the maximum number
    of iterables value lists.
    Otherwise, the count is the product of the iterables value
    list sizes.
    """
    op = max if synchronize else lambda x, y: x * y
    return reduce(op, [len(func()) for _, func in list(iterables.items())])


def walk(children, level=0, path=None, usename=True):
    """Generate all the full paths in a tree, as a dict.

    Examples
    --------
    >>> from nipype.pipeline.engine.utils import walk
    >>> iterables = [('a', lambda: [1, 2]), ('b', lambda: [3, 4])]
    >>> [val['a'] for val in walk(iterables)]
    [1, 1, 2, 2]
    >>> [val['b'] for val in walk(iterables)]
    [3, 4, 3, 4]
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
        yield from walk(tail, level + 1, path, usename)


def synchronize_iterables(iterables):
    """Synchronize the given iterables in item-wise order.

    Return: the {field: value} dictionary list

    Examples
    --------
    >>> from nipype.pipeline.engine.utils import synchronize_iterables
    >>> iterables = dict(a=lambda: [1, 2], b=lambda: [3, 4])
    >>> synced = synchronize_iterables(iterables)
    >>> synced == [{'a': 1, 'b': 3}, {'a': 2, 'b': 4}]
    True
    >>> iterables = dict(a=lambda: [1, 2], b=lambda: [3], c=lambda: [4, 5, 6])
    >>> synced = synchronize_iterables(iterables)
    >>> synced == [{'a': 1, 'b': 3, 'c': 4}, {'a': 2, 'c': 5}, {'c': 6}]
    True
    """
    out_list = []
    iterable_items = [
        (field, iter(fvals())) for field, fvals in sorted(iterables.items())
    ]
    while True:
        cur_dict = {}
        for field, iter_values in iterable_items:
            try:
                cur_dict[field] = next(iter_values)
            except StopIteration:
                pass
        if cur_dict:
            out_list.append(cur_dict)
        else:
            break

    return out_list


def evaluate_connect_function(function_source, args, first_arg):
    func = create_function_from_source(function_source)
    try:
        output_value = func(first_arg, *list(args))
    except NameError as e:
        raise NameError(
            f"{e}: Due to engine constraints all imports have to be done inside each "
            " function definition."
        )
    return output_value


def get_levels(G):
    import networkx as nx

    levels = {}
    for n in nx.topological_sort(G):
        levels[n] = 0
        for pred in G.predecessors(n):
            levels[n] = max(levels[n], levels[pred] + 1)
    return levels


def _merge_graphs(
    supergraph, nodes, subgraph, nodeid, iterables, prefix, synchronize=False
):
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
    if len(set(ids)) != len(ids):
        # This should trap the problem of miswiring when multiple iterables are
        # used at the same level. The use of the template below for naming
        # updates to nodes is the general solution.
        raise Exception(
            "Execution graph does not have a unique set of node "
            "names. Please rerun the workflow"
        )
    edgeinfo = {}
    for n in list(subgraph.nodes()):
        nidx = ids.index(n._hierarchy + n._id)
        for edge in supergraph.in_edges(list(supernodes)[nidx]):
            # make sure edge is not part of subgraph
            if edge[0] not in subgraph.nodes():
                if n._hierarchy + n._id not in list(edgeinfo.keys()):
                    edgeinfo[n._hierarchy + n._id] = []
                edgeinfo[n._hierarchy + n._id].append(
                    (edge[0], supergraph.get_edge_data(*edge))
                )
    supergraph.remove_nodes_from(nodes)
    # Add copies of the subgraph depending on the number of iterables
    iterable_params = expand_iterables(iterables, synchronize)
    # If there are no iterable subgraphs, then return
    if not iterable_params:
        return supergraph
    # Make an iterable subgraph node id template
    count = len(iterable_params)
    template = ".%s%%0%dd" % (prefix, np.ceil(np.log10(count)))
    # Copy the iterable subgraphs
    for i, params in enumerate(iterable_params):
        Gc = deepcopy(subgraph)
        ids = [n._hierarchy + n._id for n in Gc.nodes()]
        nodeidx = ids.index(nodeid)
        rootnode = list(Gc.nodes())[nodeidx]
        paramstr = ""
        for key, val in sorted(params.items()):
            paramstr = "{}_{}_{}".format(
                paramstr, _get_valid_pathstr(key), _get_valid_pathstr(val)
            )
            rootnode.set_input(key, val)

        logger.debug("Parameterization: paramstr=%s", paramstr)
        levels = get_levels(Gc)
        for n in Gc.nodes():
            # update parameterization of the node to reflect the location of
            # the output directory.  For example, if the iterables along a
            # path of the directed graph consisted of the variables 'a' and
            # 'b', then every node in the path including and after the node
            # with iterable 'b' will be placed in a directory
            # _a_aval/_b_bval/.

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
            if node._hierarchy + node._id in list(edgeinfo.keys()):
                for info in edgeinfo[node._hierarchy + node._id]:
                    supergraph.add_edges_from([(info[0], node, info[1])])
            node._id += template % i
    return supergraph


def _connect_nodes(graph, srcnode, destnode, connection_info):
    """Add a connection between two nodes"""
    data = graph.get_edge_data(srcnode, destnode, default=None)
    if not data:
        data = {"connect": connection_info}
        graph.add_edges_from([(srcnode, destnode, data)])
    else:
        data["connect"].extend(connection_info)


def _remove_nonjoin_identity_nodes(graph, keep_iterables=False):
    """Remove non-join identity nodes from the given graph

    Iterable nodes are retained if and only if the keep_iterables
    flag is set to True.
    """
    # if keep_iterables is False, then include the iterable
    # and join nodes in the nodes to delete
    for node in _identity_nodes(graph, not keep_iterables):
        if not hasattr(node, "joinsource"):
            _remove_identity_node(graph, node)
    return graph


def _identity_nodes(graph, include_iterables):
    """Return the IdentityInterface nodes in the graph

    The nodes are in topological sort order. The iterable nodes
    are included if and only if the include_iterables flag is set
    to True.
    """
    import networkx as nx

    return [
        node
        for node in nx.topological_sort(graph)
        if isinstance(node.interface, IdentityInterface)
        and (include_iterables or node.iterables is None)
    ]


def _remove_identity_node(graph, node):
    """Remove identity nodes from an execution graph"""
    portinputs, portoutputs = _node_ports(graph, node)
    for field, connections in list(portoutputs.items()):
        if portinputs:
            _propagate_internal_output(graph, node, field, connections, portinputs)
        else:
            _propagate_root_output(graph, node, field, connections)
    graph.remove_nodes_from([node])
    logger.debug("Removed the identity node %s from the graph.", node)


def _node_ports(graph, node):
    """Return the given node's input and output ports

    The return value is the (inputs, outputs) dictionaries.
    The inputs is a {destination field: (source node, source field)}
    dictionary.
    The outputs is a {source field: destination items} dictionary,
    where each destination item is a
    (destination node, destination field, source field) tuple.
    """
    portinputs = {}
    portoutputs = {}
    for u, _, d in graph.in_edges(node, data=True):
        for src, dest in d["connect"]:
            portinputs[dest] = (u, src)
    for _, v, d in graph.out_edges(node, data=True):
        for src, dest in d["connect"]:
            if isinstance(src, tuple):
                src_port = src[0]
            else:
                src_port = src
            if src_port not in portoutputs:
                portoutputs[src_port] = []
            portoutputs[src_port].append((v, dest, src))
    return (portinputs, portoutputs)


def _propagate_root_output(graph, node, field, connections):
    """Propagates the given graph root node output port
    field connections to the out-edge destination nodes."""
    for destnode, in_port, src in connections:
        value = getattr(node.inputs, field)
        if isinstance(src, tuple):
            value = evaluate_connect_function(src[1], src[2], value)
        destnode.set_input(in_port, value)


def _propagate_internal_output(graph, node, field, connections, portinputs):
    """Propagates the given graph internal node output port
    field connections to the out-edge source node and in-edge
    destination nodes."""
    for destnode, in_port, src in connections:
        if field in portinputs:
            srcnode, src_port = portinputs[field]
            if isinstance(src_port, tuple) and isinstance(src, tuple):
                src_func = src_port[1].split("\\n")[0]
                dst_func = src[1].split("\\n")[0]
                raise ValueError(
                    "Does not support two inline functions "
                    "in series ('{}'  and '{}'), found when "
                    "connecting {} to {}. Please use a Function "
                    "node.".format(src_func, dst_func, srcnode, destnode)
                )

            connect = graph.get_edge_data(srcnode, destnode, default={"connect": []})
            if isinstance(src, tuple):
                connect["connect"].append(((src_port, src[1], src[2]), in_port))
            else:
                connect = {"connect": [(src_port, in_port)]}
            old_connect = graph.get_edge_data(
                srcnode, destnode, default={"connect": []}
            )
            old_connect["connect"] += connect["connect"]
            graph.add_edges_from([(srcnode, destnode, old_connect)])
        else:
            value = getattr(node.inputs, field)
            if isinstance(src, tuple):
                value = evaluate_connect_function(src[1], src[2], value)
            destnode.set_input(in_port, value)


def generate_expanded_graph(graph_in):
    """Generates an expanded graph based on node parameterization

    Parameterization is controlled using the `iterables` field of the
    pipeline elements.  Thus if there are two nodes with iterables a=[1,2]
    and b=[3,4] this procedure will generate a graph with sub-graphs
    parameterized as (a=1,b=3), (a=1,b=4), (a=2,b=3) and (a=2,b=4).
    """
    import networkx as nx

    try:
        dfs_preorder = nx.dfs_preorder
    except AttributeError:
        dfs_preorder = nx.dfs_preorder_nodes

    logger.debug("PE: expanding iterables")
    graph_in = _remove_nonjoin_identity_nodes(graph_in, keep_iterables=True)
    # standardize the iterables as {(field, function)} dictionaries
    for node in graph_in.nodes():
        if node.iterables:
            _standardize_iterables(node)
    allprefixes = list("abcdefghijklmnopqrstuvwxyz")

    # the iterable nodes
    inodes = _iterable_nodes(graph_in)
    logger.debug("Detected iterable nodes %s", inodes)
    # while there is an iterable node, expand the iterable node's
    # subgraphs
    while inodes:
        inode = inodes[0]
        logger.debug("Expanding the iterable node %s...", inode)

        # the join successor nodes of the current iterable node
        jnodes = [
            node
            for node in graph_in.nodes()
            if hasattr(node, "joinsource")
            and inode.name == node.joinsource
            and nx.has_path(graph_in, inode, node)
        ]

        # excise the join in-edges. save the excised edges in a
        # {jnode: {source name: (destination name, edge data)}}
        # dictionary
        jedge_dict = {}
        for jnode in jnodes:
            in_edges = jedge_dict[jnode] = {}
            edges2remove = []
            for src, dest, data in graph_in.in_edges(jnode, True):
                in_edges[src.itername] = data
                edges2remove.append((src, dest))

            for src, dest in edges2remove:
                graph_in.remove_edge(src, dest)
                logger.debug("Excised the %s -> %s join node in-edge.", src, dest)

        if inode.itersource:
            # the itersource is a (node name, fields) tuple
            src_name, src_fields = inode.itersource
            # convert a single field to a list
            if isinstance(src_fields, (str, bytes)):
                src_fields = [src_fields]
            # find the unique iterable source node in the graph
            try:
                iter_src = next(
                    node
                    for node in graph_in.nodes()
                    if node.name == src_name and nx.has_path(graph_in, node, inode)
                )
            except StopIteration:
                raise ValueError(
                    "The node %s itersource %s was not found"
                    " among the iterable predecessor nodes" % (inode, src_name)
                )
            logger.debug("The node %s has iterable source node %s", inode, iter_src)
            # look up the iterables for this particular itersource descendant
            # using the iterable source ancestor values as a key
            iterables = {}
            # the source node iterables values
            src_values = [getattr(iter_src.inputs, field) for field in src_fields]
            # if there is one source field, then the key is the source value,
            # otherwise the key is the tuple of source values
            if len(src_values) == 1:
                key = src_values[0]
            else:
                key = tuple(src_values)
            # The itersource iterables is a {field: lookup} dictionary, where the
            # lookup is a {source key: iteration list} dictionary. Look up the
            # current iterable value using the predecessor itersource input values.
            iter_dict = {
                field: lookup[key] for field, lookup in inode.iterables if key in lookup
            }

            # convert the iterables to the standard {field: function} format

            def make_field_func(*pair):
                return pair[0], lambda: pair[1]

            iterables = dict(
                [make_field_func(*pair) for pair in list(iter_dict.items())]
            )
        else:
            iterables = inode.iterables.copy()
        inode.iterables = None
        logger.debug("node: %s iterables: %s", inode, iterables)

        # collect the subnodes to expand
        subnodes = list(dfs_preorder(graph_in, inode))
        prior_prefix = [re.findall(r"\.(.)I", s._id) for s in subnodes if s._id]
        prior_prefix = sorted([l for item in prior_prefix for l in item])
        if not prior_prefix:
            iterable_prefix = "a"
        else:
            if prior_prefix[-1] == "z":
                raise ValueError("Too many iterables in the workflow")
            iterable_prefix = allprefixes[allprefixes.index(prior_prefix[-1]) + 1]
        logger.debug(("subnodes:", subnodes))

        # append a suffix to the iterable node id
        inode._id += ".%sI" % iterable_prefix

        # merge the iterated subgraphs
        subgraph = graph_in.subgraph(subnodes).copy()
        graph_in = _merge_graphs(
            graph_in,
            subnodes,
            subgraph,
            inode._hierarchy + inode._id,
            iterables,
            iterable_prefix,
            inode.synchronize,
        )

        # reconnect the join nodes
        for jnode in jnodes:
            # the {node id: edge data} dictionary for edges connecting
            # to the join node in the unexpanded graph
            old_edge_dict = jedge_dict[jnode]
            # the edge source node replicates
            expansions = defaultdict(list)
            for node in graph_in:
                for src_id in list(old_edge_dict.keys()):
                    # Drop the original JoinNodes; only concerned with
                    # generated Nodes
                    itername = node.itername
                    if hasattr(node, "joinfield") and itername == src_id:
                        continue
                    # Patterns:
                    #   - src_id : Non-iterable node
                    #   - src_id.[a-z]\d+ :
                    #       IdentityInterface w/ iterables or nested JoinNode
                    #   - src_id.[a-z]I.[a-z]\d+ :
                    #       Non-IdentityInterface w/ iterables
                    #   - src_idJ\d+ : JoinNode(IdentityInterface)
                    if itername.startswith(src_id):
                        suffix = itername[len(src_id) :]
                        if re.fullmatch(r"((\.[a-z](I\.[a-z])?|J)\d+)?", suffix):
                            expansions[src_id].append(node)
            for in_id, in_nodes in list(expansions.items()):
                logger.debug(
                    "The join node %s input %s was expanded to %d nodes.",
                    jnode,
                    in_id,
                    len(in_nodes),
                )
            # preserve the node iteration order by sorting on the node id
            for in_nodes in list(expansions.values()):
                in_nodes.sort(key=lambda node: node._id)

            # the number of join source replicates.
            iter_cnt = count_iterables(iterables, inode.synchronize)
            # make new join node fields to connect to each replicated
            # join in-edge source node.
            slot_dicts = [jnode._add_join_item_fields() for _ in range(iter_cnt)]
            # for each join in-edge, connect every expanded source node
            # which matches on the in-edge source name to the destination
            # join node. Qualify each edge connect join field name by
            # appending the next join slot index, e.g. the connect
            # from two expanded nodes from field 'out_file' to join
            # field 'in' are qualified as ('out_file', 'in1') and
            # ('out_file', 'in2'), resp. This preserves connection port
            # integrity.
            for old_id, in_nodes in list(expansions.items()):
                # reconnect each replication of the current join in-edge
                # source
                for in_idx, in_node in enumerate(in_nodes):
                    olddata = old_edge_dict[old_id]
                    newdata = deepcopy(olddata)
                    # the (source, destination) field tuples
                    connects = newdata["connect"]
                    # the join fields connected to the source
                    join_fields = [
                        field for _, field in connects if field in jnode.joinfield
                    ]
                    # the {field: slot fields} maps assigned to the input
                    # node, e.g. {'image': 'imageJ3', 'mask': 'maskJ3'}
                    # for the third join source expansion replicate of a
                    # join node with join fields image and mask
                    slots = slot_dicts[in_idx]
                    for con_idx, connect in enumerate(connects):
                        src_field, dest_field = connect
                        # qualify a join destination field name
                        if dest_field in slots:
                            slot_field = slots[dest_field]
                            connects[con_idx] = (src_field, slot_field)
                            logger.debug(
                                "Qualified the %s -> %s join field %s as %s.",
                                in_node,
                                jnode,
                                dest_field,
                                slot_field,
                            )
                    graph_in.add_edge(in_node, jnode, **newdata)
                    logger.debug(
                        "Connected the join node %s subgraph to the"
                        " expanded join point %s",
                        jnode,
                        in_node,
                    )

        # nx.write_dot(graph_in, '%s_post.dot' % node)
        # the remaining iterable nodes
        inodes = _iterable_nodes(graph_in)

    for node in graph_in.nodes():
        if node.parameterization:
            node.parameterization = [
                param for _, param in sorted(node.parameterization)
            ]
    logger.debug("PE: expanding iterables ... done")

    return _remove_nonjoin_identity_nodes(graph_in)


def _iterable_nodes(graph_in):
    """Returns the iterable nodes in the given graph and their join
    dependencies.

    The nodes are ordered as follows:

    - nodes without an itersource precede nodes with an itersource
    - nodes without an itersource are sorted in reverse topological order
    - nodes with an itersource are sorted in topological order

    This order implies the following:

    - every iterable node without an itersource is expanded before any
      node with an itersource

    - every iterable node without an itersource is expanded before any
      of it's predecessor iterable nodes without an itersource

    - every node with an itersource is expanded before any of it's
      successor nodes with an itersource

    Return the iterable nodes list
    """
    import networkx as nx

    nodes = nx.topological_sort(graph_in)
    inodes = [node for node in nodes if node.iterables is not None]
    inodes_no_src = [node for node in inodes if not node.itersource]
    inodes_src = [node for node in inodes if node.itersource]
    inodes_no_src.reverse()
    return inodes_no_src + inodes_src


def _standardize_iterables(node):
    """Converts the given iterables to a {field: function} dictionary,
    if necessary, where the function returns a list."""
    if not node.iterables:
        return
    iterables = node.iterables
    # The candidate iterable fields
    fields = set(node.inputs.copyable_trait_names())
    # A synchronize iterables node without an itersource can be in
    # [fields, value tuples] format rather than
    # [(field, value list), (field, value list), ...]
    if node.synchronize:
        if len(iterables) == 2:
            first, last = iterables
            if all(isinstance(item, (str, bytes)) and item in fields for item in first):
                iterables = _transpose_iterables(first, last)

    # Convert a tuple to a list
    if isinstance(iterables, tuple):
        iterables = [iterables]
    # Validate the standard [(field, values)] format
    _validate_iterables(node, iterables, fields)
    # Convert a list to a dictionary
    if isinstance(iterables, list):
        # Convert a values list to a function. This is a legacy
        # Nipype requirement with unknown rationale.
        if not node.itersource:

            def make_field_func(*pair):
                return pair[0], lambda: pair[1]

            iter_items = [make_field_func(*field_value1) for field_value1 in iterables]
            iterables = dict(iter_items)
    node.iterables = iterables


def _validate_iterables(node, iterables, fields):
    """
    Raise TypeError if an iterables member is not iterable.

    Raise ValueError if an iterables member is not a (field, values) pair.

    Raise ValueError if an iterable field is not in the inputs.
    """
    # The iterables can be a {field: value list} dictionary.
    if isinstance(iterables, dict):
        iterables = list(iterables.items())
    elif not isinstance(iterables, tuple) and not isinstance(iterables, list):
        raise ValueError(
            "The %s iterables type is not a list or a dictionary:"
            " %s" % (node.name, iterables.__class__)
        )
    for item in iterables:
        try:
            if len(item) != 2:
                raise ValueError(
                    "The %s iterables is not a [(field, values)] list" % node.name
                )
        except TypeError as e:
            raise TypeError(f"A {node.name} iterables member is not iterable: {e}")
        field, _ = item
        if field not in fields:
            raise ValueError(
                f"The {node.name} iterables field is unrecognized: {field}"
            )


def _transpose_iterables(fields, values):
    """
    Converts the given fields and tuple values into a standardized
    iterables value.

    If the input values is a synchronize iterables dictionary, then
    the result is a (field, {key: values}) list.

    Otherwise, the result is a list of (field: value list) pairs.
    """
    if isinstance(values, dict):
        transposed = {field: defaultdict(list) for field in fields}
        for key, tuples in list(values.items()):
            for kvals in tuples:
                for idx, val in enumerate(kvals):
                    if val is not None:
                        transposed[fields[idx]][key].append(val)
        return list(transposed.items())

    return list(
        zip(
            fields,
            [
                [v for v in list(transpose) if v is not None]
                for transpose in zip(*values)
            ],
        )
    )


def export_graph(
    graph_in,
    base_dir=None,
    show=False,
    use_execgraph=False,
    show_connectinfo=False,
    dotfilename="graph.dot",
    format="png",
    simple_form=True,
):
    """Displays the graph layout of the pipeline

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
    import networkx as nx

    graph = deepcopy(graph_in)
    if use_execgraph:
        graph = generate_expanded_graph(graph)
        logger.debug("using execgraph")
    else:
        logger.debug("using input graph")
    if base_dir is None:
        base_dir = os.getcwd()

    os.makedirs(base_dir, exist_ok=True)
    out_dot = fname_presuffix(
        dotfilename, suffix="_detailed.dot", use_ext=False, newpath=base_dir
    )
    _write_detailed_dot(graph, out_dot)

    # Convert .dot if format != 'dot'
    outfname, res = _run_dot(out_dot, format_ext=format)
    if res is not None and res.runtime.returncode:
        logger.warning("dot2png: %s", res.runtime.stderr)

    pklgraph = _create_dot_graph(graph, show_connectinfo, simple_form)
    simple_dot = fname_presuffix(
        dotfilename, suffix=".dot", use_ext=False, newpath=base_dir
    )
    nx.drawing.nx_pydot.write_dot(pklgraph, simple_dot)

    # Convert .dot if format != 'dot'
    simplefname, res = _run_dot(simple_dot, format_ext=format)
    if res is not None and res.runtime.returncode:
        logger.warning("dot2png: %s", res.runtime.stderr)

    if show:
        pos = nx.graphviz_layout(pklgraph, prog="dot")
        nx.draw(pklgraph, pos)
        if show_connectinfo:
            nx.draw_networkx_edge_labels(pklgraph, pos)

    return simplefname if simple_form else outfname


def format_dot(dotfilename, format="png"):
    """Dump a directed graph (Linux only; install via `brew` on OSX)"""
    try:
        formatted_dot, _ = _run_dot(dotfilename, format_ext=format)
    except OSError as ioe:
        if "could not be found" in str(ioe):
            raise OSError("Cannot draw directed graph; executable 'dot' is unavailable")
        else:
            raise ioe
    return formatted_dot


def _run_dot(dotfilename, format_ext):
    if format_ext == "dot":
        return dotfilename, None

    dot_base = os.path.splitext(dotfilename)[0]
    formatted_dot = f"{dot_base}.{format_ext}"
    cmd = f'dot -T{format_ext} -o"{formatted_dot}" "{dotfilename}"'
    res = CommandLine(cmd, terminal_output="allatonce", resource_monitor=False).run()
    return formatted_dot, res


def get_all_files(infile):
    files = [infile]
    if infile.endswith(".img"):
        files.append(infile[:-4] + ".hdr")
        files.append(infile[:-4] + ".mat")
    if infile.endswith(".img.gz"):
        files.append(infile[:-7] + ".hdr.gz")
    return files


def walk_outputs(object):
    """Extract every file and directory from a python structure"""
    out = []
    if isinstance(object, dict):
        for _, val in sorted(object.items()):
            if isdefined(val):
                out.extend(walk_outputs(val))
    elif isinstance(object, (list, tuple)):
        for val in object:
            if isdefined(val):
                out.extend(walk_outputs(val))
    else:
        if isdefined(object) and isinstance(object, (str, bytes)):
            if os.path.islink(object) or os.path.isfile(object):
                out = [(filename, "f") for filename in get_all_files(object)]
            elif os.path.isdir(object):
                out = [(object, "d")]
    return out


def walk_files(cwd):
    for path, _, files in os.walk(cwd):
        for f in files:
            yield os.path.join(path, f)


def clean_working_directory(
    outputs, cwd, inputs, needed_outputs, config, files2keep=None, dirs2keep=None
):
    """Removes all files not needed for further analysis from the directory"""
    if not outputs:
        return
    outputs_to_keep = list(outputs.trait_get().keys())
    if needed_outputs and str2bool(config["execution"]["remove_unnecessary_outputs"]):
        outputs_to_keep = needed_outputs
    # build a list of needed files
    output_files = []
    outputdict = outputs.trait_get()
    for output in outputs_to_keep:
        output_files.extend(walk_outputs(outputdict[output]))
    needed_files = [path for path, type in output_files if type == "f"]
    if str2bool(config["execution"]["keep_inputs"]):
        input_files = []
        inputdict = inputs.trait_get()
        input_files.extend(walk_outputs(inputdict))
        needed_files += [path for path, type in input_files if type == "f"]
    for extra in [
        "_0x*.json",
        "provenance.*",
        "pyscript*.m",
        "pyjobs*.mat",
        "command.txt",
        "result*.pklz",
        "_inputs.pklz",
        "_node.pklz",
        ".proc-*",
    ]:
        needed_files.extend(glob(os.path.join(cwd, extra)))
    if files2keep:
        needed_files.extend(ensure_list(files2keep))
    needed_dirs = [path for path, type in output_files if type == "d"]
    if dirs2keep:
        needed_dirs.extend(ensure_list(dirs2keep))
    for extra in ["_nipype", "_report"]:
        needed_dirs.extend(glob(os.path.join(cwd, extra)))
    temp = []
    for filename in needed_files:
        temp.extend(get_related_files(filename))
    needed_files = temp
    logger.debug("Needed files: %s", ";".join(needed_files))
    logger.debug("Needed dirs: %s", ";".join(needed_dirs))
    if str2bool(config["execution"]["remove_unnecessary_outputs"]):
        files2remove = [
            f
            for f in walk_files(cwd)
            if f not in needed_files and not f.startswith(tuple(needed_dirs))
        ]
    elif not str2bool(config["execution"]["keep_inputs"]):
        input_files = {
            path for path, type in walk_outputs(inputs.trait_get()) if type == "f"
        }
        files2remove = [
            f for f in walk_files(cwd) if f in input_files and f not in needed_files
        ]
    else:
        files2remove = []
    logger.debug("Removing files: %s", ";".join(files2remove))
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
    >>> d2 = merge_dict(d1, d1)
    >>> len(d2)
    3
    >>> [d2[k] for k in ['a', 'b', 'c']]
    [1, 2, 3]

    >>> d3 = merge_dict(d1, d1, lambda x,y: x+y)
    >>> len(d3)
    3
    >>> [d3[k] for k in ['a', 'b', 'c']]
    [2, 4, 6]

    """
    if not isinstance(d1, dict):
        return merge(d1, d2)
    result = dict(d1)
    if d2 is None:
        return result
    for k, v in list(d2.items()):
        if k in result:
            result[k] = merge_dict(result[k], v, merge=merge)
        else:
            result[k] = v
    return result


def merge_bundles(g1, g2):
    for rec in g2.get_records():
        g1._add_record(rec)
    return g1


def write_workflow_prov(graph, filename=None, format="all"):
    """Write W3C PROV Model JSON file"""
    if not filename:
        filename = os.path.join(os.getcwd(), "workflow_provenance")

    ps = ProvStore()

    processes = []
    nodes = graph.nodes()
    for node in nodes:
        result = node.result
        classname = node.interface.__class__.__name__
        _, hashval, _, _ = node.hash_exists()
        attrs = {
            pm.PROV["type"]: nipype_ns[classname],
            pm.PROV["label"]: f"{classname}_{node.name}",
            nipype_ns["hashval"]: hashval,
        }
        process = ps.g.activity(get_id(), None, None, attrs)
        if isinstance(result.runtime, list):
            process.add_attributes({pm.PROV["type"]: nipype_ns["MapNode"]})
            # add info about sub processes
            for idx, runtime in enumerate(result.runtime):
                subresult = InterfaceResult(result.interface[idx], runtime, outputs={})
                if result.inputs:
                    if idx < len(result.inputs):
                        subresult.inputs = result.inputs[idx]
                if result.outputs:
                    for key, _ in list(result.outputs.items()):
                        values = getattr(result.outputs, key)
                        if isdefined(values) and idx < len(values):
                            subresult.outputs[key] = values[idx]
                sub_doc = ProvStore().add_results(subresult)
                sub_bundle = pm.ProvBundle(sub_doc.get_records(), identifier=get_id())
                ps.g.add_bundle(sub_bundle)
                bundle_entity = ps.g.entity(
                    sub_bundle.identifier,
                    other_attributes={"prov:type": pm.PROV_BUNDLE},
                )
                ps.g.wasGeneratedBy(bundle_entity, process)
        else:
            process.add_attributes({pm.PROV["type"]: nipype_ns["Node"]})
            if result.provenance:
                prov_doc = result.provenance
            else:
                prov_doc = ProvStore().add_results(result)
            result_bundle = pm.ProvBundle(prov_doc.get_records(), identifier=get_id())
            ps.g.add_bundle(result_bundle)
            bundle_entity = ps.g.entity(
                result_bundle.identifier, other_attributes={"prov:type": pm.PROV_BUNDLE}
            )
            ps.g.wasGeneratedBy(bundle_entity, process)
        processes.append(process)

    # add dependencies (edges)
    # Process->Process
    for idx, edgeinfo in enumerate(graph.in_edges()):
        ps.g.wasStartedBy(
            processes[list(nodes).index(edgeinfo[1])],
            starter=processes[list(nodes).index(edgeinfo[0])],
        )

    # write provenance
    ps.write_provenance(filename, format=format)
    return ps.g


def write_workflow_resources(graph, filename=None, append=None):
    """
    Generate a JSON file with profiling traces that can be loaded
    in a pandas DataFrame or processed with JavaScript like D3.js
    """
    import simplejson as json

    # Overwrite filename if nipype config is set
    filename = config.get("monitoring", "summary_file", filename)

    # If filename still does not make sense, store in $PWD
    if not filename:
        filename = os.path.join(os.getcwd(), "resource_monitor.json")

    if append is None:
        append = str2bool(config.get("monitoring", "summary_append", "true"))

    big_dict = {
        "time": [],
        "name": [],
        "interface": [],
        "rss_GiB": [],
        "vms_GiB": [],
        "cpus": [],
        "mapnode": [],
        "params": [],
    }

    # If file exists, just append new profile information
    # If we append different runs, then we will see different
    # "bursts" of timestamps corresponding to those executions.
    if append and os.path.isfile(filename):
        with open(filename) as rsf:
            big_dict = json.load(rsf)

    for _, node in enumerate(graph.nodes()):
        nodename = node.fullname
        classname = node.interface.__class__.__name__

        params = ""
        if node.parameterization:
            params = "_".join([f"{p}" for p in node.parameterization])

        try:
            rt_list = node.result.runtime
        except Exception:
            logger.warning(
                "Could not access runtime info for node %s (%s interface)",
                nodename,
                classname,
            )
            continue

        if not isinstance(rt_list, list):
            rt_list = [rt_list]

        for subidx, runtime in enumerate(rt_list):
            try:
                nsamples = len(runtime.prof_dict["time"])
            except AttributeError:
                logger.warning(
                    'Could not retrieve profiling information for node "%s" '
                    "(mapflow %d/%d).",
                    nodename,
                    subidx + 1,
                    len(rt_list),
                )
                continue

            for key in ["time", "cpus", "rss_GiB", "vms_GiB"]:
                big_dict[key] += runtime.prof_dict[key]

            big_dict["interface"] += [classname] * nsamples
            big_dict["name"] += [nodename] * nsamples
            big_dict["mapnode"] += [subidx] * nsamples
            big_dict["params"] += [params] * nsamples

    with open(filename, "w") as rsf:
        json.dump(big_dict, rsf, ensure_ascii=False)

    return filename


def topological_sort(graph, depth_first=False):
    """Returns a depth first sorted order if depth_first is True"""
    import networkx as nx

    nodesort = list(nx.topological_sort(graph))
    if not depth_first:
        return nodesort, None
    logger.debug("Performing depth first search")
    nodes = []
    groups = []
    G = nx.Graph()
    G.add_nodes_from(graph.nodes())
    G.add_edges_from(graph.edges())
    components = nx.connected_components(G)
    for group, desc in enumerate(components, start=1):
        indices = [nodesort.index(node) for node in desc]
        nodes.extend(
            np.array(nodesort)[np.array(indices)[np.argsort(indices)]].tolist()
        )
        for node in desc:
            nodesort.remove(node)
        groups.extend([group] * len(desc))
    return nodes, groups
