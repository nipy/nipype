from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec, traits,
                                    File, TraitedSpec, Directory, InputMultiPath,
                                    OutputMultiPath, isdefined)
import re
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile, list_to_filename
import os, os.path as op
import numpy as np
import nibabel as nb
import networkx as nx
import sys
import scipy.io as sio
from itertools import combinations as combo
import random
import pickle
import cmp


def read_unknown_ntwk(ntwk):
    path, name, ext = split_filename(ntwk)
    if ext == '.pck':
        ntwk = nx.read_gpickle(ntwk)
    elif ext == '.graphml':
        ntwk = nx.read_graphml(ntwk)
    return ntwk

def remove_all_edges(ntwk):
    ntwktmp = ntwk.copy()
    edges = ntwktmp.edges_iter()
    for edge in edges:
        ntwk.remove_edge(edge[0],edge[1])
    return ntwk
    
def fix_keys_for_gexf(orig):
    import networkx as nx
    ntwk = nx.Graph()
    nodes = orig.nodes_iter()
    edges = orig.edges_iter()
    for node in nodes:
        newnodedata = {}
        newnodedata.update(orig.node[node])
        newnodedata['label'] = orig.node[node]['dn_fsname']
        ntwk.add_node(str(node),newnodedata)
        if ntwk.node[str(node)].has_key('dn_position') and newnodedata.has_key('dn_position'):
            ntwk.node[str(node)]['dn_position'] = str(newnodedata['dn_position'])
    for edge in edges:
        data = {}
        data = orig.edge[edge[0]][edge[1]]
        ntwk.add_edge(str(edge[0]),str(edge[1]),data)
        if ntwk.edge[str(edge[0])][str(edge[1])].has_key('fiber_length_mean'):
            ntwk.edge[str(edge[0])][str(edge[1])]['fiber_length_mean'] = str(data['fiber_length_mean'])
        if ntwk.edge[str(edge[0])][str(edge[1])].has_key('fiber_length_std'):
            ntwk.edge[str(edge[0])][str(edge[1])]['fiber_length_std'] = str(data['fiber_length_std'])
        if ntwk.edge[str(edge[0])][str(edge[1])].has_key('number_of_fibers'):
            ntwk.edge[str(edge[0])][str(edge[1])]['number_of_fibers'] = str(data['number_of_fibers'])
        if ntwk.edge[str(edge[0])][str(edge[1])].has_key('value'):
            ntwk.edge[str(edge[0])][str(edge[1])]['value'] = str(data['value'])
    return ntwk   

def add_dicts_by_key(in_dict1, in_dict2):
    sum = {}
    for key1 in in_dict1:
        for key2 in in_dict2:
            if key1 == key2:
                sum[key1] = in_dict1[key1] + in_dict2[key2]
    return sum

def average_networks(in_files, ntwk_res_file, group_id):
    import networkx as nx
    import os.path as op
    print "Creating average network for group: {grp}".format(grp=group_id)
    if len(in_files) == 1:     
        ntwk = read_unknown_ntwk(in_files[0])
    else:
        ntwk_res_file = read_unknown_ntwk(ntwk_res_file)
        ntwk = remove_all_edges(ntwk_res_file)
        # Sum all the relevant variables
        for index, subject in enumerate(in_files):
            tmp = nx.read_gpickle(subject)
            edges = tmp.edges_iter()
            for edge in edges:
                data = {}
                data = tmp.edge[edge[0]][edge[1]]
                if ntwk.has_edge(edge[0],edge[1]):
                    current = {}
                    current = ntwk.edge[edge[0]][edge[1]]
                    data = add_dicts_by_key(current,data)
                ntwk.add_edge(edge[0],edge[1],data)
            nodes = tmp.nodes_iter()
            for node in nodes:
                data = {}
                data = tmp.node[node]
                if tmp[node].has_key('value'):
                    data['value'] = data['value'] + tmp.node[node]['value']
                ntwk.add_node(node,data)
        # Divide by number of files
        nodes = ntwk.nodes_iter()
        edges = ntwk.edges_iter()

        for edge in edges:
            data = ntwk.edge[edge[0]][edge[1]]
            for key in data:
                data[key] = data[key] / len(in_files)
        for node in nodes:
            data = ntwk.node[node]
            if data.has_key('value'):
                ntwk.node[node]['value'] = data['value'] / len(in_files)

    network_name = group_id + '_average.pck'
    nx.write_gpickle(ntwk, op.abspath(network_name))
    ntwk = fix_keys_for_gexf(ntwk)
    network_name = group_id + '_average.gexf'
    nx.write_gexf(ntwk, op.abspath(network_name))
    network_name = group_id + '_average'
    return op.abspath(network_name)

