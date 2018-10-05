#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Workflow` class provides core functionality for batch processing.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, bytes, open

import os, glob
import os.path as op
import sys
from datetime import datetime
from copy import copy, deepcopy
import pickle
import shutil

import numpy as np
import networkx as nx
import collections, itertools

from ... import config, logging
from ...exceptions import NodeError, WorkflowError, MappingError, JoinError
from ...utils.misc import str2bool
from ...utils.functions import (getsource, create_function_from_source)

from ...interfaces.base import (traits, TraitedSpec, TraitDictObject,
                                TraitListObject)
from ...utils.filemanip import save_json, makedirs, to_str
from .utils import (generate_expanded_graph, export_graph, write_workflow_prov,
                    write_workflow_resources, format_dot, topological_sort,
                    get_print_name, merge_dict, format_node)

from .base import EngineBase
from .nodes import MapNode, Node
from . import state
from . import auxiliary as aux
from . import submitter as sub

import pdb

# Py2 compat: http://python-future.org/compatible_idioms.html#collections-counter-and-ordereddict
from future import standard_library
standard_library.install_aliases()

logger = logging.getLogger('nipype.workflow')


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
        super(Workflow, self).__init__(name, base_dir)
        self._graph = nx.DiGraph()

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
             and func will be evaluated and the results sent ot targetinput

             currently func needs to define all its needed imports within the
             function as we use the inspect module to get at the source code
             and execute it remotely
        """
        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError('connect() takes either 4 arguments, or 1 list of'
                            ' connection tuples (%d args given)' % len(args))

        disconnect = False
        if kwargs:
            disconnect = kwargs.get('disconnect', False)

        if disconnect:
            self.disconnect(connection_list)
            return

        newnodes = []
        for srcnode, destnode, _ in connection_list:
            if self in [srcnode, destnode]:
                msg = ('Workflow connect cannot contain itself as node:'
                       ' src[%s] dest[%s] workflow[%s]') % (srcnode, destnode,
                                                            self.name)

                raise IOError(msg)
            if (srcnode not in newnodes) and not self._has_node(srcnode):
                newnodes.append(srcnode)
            if (destnode not in newnodes) and not self._has_node(destnode):
                newnodes.append(destnode)
        if newnodes:
            self._check_nodes(newnodes)
            for node in newnodes:
                if node._hierarchy is None:
                    node._hierarchy = self.name
        not_found = []
        connected_ports = {}
        for srcnode, destnode, connects in connection_list:
            if destnode not in connected_ports:
                connected_ports[destnode] = []
            # check to see which ports of destnode are already
            # connected.
            if not disconnect and (destnode in self._graph.nodes()):
                for edge in self._graph.in_edges(destnode):
                    data = self._graph.get_edge_data(*edge)
                    for sourceinfo, destname in data['connect']:
                        if destname not in connected_ports[destnode]:
                            connected_ports[destnode] += [destname]
            for source, dest in connects:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if dest in connected_ports[destnode]:
                    raise Exception("""\
