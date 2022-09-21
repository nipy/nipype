#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Workflow` class provides core functionality for batch processing.
"""
import os
import os.path as op
import sys
from datetime import datetime
from copy import deepcopy
import pickle
import shutil

import numpy as np

from ... import config, logging
from ...utils.misc import str2bool
from ...utils.functions import getsource, create_function_from_source

from ...interfaces.base import traits, TraitedSpec, TraitDictObject, TraitListObject
from ...utils.filemanip import save_json
from .utils import (
    generate_expanded_graph,
    export_graph,
    write_workflow_prov,
    write_workflow_resources,
    format_dot,
    topological_sort,
    get_print_name,
    merge_dict,
    format_node,
)

from .base import EngineBase
from .nodes import MapNode

logger = logging.getLogger("nipype.workflow")


class Workflow(EngineBase):
    """Controls the setup and execution of a pipeline of processes."""

    def __init__(self, name, base_dir=None):
        """Create a workflow object.

        Parameters
        ----------
        name : alphanumeric string
            unique identifier for the workflow
        base_dir : string, optional
            path to workflow storage

        """
        import networkx as nx

        super(Workflow, self).__init__(name, base_dir)
        self._graph = nx.DiGraph()

        self._nodes_cache = set()
        self._nested_workflows_cache = set()

    # PUBLIC API
    def clone(self, name):
        """Clone a workflow

        .. note::

          Will reset attributes used for executing workflow. See
          _init_runtime_fields.

        Parameters
        ----------

        name: alphanumeric name
            unique name for the workflow

        """
        clone = super(Workflow, self).clone(name)
        clone._reset_hierarchy()
        return clone

    # Graph creation functions
    def connect(self, *args, **kwargs):
        """Connect nodes in the pipeline.

        This routine also checks if inputs and outputs are actually provided by
        the nodes that are being connected.

        Creates edges in the directed graph using the nodes and edges specified
        in the `connection_list`.  Uses the NetworkX method
        DiGraph.add_edges_from.

        Parameters
        ----------

        args : list or a set of four positional arguments

            Four positional arguments of the form::

              connect(source, sourceoutput, dest, destinput)

            source : nodewrapper node
            sourceoutput : string (must be in source.outputs)
            dest : nodewrapper node
            destinput : string (must be in dest.inputs)

            A list of 3-tuples of the following form::

             [(source, target,
                 [('sourceoutput/attribute', 'targetinput'),
                 ...]),
             ...]

            Or::

             [(source, target, [(('sourceoutput1', func, arg2, ...),
                                         'targetinput'), ...]),
             ...]
             sourceoutput1 will always be the first argument to func
             and func will be evaluated and the results sent to targetinput

             currently func needs to define all its needed imports within the
             function as we use the inspect module to get at the source code
             and execute it remotely
        """
        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError(
                "connect() takes either 4 arguments, or 1 list of"
                " connection tuples (%d args given)" % len(args)
            )

        disconnect = False
        if kwargs:
            disconnect = kwargs.get("disconnect", False)

        if disconnect:
            self.disconnect(connection_list)
            return

        newnodes = set()
        for srcnode, destnode, _ in connection_list:
            if self in [srcnode, destnode]:
                msg = (
                    "Workflow connect cannot contain itself as node:"
                    " src[%s] dest[%s] workflow[%s]"
                ) % (srcnode, destnode, self.name)

                raise IOError(msg)
            if (srcnode not in newnodes) and not self._has_node(srcnode):
                newnodes.add(srcnode)
            if (destnode not in newnodes) and not self._has_node(destnode):
                newnodes.add(destnode)
        if newnodes:
            self._check_nodes(newnodes)
            for node in newnodes:
                if node._hierarchy is None:
                    node._hierarchy = self.name
        not_found = []
        connected_ports = {}
        for srcnode, destnode, connects in connection_list:
            if destnode not in connected_ports:
                connected_ports[destnode] = set()
            # check to see which ports of destnode are already
            # connected.
            if not disconnect and (destnode in self._graph.nodes()):
                for edge in self._graph.in_edges(destnode):
                    data = self._graph.get_edge_data(*edge)
                    connected_ports[destnode].update(
                        destname for _, destname in data["connect"]
                    )
            for source, dest in connects:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if dest in connected_ports[destnode]:
                    raise Exception(
                        """\