def compute_node_measures(ntwk):
    """
    These return node-based measures
    """
    print 'Computing node measures:'
    weighted = True
    measures = {}
    print '...Computing degree...'
    measures['degree'] = np.array(ntwk.degree().values())
    ##print '...Computing number of cliques for each node...'
    ##measures['number_of_cliques'] = np.array(nx.number_of_cliques(ntwk).values())
    print '...Computing load centrality...'
    measures['load_centrality'] = np.array(nx.load_centrality(ntwk).values())
    ##print '...Computing betweenness centrality...'
    ##measures['betweenness_centrality'] = np.array(nx.betweenness_centrality(ntwk).values())
    ##print '...Computing degree centrality...'
    ##measures['degree_centrality'] = np.array(nx.degree_centrality(ntwk).values())
    ##print '...Computing closeness centrality...'
    ##measures['closeness_centrality'] = np.array(nx.closeness_centrality(ntwk).values())
    ##print '...Computing eigenvector centrality...'
    ##measures['eigenvector_centrality'] = np.array(nx.eigenvector_centrality(ntwk).values())
    ##print '...Calculating node clique number'
    ##measures['node_clique_number'] = np.array(nx.node_clique_number(ntwk).values())
    ##print '...Computing pagerank...'
    ##measures['pagerank'] = np.array(nx.pagerank(ntwk).values())
    ##print '...Computing triangles...'
    ##measures['triangles'] = np.array(nx.triangles(ntwk).values())
    print '...Computing clustering...'
    measures['clustering'] = np.array(nx.clustering(ntwk).values())
    #print 'Computing closeness vitality...'
    #measures['closeness_vitality'] = np.array(nx.closeness_vitality(ntwk,weighted_edges=weighted).values())
    print '...Identifying network isolates...'
    measures['isolates'] = nx.isolates(ntwk)
    binarized = np.zeros((ntwk.number_of_nodes(),1))
    for value in measures['isolates']:
        value = value - 1 # Zero indexing
        binarized[value] = 1
    measures['isolates'] = binarized
    print '...Computing k-core number'
    measures['core_number'] = np.array(nx.core_number(ntwk).values())
    
    return measures

def compute_edge_measures(ntwk):
    """
    These return edge-based measures
    """
    print 'Computing edge measures:'
    weighted = True
    measures = {}
    #print '...Computing google matrix...' #Makes really large networks (500k+ edges)
    #measures['google_matrix'] = nx.google_matrix(ntwk)
    print '...Computing hub matrix...'
    measures['hub_matrix'] = nx.hub_matrix(ntwk)
    ##print '...Computing authority matrix...'
    ##measures['authority_matrix'] = nx.authority_matrix(ntwk)
    
    
    """
    These return other sized arrays
    """
    #dict_measures['degree_mixing_matrix'] = nx.degree_mixing_matrix(ntwk)
    return measures
    
def compute_dict_measures(ntwk):
    """
    Returns a dictionary
    """
    print 'Computing measures which return a dictionary:'
    weighted = True
    measures = {}
    ##print '...Computing connected components...'
    ##measures['connected_components'] = nx.connected_components(ntwk) # list of lists, doesn't make sense to do stats
    ##print '...Computing neighbour connectivity...'
    ##measures['neighbor_connectivity'] = nx.neighbor_connectivity(ntwk)    
    print '...Computing rich club coefficient...'
    measures['rich_club_coef'] = nx.rich_club_coefficient(ntwk)
    ##print '...Computing edge load...'
    ##measures['edge_load'] = nx.edge_load(ntwk)
    ##print '...Computing betweenness centrality...'
    ##measures['edge_betweenness_centrality'] = nx.edge_betweenness_centrality(ntwk)
    ##print '...Computing shortest path length for each node...'
    ##measures['shortest_path_length'] = np.array(nx.shortest_path_length(ntwk, weighted).values())
    return measures