Trying to connect %s:%s to %s:%s but input '%s' of node '%s' is already
connected.
""" % (srcnode, source, destnode, dest, dest, destnode))
                if not (hasattr(destnode, '_interface') and
                        ('.io' in str(destnode._interface.__class__) or any([
                            '.io' in str(val)
                            for val in destnode._interface.__class__.__bases__
                        ]))):
                    if not destnode._check_inputs(dest):
                        not_found.append(['in', destnode.name, dest])
                if not (hasattr(srcnode, '_interface') and
                        ('.io' in str(srcnode._interface.__class__) or any([
                            '.io' in str(val)
                            for val in srcnode._interface.__class__.__bases__
                        ]))):
                    if isinstance(source, tuple):
                        # handles the case that source is specified
                        # with a function
                        sourcename = source[0]
                    elif isinstance(source, (str, bytes)):
                        sourcename = source
                    else:
                        raise Exception(
                            ('Unknown source specification in '
                             'connection from output of %s') % srcnode.name)
                    if sourcename and not srcnode._check_outputs(sourcename):
                        not_found.append(['out', srcnode.name, sourcename])
                connected_ports[destnode] += [dest]
        infostr = []
        for info in not_found:
            infostr += [
                "Module %s has no %sput called %s\n" % (info[1], info[0],
                                                        info[2])
            ]
        if not_found:
            raise Exception(
                '\n'.join(['Some connections were not found'] + infostr))

        # turn functions into strings
        for srcnode, destnode, connects in connection_list:
            for idx, (src, dest) in enumerate(connects):
                if isinstance(src,
                              tuple) and not isinstance(src[1], (str, bytes)):
                    function_source = getsource(src[1])
                    connects[idx] = ((src[0], function_source, src[2:]), dest)

        # add connections
        for srcnode, destnode, connects in connection_list:
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            if edge_data:
                logger.debug('(%s, %s): Edge data exists: %s', srcnode,
                             destnode, to_str(edge_data))
                for data in connects:
                    if data not in edge_data['connect']:
                        edge_data['connect'].append(data)
                    if disconnect:
                        logger.debug('Removing connection: %s', to_str(data))
                        edge_data['connect'].remove(data)
                if edge_data['connect']:
                    self._graph.add_edges_from([(srcnode, destnode,
                                                 edge_data)])
                else:
                    # pass
                    logger.debug('Removing connection: %s->%s', srcnode,
                                 destnode)
                    self._graph.remove_edges_from([(srcnode, destnode)])
            elif not disconnect:
                logger.debug('(%s, %s): No edge data', srcnode, destnode)
                self._graph.add_edges_from([(srcnode, destnode, {
                    'connect': connects
                })])
            edge_data = self._graph.get_edge_data(srcnode, destnode)
            logger.debug('(%s, %s): new edge data: %s', srcnode, destnode,
                         to_str(edge_data))

    def disconnect(self, *args):
        """Disconnect nodes
        See the docstring for connect for format.
        """
        if len(args) == 1:
            connection_list = args[0]
        elif len(args) == 4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise TypeError('disconnect() takes either 4 arguments, or 1 list '
                            'of connection tuples (%d args given)' % len(args))

        for srcnode, dstnode, conn in connection_list:
            logger.debug('disconnect(): %s->%s %s', srcnode, dstnode,
                         to_str(conn))
            if self in [srcnode, dstnode]:
                raise IOError(
                    'Workflow connect cannot contain itself as node: src[%s] '
                    'dest[%s] workflow[%s]') % (srcnode, dstnode, self.name)

            # If node is not in the graph, not connected
            if not self._has_node(srcnode) or not self._has_node(dstnode):
                continue

            edge_data = self._graph.get_edge_data(srcnode, dstnode, {
                'connect': []
            })
            ed_conns = [(c[0], c[1]) for c in edge_data['connect']]

            remove = []
            for edge in conn:
                if edge in ed_conns:
                    # idx = ed_conns.index(edge)
                    remove.append((edge[0], edge[1]))

            logger.debug('disconnect(): remove list %s', to_str(remove))
            for el in remove:
                edge_data['connect'].remove(el)
                logger.debug('disconnect(): removed connection %s', to_str(el))

            if not edge_data['connect']:
                self._graph.remove_edge(srcnode, dstnode)
            else:
                self._graph.add_edges_from([(srcnode, dstnode, edge_data)])

    def add_nodes(self, nodes):
        """ Add nodes to a workflow

        Parameters
        ----------
        nodes : list
            A list of EngineBase-based objects
        """
        newnodes = []
        all_nodes = self._get_all_nodes()
        for node in nodes:
            if self._has_node(node):
                raise IOError('Node %s already exists in the workflow' % node)
            if isinstance(node, Workflow):
                for subnode in node._get_all_nodes():
                    if subnode in all_nodes:
                        raise IOError(('Subnode %s of node %s already exists '
                                       'in the workflow') % (subnode, node))
            newnodes.append(node)
        if not newnodes:
            logger.debug('no new nodes to add')
            return
        for node in newnodes:
            if not issubclass(node.__class__, EngineBase):
                raise Exception('Node %s must be a subclass of EngineBase',
                                node)
        self._check_nodes(newnodes)
        for node in newnodes:
            if node._hierarchy is None:
                node._hierarchy = self.name
        self._graph.add_nodes_from(newnodes)

    def remove_nodes(self, nodes):
        """ Remove nodes from a workflow

        Parameters
        ----------
        nodes : list
            A list of EngineBase-based objects
        """
        self._graph.remove_nodes_from(nodes)

    # Input-Output access
    @property
    def inputs(self):
        return self._get_inputs()

    @property
    def outputs(self):
        return self._get_outputs()

    def get_node(self, name):
        """Return an internal node by name
        """
        nodenames = name.split('.')
        nodename = nodenames[0]
        outnode = [
            node for node in self._graph.nodes()
            if str(node).endswith('.' + nodename)
        ]
        if outnode:
            outnode = outnode[0]
            if nodenames[1:] and issubclass(outnode.__class__, Workflow):
                outnode = outnode.get_node('.'.join(nodenames[1:]))
        else:
            outnode = None
        return outnode

    def list_node_names(self):
        """List names of all nodes in a workflow
        """
        outlist = []
        for node in nx.topological_sort(self._graph):
            if isinstance(node, Workflow):
                outlist.extend([
                    '.'.join((node.name, nodename))
                    for nodename in node.list_node_names()
                ])
            else:
                outlist.append(node.name)
        return sorted(outlist)

    def write_graph(self,
                    dotfilename='graph.dot',
                    graph2use='hierarchical',
                    format="png",
                    simple_form=True):
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
        graphtypes = ['orig', 'flat', 'hierarchical', 'exec', 'colored']
        if graph2use not in graphtypes:
            raise ValueError('Unknown graph2use keyword. Must be one of: ' +
                             str(graphtypes))
        base_dir, dotfilename = op.split(dotfilename)
        if base_dir == '':
            if self.base_dir:
                base_dir = self.base_dir
                if self.name:
                    base_dir = op.join(base_dir, self.name)
            else:
                base_dir = os.getcwd()
        base_dir = makedirs(base_dir, exist_ok=True)
        if graph2use in ['hierarchical', 'colored']:
            if self.name[:1].isdigit():  # these graphs break if int
                raise ValueError('{} graph failed, workflow name cannot begin '
                                 'with a number'.format(graph2use))
            dotfilename = op.join(base_dir, dotfilename)
            self.write_hierarchical_dotfile(
                dotfilename=dotfilename,
                colored=graph2use == "colored",
                simple_form=simple_form)
            outfname = format_dot(dotfilename, format=format)
        else:
            graph = self._graph
            if graph2use in ['flat', 'exec']:
                graph = self._create_flat_graph()
            if graph2use == 'exec':
                graph = generate_expanded_graph(deepcopy(graph))
            outfname = export_graph(
                graph,
                base_dir,
                dotfilename=dotfilename,
                format=format,
                simple_form=simple_form)

        logger.info(
            'Generated workflow graph: %s (graph2use=%s, simple_form=%s).' %
            (outfname, graph2use, simple_form))
        return outfname

    def write_hierarchical_dotfile(self,
                                   dotfilename=None,
                                   colored=False,
                                   simple_form=True):
        dotlist = ['digraph %s{' % self.name]
        dotlist.append(
            self._get_dot(
                prefix='  ', colored=colored, simple_form=simple_form))
        dotlist.append('}')
        dotstr = '\n'.join(dotlist)
        if dotfilename:
            fp = open(dotfilename, 'wt')
            fp.writelines(dotstr)
            fp.close()
        else:
            logger.info(dotstr)

    def export(self,
               filename=None,
               prefix="output",
               format="python",
               include_config=False):
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
        formats = ["python"]
        if format not in formats:
            raise ValueError('format must be one of: %s' % '|'.join(formats))
        flatgraph = self._create_flat_graph()
        nodes = nx.topological_sort(flatgraph)

        all_lines = None
        lines = ['# Workflow']
        importlines = [
            'from nipype.pipeline.engine import Workflow, '
            'Node, MapNode'
        ]
        functions = {}
        if format == "python":
            connect_template = '%s.connect(%%s, %%s, %%s, "%%s")' % self.name
            connect_template2 = '%s.connect(%%s, "%%s", %%s, "%%s")' \
                                % self.name
            wfdef = '%s = Workflow("%s")' % (self.name, self.name)
            lines.append(wfdef)
            if include_config:
                lines.append('%s.config = %s' % (self.name, self.config))
            for idx, node in enumerate(nodes):
                nodename = node.fullname.replace('.', '_')
                # write nodes
                nodelines = format_node(
                    node, format='python', include_config=include_config)
                for line in nodelines:
                    if line.startswith('from'):
                        if line not in importlines:
                            importlines.append(line)
                    else:
                        lines.append(line)
                # write connections
                for u, _, d in flatgraph.in_edges(nbunch=node, data=True):
                    for cd in d['connect']:
                        if isinstance(cd[0], tuple):
                            args = list(cd[0])
                            if args[1] in functions:
                                funcname = functions[args[1]]
                            else:
                                func = create_function_from_source(args[1])
                                funcname = [
                                    name for name in func.__globals__
                                    if name != '__builtins__'
                                ][0]
                                functions[args[1]] = funcname
                            args[1] = funcname
                            args = tuple([arg for arg in args if arg])
                            line_args = (u.fullname.replace('.', '_'), args,
                                         nodename, cd[1])
                            line = connect_template % line_args
                            line = line.replace("'%s'" % funcname, funcname)
                            lines.append(line)
                        else:
                            line_args = (u.fullname.replace('.', '_'), cd[0],
                                         nodename, cd[1])
                            lines.append(connect_template2 % line_args)
            functionlines = ['# Functions']
            for function in functions:
                functionlines.append(pickle.loads(function).rstrip())
            all_lines = importlines + functionlines + lines

            if not filename:
                filename = '%s%s.py' % (prefix, self.name)
            with open(filename, 'wt') as fp:
                fp.writelines('\n'.join(all_lines))
        return all_lines

    def run(self, plugin=None, plugin_args=None, updatehash=False):
        """ Execute the workflow

        Parameters
        ----------

        plugin: plugin name or object
            Plugin to use for execution. You can create your own plugins for
            execution.
        plugin_args : dictionary containing arguments to be sent to plugin
            constructor. see individual plugin doc strings for details.
        """
        if plugin is None:
            plugin = config.get('execution', 'plugin')
        if not isinstance(plugin, (str, bytes)):
            runner = plugin
        else:
            name = '.'.join(__name__.split('.')[:-2] + ['plugins'])
            try:
                __import__(name)
            except ImportError:
                msg = 'Could not import plugin module: %s' % name
                logger.error(msg)
                raise ImportError(msg)
            else:
                plugin_mod = getattr(sys.modules[name], '%sPlugin' % plugin)
                runner = plugin_mod(plugin_args=plugin_args)
        flatgraph = self._create_flat_graph()
        self.config = merge_dict(deepcopy(config._sections), self.config)
        logger.info('Workflow %s settings: %s', self.name,
                    to_str(sorted(self.config)))
        self._set_needed_outputs(flatgraph)
        execgraph = generate_expanded_graph(deepcopy(flatgraph))
        for index, node in enumerate(execgraph.nodes()):
            node.config = merge_dict(deepcopy(self.config), node.config)
            node.base_dir = self.base_dir
            node.index = index
            if isinstance(node, MapNode):
                node.use_plugin = (plugin, plugin_args)
        self._configure_exec_nodes(execgraph)
        if str2bool(self.config['execution']['create_report']):
            self._write_report_info(self.base_dir, self.name, execgraph)
        runner.run(execgraph, updatehash=updatehash, config=self.config)
        datestr = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
        if str2bool(self.config['execution']['write_provenance']):
            prov_base = op.join(self.base_dir,
                                'workflow_provenance_%s' % datestr)
            logger.info('Provenance file prefix: %s' % prov_base)
            write_workflow_prov(execgraph, prov_base, format='all')

        if config.resource_monitor:
            base_dir = self.base_dir or os.getcwd()
            write_workflow_resources(
                execgraph,
                filename=op.join(base_dir, self.name, 'resource_monitor.json'))
        return execgraph

    # PRIVATE API AND FUNCTIONS

    def _write_report_info(self, workingdir, name, graph):
        if workingdir is None:
            workingdir = os.getcwd()
        report_dir = op.join(workingdir, name)
        makedirs(report_dir, exist_ok=True)
        shutil.copyfile(
            op.join(op.dirname(__file__), 'report_template.html'),
            op.join(report_dir, 'index.html'))
        shutil.copyfile(
            op.join(op.dirname(__file__), '..', '..', 'external', 'd3.js'),
            op.join(report_dir, 'd3.js'))
        nodes, groups = topological_sort(graph, depth_first=True)
        graph_file = op.join(report_dir, 'graph1.json')
        json_dict = {'nodes': [], 'links': [], 'groups': [], 'maxN': 0}
        for i, node in enumerate(nodes):
            report_file = "%s/_report/report.rst" % \
                          node.output_dir().replace(report_dir, '')
            result_file = "%s/result_%s.pklz" % \
                          (node.output_dir().replace(report_dir, ''),
                           node.name)
            json_dict['nodes'].append(
                dict(
                    name='%d_%s' % (i, node.name),
                    report=report_file,
                    result=result_file,
                    group=groups[i]))
        maxN = 0
        for gid in np.unique(groups):
            procs = [i for i, val in enumerate(groups) if val == gid]
            N = len(procs)
            if N > maxN:
                maxN = N
            json_dict['groups'].append(
                dict(procs=procs, total=N, name='Group_%05d' % gid))
        json_dict['maxN'] = maxN
        for u, v in graph.in_edges():
            json_dict['links'].append(
                dict(source=nodes.index(u), target=nodes.index(v), value=1))
        save_json(graph_file, json_dict)
        graph_file = op.join(report_dir, 'graph.json')
        # Avoid RuntimeWarning: divide by zero encountered in log10
        num_nodes = len(nodes)
        if num_nodes > 0:
            index_name = np.ceil(np.log10(num_nodes)).astype(int)
        else:
            index_name = 0
        template = '%%0%dd_' % index_name

        def getname(u, i):
            name_parts = u.fullname.split('.')
            # return '.'.join(name_parts[:-1] + [template % i + name_parts[-1]])
            return template % i + name_parts[-1]

        json_dict = []
        for i, node in enumerate(nodes):
            imports = []
            for u, v in graph.in_edges(nbunch=node):
                imports.append(getname(u, nodes.index(u)))
            json_dict.append(
                dict(
                    name=getname(node, i),
                    size=1,
                    group=groups[i],
                    imports=imports))
        save_json(graph_file, json_dict)

    def _set_needed_outputs(self, graph):
        """Initialize node with list of which outputs are needed."""
        rm_outputs = self.config['execution']['remove_unnecessary_outputs']
        if not str2bool(rm_outputs):
            return
        for node in graph.nodes():
            node.needed_outputs = []
            for edge in graph.out_edges(node):
                data = graph.get_edge_data(*edge)
                sourceinfo = [
                    v1[0] if isinstance(v1, tuple) else v1
                    for v1, v2 in data['connect']
                ]
                node.needed_outputs += [
                    v for v in sourceinfo if v not in node.needed_outputs
                ]
            if node.needed_outputs:
                node.needed_outputs = sorted(node.needed_outputs)

    def _configure_exec_nodes(self, graph):
        """Ensure that each node knows where to get inputs from
        """
        for node in graph.nodes():
            node.input_source = {}
            for edge in graph.in_edges(node):
                data = graph.get_edge_data(*edge)
                for sourceinfo, field in data['connect']:
                    node.input_source[field] = \
                        (op.join(edge[0].output_dir(),
                                 'result_%s.pklz' % edge[0].name),
                         sourceinfo)

    def _check_nodes(self, nodes):
        """Checks if any of the nodes are already in the graph

        """
        node_names = [node.name for node in self._graph.nodes()]
        node_lineage = [node._hierarchy for node in self._graph.nodes()]
        for node in nodes:
            if node.name in node_names:
                idx = node_names.index(node.name)
                try:
                    this_node_lineage = node_lineage[idx]
                except IndexError:
                    raise IOError(
                        'Duplicate node name "%s" found.' % node.name)
                else:
                    if this_node_lineage in [node._hierarchy, self.name]:
                        raise IOError(
                            'Duplicate node name "%s" found.' % node.name)
            else:
                node_names.append(node.name)

    def _has_attr(self, parameter, subtype='in'):
        """Checks if a parameter is available as an input or output
        """
        if subtype == 'in':
            subobject = self.inputs
        else:
            subobject = self.outputs
        attrlist = parameter.split('.')
        cur_out = subobject
        for attr in attrlist:
            if not hasattr(cur_out, attr):
                return False
            cur_out = getattr(cur_out, attr)
        return True

    def _get_parameter_node(self, parameter, subtype='in'):
        """Returns the underlying node corresponding to an input or
        output parameter
        """
        if subtype == 'in':
            subobject = self.inputs
        else:
            subobject = self.outputs
        attrlist = parameter.split('.')
        cur_out = subobject
        for attr in attrlist[:-1]:
            cur_out = getattr(cur_out, attr)
        return cur_out.traits()[attrlist[-1]].node

    def _check_outputs(self, parameter):
        return self._has_attr(parameter, subtype='out')

    def _check_inputs(self, parameter):
        return self._has_attr(parameter, subtype='in')

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
                    for cd in d['connect']:
                        taken_inputs.append(cd[1])
                unconnectedinputs = TraitedSpec()
                for key, trait in list(node.inputs.items()):
                    if key not in taken_inputs:
                        unconnectedinputs.add_trait(key,
                                                    traits.Trait(
                                                        trait, node=node))
                        value = getattr(node.inputs, key)
                        setattr(unconnectedinputs, key, value)
                setattr(inputdict, node.name, unconnectedinputs)
                getattr(inputdict, node.name).on_trait_change(self._set_input)
        return inputdict

    def _get_outputs(self):
        """Returns all possible output ports that are not already connected
        """
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
        """Trait callback function to update a node input
        """
        objekt.traits()[name].node.set_input(name, newvalue)

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, (str, bytes)):
            val = source.get_output(sourceinfo)
        elif isinstance(sourceinfo, tuple):
            if callable(sourceinfo[1]):
                val = sourceinfo[1](source.get_output(sourceinfo[0]),
                                    *sourceinfo[2:])
        newval = val
        if isinstance(val, TraitDictObject):
            newval = dict(val)
        if isinstance(val, TraitListObject):
            newval = val[:]
        logger.debug('setting node input: %s->%s', param, to_str(newval))
        node.set_input(param, deepcopy(newval))

    def _get_all_nodes(self):
        allnodes = []
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                allnodes.extend(node._get_all_nodes())
            else:
                allnodes.append(node)
        return allnodes

    def _has_node(self, wanted_node):
        for node in self._graph.nodes():
            if wanted_node == node:
                return True
            if isinstance(node, Workflow):
                if node._has_node(wanted_node):
                    return True
        return False

    def _create_flat_graph(self):
        """Make a simple DAG where no node is a workflow."""
        logger.debug('Creating flat graph for workflow: %s', self.name)
        workflowcopy = deepcopy(self)
        workflowcopy._generate_flatgraph()
        return workflowcopy._graph

    def _reset_hierarchy(self):
        """Reset the hierarchy on a graph
        """
        for node in self._graph.nodes():
            if isinstance(node, Workflow):
                node._reset_hierarchy()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = '.'.join((self.name,
                                                     innernode._hierarchy))
            else:
                node._hierarchy = self.name

    def _generate_flatgraph(self):
        """Generate a graph containing only Nodes or MapNodes
        """
        logger.debug('expanding workflow: %s', self)
        nodes2remove = []
        if not nx.is_directed_acyclic_graph(self._graph):
            raise Exception(('Workflow: %s is not a directed acyclic graph '
                             '(DAG)') % self.name)
        nodes = nx.topological_sort(self._graph)
        for node in nodes:
            logger.debug('processing node: %s', node)
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                # use in_edges instead of in_edges_iter to allow
                # disconnections to take place properly. otherwise, the
                # edge dict is modified.
                # dj: added list() for networkx ver.2
                for u, _, d in list(
                        self._graph.in_edges(nbunch=node, data=True)):
                    logger.debug('in: connections-> %s', to_str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("in: %s", to_str(cd))
                        dstnode = node._get_parameter_node(cd[1], subtype='in')
                        srcnode = u
                        srcout = cd[0]
                        dstin = cd[1].split('.')[-1]
                        logger.debug('in edges: %s %s %s %s', srcnode, srcout,
                                     dstnode, dstin)
                        self.disconnect(u, cd[0], node, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # do not use out_edges_iter for reasons stated in in_edges
                # dj: for ver 2 use list(out_edges)
                for _, v, d in list(
                        self._graph.out_edges(nbunch=node, data=True)):
                    logger.debug('out: connections-> %s', to_str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("out: %s", to_str(cd))
                        dstnode = v
                        if isinstance(cd[0], tuple):
                            parameter = cd[0][0]
                        else:
                            parameter = cd[0]
                        srcnode = node._get_parameter_node(
                            parameter, subtype='out')
                        if isinstance(cd[0], tuple):
                            srcout = list(cd[0])
                            srcout[0] = parameter.split('.')[-1]
                            srcout = tuple(srcout)
                        else:
                            srcout = parameter.split('.')[-1]
                        dstin = cd[1]
                        logger.debug('out edges: %s %s %s %s', srcnode, srcout,
                                     dstnode, dstin)
                        self.disconnect(node, cd[0], v, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # expand the workflow node
                # logger.debug('expanding workflow: %s', node)
                node._generate_flatgraph()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = '.'.join((self.name,
                                                     innernode._hierarchy))
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
        if nodes2remove:
            self._graph.remove_nodes_from(nodes2remove)
        logger.debug('finished expanding workflow: %s', self)

    def _get_dot(self,
                 prefix=None,
                 hierarchy=None,
                 colored=False,
                 simple_form=True,
                 level=0):
        """Create a dot file with connection info
        """
        if prefix is None:
            prefix = '  '
        if hierarchy is None:
            hierarchy = []
        colorset = [
            '#FFFFC8',  # Y
            '#0000FF',
            '#B4B4FF',
            '#E6E6FF',  # B
            '#FF0000',
            '#FFB4B4',
            '#FFE6E6',  # R
            '#00A300',
            '#B4FFB4',
            '#E6FFE6',  # G
            '#0000FF',
            '#B4B4FF'
        ]  # loop B
        if level > len(colorset) - 2:
            level = 3  # Loop back to blue

        dotlist = ['%slabel="%s";' % (prefix, self.name)]
        for node in nx.topological_sort(self._graph):
            fullname = '.'.join(hierarchy + [node.fullname])
            nodename = fullname.replace('.', '_')
            if not isinstance(node, Workflow):
                node_class_name = get_print_name(node, simple_form=simple_form)
                if not simple_form:
                    node_class_name = '.'.join(node_class_name.split('.')[1:])
                if hasattr(node, 'iterables') and node.iterables:
                    dotlist.append(('%s[label="%s", shape=box3d,'
                                    'style=filled, color=black, colorscheme'
                                    '=greys7 fillcolor=2];') %
                                   (nodename, node_class_name))
                else:
                    if colored:
                        dotlist.append(
                            ('%s[label="%s", style=filled,'
                             ' fillcolor="%s"];') % (nodename, node_class_name,
                                                     colorset[level]))
                    else:
                        dotlist.append(('%s[label="%s"];') % (nodename,
                                                              node_class_name))

        for node in nx.topological_sort(self._graph):
            if isinstance(node, Workflow):
                fullname = '.'.join(hierarchy + [node.fullname])
                nodename = fullname.replace('.', '_')
                dotlist.append('subgraph cluster_%s {' % nodename)
                if colored:
                    dotlist.append(prefix + prefix + 'edge [color="%s"];' %
                                   (colorset[level + 1]))
                    dotlist.append(prefix + prefix + 'style=filled;')
                    dotlist.append(prefix + prefix + 'fillcolor="%s";' %
                                   (colorset[level + 2]))
                dotlist.append(
                    node._get_dot(
                        prefix=prefix + prefix,
                        hierarchy=hierarchy + [self.name],
                        colored=colored,
                        simple_form=simple_form,
                        level=level + 3))
                dotlist.append('}')
            else:
                for subnode in self._graph.successors(node):
                    if node._hierarchy != subnode._hierarchy:
                        continue
                    if not isinstance(subnode, Workflow):
                        nodefullname = '.'.join(hierarchy + [node.fullname])
                        subnodefullname = '.'.join(
                            hierarchy + [subnode.fullname])
                        nodename = nodefullname.replace('.', '_')
                        subnodename = subnodefullname.replace('.', '_')
                        for _ in self._graph.get_edge_data(node,
                                                           subnode)['connect']:
                            dotlist.append('%s -> %s;' % (nodename,
                                                          subnodename))
                        logger.debug('connection: %s', dotlist[-1])
        # add between workflow connections
        for u, v, d in self._graph.edges(data=True):
            uname = '.'.join(hierarchy + [u.fullname])
            vname = '.'.join(hierarchy + [v.fullname])
            for src, dest in d['connect']:
                uname1 = uname
                vname1 = vname
                if isinstance(src, tuple):
                    srcname = src[0]
                else:
                    srcname = src
                if '.' in srcname:
                    uname1 += '.' + '.'.join(srcname.split('.')[:-1])
                if '.' in dest and '@' not in dest:
                    if not isinstance(v, Workflow):
                        if 'datasink' not in \
                           str(v._interface.__class__).lower():
                            vname1 += '.' + '.'.join(dest.split('.')[:-1])
                    else:
                        vname1 += '.' + '.'.join(dest.split('.')[:-1])
                if uname1.split('.')[:-1] != vname1.split('.')[:-1]:
                    dotlist.append('%s -> %s;' % (uname1.replace('.', '_'),
                                                  vname1.replace('.', '_')))
                    logger.debug('cross connection: %s', dotlist[-1])
        return ('\n' + prefix).join(dotlist)

    def add(self, name, node_like):
        if is_function_interface(node_like):
            node = Node(node_like, name=name)
        elif is_node(node_like):
            node = node_like

        self.add_nodes([node])


class Map(Node):
    pass


class Join(Node):
    pass


class MapState(object):
    pass


# dj ??: should I use EngineBase?
class NewBase(object):
    def __init__(self, name, mapper=None, inputs=None, other_mappers=None, mem_gb=None,
                 cache_location=None, print_val=True, *args, **kwargs):
        self.name = name
        #dj TODO: I should think what is needed in the __init__ (I redefine some of rhe attributes anyway)
        if inputs:
            # adding name of the node to the input name
            self._inputs = dict(("{}.{}".format(self.name, key), value) for (key, value) in inputs.items())
            self._inputs = dict((key, np.array(val)) if type(val) is list else (key, val)
                                for (key, val) in self._inputs.items())
            self._state_inputs = self._inputs.copy()
        else:
            self._inputs = {}
            self._state_inputs = {}
        if mapper:
            # adding name of the node to the input name within the mapper
            mapper = aux.change_mapper(mapper, self.name)
        self._mapper = mapper
        # information about other nodes' mappers from workflow (in case the mapper from previous node is used)
        self._other_mappers = other_mappers
        # create state (takes care of mapper, connects inputs with axes, so we can ask for specifc element)
        self._state = state.State(mapper=self._mapper, node_name=self.name, other_mappers=self._other_mappers)
        self._output = {}
        self._result = {}
        # flag that says if the node/wf is ready to run (has all input)
        self.ready2run = True
        # needed outputs from other nodes if the node part of a wf
        self.needed_outputs = []
        # flag that says if node finished all jobs
        self._is_complete = False
        # flag that says if value of state input should be printed in output and directories (otherwise indices)
        self.print_val = print_val

        # TODO: don't use it yet
        self.mem_gb = mem_gb
        self.cache_location = cache_location


    # TBD
    def join(self, field):
        pass

    @property
    def state(self):
        return self._state

    @property
    def mapper(self):
        return self._mapper

    @mapper.setter
    def mapper(self, mapper):
        self._mapper = mapper
        # updating state
        self._state = state.State(mapper=self._mapper, node_name=self.name, other_mappers=self._other_mappers)

    @property
    def state_inputs(self):
        return self._state_inputs

    @state_inputs.setter
    def state_inputs(self, state_inputs):
        self._state_inputs.update(state_inputs)


    @property
    def output(self):
        return self._output

    @property
    def result(self):
        if not self._result:
            self._reading_results()
        return self._result


    def prepare_state_input(self):
        self._state.prepare_state_input(state_inputs=self.state_inputs)


    def map(self, mapper, inputs=None):
        if self._mapper:
            raise Exception("mapper is already set")
        else:
            self._mapper = aux.change_mapper(mapper, self.name)

        if inputs:
            inputs = dict(("{}.{}".format(self.name, key), value) for (key, value) in inputs.items())
            inputs = dict((key, np.array(val)) if type(val) is list else (key, val)
                          for (key, val) in inputs.items())
            self._inputs.update(inputs)
            self._state_inputs.update(inputs)
        if mapper:
            # updating state if we have a new mapper
            self._state = state.State(mapper=self._mapper, node_name=self.name, other_mappers=self._other_mappers)


    def join(self, field, node=None):
        # TBD
        pass


    def checking_input_el(self, ind):
        """checking if all inputs are available (for specific state element)"""
        try:
            self._collecting_input_el(ind)
            return True
        except: #TODO specify
            return False


    # dj: this is not used for a single node
    def _collecting_input_el(self, ind):
        """collecting all inputs required to run the node (for specific state element)"""
        state_dict = self.state.state_values(ind)
        inputs_dict = {k: state_dict[k] for k in self._inputs.keys()}
        # reading extra inputs that come from previous nodes
        for (from_node, from_socket, to_socket) in self.needed_outputs:
            dir_nm_el_from = "_".join(["{}:{}".format(i, j) for i, j in list(state_dict.items())
                                       if i in list(from_node._state_inputs.keys())])
            if not from_node.mapper:
                dir_nm_el_from = ""
            file_from = os.path.join(from_node.workingdir, dir_nm_el_from, from_socket+".txt")
            with open(file_from) as f:
                inputs_dict["{}.{}".format(self.name, to_socket)] = eval(f.readline())
        return state_dict, inputs_dict


   # checking if all outputs are saved
    @property
    def is_complete(self):
        # once _is_complete os True, this should not change
        logger.debug('is_complete {}'.format(self._is_complete))
        if self._is_complete:
            return self._is_complete
        else:
            return self._check_all_results()


    def get_output(self):
        raise NotImplementedError

    def _check_all_results(self):
        raise NotImplementedError

    def _reading_results(self):
        raise NotImplementedError


    def _dict_tuple2list(self, container):
        if type(container) is dict:
            val_l = [val for (_, val) in container.items()]
        elif type(container) is tuple:
            val_l = [container]
        else:
            raise Exception("{} has to be dict or tuple".format(container))
        return val_l


class NewNode(NewBase):
    def __init__(self, name, interface, inputs=None, mapper=None, join_by=None,
                 workingdir=None, other_mappers=None, mem_gb=None, cache_location=None,
                 output_names=None, print_val=True, *args, **kwargs):
        super(NewNode, self).__init__(name=name, mapper=mapper, inputs=inputs,
                                      other_mappers=other_mappers, mem_gb=mem_gb,
                                      cache_location=cache_location, print_val=print_val,
                                      *args, **kwargs)

        # working directory for node, will be change if node is a part of a wf
        self.workingdir = workingdir
        self.interface = interface

        # TODO: fixing mess with outputs_names etc.
        if is_function_interface(self.interface):
            # adding node name to the interface's name mapping
            self.interface.input_map = dict((key, "{}.{}".format(self.name, value))
                                             for (key, value) in self.interface.input_map.items())
            # output names taken from interface output name
            self.output_names = self.interface._output_nm
        elif is_current_interface(self.interface):
            # TODO: assuming file_name, inter_key_out, node_key_out
            # used to define name of the output file of current interface
            self.output_names = output_names

        self.print_val = print_val




    # dj: not sure if I need it
    # def __deepcopy__(self, memo): # memo is a dict of id's to copies
    #     id_self = id(self)        # memoization avoids unnecesary recursion
    #     _copy = memo.get(id_self)
    #     if _copy is None:
    #         # changing names of inputs and input_map, so it doesnt contain node.name
    #         inputs_copy = dict((key[len(self.name)+1:], deepcopy(value))
    #                            for (key, value) in self.inputs.items())
    #         interface_copy = deepcopy(self.interface)
    #         interface_copy.input_map = dict((key, val[len(self.name)+1:])
    #                                         for (key, val) in interface_copy.input_map.items())
    #         _copy = type(self)(
    #             name=deepcopy(self.name), interface=interface_copy,
    #             inputs=inputs_copy, mapper=deepcopy(self.mapper),
    #             base_dir=deepcopy(self.nodedir), other_mappers=deepcopy(self._other_mappers))
    #         memo[id_self] = _copy
    #     return _copy


    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, inputs):
        self._inputs.update(inputs)


    def run_interface_el(self, i, ind):
        """ running interface one element generated from node_state."""
        logger.debug("Run interface el, name={}, i={}, ind={}".format(self.name, i, ind))
        state_dict, inputs_dict = self._collecting_input_el(ind)
        if not self.print_val:
            state_dict = self.state.state_ind(ind)
        dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(state_dict.items())])
        print("Run interface el, dict={}".format(state_dict))
        logger.debug("Run interface el, name={}, inputs_dict={}, state_dict={}".format(
                                                            self.name, inputs_dict, state_dict))
        if is_function_interface(self.interface):
            res = self.interface.run(inputs_dict)
            output = self.interface.output
            print("Run fun interface el, output={}".format(output))
            logger.debug("Run fun interface el, output={}".format(output))
            self._writting_results_tmp(state_dict, dir_nm_el, output)
        elif is_current_interface(self.interface):
            set_nm = {}
            for out_nm in self.output_names:
                if len(out_nm) == 2:
                    out_nm = (out_nm[0], out_nm[1], out_nm[1])
                if out_nm[2] not in self._output.keys():
                    self._output[out_nm[2]] = {}
                set_nm[out_nm[1]] = out_nm[0]
            if not self.mapper:
                dir_nm_el = ""
            res = self.interface.run(inputs=inputs_dict, base_dir=os.path.join(os.getcwd(), self.workingdir),
                                     set_out_nm=set_nm, dir_nm_el=dir_nm_el)

        # TODO when join
        #if self._joinByKey:
        #    dir_join = "join_" + "_".join(["{}.{}".format(i, j) for i, j in list(state_dict.items()) if i not in self._joinByKey])
        #elif self._join:
        #    dir_join = "join_"
        #if self._joinByKey or self._join:
        #    os.makedirs(os.path.join(self.nodedir, dir_join), exist_ok=True)
        #    dir_nm_el = os.path.join(dir_join, dir_nm_el)
        return res


    def _writting_results_tmp(self, state_dict, dir_nm_el, output):
        """temporary method to write the results in the files (this is usually part of a interface)"""
        if not self.mapper:
            dir_nm_el = ''
        os.makedirs(os.path.join(self.workingdir, dir_nm_el), exist_ok=True)
        for key_out, val_out in output.items():
            with open(os.path.join(self.workingdir, dir_nm_el, key_out+".txt"), "w") as fout:
                fout.write(str(val_out))


    def get_output(self):
        for key_out in self.output_names:
            if is_current_interface(self.interface):
                key_out, filename = key_out[-1], key_out[0]
            self._output[key_out] = {}
            for (i, ind) in enumerate(itertools.product(*self.state.all_elements)):
                if self.print_val:
                    state_dict = self.state.state_values(ind)
                else:
                    state_dict = self.state.state_ind(ind)
                dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(state_dict.items())])
                if self.mapper:
                    self._output[key_out][dir_nm_el] = (state_dict, os.path.join(self.workingdir, dir_nm_el, key_out + ".txt"))
                else:
                    if is_function_interface(self.interface):
                        self._output[key_out] = (state_dict, os.path.join(self.workingdir, key_out + ".txt"))
                    elif is_current_interface(self.interface):
                        self._output[key_out] = (state_dict, os.path.join(self.workingdir, self.interface.nn.name, filename))
        return self._output


    # dj: version without join
    def _check_all_results(self):
        """checking if all files that should be created are present"""
        for ind in itertools.product(*self.state.all_elements):
            if self.print_val:
                state_dict = self.state.state_values(ind)
            else:
                state_dict = self.state.state_ind(ind)
            dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(state_dict.items())])
            if not self.mapper:
                dir_nm_el = ""
            for key_out in self.output_names:
                if is_function_interface(self.interface):
                    if not os.path.isfile(os.path.join(self.workingdir, dir_nm_el, key_out+".txt")):
                        return False
                elif is_current_interface(self.interface):
                    if not os.path.isfile(os.path.join(os.getcwd(), self.workingdir,
                                                       dir_nm_el, self.interface.nn.name, key_out[0])):
                        return False
        self._is_complete = True
        return True


    def _reading_results(self):
        """temporary: reading results from output files (that is now just txt)
            should be probably just reading output for self.output_names
        """
        for key_out in self.output_names:
            self._result[key_out] = []
            #pdb.set_trace()
            if self._state_inputs:
                val_l = self._dict_tuple2list(self._output[key_out])
                for (st_dict, filename) in val_l:
                    with open(filename) as fout:
                        self._result[key_out].append((st_dict, eval(fout.readline())))
            else:
                # st_dict should be {}
                # not sure if this is used (not tested)
                (st_dict, filename) = self._output[key_out][None]
                with open(filename) as fout:
                    self._result[key_out].append(({}, eval(fout.readline())))

    # dj: removing temp. from NewNode class
    # def run(self, plugin="serial"):
    #     """preparing the node to run and run the interface"""
    #     self.prepare_state_input()
    #     submitter = sub.SubmitterNode(plugin, node=self)
    #     submitter.run_node()
    #     submitter.close()
    #     self.collecting_output()


class NewWorkflow(NewBase):
    def __init__(self, name, inputs=None, wf_output_names=None, mapper=None, #join_by=None,
                 nodes=None, workingdir=None, mem_gb=None, cache_location=None, print_val=True, *args, **kwargs):
        super(NewWorkflow, self).__init__(name=name, mapper=mapper, inputs=inputs, mem_gb=mem_gb,
                                          cache_location=cache_location, print_val=print_val, *args, **kwargs)

        self.graph = nx.DiGraph()
        # all nodes in the workflow (probably will be removed)
        self._nodes = []
        # saving all connection between nodes
        self.connected_var = {}
        # input that are expected by nodes to get from wf.inputs
        self.needed_inp_wf = []
        if nodes:
            self.add_nodes(nodes)
        for nn in self._nodes:
            self.connected_var[nn] = {}
        # key: name of a node, value: the node
        self._node_names = {}
        # key: name of a node, value: mapper of the node
        self._node_mappers = {}
        # dj: not sure if this should be different than base_dir
        self.workingdir = os.path.join(os.getcwd(), workingdir)
        # list of (nodename, output name in the name, output name in wf) or (nodename, output name in the name)
        # dj: using different name than for node, since this one it is defined by a user
        self.wf_output_names = wf_output_names

        # nodes that are created when the workflow has mapper (key: node name, value: list of nodes)
        self.inner_nodes = {}
        # in case of inner workflow this points to the main/parent workflow
        self.parent_wf = None
        # dj not sure what was the motivation, wf_klasses gives an empty list
        #mro = self.__class__.mro()
        #wf_klasses = mro[:mro.index(NewWorkflow)][::-1]
        #items = {}
        #for klass in wf_klasses:
        #    items.update(klass.__dict__)
        #for name, runnable in items.items():
        #    if name in ('__module__', '__doc__'):
        #        continue

        #    self.add(name, value)

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, inputs):
        self._inputs.update(dict(("{}.{}".format(self.name, key), value) for (key, value) in inputs.items()))


    @property
    def nodes(self):
        return self._nodes

    @property
    def graph_sorted(self):
        # TODO: should I always update the graph?
        return list(nx.topological_sort(self.graph))


    def map_node(self, mapper, node=None, inputs=None):
        """this is setting a mapper to the wf's nodes (not to the wf)"""
        if not node:
            node = self._last_added
        if node.mapper:
            raise WorkflowError("Cannot assign two mappings to the same input")
        node.map(mapper=mapper, inputs=inputs)
        self._node_mappers[node.name] = node.mapper


    def get_output(self):
        # not sure, if I should collecto output of all nodes or only the ones that are used in wf.output
        self.node_outputs = {}
        for nn in self.graph:
            if self.mapper:
                self.node_outputs[nn.name] = [ni.get_output() for ni in self.inner_nodes[nn.name]]
            else:
                self.node_outputs[nn.name] = nn.get_output()
        if self.wf_output_names:
            for out in self.wf_output_names:
                if len(out) == 2:
                    node_nm, out_nd_nm, out_wf_nm = out[0], out[1], out[1]
                elif len(out) == 3:
                    node_nm, out_nd_nm, out_wf_nm = out
                else:
                    raise Exception("wf_output_names should have 2 or 3 elements")
                if out_wf_nm not in self._output.keys():
                    if self.mapper:
                        self._output[out_wf_nm] = {}
                        for (i, ind) in enumerate(itertools.product(*self.state.all_elements)):
                            if self.print_val:
                                wf_inputs_dict = self.state.state_values(ind)
                                dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(wf_inputs_dict.items())])
                            else:
                                wf_ind_dict = self.state.state_ind(ind)
                                dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(wf_ind_dict.items())])
                            self._output[out_wf_nm][dir_nm_el] = self.node_outputs[node_nm][i][out_nd_nm]
                    else:
                        self._output[out_wf_nm] = self.node_outputs[node_nm][out_nd_nm]
                else:
                    raise Exception("the key {} is already used in workflow.result".format(out_wf_nm))
        return self._output


    # dj: version without join
    # TODO: might merge with the function from Node
    def _check_all_results(self):
        """checking if all files that should be created are present"""
        for nn in self.graph_sorted:
            if nn.name in self.inner_nodes.keys():
                if not all([ni.is_complete for ni in self.inner_nodes[nn.name]]):
                    return False
            else:
                if not nn.is_complete:
                    return False
        self._is_complete = True
        return True


    # TODO: should try to merge with the function from Node
    def _reading_results(self):
        """reading all results of the workflow
           using temporary Node._reading_results that reads txt files
        """
        if self.wf_output_names:
            for out in self.wf_output_names:
                key_out = out[2] if len(out)==3 else out[1]
                self._result[key_out] = []
                if self.mapper:
                    for (i, ind) in enumerate(itertools.product(*self.state.all_elements)):
                        if self.print_val:
                            wf_inputs_dict = self.state.state_values(ind)
                        else:
                            wf_inputs_dict = self.state.state_ind(ind)
                        dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(wf_inputs_dict.items())])
                        res_l= []
                        val_l = self._dict_tuple2list(self.output[key_out][dir_nm_el])
                        for val in val_l:
                            with open(val[1]) as fout:
                                logger.debug('Reading Results: file={}, st_dict={}'.format(val[1], val[0]))
                                res_l.append((val[0], eval(fout.readline())))
                        self._result[key_out].append((wf_inputs_dict, res_l))
                else:
                    val_l = self._dict_tuple2list(self.output[key_out])
                    for val in val_l:
                        #TODO: I think that val shouldn't be dict here...
                        # TMP solution
                        if type(val) is dict:
                            val = [v for k,v in val.items()][0]
                        with open(val[1]) as fout:
                            logger.debug('Reading Results: file={}, st_dict={}'.format(val[1], val[0]))
                            self._result[key_out].append((val[0], eval(fout.readline())))


    def add_nodes(self, nodes):
        """adding nodes without defining connections"""
        self.graph.add_nodes_from(nodes)
        for nn in nodes:
            self._nodes.append(nn)
            #self._inputs.update(nn.inputs)
            self.connected_var[nn] = {}
            self._node_names[nn.name] = nn
            self._node_mappers[nn.name] = nn.mapper


    def add(self, runnable, name=None, workingdir=None, inputs=None, output_nm=None, mapper=None,
            mem_gb=None, **kwargs):
        if is_function(runnable):
            if not output_nm:
                output_nm = ["out"]
            interface = aux.Function_Interface(function=runnable, output_nm=output_nm)
            if not name:
                raise Exception("you have to specify name for the node")
            if not workingdir:
                workingdir = name
            node = NewNode(interface=interface, workingdir=workingdir, name=name, inputs=inputs, mapper=mapper,
                           other_mappers=self._node_mappers, mem_gb=mem_gb)
        elif is_function_interface(runnable): # TODO: add current_dir
            if not name:
                raise Exception("you have to specify name for the node")
            if not workingdir:
                workingdir = name
            node = NewNode(interface=runnable, workingdir=workingdir, name=name, inputs=inputs, mapper=mapper,
                           other_mappers=self._node_mappers, mem_gb_node=mem_gb)
        elif is_node(runnable):
            node = runnable
        elif is_workflow(runnable):
            node = runnable
        else:
            raise ValueError("Unknown workflow element: {!r}".format(runnable))
        self.add_nodes([node])
        self._last_added = node

        # connecting inputs to other nodes outputs
        for (inp, source) in kwargs.items():
            try:
                from_node_nm, from_socket = source.split(".")
                self.connect(from_node_nm, from_socket, node.name, inp)
            # TODO not sure if i need it, just check if from_node_nm is not None??
            except(ValueError):
                self.connect_wf_input(source, node.name, inp)
        return self


    def connect(self, from_node_nm, from_socket, to_node_nm, to_socket):
        from_node = self._node_names[from_node_nm]
        to_node = self._node_names[to_node_nm]
        self.graph.add_edges_from([(from_node, to_node)])
        if not to_node in self.nodes:
            self.add_nodes(to_node)
        self.connected_var[to_node][to_socket] = (from_node, from_socket)
        # from_node.sending_output.append((from_socket, to_node, to_socket))
        logger.debug('connecting {} and {}'.format(from_node, to_node))


    def connect_wf_input(self, inp_wf, node_nm, inp_nd):
        self.needed_inp_wf.append((node_nm, inp_wf, inp_nd))


    def preparing(self, wf_inputs=None, wf_inputs_ind=None):
        """preparing nodes which are connected: setting the final mapper and state_inputs"""
        #pdb.set_trace()
        for node_nm, inp_wf, inp_nd in self.needed_inp_wf:
            node = self._node_names[node_nm]
            if "{}.{}".format(self.name, inp_wf) in wf_inputs:
                node.state_inputs.update({"{}.{}".format(node_nm, inp_nd): wf_inputs["{}.{}".format(self.name, inp_wf)]})
                node.inputs.update({"{}.{}".format(node_nm, inp_nd): wf_inputs["{}.{}".format(self.name, inp_wf)]})
            else:
                raise Exception("{}.{} not in the workflow inputs".format(self.name, inp_wf))
        for nn in self.graph_sorted:
            if self.print_val:
                dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(wf_inputs.items())])
            else:
                dir_nm_el = "_".join(["{}:{}".format(i, j) for i, j in list(wf_inputs_ind.items())])
            if not self.mapper:
                dir_nm_el = ""
            nn.workingdir = os.path.join(self.workingdir, dir_nm_el, nn.name)
            nn._is_complete = False # helps when mp is used
            try:
                for inp, (out_node, out_var) in self.connected_var[nn].items():
                    nn.ready2run = False #it has some history (doesnt have to be in the loop)
                    nn.state_inputs.update(out_node.state_inputs)
                    nn.needed_outputs.append((out_node, out_var, inp))
                    #if there is no mapper provided, i'm assuming that mapper is taken from the previous node
                    if (not nn.mapper or nn.mapper == out_node.mapper) and out_node.mapper:
                        nn.mapper = out_node.mapper
                    else:
                        pass
                    #TODO: implement inner mapper
            except(KeyError):
                # tmp: we don't care about nn that are not in self.connected_var
                pass

            nn.prepare_state_input()

    # removing temp. from NewWorkflow
    # def run(self, plugin="serial"):
    #     #self.preparing(wf_inputs=self.inputs) # moved to submitter
    #     self.prepare_state_input()
    #     logger.debug('the sorted graph is: {}'.format(self.graph_sorted))
    #     submitter = sub.SubmitterWorkflow(workflow=self, plugin=plugin)
    #     submitter.run_workflow()
    #     submitter.close()
    #     self.collecting_output()


def is_function(obj):
    return hasattr(obj, '__call__')

def is_function_interface(obj):
    return type(obj) is aux.Function_Interface

def is_current_interface(obj):
    return type(obj) is aux.CurrentInterface


def is_node(obj):
    return type(obj) is NewNode

def is_workflow(obj):
    return type(obj) is NewWorkflow
