# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Defines functionality for pipelined execution of interfaces

The `Pipeline` class provides core functionality for batch processing.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)

"""

from glob import glob
import gzip
from copy import deepcopy
import cPickle
import os
import shutil
from shutil import rmtree
from socket import gethostname
import sys
from tempfile import mkdtemp

import numpy as np

from nipype.utils.misc import package_check, str2bool
package_check('networkx', '1.3')
import networkx as nx

from nipype.interfaces.base import (traits, InputMultiPath, CommandLine,
                                    Undefined, TraitedSpec, DynamicTraitedSpec,
                                    Bunch, InterfaceResult, md5, Interface,
                                    TraitDictObject, TraitListObject, isdefined)
from nipype.utils.misc import getsource, create_function_from_source
from nipype.utils.filemanip import (save_json, FileNotFoundError,
                                    filename_to_list, list_to_filename,
                                    copyfiles, fnames_presuffix, loadpkl,
                                    split_filename, load_json, savepkl,
                                    write_rst_header, write_rst_dict,
                                    write_rst_list)

from nipype.pipeline.utils import (generate_expanded_graph, modify_paths,
                                   export_graph, make_output_dir,
                                   clean_working_directory, format_dot,
                                   get_print_name, merge_dict)
from nipype.utils.logger import (logger, config, logdebug_dict_differences)

class WorkflowBase(object):
    """ Define common attributes and functions for workflows and nodes
    """

    def __init__(self, name=None, base_dir=None,
                 overwrite=False, **kwargs):
        """ Initialize base parameters of a workflow or node

        Parameters
        ----------

        base_dir : directory
            base output directory (will be hashed before creations)
            default=None, which results in the use of mkdtemp
        overwrite : Boolean
            Whether to overwrite contents of output directory if it already
            exists. If directory exists and hash matches it
            assumes that process has been executed (default : False)
        name : string (mandatory)
            Name of this node. Name must be alphanumeric and not contain any
            special characters (e.g., '.', '@').
        """
        self.base_dir = base_dir
        self.overwrite = overwrite
        self.config = deepcopy(config._sections)
        if name is None:
            raise Exception("init requires a name for this %s" % self.__class__.__name__)
        if '.' in name:
            raise Exception('the name keyword-arg must not contain a period "."')
        self.name = name
        # for compatibility with node expansion using iterables
        self._id = self.name
        self._hierarchy = None

    @property
    def inputs(self):
        raise NotImplementedError

    @property
    def outputs(self):
        raise NotImplementedError

    @property
    def fullname(self):
        fullname = self.name
        if self._hierarchy:
            fullname = self._hierarchy + '.' + self.name
        return fullname            

    def clone(self, name):
        """Clone a workflowbase object

        Parameters
        ----------

        name : string (mandatory)
            A clone of node or workflow must have a new name
        """
        if (name is None) or (name == self.name):
            raise Exception('Cloning requires a new name')
        clone = deepcopy(self)
        clone.name = name
        clone._id = name
        clone._hierarchy = None
        return clone

    def _check_outputs(self, parameter):
        return hasattr(self.outputs, parameter)

    def _check_inputs(self, parameter):
        return hasattr(self.inputs, parameter)

    def __repr__(self):
        if self._hierarchy:
            return '.'.join((self._hierarchy, self._id))
        else:
            return self._id

    def save(self, filename=None):
        if filename is None:
            filename = 'temp.npz'
        np.savez(filename, object=self)

    def load(self, filename):
        return np.load(filename)

class Workflow(WorkflowBase):
    """Controls the setup and execution of a pipeline of processes
    """

    def __init__(self, **kwargs):
        super(Workflow, self).__init__(**kwargs)
        self._graph = nx.DiGraph()

    # PUBLIC API
    def clone(self, name):
        """Clone a workflow

        .. note::

        Will reset attributes used for executing workflow. See
        _init_runtime_fields. 

        Parameters
        ----------

        name: string (mandatory )
            every clone requires a new name
            
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
        if len(args)==1:
            connection_list = args[0]
        elif len(args)==4:
            connection_list = [(args[0], args[2], [(args[1], args[3])])]
        else:
            raise Exception('unknown set of parameters to connect function')
        if not kwargs:
            disconnect = False
        else:
            disconnect = kwargs['disconnect']
        newnodes = []
        for srcnode, destnode, _ in connection_list:
            if self in [srcnode, destnode]:
                raise IOError('Workflow connect cannot contain itself as node: src[%s] dest[%s] workflow[%s]'%(srcnode, destnode, self.name))
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
        for srcnode, destnode, connects in connection_list:
            connected_ports = []
            # check to see which ports of destnode are already
            # connected. 
            if not disconnect and (destnode in self._graph.nodes()):
                for edge in self._graph.in_edges_iter(destnode):
                    data = self._graph.get_edge_data(*edge)
                    for sourceinfo, destname in data['connect']:
                        connected_ports += [destname]
            for source, dest in connects:
                # Currently datasource/sink/grabber.io modules
                # determine their inputs/outputs depending on
                # connection settings.  Skip these modules in the check
                if dest in connected_ports:
                    raise Exception('Input %s of node %s is already ' \
                                        'connected'%(dest,destnode))
                if not (hasattr(destnode, '_interface') and '.io' in str(destnode._interface.__class__)):
                    if not destnode._check_inputs(dest):
                        not_found.append(['in', destnode.name, dest])
                if not (hasattr(srcnode, '_interface') and '.io' in str(srcnode._interface.__class__)):
                    if isinstance(source, tuple):
                        # handles the case that source is specified
                        # with a function
                        sourcename = source[0]
                    elif isinstance(source, str):
                        sourcename = source
                    else:
                        raise Exception('Unknown source specification in' \
                                         'connection from output of %s'%
                                        srcnode.name)
                    if sourcename and not srcnode._check_outputs(sourcename):
                        not_found.append(['out', srcnode.name, sourcename])
        infostr = []
        for info in not_found:
            infostr += ["Module %s has no %sput called %s\n"%(info[1], info[0],
                                                              info[2])]
        if not_found:
            raise Exception('\n'.join(['Some connections were not found']+infostr))

        # turn functions into strings
        for srcnode, destnode, connects in connection_list:
            for idx, (src, dest) in enumerate(connects):
                if isinstance(src, tuple) and not isinstance(src[1], str):
                    function_source = getsource(src[1])
                    connects[idx] = ((src[0], function_source, src[2:]), dest)

        # add connections
        for srcnode, destnode, connects in connection_list:
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            if edge_data:
                logger.debug('(%s, %s): Edge data exists: %s' % \
                                 (srcnode, destnode, str(edge_data)))
                for data in connects:
                    if data not in edge_data['connect']:
                        edge_data['connect'].append(data)
                    if disconnect:
                        logger.debug('Removing connection: %s'%str(data))
                        edge_data['connect'].remove(data)
                if edge_data['connect']:
                    self._graph.add_edges_from([(srcnode, destnode, edge_data)])
                else:
                    #pass
                    logger.debug('Removing connection: %s->%s'%(srcnode,destnode))
                    self._graph.remove_edges_from([(srcnode, destnode)])
            elif not disconnect:
                logger.debug('(%s, %s): No edge data' % (srcnode, destnode))
                self._graph.add_edges_from([(srcnode, destnode,
                                             {'connect': connects})])
            edge_data = self._graph.get_edge_data(srcnode, destnode, None)
            logger.debug('(%s, %s): new edge data: %s'% (srcnode, destnode,
                                                         str(edge_data)))

    def disconnect(self, *args):
        """Disconnect two nodes

        See the docstring for connect for format.
        """
        # yoh: explicit **dict was introduced for compatibility with Python 2.5
        return self.connect(*args, **dict(disconnect=True))

    def add_nodes(self, nodes):
        """ Add nodes to a workflow

        Parameters
        ----------
        nodes : list
            A list of WorkflowBase-based objects
        """
        newnodes = []
        all_nodes = self._get_all_nodes()
        for node in nodes:
            if self._has_node(node):
                raise IOError('Node %s already exists in the workflow'%node)
            if isinstance(node, Workflow):
                for subnode in node._get_all_nodes():
                    if subnode in all_nodes:
                        raise IOError('Subnode %s of node %s already exists in the workflow'%(subnode, node))
            newnodes.append(node)
        if not newnodes:
            logger.debug('no new nodes to add')
            return
        for node in newnodes:
            if not issubclass(node.__class__, WorkflowBase):
                raise Exception('Node %s must be a subclass of WorkflowBase' % str(node))
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
            A list of WorkflowBase-based objects
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
        outnode = [node for node in self._graph.nodes() if str(node).endswith('.'+nodename)]
        if outnode:
            outnode = outnode[0]
            if nodenames[1:] and issubclass(outnode.__class__, Workflow):
                outnode = outnode.get_node('.'.join(nodenames[1:]))
        else:
            outnode = None
        return outnode

    def write_graph(self, dotfilename='graph.dot', graph2use='hierarchical', format="png"):
        """Generates a graphviz dot file and a png file

        Parameters
        ----------
        
        graph2use: 'orig', 'hierarchical' (default), 'flat', 'exec'
            orig - creates a top level graph without expanding internal
                   workflow nodes
            flat - expands workflow nodes recursively
            exec - expands workflows to depict iterables
        
        format: 'png', 'svg'
            
        """
        graphtypes = ['orig', 'flat', 'hierarchical', 'exec']
        if graph2use not in graphtypes:
            raise ValueError('Unknown graph2use keyword. Must be one of: ' +str(graphtypes))
        base_dir, dotfilename = os.path.split(dotfilename)
        if base_dir == '':
            if self.base_dir:
                base_dir = self.base_dir
                if self.name:
                    base_dir = os.path.join(base_dir, self.name)
            else:
                base_dir = os.getcwd()
        base_dir = make_output_dir(base_dir)
        if graph2use == 'hierarchical':
            dotfilename = os.path.join(base_dir, dotfilename)
            self.write_hierarchical_dotfile(dotfilename=dotfilename, colored=False)
            format_dot(dotfilename, format=format)
        else:
            graph = self._graph
            if graph2use in ['flat', 'exec']:
                graph = self._create_flat_graph()
            if graph2use == 'exec':
                graph = generate_expanded_graph(deepcopy(graph))
            export_graph(graph, base_dir, dotfilename=dotfilename, format=format)

    def write_hierarchical_dotfile(self, dotfilename=None, colored=True):
        dotlist = ['digraph %s{'%self.name]
        if colored:
            dotlist.append('  '+'colorscheme=pastel28;')
        dotlist.append(self._get_dot(prefix='  ', colored=colored))
        dotlist.append('}')
        dotstr = '\n'.join(dotlist)
        if dotfilename:
            fp = open(dotfilename, 'wt')
            fp.writelines(dotstr)
            fp.close()
        else:
            logger.info(dotstr)

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
            plugin = config.get('execution','plugin')
        if type(plugin) is not str:
            runner = plugin
        else:
            name = 'nipype.pipeline.plugins'
            try:
                __import__(name)
            except ImportError:
                msg = 'Could not import plugin module: %s'%name
                logger.error(msg)
                raise ImportError(msg)
            else:
                runner = getattr(sys.modules[name], '%sPlugin'%plugin)(plugin_args=plugin_args)
        flatgraph = self._create_flat_graph()
        self.config = merge_dict(deepcopy(config._sections), self.config)
        logger.info(str(sorted(self.config)))
        self._set_needed_outputs(flatgraph)
        execgraph = generate_expanded_graph(deepcopy(flatgraph))
        for index, node in enumerate(execgraph.nodes()):
            node.config = self.config
            node.base_dir = self.base_dir
            node.index = index
            if isinstance(node, MapNode):
                node.use_plugin = (plugin, plugin_args)
        self._configure_exec_nodes(execgraph)
        self._write_report_info(self.base_dir, self.name, execgraph)
        runner.run(execgraph, updatehash=updatehash, config=self.config)
        return execgraph

    # PRIVATE API AND FUNCTIONS

    def _write_report_info(self, workingdir, name, graph):
        if workingdir is None:
            workingdir = os.getcwd()
        report_dir = os.path.join(workingdir, name, 'report')
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
        os.makedirs(report_dir)
        fp = open(os.path.join(report_dir,'index.html'), 'wt')
        fp.writelines('<html>')
        script="""
<head>
<style type="text/css">
  #page_container{width:1200px;margin:0;}
  #toc{width:450px;float:left;}
  #content{width:750px;float:left;}
  pre {
   white-space: pre-wrap;       /* css-3 */
   white-space: -moz-pre-wrap !important;  /* Mozilla, since 1999 */
   white-space: -pre-wrap;      /* Opera 4-6 */
   white-space: -o-pre-wrap;    /* Opera 7 */
   word-wrap: break-word;       /* Internet Explorer 5.5+ */
  }
</style>

<script type="text/javascript">
<!--
function readfile(srcfile, outputcontrol) {
  try {
    netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
  } catch (e) {
    alert("Permission to read file was denied.");
  }
  var file = Components.classes["@mozilla.org/file/local;1"].createInstance(Components.interfaces.nsILocalFile);
  file.initWithPath( srcfile );
  if ( file.exists() == false ) {
    alert("File does not exist");
  }
  var is = Components.classes["@mozilla.org/network/file-input-stream;1"].createInstance( Components.interfaces.nsIFileInputStream );
  is.init( file,0x01, 00004, null);
  var sis = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance( Components.interfaces.nsIScriptableInputStream );
  sis.init( is );
  var output = sis.read( sis.available() );
  document.getElementById(outputcontrol).innerHTML = '<pre>'+output+'</pre>';
}

function load(name, div) {
  readfile(name, div); 
  return false;
}
function loadimg(name, div) {
  document.getElementById(div).innerHTML = '<img src="'+name+'"></img>';
  return false;
}

var report_files = new Array(%d);
var result_files = new Array(%d);
%s
function isnodedone(srcfile){
  try {
    netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
  } catch (e) {
    alert("Permission to read file was denied.");
  }
  var file = Components.classes["@mozilla.org/file/local;1"].createInstance(Components.interfaces.nsILocalFile);
  file.initWithPath( srcfile );
  if ( file.exists() == false ) {
    return false;
  }
  return true;
}

function beginrefresh(){
  var num_nodes = %d;
  var nodes_done = -1;
  for(counter=nodes_done+1;counter<num_nodes;counter++){
    cell_id = 'td'+counter;
    if (isnodedone(report_files[counter]) == true){
      document.getElementById(cell_id).style.backgroundColor = "#afa";
      if (isnodedone(result_files[counter]) == true){
        document.getElementById(cell_id).style.backgroundColor = "#fff";
        nodes_done += 1;
      }
    }
    else{
      document.getElementById(cell_id).style.backgroundColor = "#aaa";
    }
  }
  if (nodes_done+1 < num_nodes){
    setTimeout("beginrefresh()", 1000);
  }
  else{
    alert('Workflow finished running');
  }
}

window.onload=beginrefresh
-->
</script>
</head>
"""
        nodes = nx.topological_sort(graph)
        report_files = []
        for i, node in enumerate(nodes):
            report_files.append('result_files[%d] = "%s/result_%s.pklz";'%(i, os.path.realpath(node.output_dir()), node.name))
            report_files.append('report_files[%d] = "%s/_report/report.rst";'%(i, os.path.realpath(node.output_dir())))
        report_files = '\n'.join(report_files)
        fp.writelines(script%(len(nodes), len(nodes), report_files, len(nodes)))
        fp.writelines('<body><div id="page_container">\n')
        fp.writelines('<div id="toc">\n')
        fp.writelines('<pre>Works only with mozilla/firefox browsers</pre><br>\n')
        script_file = os.path.join(os.path.dirname(sys.argv[0]), sys.argv[0])
        fp.writelines('<a href="#" onclick="load(\'%s\',\'content\');return false;">Script</a><br>\n'%(script_file))
        if self.base_dir:
            graph_file = 'file://'+os.path.join(self.base_dir, self.name, 'graph.dot.png')
            fp.writelines('<a href="#" onclick="loadimg(\'%s\',\'content\');return false;">Graph - requires write_graph() in script</a><br>\n'%(graph_file))
        fp.writelines('<table>\n')
        fp.writelines('<tr><td>Name</td><td>Hierarchy</td><td>Source</td></tr>\n')
        for i, node in enumerate(nodes):
            report_file = '%s/_report/report.rst'%os.path.realpath(node.output_dir())
            local_file = '%s.rst'%node._id
            url = '<tr><td id="td%d"><a href="#" onclick="load(\'%s\',\'content\');return false;">%s</a></td>'%(i,report_file, node._id)
            url += '<td>%s</td>'%('.'.join(node.fullname.split('.')[:-1]))
            url += '<td>%s</td></tr>\n'%('.'.join(get_print_name(node).split('.')[1:]))
            fp.writelines(url)
        fp.writelines('</table></div>')
        fp.writelines('<div id="content">content</div>')
        fp.writelines('</div></body></html>')
        fp.close()
        
    def _set_needed_outputs(self, graph):
        """Initialize node with list of which outputs are needed
        """
        if not str2bool(self.config['execution']['remove_unnecessary_outputs']):
            return
        for node in graph.nodes():
            node.needed_outputs = []
            for edge in graph.out_edges_iter(node):
                data = graph.get_edge_data(*edge)
                for sourceinfo, _ in sorted(data['connect']):
                    if isinstance(sourceinfo, tuple):
                        input_name =  sourceinfo[0]
                    else:
                        input_name = sourceinfo
                    if input_name not in node.needed_outputs:
                        node.needed_outputs += [input_name]
                        
    def _configure_exec_nodes(self, graph):
        """Ensure that each node knows where to get inputs from
        """
        for node in graph.nodes():
            node.input_source = {}
            for edge in graph.in_edges_iter(node):
                data = graph.get_edge_data(*edge)
                for sourceinfo, field in sorted(data['connect']):
                    node.input_source[field] = (os.path.join(edge[0].output_dir(),
                                                             'result_%s.pklz'%edge[0].name),
                                                sourceinfo)

    def _check_nodes(self, nodes):
        """Checks if any of the nodes are already in the graph
        
        """
        node_names = [node.name for node in self._graph.nodes()]
        node_lineage = [node._hierarchy for node in self._graph.nodes()]
        for node in nodes:
            if node.name in node_names:
                idx = node_names.index(node.name)
                if node_lineage[idx] in [node._hierarchy, self.name]:
                    raise IOError('Duplicate node name %s found.'%node.name)
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

        This function does not return any input ports that are already connected
        """
        inputdict = TraitedSpec()
        for node in self._graph.nodes():
            inputdict.add_trait(node.name, traits.Instance(TraitedSpec))
            if isinstance(node, Workflow):
                setattr(inputdict, node.name, node.inputs)
            else:
                taken_inputs = []
                for _, _, d in self._graph.in_edges_iter(nbunch=node, data=True):
                    for cd in d['connect']:
                        taken_inputs.append(cd[1])
                unconnectedinputs = TraitedSpec()
                for key, trait in node.inputs.items():
                    if key not in taken_inputs:
                        unconnectedinputs.add_trait(key, traits.Trait(trait, node=node))
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
            else:
                outputs = TraitedSpec()
                for key, _ in node.outputs.items():
                    outputs.add_trait(key, traits.Any(node=node))
                    setattr(outputs, key, None)
                setattr(outputdict, node.name, outputs)
        return outputdict

    def _set_input(self, object, name, newvalue):
        """Trait callback function to update a node input
        """
        object.traits()[name].node.set_input(name, newvalue)

    def _set_node_input(self, node, param, source, sourceinfo):
        """Set inputs of a node given the edge connection"""
        if isinstance(sourceinfo, str):
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
        logger.debug('setting node input: %s->%s', param, str(newval))
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
        """Turn a hierarchical DAG into a simple DAG where no node is a workflow
        """
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
                    innernode._hierarchy = '.'.join((self.name,innernode._hierarchy))
            else:
                node._hierarchy = self.name

    def _generate_flatgraph(self):
        """Generate a graph containing only Nodes or MapNodes
        """
        logger.debug('expanding workflow: %s', self)
        nodes2remove = []
        if not nx.is_directed_acyclic_graph(self._graph):
            raise Exception('Workflow: %s is not a directed acyclic graph (DAG)'%self.name)
        nodes = nx.topological_sort(self._graph)
        for node in nodes:
            logger.debug('processing node: %s'%node)
            if isinstance(node, Workflow):
                nodes2remove.append(node)
                # use in_edges instead of in_edges_iter to allow
                # disconnections to take place properly. otherwise, the
                # edge dict is modified.
                for u, _, d in self._graph.in_edges(nbunch=node, data=True):
                    logger.debug('in: connections-> %s'%str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("in: %s" % str (cd))
                        dstnode = node._get_parameter_node(cd[1],subtype='in')
                        srcnode = u
                        srcout = cd[0]
                        dstin = cd[1].split('.')[-1]
                        logger.debug('in edges: %s %s %s %s'%(srcnode, srcout, dstnode, dstin))
                        self.disconnect(u, cd[0], node, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # do not use out_edges_iter for reasons stated in in_edges
                for _, v, d in self._graph.out_edges(nbunch=node, data=True):
                    logger.debug('out: connections-> %s'%str(d['connect']))
                    for cd in deepcopy(d['connect']):
                        logger.debug("out: %s" % str (cd))
                        dstnode = v
                        if isinstance(cd[0], tuple):
                            parameter = cd[0][0]
                        else:
                            parameter = cd[0]
                        srcnode = node._get_parameter_node(parameter, subtype='out')
                        if isinstance(cd[0], tuple):
                            srcout = list(cd[0])
                            srcout[0] = parameter.split('.')[-1]
                            srcout = tuple(srcout)
                        else:
                            srcout = parameter.split('.')[-1]
                        dstin = cd[1]
                        logger.debug('out edges: %s %s %s %s'%(srcnode, srcout, dstnode, dstin))
                        self.disconnect(node, cd[0], v, cd[1])
                        self.connect(srcnode, srcout, dstnode, dstin)
                # expand the workflow node
                #logger.debug('expanding workflow: %s', node)
                node._generate_flatgraph()
                for innernode in node._graph.nodes():
                    innernode._hierarchy = '.'.join((self.name,innernode._hierarchy))
                self._graph.add_nodes_from(node._graph.nodes())
                self._graph.add_edges_from(node._graph.edges(data=True))
        if nodes2remove:
            self._graph.remove_nodes_from(nodes2remove)
        logger.debug('finished expanding workflow: %s', self)

    def _get_dot(self, prefix=None, hierarchy=None, colored=True):
        """Create a dot file with connection info
        """
        if prefix is None:
            prefix='  '
        if hierarchy is None:
            hierarchy = []
        level = len(prefix)/2+1
        dotlist = ['%slabel="%s";'%(prefix,self.name)]
        if colored:
            dotlist.append('%scolor=%d;'%(prefix, level))
        for node in nx.topological_sort(self._graph):
            fullname = '.'.join(hierarchy + [node.fullname])
            nodename = fullname.replace('.','_')
            if not isinstance(node, Workflow):
                node_class_name = get_print_name(node)
                if hasattr(node, 'iterables') and node.iterables:
                    dotlist.append('%s[label="%s", style=filled, colorscheme=greys7 color=2];'%(nodename, node_class_name))
                else:
                    dotlist.append('%s[label="%s"];'%(nodename, node_class_name))
        for node in nx.topological_sort(self._graph):
            if isinstance(node, Workflow):
                fullname = '.'.join(hierarchy + [node.fullname])
                nodename = fullname.replace('.','_')
                dotlist.append('subgraph cluster_%s {'%(nodename))
                if colored:
                    dotlist.append(prefix+prefix+'style=filled;')
                dotlist.append(node._get_dot(prefix=prefix + prefix,
                                             hierarchy=hierarchy+[self.name],
                                             colored=colored))
                dotlist.append('}')
            else:
                for subnode in self._graph.successors_iter(node):
                    if node._hierarchy != subnode._hierarchy:
                        continue
                    if not isinstance(subnode, Workflow):
                        nodefullname = '.'.join(hierarchy + [node.fullname])
                        subnodefullname = '.'.join(hierarchy + [subnode.fullname])
                        nodename = nodefullname.replace('.','_')
                        subnodename = subnodefullname.replace('.','_')
                        for _ in self._graph.get_edge_data(node, subnode)['connect']:
                            dotlist.append('%s -> %s;'%(nodename, subnodename))
                        logger.debug('connection: ' + dotlist[-1]) 
        # add between workflow connections
        for u,v,d in self._graph.edges_iter(data=True):
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
                        if 'datasink' not in str(v._interface.__class__).lower():
                            vname1 += '.' + '.'.join(dest.split('.')[:-1])
                    else:
                        vname1 += '.' + '.'.join(dest.split('.')[:-1])
                if uname1.split('.')[:-1] != vname1.split('.')[:-1]:
                    dotlist.append('%s -> %s;'%(uname1.replace('.','_'),
                                                vname1.replace('.','_')))
                    logger.debug('cross connection: ' + dotlist[-1]) 
        return ('\n'+prefix).join(dotlist)


class Node(WorkflowBase):
    """Wraps interface objects for use in pipeline


    Parameters
    ----------
    
    interface : interface object
        node specific interface  (fsl.Bet(), spm.Coregister())
    iterables : generator
        input field and list to iterate using the pipeline engine
        for example to iterate over different frac values in fsl.Bet()
        for a single field the input can be a tuple, otherwise a list
        of tuples
        node.iterables = ('frac',[0.5,0.6,0.7])
        node.iterables = [('fwhm',[2,4]),('fieldx',[0.5,0.6,0.7])]

    Notes
    -----
    
    creates output directory
    copies/discovers files to work with
    saves a hash.json file to indicate that a process has been completed

    Examples
    --------
    
    >>> import nipype.interfaces.spm as spm
    >>> realign = Node(interface=spm.Realign(), name='realign')
    >>> realign.inputs.in_files = 'functional.nii'
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """
    def __init__(self, interface, iterables=None, **kwargs):
        # interface can only be set at initialization
        super(Node, self).__init__(**kwargs)
        if interface is None:
            raise IOError('Interface must be provided')
        if not isinstance(interface, Interface):
            raise IOError('interface must be an instance of an Interface')
        self._interface  = interface
        self._result     = None
        self.iterables  = iterables
        self.parameterization = None
        self.input_source = {}
        self.needed_outputs = []

    @property
    def interface(self):
        return self._interface

    @property
    def result(self):
        return self._result

    @property
    def inputs(self):
        return self._interface.inputs

    @property
    def outputs(self):
        return self._interface._outputs()

    def output_dir(self):
        if self.base_dir is None:
            self.base_dir = mkdtemp()
        outputdir = self.base_dir
        if self._hierarchy:
            outputdir = os.path.join(outputdir, *self._hierarchy.split('.'))
        if self.parameterization:
            outputdir = os.path.join(outputdir, *self.parameterization)
        return os.path.abspath(os.path.join(outputdir,
                                            self.name))
    
    def set_input(self, parameter, val):
        """ Set interface input value or nodewrapper attribute

        Priority goes to interface.
        """
        logger.debug('setting nodelevel input %s = %s' % (parameter, str(val)))
        setattr(self.inputs, parameter, deepcopy(val))

    def get_output(self, parameter):
        val = None
        if self._result:
            val = getattr(self._result.outputs, parameter)
        return val

    def help(self):
        """ Print interface help
        """
        self._interface.help()

    def _get_hashval(self):
        hashed_inputs, hashvalue =  self.inputs.get_hashval(hash_method=self.config['execution']['hash_method'])
        if str2bool(self.config['execution']['remove_unnecessary_outputs']) and \
        self.needed_outputs:
            hashobject = md5()
            hashobject.update(hashvalue)
            sorted_outputs = sorted(self.needed_outputs)
            hashobject.update(str(sorted_outputs))
            hashvalue = hashobject.hexdigest()
            hashed_inputs['needed_outputs'] = sorted_outputs
        return hashed_inputs, hashvalue

    def _save_hashfile(self, hashfile, hashed_inputs):
        try:
            save_json(hashfile, hashed_inputs)
        except (IOError, TypeError):
            err_type = sys.exc_info()[0]
            if err_type is TypeError:
                # XXX - SG current workaround is to just
                # create the hashed file and not put anything
                # in it
                fd = open(hashfile,'wt')
                fd.writelines(str(hashed_inputs))
                fd.close()
                logger.debug('Unable to write a particular type to the json '\
                                 'file')
            else:
                logger.critical('Unable to open the file in write mode: %s'% \
                                    hashfile)

    def _get_inputs(self):
        """Retrieve inputs from pointers to results file

        This mechanism can be easily extended/replaced to retrieve data from
        other data sources (e.g., XNAT, HTTP, etc.,.)
        """
        logger.debug('Setting node inputs')
        for key, info in self.input_source.items():
            logger.debug('input: %s'%key)
            results_file = info[0]
            logger.debug('results file: %s'%results_file)
            results = loadpkl(results_file)
            output_value = Undefined
            if isinstance(info[1], tuple):
                output_name = info[1][0]
                func = create_function_from_source(info[1][1])
                value = getattr(results.outputs, output_name)
                if isdefined(value):
                    try:
                        output_value = func(value,
                                        *list(info[1][2]))
                    except NameError as e:
                        if e.args[0].startswith("global name") and e.args[0].endswith("is not defined"):
                            e.args = (e.args[0], "Due to engine constraints all imports have to be done inside each function definition")
                        raise e
                        
            else:
                output_name = info[1]
                try:
                    output_value = results.outputs.get()[output_name]
                except TypeError:
                    output_value = results.outputs.dictcopy()[output_name]
            logger.debug('output: %s'%output_name)
            try:
                self.set_input(key, deepcopy(output_value))
            except traits.TraitError, e:
                msg = ['Error setting node input:',
                       'Node: %s'%self.name,
                       'input: %s'%key,
                       'results_file: %s'%results_file,
                       'value: %s'%str(output_value)]
                e.args = (e.args[0] + "\n" + '\n'.join(msg),)
                raise

    def run(self, updatehash=False, force_execute=False):
        """Executes an interface within a directory.

        Parameters
        ----------

        updatehash: boolean
            Update the hash stored in the output directory
        force_execute: boolean
            Force rerunning the node
        """
        # check to see if output directory and hash exist
        self._get_inputs()
        outdir = self.output_dir()
        logger.info("Executing node %s in dir: %s"%(self._id,outdir))
        # Get a dictionary with hashed filenames and a hashvalue
        # of the dictionary itself.
        hashed_inputs, hashvalue = self._get_hashval()
        hashfile = os.path.join(outdir, '_0x%s.json' % hashvalue)
        if updatehash and os.path.exists(outdir):
            logger.debug("Updating hash: %s" % hashvalue)
            for file in glob(os.path.join(outdir, '_0x*.json')):
                os.remove(file)
            self._save_hashfile(hashfile, hashed_inputs)
        if force_execute or (not updatehash and (self.overwrite or not os.path.exists(hashfile))):
            logger.debug("Node hash: %s"%hashvalue)
            
            #by rerunning we mean only nodes that did finish to run previously
            if os.path.exists(outdir) \
            and not isinstance(self, MapNode) \
            and len(glob(os.path.join(outdir, '_0x*.json'))) != 0 \
            and len(glob(os.path.join(outdir, '_0x*_unfinished.json'))) == 0:
                logger.debug("Rerunning node")
                logger.debug("force_execute = %s, updatehash = %s, self.overwrite = %s, os.path.exists(%s) = %s, hash_method = ,%s,"%(str(force_execute),
                                                                                                                  str(updatehash),
                                                                                                                  str(self.overwrite),
                                                                                                                  hashfile,
                                                                                                                  str(os.path.exists(hashfile)),
                                                                                                                  self.config['execution']['hash_method'].lower()))
                if config.get('logging','workflow_level') == 'DEBUG' and not os.path.exists(hashfile):
                        exp_hash_paths = glob(os.path.join(outdir, '_0x*.json'))
                        if len(exp_hash_paths) == 1:
                            _, exp_hash_file_base, _ = split_filename(exp_hash_paths[0])
                            exp_hash = exp_hash_file_base[len('_0x'):]
                            logger.debug("Previous node hash = %s"%exp_hash)
                            try:
                                prev_inputs = load_json(exp_hash_paths[0])
                            except:
                                pass
                            else:
                                logdebug_dict_differences(prev_inputs, hashed_inputs)
                if str2bool(self.config['execution']['stop_on_first_rerun']):        
                    raise Exception("Cannot rerun when 'stop_on_first_rerun' is set to True")
            hashfile_unfinished = os.path.join(outdir, '_0x%s_unfinished.json' % hashvalue)
            if os.path.exists(hashfile):
                os.remove(hashfile)
            if os.path.exists(outdir) and \
               not (os.path.exists(hashfile_unfinished) and self._interface.can_resume) and \
               not isinstance(self, MapNode):
                logger.debug("Removing old %s and its contents"%outdir)
                rmtree(outdir)
            else:
                logger.debug("%s found and can_resume is True or Node is a MapNode - resuming execution" % hashfile_unfinished)
            outdir = make_output_dir(outdir)
            self._save_hashfile(hashfile_unfinished, hashed_inputs)
            self.write_report(report_type='preexec', cwd=outdir)
            savepkl(os.path.join(outdir, '_inputs.pklz'), self.inputs.get_traitsfree())
            try:
                self._run_interface(execute=True)
            except:
                os.remove(hashfile_unfinished)
                raise
            shutil.move(hashfile_unfinished, hashfile)
            self.write_report(report_type='postexec', cwd=outdir)
        else:
            if not os.path.exists(os.path.join(outdir, '_inputs.pklz')):
                logger.debug('%s: creating inputs file'%self.name)
                savepkl(os.path.join(outdir, '_inputs.pklz'), self.inputs.get_traitsfree())
            logger.debug("Hashfile exists. Skipping execution")
            self._run_interface(execute=False, updatehash=updatehash)
        logger.debug('Finished running %s in dir: %s\n'%(self._id,outdir))
        return self._result

    def _run_interface(self, execute=True, updatehash=False):
        if updatehash:
            return
        old_cwd = os.getcwd()
        os.chdir(self.output_dir())
        self._result = self._run_command(execute)
        os.chdir(old_cwd)

    def _save_results(self, result, cwd):
        resultsfile = os.path.join(cwd, 'result_%s.pklz' % self.name)
        if result.outputs:
            try:
                outputs = result.outputs.get()
            except TypeError:
                outputs = result.outputs.dictcopy() # outputs was a bunch
            result.outputs.set(**modify_paths(outputs, relative=True, basedir=cwd))
        logger.debug('saving results in %s'%resultsfile)
        savepkl(resultsfile, result)
        if result.outputs:
            result.outputs.set(**outputs)

    def _load_results(self, cwd):
        resultsfile = os.path.join(cwd, 'result_%s.pklz' % self.name)
        aggregate = True
        result = None
        attribute_error = False
        if os.path.exists(resultsfile):
            pkl_file = gzip.open(resultsfile, 'rb')
            try:
                result = cPickle.load(pkl_file)
            except (traits.TraitError, AttributeError, ImportError), err:
                if isinstance(err, (AttributeError, ImportError)):
                    attribute_error = True
                    logger.debug('attribute error: %s probably using different trait pickled file'%str(err))
                else:
                    logger.debug('some file does not exist. hence trait cannot be set')
            else:
                if result.outputs:
                    try:
                        outputs = result.outputs.get()
                    except TypeError:
                        outputs = result.outputs.dictcopy() # outputs was a bunch
                    try:
                        result.outputs.set(**modify_paths(outputs, relative=False, basedir=cwd))
                    except FileNotFoundError:
                        logger.debug('conversion to full path results in non existent file')
                    else:
                        aggregate = False
            pkl_file.close()
        logger.debug('Aggregate: %s', aggregate)
        # try aggregating first
        if aggregate:
            logger.debug('aggregating results')
            if attribute_error:
                old_inputs = loadpkl(os.path.join(cwd, '_inputs.pklz'))
                self.inputs.set(**old_inputs)
            if not isinstance(self, MapNode):
                self._copyfiles_to_wd(cwd, True, linksonly=True)
                aggouts = self._interface.aggregate_outputs(needed_outputs=self.needed_outputs)
                runtime = Bunch(cwd=cwd,returncode = 0, environ = deepcopy(os.environ.data), hostname = gethostname())
                result = InterfaceResult(interface=None,
                                         runtime=runtime,
                                         outputs=aggouts)
                self._save_results(result, cwd)
            else:
                logger.debug('aggregating mapnode results')
                self._run_interface()
                result = self._result
        return result

    def _run_command(self, execute, copyfiles=True):
        cwd = os.getcwd()
        if execute and copyfiles:
            self._originputs = deepcopy(self._interface.inputs)
        if execute:
            runtime = Bunch(returncode = 1,
                            environ = deepcopy(os.environ.data),
                            hostname = gethostname())
            result = InterfaceResult(interface=self._interface,
                                     runtime=runtime,
                                     outputs=None)
            self._result = result
            logger.debug('Executing node')
            if copyfiles:
                self._copyfiles_to_wd(cwd, execute)
            if issubclass(self._interface.__class__, CommandLine):
                try:
                    cmd = self._interface.cmdline
                except Exception, msg:
                    self._result.runtime.stderr = msg
                    raise
                cmdfile = os.path.join(cwd,'command.txt')
                fd = open(cmdfile,'wt')
                fd.writelines(cmd)
                fd.close()
                logger.info('Running: %s' % cmd)
            try:
                result = self._interface.run()
            except Exception, msg:
                self._result.runtime.stderr = msg
                raise
            
            if str2bool(self.config['execution']['remove_unnecessary_outputs']):
                dirs2keep = None
                if isinstance(self, MapNode):
                    dirs2keep = [os.path.join(cwd, 'mapflow')]
                result.outputs = clean_working_directory(result.outputs, cwd,
                                                         self._interface.inputs,
                                                         self.needed_outputs,
                                                         dirs2keep=dirs2keep)
            self._save_results(result, cwd)
        else:
            logger.info("Collecting precomputed outputs")
            try:
                result = self._load_results(cwd)
            except (FileNotFoundError, AttributeError):
                # if aggregation does not work, rerun the node
                logger.info("Some of the outputs were not found: rerunning node.")
                result = self._run_command(execute=True, copyfiles=False)
        return result

    def _strip_temp(self, files, wd):
        out = []
        for f in files:
            if isinstance(f, list):
                out.append(self._strip_temp(f, wd))
            else:
                out.append(f.replace(os.path.join(wd,'_tempinput'),wd))
        return out
            

    def _copyfiles_to_wd(self, outdir, execute, linksonly=False):
        """ copy files over and change the inputs"""
        if hasattr(self._interface,'_get_filecopy_info'):
            logger.debug('copying files to wd [execute=%s, linksonly=%s]'%(str(execute),
                                                                           str(linksonly)))
            if execute and linksonly:
                olddir = outdir
                outdir = os.path.join(outdir, '_tempinput')
                os.makedirs(outdir)
            for info in self._interface._get_filecopy_info():
                files = self.inputs.get().get(info['key'])
                if not isdefined(files):
                    continue
                if files:
                    infiles = filename_to_list(files)
                    if execute:
                        if linksonly:
                            if info['copy'] == False:
                                newfiles = copyfiles(infiles, [outdir], copy=info['copy'], create_new=True)
                            else:
                                newfiles = fnames_presuffix(infiles, newpath=outdir)
                            newfiles = self._strip_temp(newfiles,
                                                        os.path.abspath(olddir).split(os.path.sep)[-1])
                        else:
                            newfiles = copyfiles(infiles, [outdir], copy=info['copy'], create_new=True)
                    else:
                        newfiles = fnames_presuffix(infiles, newpath=outdir)
                    if not isinstance(files, list):
                        newfiles = list_to_filename(newfiles)
                    setattr(self.inputs, info['key'], newfiles)
            if execute and linksonly:
                rmtree(outdir)

    def update(self, **opts):
        self.inputs.update(**opts)

    def write_report(self, report_type=None, cwd=None):
        report_dir = os.path.join(cwd, '_report')
        report_file = os.path.join(report_dir, 'report.rst')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        if report_type == 'preexec':
            logger.debug('writing pre-exec report to %s'%report_file)
            fp = open(report_file, 'wt')
            fp.writelines(write_rst_header('Node: %s'%get_print_name(self), level=0))
            fp.writelines(write_rst_list(['Hierarchy : %s'%self.fullname,
                                          'Exec ID : %s'%self._id]))
            fp.writelines(write_rst_header('Original Inputs', level=1))
            fp.writelines(write_rst_dict(self.inputs.get()))
        if report_type == 'postexec':
            logger.debug('writing post-exec report to %s'%report_file)
            fp = open(report_file, 'at')
            fp.writelines(write_rst_header('Execution Inputs', level=1))
            fp.writelines(write_rst_dict(self.inputs.get()))
            if not hasattr(self.result, 'outputs') or self.result.outputs is None:
                return
            fp.writelines(write_rst_header('Execution Outputs', level=1))
            if isinstance(self.result.outputs, Bunch):
                fp.writelines(write_rst_dict(self.result.outputs.dictcopy()))
            elif self.result.outputs:
                fp.writelines(write_rst_dict(self.result.outputs.get()))
            if isinstance(self, MapNode):
                fp.close()
                return
            fp.writelines(write_rst_header('Runtime info', level=1))
            if hasattr(self.result.runtime, 'cmdline'):
                fp.writelines(write_rst_dict({'hostname' : self.result.runtime.hostname,
                                              'duration' : self.result.runtime.duration,
                                              'command' : self.result.runtime.cmdline}))
            else: 
                fp.writelines(write_rst_dict({'hostname' : self.result.runtime.hostname,
                                              'duration' : self.result.runtime.duration}))
            if hasattr(self.result.runtime, 'merged'):
                fp.writelines(write_rst_header('Terminal output', level=2))
                fp.writelines(write_rst_list(self.result.runtime.merged))
            if hasattr(self.result.runtime, 'environ'):
                fp.writelines(write_rst_header('Environment', level=2))
                fp.writelines(write_rst_dict(self.result.runtime.environ))
        fp.close()


class MapNode(Node):
    """Wraps interface objects that need to be iterated on a list of inputs.

    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> realign = MapNode(interface=fsl.MCFLIRT(), name='realign', iterfield=['in_file']) # doctest: +SKIP
    >>> realign.inputs.in_file = ['functional.nii', 'functional2.nii', 'functional3.nii'] # doctest: +SKIP
    >>> realign.run() # doctest: +SKIP
    
    """

    def __init__(self, interface, iterfield=None, **kwargs):
        """

        Parameters
        ----------

        iterfield : 1+-element list
        key(s) over which to repeatedly call the interface.
        for example, to iterate FSL.Bet over multiple files, one can
        set node.iterfield = ['infile'].  If this list has more than 1 item
        then the inputs are selected in order simultaneously from each of these
        fields and each field will need to have the same number of members.
        """
        super(MapNode, self).__init__(interface, **kwargs)
        self.iterfield  = iterfield
        if self.iterfield is None:
            raise Exception("Iterfield must be provided")
        elif isinstance(self.iterfield, str):
            self.iterfield = [self.iterfield]
        self._inputs = self._create_dynamic_traits(self._interface.inputs,
                                                   fields=self.iterfield)
        self._inputs.on_trait_change(self._set_mapnode_input)
        self._got_inputs = False

    def _create_dynamic_traits(self, basetraits, fields=None, nitems=None):
        """Convert specific fields of a trait to accept multiple inputs
        """
        output = DynamicTraitedSpec()
        if fields is None:
            fields = basetraits.copyable_trait_names()
        for name, spec in basetraits.items():
            if name in fields and ((nitems is None) or (nitems > 1)):
                logger.debug('adding multipath trait: %s'%name)
                output.add_trait(name, InputMultiPath(spec.trait_type))
            else:
                output.add_trait(name, traits.Trait(spec))
            setattr(output, name, Undefined)
            value = getattr(basetraits, name)
            if isdefined(value):
                setattr(output, name, value)
            value = getattr(output, name)
        return output

    def set_input(self, parameter, val):
        """ Set interface input value or nodewrapper attribute

        Priority goes to interface.
        """
        logger.debug('setting nodelevel input %s = %s' % (parameter, str(val)))
        self._set_mapnode_input(self.inputs, parameter, deepcopy(val))

    def _set_mapnode_input(self, object, name, newvalue):
        logger.debug('setting mapnode input: %s -> %s' %(name, str(newvalue)))
        if name in self.iterfield:
            setattr(self._inputs, name, newvalue)
        else:
            setattr(self._interface.inputs, name, newvalue)

    def _get_hashval(self):
        """ Compute hash including iterfield lists
        """
        hashinputs = deepcopy(self._interface.inputs)
        for name in self.iterfield:
            hashinputs.remove_trait(name)
            hashinputs.add_trait(name, InputMultiPath(self._interface.inputs.traits()[name].trait_type))
            logger.debug('setting hashinput %s-> %s'%(name,getattr(self._inputs, name)))
            setattr(hashinputs, name, getattr(self._inputs, name))
        hashed_inputs, hashvalue = hashinputs.get_hashval(hash_method=self.config['execution']['hash_method'])
        if str2bool(self.config['execution']['remove_unnecessary_outputs']) and \
        self.needed_outputs:
            hashobject = md5()
            hashobject.update(hashvalue)
            sorted_outputs = sorted(self.needed_outputs)
            hashobject.update(str(sorted_outputs))
            hashvalue = hashobject.hexdigest()
            hashed_inputs['needed_outputs'] = sorted_outputs
        return hashed_inputs, hashvalue

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        if self._interface._outputs():
            return Bunch(self._interface._outputs().get())
        else:
            return None

    def _make_nodes(self, cwd=None):
        if cwd is None:
            cwd = self.output_dir()
        nitems = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
        for i in range(nitems):
            nodename = '_' + self.name+str(i)
            node = Node(deepcopy(self._interface), name=nodename)
            node.overwrite = self.overwrite
            node._interface.inputs.set(**deepcopy(self._interface.inputs.get()))
            for field in self.iterfield:
                fieldvals = filename_to_list(getattr(self.inputs, field))
                logger.debug('setting input %d %s %s'%(i, field,
                                                      fieldvals[i]))
                setattr(node.inputs, field,
                        fieldvals[i])
            node.config = self.config
            node.base_dir = os.path.join(cwd, 'mapflow') # for backwards compatibility
            yield i, node

    def _node_runner(self, nodes, updatehash=False):
        for i, node in nodes:
            err = None
            try:
                node.run(updatehash=updatehash)
            except Exception, err:
                if str2bool(self.config['execution']['stop_on_first_crash']):
                    self._result = node.result
                    raise
            yield i, node, err

    def _collate_results(self, nodes):
        self._result = InterfaceResult(interface=[], runtime=[],
                                       outputs=self.outputs)
        returncode = []
        for i, node, err in nodes:
            self._result.runtime.insert(i, None)
            if node.result and hasattr(node.result, 'runtime'):
                self._result.interface.insert(i, node.result.interface)
                self._result.runtime[i] = node.result.runtime
            returncode.insert(i, err)
            if self.outputs:
                for key, _ in self.outputs.items():
                    if str2bool(self.config['execution']['remove_unnecessary_outputs']) and \
                    self.needed_outputs:
                        if key not in self.needed_outputs:
                            continue
                    values = getattr(self._result.outputs, key)
                    if not isdefined(values):
                        values = []
                    if node.result.outputs:
                        values.insert(i, node.result.outputs.get()[key])
                    else:
                        values.insert(i, None)
                    if any([val != Undefined for val in values]) and self._result.outputs:
                        setattr(self._result.outputs, key, values)
        if returncode and any([code is not None for code in returncode]):
            msg = []
            for i, code in enumerate(returncode):
                if code is not None:
                    msg += ['Subnode %d failed'%i]
                    msg += ['Error:', str(code)]
            raise Exception('Subnodes of node: %s failed:\n%s'%(self.name,
                                                                '\n'.join(msg)))

    def write_report(self, report_type=None, cwd=None):
        if report_type == 'preexec':
            super(MapNode, self).write_report(report_type=report_type, cwd=cwd)
        if report_type == 'postexec':
            super(MapNode, self).write_report(report_type=report_type, cwd=cwd)
            report_dir = os.path.join(cwd, '_report')
            report_file = os.path.join(report_dir, 'report.rst')
            fp = open(report_file, 'at')
            fp.writelines(write_rst_header('Subnode reports', level=1))
            nitems = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
            subnode_report_files = []
            for i in range(nitems):
                nodename = '_' + self.name+str(i)
                subnode_report_files.insert(i, 'subnode %d'%i + ' : ' + os.path.join(cwd, 'mapflow', nodename, '_report', 'report.rst'))
            fp.writelines(write_rst_list(subnode_report_files))
            fp.close()
        
    def get_subnodes(self):
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        self.write_report(report_type='preexec', cwd = self.output_dir())
        return [node for _, node in self._make_nodes()]
    
    def num_subnodes(self):
        if not self._got_inputs:
            self._get_inputs()
            self._got_inputs = True
        return len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
    
    def _get_inputs(self):
        old_inputs = self._inputs.get()
        self._inputs = self._create_dynamic_traits(self._interface.inputs,
                                                   fields=self.iterfield)
        self._inputs.set(**old_inputs)
        super(MapNode, self)._get_inputs()

    def _run_interface(self, execute=True, updatehash=False):
        """Run the mapnode interface

        This is primarily intended for serial execution of mapnode. A parallel
        execution requires creation of new nodes that can be spawned
        """
        old_cwd = os.getcwd()
        cwd = self.output_dir()
        os.chdir(cwd)
        for iterfield in self.iterfield:
            if not isdefined(getattr(self.inputs, iterfield)):
                raise ValueError("Input %s is not defined but listed in iterfields."%iterfield)
        if len(self.iterfield) > 1:
            first_len = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
            for iterfield in self.iterfield[1:]:
                if first_len != len(filename_to_list(getattr(self.inputs, iterfield))):
                    raise ValueError("All iterfields of a MapNode have to have the same length.")

        if execute:
            nitems = len(filename_to_list(getattr(self.inputs, self.iterfield[0])))
            nodenames = ['_' + self.name+str(i) for i in range(nitems)]
            # map-reduce formulation
            self._collate_results(self._node_runner(self._make_nodes(cwd),
                                                    updatehash=updatehash))
            self._save_results(self._result, cwd)
            # remove any node directories no longer required
            dirs2remove = []
            for path in glob(os.path.join(cwd,'mapflow','*')):
                if os.path.isdir(path):
                    if path.split(os.path.sep)[-1] not in nodenames:
                        dirs2remove.append(path)
            for path in dirs2remove:
                shutil.rmtree(path)
        else:
            self._result = self._load_results(cwd)
        os.chdir(old_cwd)