def compute_singlevalued_measures(ntwk):
    """
    Returns a single value per network
    """
    print 'Computing single valued measures:'
    weighted = True
    measures = {}
    print '...Computing degree assortativity (pearson number) ...'
    measures['degree_pearsonr'] = nx.degree_pearsonr(ntwk)
    print '...Computing degree assortativity...'
    measures['degree_assortativity'] = nx.degree_assortativity(ntwk)
    print '...Computing transitivity...'
    measures['transitivity'] = nx.transitivity(ntwk)
    print '...Computing number of connected_components...'
    measures['number_connected_components'] = nx.number_connected_components(ntwk)
    print '...Computing average clustering...'
    measures['average_clustering'] = nx.average_clustering(ntwk)
    #print '...Computing graph clique number...'
    #measures['graph_clique_number'] = nx.graph_clique_number(ntwk)
    #print '...Calculating average shortest path length...'
    #measures['average_shortest_path_length'] = nx.average_shortest_path_length(ntwk, weighted)
    return measures
    
def compute_nx_measures(ntwk):
    measures = {}
    node = compute_node_measures(ntwk)
    edge = compute_edge_measures(ntwk)
    singlevalued = compute_singlevalued_measures(ntwk)
    measures.update(node)
    measures.update(edge)
    measures.update(singlevalued)
    return measures

def group_nx_stats(in_networks, output_prefix, group_id, subject_ids_group, ntwk_res_file):
    print 'Running group-level NetworkX stats...'
    if not subject_ids_group == 0:
        print 'Subject IDs: {subj_IDs}'.format(subj_IDs=subject_ids_group)
    node_measures = {}
    edge_measures = {}
    ntwk_measures = {}
    dict_measures = {}

    print in_networks    
    print ntwk_res_file
    average = average_networks(in_networks, ntwk_res_file, group_id)
    ntwk_res_file = read_unknown_ntwk(ntwk_res_file)
    tmp = []
    for subject in in_networks:
        print subject
        tmp = nx.read_gpickle(subject)
        node_measures[subject] = compute_node_measures(tmp)
        edge_measures[subject] = compute_edge_measures(tmp)
        ntwk_measures[subject] = compute_singlevalued_measures(tmp)
        dict_measures[subject] = compute_dict_measures(tmp)
    
    data = np.array((ntwk_res_file.number_of_nodes()))
    node_keys = node_measures[subject].keys()
    nodes = {}
    for measure in node_keys:
        for idx, subject in enumerate(node_measures.keys()):
            tmp = node_measures[subject][measure]
            n = max(np.shape(tmp))
            tmp = np.reshape(tmp, (n, -1))
            if idx == 0:
                data = tmp
            else:
                data = np.dstack((data,tmp))
        print np.shape(data)
        nodes[measure] = np.mean(data,2)

    edge_keys = edge_measures[subject].keys()    
    edges = {}
    for measure in edge_keys:
        for idx, subject in enumerate(edge_measures.keys()):
            tmp = np.array(edge_measures[subject][measure])
            n = max(np.shape(tmp))
            tmp = np.reshape(tmp, (n, n, -1))
            if idx == 0:
                data = tmp
            else:
                data = np.concatenate((data,tmp),2)
        edges[measure] = np.mean(data,2)
    
    ntwk_keys = ntwk_measures[subject].keys()
    singles = {}
    for measure in ntwk_keys:
        for idx, subject in enumerate(ntwk_measures.keys()):
            tmp = ntwk_measures[subject][measure]
            if idx == 0:
                data = tmp
            else:
                data = np.dstack((data,tmp))
        print np.shape(data)
        singles[measure] = np.mean(data)
    
    returnall = {'node_measures':nodes, 'edge_measures':edges, 'ntwk_measures':singles, 'average':average, 'dict_measures':dict_measures}
    return returnall