Trying to connect %s:%s to %s:%s but input '%s' of node '%s' is already
connected.
"""
                        % (srcnode, source, destnode, dest, dest, destnode)
                    )
                if not (
                    hasattr(destnode, "_interface")
                    and (
                        ".io" in str(destnode._interface.__class__)
                        or any(
                            [
                                ".io" in str(val)
                                for val in destnode._interface.__class__.__bases__
                            ]
                        )
                    )
                ):
                    if not destnode._check_inputs(dest):
                        not_found.append(["in", destnode.name, dest])
                if not (
                    hasattr(srcnode, "_interface")
                    and (
                        ".io" in str(srcnode._interface.__class__)
                        or any(
                            [
                                ".io" in str(val)
                                for val in srcnode._interface.__class__.__bases__
                            ]
                        )
                    )
                ):
                    if isinstance(source, tuple):
                        # handles the case that source is specified
                        # with a function
                        sourcename = source[0]
                    elif isinstance(source, (str, bytes)):
                        sourcename = source
                    else:
                        raise Exception(
                            (
                                "Unknown source specification in "
                                "connection from output of %s"
                            )
                            % srcnode.name
                        )
                    if sourcename and not srcnode._check_outputs(sourcename):
                        not_found.append(["out", srcnode.name, sourcename])
                connected_ports[destnode].add(dest)
        infostr = []
        for info in not_found:
            infostr += [
                "Module %s has no %sput called %s\n" % (info[1], info[0], info[2])
            ]
        if not_found:
            raise Exception("\n".join(["Some connections were not found"] + infostr))

        # turn functions into strings
        for srcnode, destnode, connects in connection_list:
            for idx, (src, dest) in enumerate(connects):
                if isinstance(src, tuple) and not isinstance(src[1], (str, bytes)):
                    function_source = getsource(src[1])
                    connects[idx] = ((src[0], function_source, src[2:]), dest)

        # add connections
        for srcnode, destnode, connects in connection_list:
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            if edge_data:
                logger.debug(
                    "(%s, %s): Edge data exists: %s", srcnode, destnode, str(edge_data)
                )
                for data in connects:
                    if data not in edge_data["connect"]:
                        edge_data["connect"].append(data)
                    if disconnect:
                        logger.debug("Removing connection: %s", str(data))
                        edge_data["connect"].remove(data)
                if edge_data["connect"]:
                    self._graph.add_edges_from([(srcnode, destnode, edge_data)])
                else:
                    # pass
                    logger.debug("Removing connection: %s->%s", srcnode, destnode)
                    self._graph.remove_edges_from([(srcnode, destnode)])
            elif not disconnect:
                logger.debug("(%s, %s): No edge data", srcnode, destnode)
                self._graph.add_edges_from([(srcnode, destnode, {"connect": connects})])
            edge_data = self._graph.get_edge_data(srcnode, destnode)
            logger.debug(
                "(%s, %s): new edge data: %s", srcnode, destnode, str(edge_data)
            )

        if newnodes:
            self._update_node_cache()

    def disconnect(self, *args):
        """Disconnect nodes
        See the docstring for connect for format.
        """
        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError(
                "disconnect() takes either 4 arguments, or 1 list "
                "of connection tuples (%d args given)" % len(args)
            )

        for srcnode, dstnode, conn in connection_list:
            logger.debug("disconnect(): %s->%s %s", srcnode, dstnode, str(conn))
            if self in [srcnode, dstnode]:
                raise IOError(
                    "Workflow connect cannot contain itself as node: src[%s] "
                    "dest[%s] workflow[%s]"
                ) % (srcnode, dstnode, self.name)

            # If node is not in the graph, not connected
            if not self._has_node(srcnode) or not self._has_node(dstnode):
                continue

            edge_data = self._graph.get_edge_data(srcnode, dstnode, {"connect": []})
            ed_conns = [(c[0], c[1]) for c in edge_data["connect"]]

            remove = []
            for edge in conn:
                if edge in ed_conns:
                    # idx = ed_conns.index(edge)
                    remove.append((edge[0], edge[1]))

            logger.debug("disconnect(): remove list %s", str(remove))
            for el in remove:
                edge_data["connect"].remove(el)
                logger.debug("disconnect(): removed connection %s", str(el))

            if not edge_data["connect"]:
                self._graph.remove_edge(srcnode, dstnode)
            else:
                self._graph.add_edges_from([(srcnode, dstnode, edge_data)])

    def add_nodes(self, nodes):
        """Add nodes to a workflow

        Parameters
        ----------
        nodes : list
            A list of EngineBase-based objects
        """
        newnodes = []
        all_nodes = self._get_all_nodes()
        for node in nodes:
            if node in all_nodes:
                raise IOError("Node %s already exists in the workflow" % node)
            if isinstance(node, Workflow):
                for subnode in node._get_all_nodes():
                    if subnode in all_nodes:
                        raise IOError(
                            ("Subnode %s of node %s already exists " "in the workflow")
                            % (subnode, node)
                        )
            newnodes.append(node)
        if not newnodes:
            logger.debug("no new nodes to add")
            return
        for node in newnodes:
            if not issubclass(node.__class__, EngineBase):
                raise Exception("Node %s must be a subclass of EngineBase", node)
        self._check_nodes(newnodes)
        for node in newnodes:
            if node._hierarchy is None:
                node._hierarchy = self.name
        self._graph.add_nodes_from(newnodes)
        self._update_node_cache()

    def remove_nodes(self, nodes):
        """Remove nodes from a workflow

        Parameters
        ----------
        nodes : list
            A list of EngineBase-based objects
        """
        self._graph.remove_nodes_from(nodes)
        self._update_node_cache()

    # Input-Output access
    @property
    def inputs(self):
        return self._get_inputs()

    @property
    def outputs(self):
        return self._get_outputs()

    def get_node(self, name):
        """Return an internal node by name"""
        nodenames = name.split(".")
        nodename = nodenames[0]
        outnode = [
            node for node in self._graph.nodes() if str(node).endswith("." + nodename)
        ]
        if outnode:
            outnode = outnode[0]
            if nodenames[1:] and issubclass(outnode.__class__, Workflow):
                outnode = outnode.get_node(".".join(nodenames[1:]))
        else:
            outnode = None
        return outnode

    def list_node_names(self):
        """List names of all nodes in a workflow"""
        import networkx as nx

        outlist = []
        for node in nx.topological_sort(self._graph):
            if isinstance(node, Workflow):
                outlist.extend(
                    [
                        ".".join((node.name, nodename))
                        for nodename in node.list_node_names()
                    ]
                )
            else:
                outlist.append(node.name)
        return sorted(outlist)

    def write_graph(
        self,
        dotfilename="graph.dot",
        graph2use="hierarchical",
        format="png",
        simple_form=True,
    ):
        """Generates a graphviz dot file and a png file

        Parameters
        ----------

        graph2use: 'orig', 'hierarchical' (default), 'flat', 'exec', 'colored'
            orig - creates a top level graph without expanding internal
            workflow nodes;
            flat - expands workflow nodes recursively;
            hierarchical - expands workflow nodes recursively with a
            notion on hierarchy;
            colored - expands workflow nodes recursively with a
            notion on hierarchy in color;
            exec - expands workflows to depict iterables

        format: 'png', 'svg'

        simple_form: boolean (default: True)
            Determines if the node name used in the graph should be of the form
            'nodename (package)' when True or 'nodename.Class.package' when
            False.

        """
        graphtypes = ["orig", "flat", "hierarchical", "exec", "colored"]
        if graph2use not in graphtypes:
            raise ValueError(
                "Unknown graph2use keyword. Must be one of: " + str(graphtypes)
            )
        base_dir, dotfilename = op.split(dotfilename)
        if base_dir == "":
            if self.base_dir:
                base_dir = self.base_dir
                if self.name:
                    base_dir = op.join(base_dir, self.name)
            else:
                base_dir = os.getcwd()
        os.makedirs(base_dir, exist_ok=True)
        if graph2use in ["hierarchical", "colored"]:
            if self.name[:1].isdigit():  # these graphs break if int
                raise ValueError(
                    "{} graph failed, workflow name cannot begin "
                    "with a number".format(graph2use)
                )
            dotfilename = op.join(base_dir, dotfilename)
            self.write_hierarchical_dotfile(
                dotfilename=dotfilename,
                colored=graph2use == "colored",
                simple_form=simple_form,
            )
            outfname = format_dot(dotfilename, format=format)
        else:
            graph = self._graph
            if graph2use in ["flat", "exec"]:
                graph = self._create_flat_graph()
            if graph2use == "exec":
                graph = generate_expanded_graph(deepcopy(graph))
            outfname = export_graph(
                graph,
                base_dir,
                dotfilename=dotfilename,
                format=format,
                simple_form=simple_form,
            )

        logger.info(
            "Generated workflow graph: %s (graph2use=%s, simple_form=%s)."
            % (outfname, graph2use, simple_form)
        )
        return outfname

    def write_hierarchical_dotfile(
        self, dotfilename=None, colored=False, simple_form=True
    ):
        dotlist = ["digraph %s{" % self.name]
        dotlist.append(
            self._get_dot(prefix="  ", colored=colored, simple_form=simple_form)
        )
        dotlist.append("}")
        dotstr = "\n".join(dotlist)
        if dotfilename:
            fp = open(dotfilename, "wt")
            fp.writelines(dotstr)
            fp.close()
        else:
            logger.info(dotstr)

    def export(
        self, filename=None, prefix="output", format="python", include_config=False
    ):
        """Export object into a different format

        Parameters
        ----------
        filename: string
           file to save the code to; overrides prefix
        prefix: string
           prefix to use for output file
        format: string
           one of "python"
        include_config: boolean
           whether to include node and workflow config values

        """
        import networkx as nx

        formats = ["python"]
        if format not in formats:
            raise ValueError("format must be one of: %s" % "|".join(formats))
        flatgraph = self._create_flat_graph()
        nodes = nx.topological_sort(flatgraph)

        all_lines = None
        lines = ["# Workflow"]
        importlines = ["from nipype.pipeline.engine import Workflow, " "Node, MapNode"]
        functions = {}
        if format == "python":
            connect_template = '%s.connect(%%s, %%s, %%s, "%%s")' % self.name
            connect_template2 = '%s.connect(%%s, "%%s", %%s, "%%s")' % self.name
            wfdef = '%s = Workflow("%s")' % (self.name, self.name)
            lines.append(wfdef)
            if include_config:
                lines.append("%s.config = %s" % (self.name, self.config))
            for idx, node in enumerate(nodes):
                nodename = node.fullname.replace(".", "_")
                # write nodes
                nodelines = format_node(
                    node, format="python", include_config=include_config
                )
                for line in nodelines:
                    if line.startswith("from"):
                        if line not in importlines:
                            importlines.append(line)
                    else:
                        lines.append(line)
                # write connections
                for u, _, d in flatgraph.in_edges(nbunch=node, data=True):
                    for cd in d["connect"]:
                        if isinstance(cd[0], tuple):
                            args = list(cd[0])
                            if args[1] in functions:
                                funcname = functions[args[1]]
                            else:
                                func = create_function_from_source(args[1])
                                funcname = [
                                    name
                                    for name in func.__globals__
                                    if name != "__builtins__"
                                ][0]
                                functions[args[1]] = funcname
                            args[1] = funcname
                            args = tuple([arg for arg in args if arg])
                            line_args = (
                                u.fullname.replace(".", "_"),
                                args,
                                nodename,
                                cd[1],
                            )
                            line = connect_template % line_args
                            line = line.replace("'%s'" % funcname, funcname)
                            lines.append(line)
                        else:
                            line_args = (
                                u.fullname.replace(".", "_"),
                                cd[0],
                                nodename,
                                cd[1],
                            )
                            lines.append(connect_template2 % line_args)
            functionlines = ["# Functions"]
            for function in functions:
                functionlines.append(pickle.loads(function).rstrip())
            all_lines = importlines + functionlines + lines

            if not filename:
                filename = "%s%s.py" % (prefix, self.name)
            with open(filename, "wt") as fp:
                fp.writelines("\n".join(all_lines))
        return all_lines

    def run(self, plugin=None, plugin_args=None, updatehash=False):
        """Execute the workflow

        Parameters
        ----------

        plugin: plugin name or object
            Plugin to use for execution. You can create your own plugins for
            execution.
        plugin_args : dictionary containing arguments to be sent to plugin
            constructor. see individual plugin doc strings for details.
        """
        if plugin is None:
            plugin = config.get("execution", "plugin")
        if not isinstance(plugin, (str, bytes)):
            runner = plugin
            plugin = runner.__class__.__name__[: -len("Plugin")]
            plugin_args = runner.plugin_args
        else:
            name = ".".join(__name__.split(".")[:-2] + ["plugins"])
            try:
                __import__(name)
            except ImportError:
                msg = "Could not import plugin module: %s" % name
                logger.error(msg)
                raise ImportError(msg)
            else:
                plugin_mod = getattr(sys.modules[name], "%sPlugin" % plugin)
                runner = plugin_mod(plugin_args=plugin_args)
        flatgraph = self._create_flat_graph()
        self.config = merge_dict(deepcopy(config._sections), self.config)
        logger.info("Workflow %s settings: %s", self.name, str(sorted(self.config)))
        self._set_needed_outputs(flatgraph)
        execgraph = generate_expanded_graph(deepcopy(flatgraph))
        for index, node in enumerate(execgraph.nodes()):
            node.config = merge_dict(deepcopy(self.config), node.config)
            node.base_dir = self.base_dir
            node.index = index
            if isinstance(node, MapNode):
                node.use_plugin = (plugin, plugin_args)
        self._configure_exec_nodes(execgraph)
        if str2bool(self.config["execution"]["create_report"]):
            self._write_report_info(self.base_dir, self.name, execgraph)
        runner.run(execgraph, updatehash=updatehash, config=self.config)
        datestr = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        if str2bool(self.config["execution"]["write_provenance"]):
            prov_base = op.join(self.base_dir, "workflow_provenance_%s" % datestr)
            logger.info("Provenance file prefix: %s" % prov_base)
            write_workflow_prov(execgraph, prov_base, format="all")

        if config.resource_monitor:
            base_dir = self.base_dir or os.getcwd()
            write_workflow_resources(
                execgraph,
                filename=op.join(base_dir, self.name, "resource_monitor.json"),
            )
        return execgraph

    # PRIVATE API AND FUNCTIONS

    def _write_report_info(self, workingdir, name, graph):
        if workingdir is None:
            workingdir = os.getcwd()
        report_dir = op.join(workingdir, name)
        os.makedirs(report_dir, exist_ok=True)
        shutil.copyfile(
            op.join(op.dirname(__file__), "report_template.html"),
            op.join(report_dir, "index.html"),
        )
        shutil.copyfile(
            op.join(op.dirname(__file__), "..", "..", "external", "d3.js"),
            op.join(report_dir, "d3.js"),
        )
        nodes, groups = topological_sort(graph, depth_first=True)
        graph_file = op.join(report_dir, "graph1.json")
        json_dict = {"nodes": [], "links": [], "groups": [], "maxN": 0}
        for i, node in enumerate(nodes):
            report_file = "%s/_report/report.rst" % node.output_dir().replace(
                report_dir, ""
            )
            result_file = "%s/result_%s.pklz" % (
                node.output_dir().replace(report_dir, ""),
                node.name,
            )
            json_dict["nodes"].append(
                dict(
                    name="%d_%s" % (i, node.name),
                    report=report_file,
                    result=result_file,
                    group=groups[i],
                )
            )
        maxN = 0
        for gid in np.unique(groups):
            procs = [i for i, val in enumerate(groups) if val == gid]
            N = len(procs)
            if N > maxN:
                maxN = N
            json_dict["groups"].append(
                dict(procs=procs, total=N, name="Group_%05d" % gid)
            )
        json_dict["maxN"] = maxN
        for u, v in graph.in_edges():
            json_dict["links"].append(
                dict(source=nodes.index(u), target=nodes.index(v), value=1)
            )
        save_json(graph_file, json_dict)
        graph_file = op.join(report_dir, "graph.json")
        # Avoid RuntimeWarning: divide by zero encountered in log10
        num_nodes = len(nodes)
        if num_nodes > 0:
            index_name = np.ceil(np.log10(num_nodes)).astype(int)
        else:
            index_name = 0
        template = "%%0%dd_" % index_name

        def getname(u, i):
            name_parts = u.fullname.split(".")
            # return '.'.join(name_parts[:-1] + [template % i + name_parts[-1]])
            return template % i + name_parts[-1]

        json_dict = []
        for i, node in enumerate(nodes):
            imports = []
            for u, v in graph.in_edges(nbunch=node):
                imports.append(getname(u, nodes.index(u)))
            json_dict.append(
                dict(name=getname(node, i), size=1, group=groups[i], imports=imports)
            )
        save_json(graph_file, json_dict)

    def _set_needed_outputs(self, graph):
        """Initialize node with list of which outputs are needed."""
        rm_outputs = self.config["execution"]["remove_unnecessary_outputs"]
        if not str2bool(rm_outputs):
            return
        for node in graph.nodes():
            node.needed_outputs = []
            for edge in graph.out_edges(node):
                data = graph.get_edge_data(*edge)
                sourceinfo = [
                    v1[0] if isinstance(v1, tuple) else v1 for v1, v2 in data["connect"]
                ]
                node.needed_outputs += [
                    v for v in sourceinfo if v not in node.needed_outputs
                ]
            if node.needed_outputs:
                node.needed_outputs = sorted(node.needed_outputs)

    def _configure_exec_nodes(self, graph):
        """Ensure that each node knows where to get inputs from"""
        for node in graph.nodes():
            node.input_source = {}
            for edge in graph.in_edges(node):
                data = graph.get_edge_data(*edge)
                for sourceinfo, field in data["connect"]:
                    node.input_source[field] = (
                        op.join(edge[0].output_dir(), "result_%s.pklz" % edge[0].name),
                        sourceinfo,
                    )

    def _check_nodes(self, nodes):
        """Checks if any of the nodes are already in the graph"""
        node_names = [node.name for node in self._graph.nodes()]
        node_lineage = [node._hierarchy for node in self._graph.nodes()]
        for node in nodes:
            if node.name in node_names:
                idx = node_names.index(node.name)
                try:
                    this_node_lineage = node_lineage[idx]
                except IndexError:
                    raise IOError('Duplicate node name "%s" found.' % node.name)
                else:
                    if this_node_lineage in [node._hierarchy, self.name]:
                        raise IOError('Duplicate node name "%s" found.' % node.name)
            else:
                node_names.append(node.name)

    def _has_attr(self, parameter, subtype="in"):
        """Checks if a parameter is available as an input or output"""
        hierarchy = parameter.split(".")

        # Connecting to a workflow needs at least two values,
        # the name of the child node and the name of the input/output
        if len(hierarchy) < 2:
            return False

        attrname = hierarchy.pop()
        nodename = hierarchy.pop()

        def _check_is_already_connected(workflow, node, attrname):
            for _, _, d in workflow._graph.in_edges(nbunch=node, data=True):
                for cd in d["connect"]:
                    if attrname == cd[1]:
                        return False
            return True

        targetworkflow = self
        while hierarchy:
            workflowname = hierarchy.pop(0)
            workflow = None
            for node in targetworkflow._graph.nodes():
                if node.name == workflowname:
                    if isinstance(node, Workflow):
                        workflow = node
                        break
            if workflow is None:
                return False
            # Verify input does not already have an incoming connection
            # in the hierarchy of workflows
            if subtype == "in":
                hierattrname = ".".join(hierarchy + [nodename, attrname])
                if not _check_is_already_connected(
                    targetworkflow, workflow, hierattrname
                ):
                    return False
            targetworkflow = workflow

        targetnode = None
        for node in targetworkflow._graph.nodes():
            if node.name == nodename:
                if isinstance(node, Workflow):
                    return False
                else:
                    targetnode = node
                    break
        if targetnode is None:
            return False

        if subtype == "in":
            if not hasattr(targetnode.inputs, attrname):
                return False
        else:
            if not hasattr(targetnode.outputs, attrname):
                return False

        # Verify input does not already have an incoming connection
        # in the target workflow
        if subtype == "in":
            if not _check_is_already_connected(targetworkflow, targetnode, attrname):
                return False

        return True

    def _check_outputs(self, parameter):
        return self._has_attr(parameter, subtype="out")

    def _check_inputs(self, parameter):
        return self._has_attr(parameter, subtype="in")

    def _get_inputs(self):
        """Returns the inputs of a workflow

        This function does not return any input ports that are already
        connected
        """
        inputdict = TraitedSpec()
        for node in self._graph.nodes():
            inputdict.add_trait(node.name, traits.Instance(TraitedSpec))
            if isinstance(node, Workflow):
                setattr(inputdict, node.name, node.inputs)
            else:
                taken_inputs = []
                for _, _, d in self._graph.in_edges(nbunch=node, data=True):
                    for cd in d["connect"]:
                        taken_inputs.append(cd[1])
                unconnectedinputs = TraitedSpec()
                for key, trait in list(node.inputs.items()):
                    if key not in taken_inputs:
                        unconnectedinputs.add_trait(key, traits.Trait(trait, node=node))
                        value = getattr(node.inputs, key)
                        setattr(unconnectedinputs, key, value)
                setattr(inputdict, node.name, unconnectedinputs)
                getattr(inputdict, node.name).on_trait_change(self._set_input)
        return inputdict

    def _get_outputs(self):
        """Returns all possible output ports that are not already connected"""
        outputdict = TraitedSpec()
        for node in self._graph.nodes():
            outputdict.add_trait(node.name, traits.Instance(TraitedSpec))
            if isinstance(node, Workflow):
                setattr(outputdict, node.name, node.outputs)
            elif node.outputs:
                outputs = TraitedSpec()
                for key, _ in list(node.outputs.items()):
                    outputs.add_trait(key, traits.Any(node=node))
                    setattr(outputs, key, None)
                setattr(outputdict, node.name, outputs)
        return outputdict

    def _set_input(self, objekt, name, newvalue):
        """Trait callback function to update a node input"""
        objekt.traits()[name].node.set_input(name, newvalue)

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, (str, bytes)):
            val = source.get_output(sourceinfo)
        elif isinstance(sourceinfo, tuple):
            if callable(sourceinfo[1]):
                val = sourceinfo[1](source.get_output(sourceinfo[0]), *sourceinfo[2:])
        newval = val
        if isinstance(val, TraitDictObject):
            newval = dict(val)
        if isinstance(val, TraitListObject):
            newval = val[:]
        logger.debug("setting node input: %s->%s", param, str(newval))
        node.set_input(param, deepcopy(newval))

    def _get_all_nodes(self):
        allnodes = self._nodes_cache - self._nested_workflows_cache
        for node in self._nested_workflows_cache:
            allnodes |= node._get_all_nodes()
        return allnodes

    def _update_node_cache(self):
        nodes = set(self._graph)

        added_nodes = nodes.difference(self._nodes_cache)
        removed_nodes = self._nodes_cache.difference(nodes)

        self._nodes_cache = nodes
        self._nested_workflows_cache.difference_update(removed_nodes)

        for node in added_nodes:
            if isinstance(node, Workflow):
                self._nested_workflows_cache.add(node)

    def _has_node(self, wanted_node):
        return wanted_node in self._nodes_cache or any(
            wf._has_node(wanted_node) for wf in self._nested_workflows_cache
        )

    def _create_flat_graph(self):
        """Make a simple DAG where no node is a workflow."""
        logger.debug("Creating flat graph for workflow: %s", self.name)
        workflowcopy = deepcopy(self)
        workflowcopy._generate_flatgraph()
        return workflowcopy._graph

    def _reset_hierarchy(self):
        """Reset the hierarchy on a graph"""
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                node._reset_hierarchy()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = ".".join((self.name, innernode._hierarchy))
            else:
                node._hierarchy = self.name

    def _generate_flatgraph(self):
        """Generate a graph containing only Nodes or MapNodes"""
        import networkx as nx

        logger.debug("expanding workflow: %s", self)
        nodes2remove = []
        if not nx.is_directed_acyclic_graph(self._graph):
            raise Exception(
                ("Workflow: %s is not a directed acyclic graph " "(DAG)") % self.name
            )
        nodes = list(self._graph.nodes)
        for node in nodes:
            logger.debug("processing node: %s", node)
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                # use in_edges instead of in_edges_iter to allow
                # disconnections to take place properly. otherwise, the
                # edge dict is modified.
                # dj: added list() for networkx ver.2
                for u, _, d in list(self._graph.in_edges(nbunch=node, data=True)):
                    logger.debug("in: connections-> %s", str(d["connect"]))
                    for cd in deepcopy(d["connect"]):
                        logger.debug("in: %s", str(cd))
                        dstnode = node.get_node(cd[1].rsplit(".", 1)[0])
                        srcnode = u
                        srcout = cd[0]
                        dstin = cd[1].split(".")[-1]
                        logger.debug(
                            "in edges: %s %s %s %s", srcnode, srcout, dstnode, dstin
                        )
                        self.disconnect(u, cd[0], node, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # do not use out_edges_iter for reasons stated in in_edges
                # dj: for ver 2 use list(out_edges)
                for _, v, d in list(self._graph.out_edges(nbunch=node, data=True)):
                    logger.debug("out: connections-> %s", str(d["connect"]))
                    for cd in deepcopy(d["connect"]):
                        logger.debug("out: %s", str(cd))
                        dstnode = v
                        if isinstance(cd[0], tuple):
                            parameter = cd[0][0]
                        else:
                            parameter = cd[0]
                        srcnode = node.get_node(parameter.rsplit(".", 1)[0])
                        if isinstance(cd[0], tuple):
                            srcout = list(cd[0])
                            srcout[0] = parameter.split(".")[-1]
                            srcout = tuple(srcout)
                        else:
                            srcout = parameter.split(".")[-1]
                        dstin = cd[1]
                        logger.debug(
                            "out edges: %s %s %s %s", srcnode, srcout, dstnode, dstin
                        )
                        self.disconnect(node, cd[0], v, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # expand the workflow node
                # logger.debug('expanding workflow: %s', node)
                node._generate_flatgraph()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = ".".join((self.name, innernode._hierarchy))
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
        if nodes2remove:
            self._graph.remove_nodes_from(nodes2remove)
        logger.debug("finished expanding workflow: %s", self)

    def _get_dot(
        self, prefix=None, hierarchy=None, colored=False, simple_form=True, level=0
    ):
        """Create a dot file with connection info"""
        import networkx as nx

        if prefix is None:
            prefix = "  "
        if hierarchy is None:
            hierarchy = []
        colorset = [
            "#FFFFC8",  # Y
            "#0000FF",
            "#B4B4FF",
            "#E6E6FF",  # B
            "#FF0000",
            "#FFB4B4",
            "#FFE6E6",  # R
            "#00A300",
            "#B4FFB4",
            "#E6FFE6",  # G
            "#0000FF",
            "#B4B4FF",
        ]  # loop B
        if level > len(colorset) - 2:
            level = 3  # Loop back to blue

        dotlist = ['%slabel="%s";' % (prefix, self.name)]
        for node in nx.topological_sort(self._graph):
            fullname = ".".join(hierarchy + [node.fullname])
            nodename = fullname.replace(".", "_")
            if not isinstance(node, Workflow):
                node_class_name = get_print_name(node, simple_form=simple_form)
                if not simple_form:
                    node_class_name = ".".join(node_class_name.split(".")[1:])
                if hasattr(node, "iterables") and node.iterables:
                    dotlist.append(
                        (
                            '%s[label="%s", shape=box3d,'
                            "style=filled, color=black, colorscheme"
                            "=greys7 fillcolor=2];"
                        )
                        % (nodename, node_class_name)
                    )
                else:
                    if colored:
                        dotlist.append(
                            ('%s[label="%s", style=filled,' ' fillcolor="%s"];')
                            % (nodename, node_class_name, colorset[level])
                        )
                    else:
                        dotlist.append(
                            ('%s[label="%s"];') % (nodename, node_class_name)
                        )

        for node in nx.topological_sort(self._graph):
            if isinstance(node, Workflow):
                fullname = ".".join(hierarchy + [node.fullname])
                nodename = fullname.replace(".", "_")
                dotlist.append("subgraph cluster_%s {" % nodename)
                if colored:
                    dotlist.append(
                        prefix + prefix + 'edge [color="%s"];' % (colorset[level + 1])
                    )
                    dotlist.append(prefix + prefix + "style=filled;")
                    dotlist.append(
                        prefix + prefix + 'fillcolor="%s";' % (colorset[level + 2])
                    )
                dotlist.append(
                    node._get_dot(
                        prefix=prefix + prefix,
                        hierarchy=hierarchy + [self.name],
                        colored=colored,
                        simple_form=simple_form,
                        level=level + 3,
                    )
                )
                dotlist.append("}")
            else:
                for subnode in self._graph.successors(node):
                    if node._hierarchy != subnode._hierarchy:
                        continue
                    if not isinstance(subnode, Workflow):
                        nodefullname = ".".join(hierarchy + [node.fullname])
                        subnodefullname = ".".join(hierarchy + [subnode.fullname])
                        nodename = nodefullname.replace(".", "_")
                        subnodename = subnodefullname.replace(".", "_")
                        for _ in self._graph.get_edge_data(node, subnode)["connect"]:
                            dotlist.append("%s -> %s;" % (nodename, subnodename))
                        logger.debug("connection: %s", dotlist[-1])
        # add between workflow connections
        for u, v, d in self._graph.edges(data=True):
            uname = ".".join(hierarchy + [u.fullname])
            vname = ".".join(hierarchy + [v.fullname])
            for src, dest in d["connect"]:
                uname1 = uname
                vname1 = vname
                if isinstance(src, tuple):
                    srcname = src[0]
                else:
                    srcname = src
                if "." in srcname:
                    uname1 += "." + ".".join(srcname.split(".")[:-1])
                if "." in dest and "@" not in dest:
                    if not isinstance(v, Workflow):
                        if "datasink" not in str(v._interface.__class__).lower():
                            vname1 += "." + ".".join(dest.split(".")[:-1])
                    else:
                        vname1 += "." + ".".join(dest.split(".")[:-1])
                if uname1.split(".")[:-1] != vname1.split(".")[:-1]:
                    dotlist.append(
                        "%s -> %s;"
                        % (uname1.replace(".", "_"), vname1.replace(".", "_"))
                    )
                    logger.debug("cross connection: %s", dotlist[-1])
        return ("\n" + prefix).join(dotlist)