class NetworkXStatsInputSpec(TraitedSpec):
    in_networks = InputMultiPath(File(exists=True), mandatory=True, desc='Networks for a group of subjects')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    subject_ids = traits.List(traits.Str, desc='Subject IDs for each input file')
    output_prefix = traits.Str('nxstats_', usedefault=True, desc='Prefix to append to output files')
    group_id = traits.Str('group1', usedefault=True, desc='ID for group')
    out_stats_file = File('nxstats.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')
    out_group_average = File('group1_average.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_group_measures = File('group1_measures.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_pickled_extra_measures_group = File('group1_extra_measures.pck', usedefault=True, desc='Network measures for group 1 that return dictionaries stored as a Pickle.')

class NetworkXStatsOutputSpec(TraitedSpec):
    stats_file = File(desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')
    out_gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    out_gpickled_groupavg = File(desc='Average connectome for the group in gpickled format')
    out_gexf_network_files = OutputMultiPath(File(desc='Output gexf network files'))
    out_gexf_groupavg = File(desc='Average connectome for the group in gexf format (for Gephi)')
    out_group_measures = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_group_average = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_pickled_extra_measures = File(desc='Network measures for the group that return dictionaries, stored as a Pickle.')

class NetworkXStats(BaseInterface):
    input_spec = NetworkXStatsInputSpec
    output_spec = NetworkXStatsOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.subject_ids):
            subject_ids = self.inputs.subject_ids
        else:
            subject_ids = 0

        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
            cmp_config.parcellation_scheme = "NativeFreesurfer"
            ntwk_res_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']
        global gpickled
        global gexf
        gpickled = []
        gexf = []

        returnall = group_nx_stats(self.inputs.in_networks, self.inputs.output_prefix, self.inputs.group_id, subject_ids, ntwk_res_file)

        node_measures = returnall['node_measures']
        edge_measures = returnall['edge_measures']
        ntwk_measures = returnall['ntwk_measures']
        subject_average = returnall['average']
        subject_dict_measures = returnall['dict_measures']

        out_node_measures = op.abspath(self._gen_outfilename(self.inputs.group_id + '_node_measures', 'mat'))
        out_edge_measures = op.abspath(self._gen_outfilename(self.inputs.group_id + '_edge_measures', 'mat'))
        out_ntwk_measures = op.abspath(self._gen_outfilename(self.inputs.group_id + '_ntwk_measures', 'mat'))
        out_average = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average', 'mat'))
        out_pickled_extra_measures = op.abspath(self._gen_outfilename(self.inputs.group_id + '_extra_measures', 'pck'))
        print 'Saving node measures as {file}'.format(file=out_node_measures)
        sio.savemat(out_node_measures, node_measures)
        print 'Saving edge measures as {file}'.format(file=out_edge_measures)
        sio.savemat(out_edge_measures, edge_measures)
        print 'Saving single valued measures as {file}'.format(file=out_ntwk_measures)
        sio.savemat(out_ntwk_measures, ntwk_measures)

        nodentwks = []
        for key in node_measures.keys():
            newntwk = add_node_data(node_measures[key], ntwk_res_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            nodentwks.append(out_file)
        gpickled.extend(nodentwks)

        edgentwks = []
        for key in edge_measures.keys():
            newntwk = add_edge_data(edge_measures[key], ntwk_res_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            edgentwks.append(out_file)
        gpickled.extend(edgentwks)
        
        #print 'Saving subject average as {file}'.format(file=out_average)
        #sio.savemat(out_average, subject_average)

        print 'Saving extra measure File for group 1 to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures))
        file = open(out_pickled_extra_measures, 'w')
        pickle.dump(subject_dict_measures, file)
        file.close()        

        groupavg = average_networks(self.inputs.in_networks, ntwk_res_file, self.inputs.group_id)
        gpickled.append(groupavg + '.pck')
        gexf.append(groupavg + '.gexf')
        return runtime

    def _list_outputs(self):
        global gpickled
        global gexf
        outputs = self.output_spec().get()
        outputs["out_group_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_measures', 'mat'))
        outputs["out_group_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average', 'mat'))
        outputs["out_pickled_extra_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_extra_measures', 'pck'))
        outputs["out_gpickled_groupavg"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average','pck'))
        outputs["out_gexf_groupavg"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average','gexf'))
        outputs["stats_file"] = op.abspath(self.inputs.out_stats_file)
        outputs["out_gpickled_network_files"] = gpickled
        outputs["out_gexf_network_files"] = gexf
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext

def compute_network_measures(ntwk):
    measures = {}
    print 'Identifying k-core'
    measures['k_core'] = nx.k_core(ntwk)
    print 'Identifying k-shell'
    measures['k_shell'] = nx.k_shell(ntwk)
    print 'Identifying k-crust'
    measures['k_crust'] = nx.k_crust(ntwk)
    return measures

def add_node_data(node_array, ntwk):
    ntwk = read_unknown_ntwk(ntwk)
    node_ntwk = ntwk.copy()
    newdata = {}
    for idx, data in ntwk.nodes_iter(data=True):
        newdata['value'] = node_array[int(idx)-1]
        data.update(newdata)
        node_ntwk.node[idx] = data
    return node_ntwk

def add_edge_data(edge_array, ntwk):
    ntwk = read_unknown_ntwk(ntwk)
    edge_ntwk = ntwk.copy()
    data = {}
    for x, row in enumerate(edge_array):
        for y in range(0,np.max(np.shape(edge_array[x]))):
            if not edge_array[x, y] == 0:
                data['value'] = edge_array[x, y]
                if edge_ntwk.has_edge(x,y):
                    old_edge_dict = edge_ntwk.edge[x][y]
                    edge_ntwk.remove_edge(x,y)
                    data.update(old_edge_dict)
                edge_ntwk.add_edge(x,y,data)                
    return edge_ntwk


class NetworkXMetricsInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='Input network')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as NetworkX graphs.')
    subject_id = traits.Str('subject', usedefault=True, desc='Subject ID for the input network')
    out_k_core = File('k_core', usedefault=True, desc='Computed k-core network stored as a NetworkX pickle.')
    out_k_shell = File('k_shell', usedefault=True, desc='Computed k-shell network stored as a NetworkX pickle.')
    out_k_crust = File('k_crust', usedefault=True, desc='Computed k-crust network stored as a NetworkX pickle.')
    out_pickled_extra_measures = File('extra_measures', usedefault=True, desc='Network measures for group 1 that return dictionaries stored as a Pickle.')

class NetworkXMetricsOutputSpec(TraitedSpec):
    gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    node_measure_networks = OutputMultiPath(File(desc='Output gpickled network files for all node-based measures'))
    edge_measure_networks = OutputMultiPath(File(desc='Output gpickled network files for all edge-based measures'))
    k_networks = OutputMultiPath(File(desc='Output gpickled network files for the k-core, k-shell, and k-crust networks'))
    k_core = File(desc='Computed k-core network stored as a NetworkX pickle.')
    k_shell = File(desc='Computed k-shell network stored as a NetworkX pickle.')
    k_crust = File(desc='Computed k-crust network stored as a NetworkX pickle.')
    out_pickled_extra_measures = File(desc='Network measures for the group that return dictionaries, stored as a Pickle.')
    matlab_dict_measures = OutputMultiPath(File(desc='Network measures for the group that return dictionaries, stored as matlab matrices.'))

class NetworkXMetrics(BaseInterface):
    """
    Calculates and outputs NetworkX-based measures for an input network

    Example
    -------
    
    >>> import nipype.interfaces.cmtk as cmtk
    >>> import cmp
    >>> nxmetrics = cmtk.NetworkXMetrics()
    >>> nxmetrics.inputs.in_file = 'subj1.pck'
    >>> cmp_config = cmp.configuration.PipelineConfiguration()
    >>> cmp_config.parcellation_scheme = "Lausanne2008"
    >>> nxmetrics.inputs.resolution_network_file = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']
    >>> nxmetrics.inputs.subject_id = 'subj1'
    >>> nxmetrics.run()                 # doctest: +SKIP
    """
    input_spec = NetworkXMetricsInputSpec
    output_spec = NetworkXMetricsOutputSpec

    def _run_interface(self, runtime):
        global gpickled, nodentwks, edgentwks, kntwks
        gpickled = list()
        nodentwks = list()
        edgentwks = list()
        kntwks = list()
        ntwk = nx.read_gpickle(op.abspath(self.inputs.in_file))

        node_measures = compute_node_measures(ntwk)
        for key in node_measures.keys():
            newntwk = add_node_data(node_measures[key],self.inputs.in_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            nodentwks.append(out_file)
        gpickled.extend(nodentwks)

        edge_measures = compute_edge_measures(ntwk)
        for key in edge_measures.keys():
            newntwk = add_edge_data(edge_measures[key],self.inputs.in_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            edgentwks.append(out_file)
        gpickled.extend(edgentwks)

        ntwk_measures = compute_network_measures(ntwk)
        for key in ntwk_measures.keys():
            if key == 'k_core':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_core, 'pck'))
            if key == 'k_shell':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_shell, 'pck'))
            if key == 'k_crust':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_crust, 'pck'))
            nx.write_gpickle(ntwk_measures[key], out_file)
            kntwks.append(out_file)
        gpickled.extend(kntwks)
        
        out_pickled_extra_measures = op.abspath(self._gen_outfilename(self.inputs.out_pickled_extra_measures, 'pck'))
        dict_measures = compute_dict_measures(ntwk)
        print 'Saving extra measure file to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures))
        file = open(out_pickled_extra_measures, 'w')
        pickle.dump(dict_measures, file)
        file.close()
        
        global dicts
        dicts = list()
        for idx, key in enumerate(dict_measures.keys()):
            for idxd, keyd in enumerate(dict_measures[key].keys()):
                if idxd == 0:
                    nparraykeys = np.array(keyd)
                    nparrayvalues = np.array(dict_measures[key][keyd])
                else:
                    nparraykeys = np.append(nparraykeys,np.array(keyd))
                    values = np.array(dict_measures[key][keyd])
                    nparrayvalues = np.append(nparrayvalues,values)
            nparray = np.vstack((nparraykeys,nparrayvalues))
            out_file = op.abspath(self._gen_outfilename(key, 'mat'))
            npdict = {}
            npdict[key] = nparray
            print np.shape(nparray)
            print type(nparray)
            sio.savemat(out_file, npdict)
            dicts.append(out_file)
        return runtime

    def _list_outputs(self):
        global gpickled
        outputs = self.output_spec().get()
        outputs["k_core"] = op.abspath(self._gen_outfilename(self.inputs.out_k_core, 'pck'))
        outputs["k_shell"] = op.abspath(self._gen_outfilename(self.inputs.out_k_shell, 'pck'))
        outputs["k_crust"] = op.abspath(self._gen_outfilename(self.inputs.out_k_crust, 'pck'))
        outputs["gpickled_network_files"] = gpickled
        outputs["k_networks"] = kntwks
        outputs["node_measure_networks"] = nodentwks
        outputs["edge_measure_networks"] = edgentwks
        outputs["matlab_dict_measures"] = dicts
        outputs["out_pickled_extra_measures"] = op.abspath(self._gen_outfilename(self.inputs.out_pickled_extra_measures, 'pck'))
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext
        
class AverageNetworksInputSpec(TraitedSpec):
    in_networks = InputMultiPath(File(exists=True), mandatory=True, desc='Networks for a group of subjects')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    group_id = traits.Str('group1', usedefault=True, desc='ID for group')
    out_group_average = File('group1_average.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_gpickled_groupavg = File('group1_average.pck', usedefault=True, desc='Group 1 measures saved as a NetworkX .pck')

class AverageNetworksOutputSpec(TraitedSpec):
    out_gpickled_groupavg = File(desc='Average connectome for the group in gpickled format')
    out_group_average = File(desc='Some simple image statistics saved as a Matlab .mat')

class AverageNetworks(BaseInterface):
    input_spec = AverageNetworksInputSpec
    output_spec = AverageNetworksOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
            cmp_config.parcellation_scheme = "NativeFreesurfer"
            ntwk_res_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']

        groupavg = average_networks(self.inputs.in_networks, ntwk_res_file, self.inputs.group_id)
        gpickled.append(groupavg + '.pck')
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_group_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average', 'mat'))
        outputs["out_gpickled_groupavg"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average','pck'))
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext

