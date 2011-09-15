from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec, Directory, InputMultiPath, OutputMultiPath
import re
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile, list_to_filename
import os, os.path as op
import numpy as np
import nibabel as nb
import networkx as nx
from nipype.utils.misc import isdefined
import sys
import scipy.io as sio
from itertools import combinations as combo
import random
import pickle
from nipype.interfaces.cmtk.bct import perm_test_robust, permutation_test, run_stats, makenetworks
import cmp

def remove_all_edges(ntwk):
    ntwktmp = ntwk.copy()
    edges = ntwktmp.edges_iter()
    for edge in edges:
        ntwk.remove_edge(edge[0],edge[1])
    return ntwk

def compute_node_measures(ntwk):
    """
    These return node-based measures
    """
    print 'Computing node measures...'
    weighted = True
    measures = {}
    print 'Computing degree...'
    measures['degree'] = np.array(ntwk.degree().values())
    print 'Computing number of cliques for each node...'
    measures['number_of_cliques'] = np.array(nx.number_of_cliques(ntwk).values())
    print 'Computing load centrality...'
    measures['load_centrality'] = np.array(nx.load_centrality(ntwk).values())
    print 'Computing betweenness centrality...'
    measures['betweenness_centrality'] = np.array(nx.betweenness_centrality(ntwk).values())
    print 'Computing degree centrality...'
    measures['degree_centrality'] = np.array(nx.degree_centrality(ntwk).values())
    print 'Computing closeness centrality...'
    measures['closeness_centrality'] = np.array(nx.closeness_centrality(ntwk).values())
    print 'Computing eigenvector centrality...'
    measures['eigenvector_centrality'] = np.array(nx.eigenvector_centrality(ntwk).values())
    print 'Calculating node clique number'
    measures['node_clique_number'] = np.array(nx.node_clique_number(ntwk).values())
    print 'Computing pagerank...'
    measures['pagerank'] = np.array(nx.pagerank(ntwk).values())
    print 'Computing triangles...'
    measures['triangles'] = np.array(nx.triangles(ntwk).values())
    print 'Computing clustering...'
    measures['clustering'] = np.array(nx.clustering(ntwk).values())
    #print 'Computing closeness vitality...'
    #measures['closeness_vitality'] = np.array(nx.closeness_vitality(ntwk,weighted_edges=weighted).values())
    print 'Identifying network isolates'
    measures['isolates'] = nx.isolates(ntwk)
    binarized = np.zeros((ntwk.number_of_nodes(),1))
    for value in measures['isolates']:
        value = value - 1 # Zero indexing
        binarized[value] = 1
    measures['isolates'] = binarized
    print 'Computing k-core number'
    measures['core_number'] = np.array(nx.core_number(ntwk).values())
    return measures

def compute_edge_measures(ntwk):
    """
    These return edge-based measures
    """
    print 'Computing edge measures...'
    weighted = True
    measures = {}
    #print 'Computing google matrix...' #Makes really large networks (500k+ edges)
    #measures['google_matrix'] = nx.google_matrix(ntwk)
    print 'Computing hub matrix...'
    measures['hub_matrix'] = nx.hub_matrix(ntwk)
    print 'Computing authority matrix...'
    measures['authority_matrix'] = nx.authority_matrix(ntwk)
    """
    These return other sized arrays
    """
    #dict_measures['degree_mixing_matrix'] = nx.degree_mixing_matrix(ntwk)
    return measures
    
def compute_dict_measures(ntwk):
    """
    Returns a dictionary
    """
    print 'Computing single valued measures...'
    weighted = True
    measures = {}
    #print 'Computing connected components...'
    #measures['connected_components'] = nx.connected_components(ntwk) # list of lists, doesn't make sense to do stats
    #print 'Computing neighbour connectivity...'
    #measures['neighbor_connectivity'] = nx.neighbor_connectivity(ntwk)    
    #print 'Computing rich club coefficient...'
    #measures['rich_club_coef'] = nx.rich_club_coefficient(ntwk)
    #print 'Computing edge load...'
    #measures['edge_load'] = nx.edge_load(ntwk)
    #print 'Computing betweenness centrality...'
    #measures['edge_betweenness_centrality'] = nx.edge_betweenness_centrality(ntwk)
    #print 'Computing shortest path length for each node...'
    #measures['shortest_path_length'] = np.array(nx.shortest_path_length(ntwk, weighted).values())
    return measures

def compute_singlevalued_measures(ntwk):
    """
    Returns a single value per network
    """
    print 'Computing single valued measures...'
    weighted = True
    measures = {}
    print 'Computing degree assortativity (pearson number) ...'
    measures['degree_pearsonr'] = nx.degree_pearsonr(ntwk)
    print 'Computing degree assortativity...'
    measures['degree_assortativity'] = nx.degree_assortativity(ntwk)
    #print 'Computing transitivity...'
    #measures['transitivity'] = nx.transitivity(ntwk)
    print 'Computing number of connected_components...'
    measures['number_connected_components'] = nx.number_connected_components(ntwk)
    
    #print 'Computing average clustering...'
    #measures['average_clustering'] = nx.average_clustering(ntwk)
    
    #print 'Computing graph clique number...'
    #measures['graph_clique_number'] = nx.graph_clique_number(ntwk)
    #print 'Calculating average shortest path length...'
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

def group_nx_stats(in_group1,in_group2,significance,output_prefix, group_id1, group_id2, subject_ids_group1, subject_ids_group2):
    print 'Running group-level NetworkX stats...'
    if not subject_ids_group1 == 0:
        print 'Subject IDs: {subj_IDs}'.format(subj_IDs=subject_ids_group1)
    if not subject_ids_group2 == 0:
        print 'Patient IDs: {patient_IDs}'.format(subj_IDs=subject_ids_group1)
    subject_measures = {}
    patient_measures = {}
    subject_dict_measures = {}
    patient_dict_measures = {}

    tmp = []
    for subject in in_group1:
        tmp = nx.read_gpickle(subject)
        subject_measures[subject] = compute_nx_measures(tmp)
        subject_dict_measures[subject] = compute_dict_measures(tmp)
                
    tmp = []    
    for patient in in_group2:
        tmp = nx.read_gpickle(patient)
        patient_measures[patient] = compute_nx_measures(tmp)
        patient_dict_measures[patient] = compute_dict_measures(tmp)
    
    returnall = run_stats(subject_measures, patient_measures, significance, group_id1, group_id2)
    stats = returnall['p']
    subject_average = returnall['subject_average']
    patient_average = returnall['patient_average']
    returnall = {'stats':stats, 'subject_measures':subject_measures, 'patient_measures':patient_measures, 'subject_average':subject_average,
    'patient_average':patient_average, 'subject_dict_measures':subject_dict_measures, 'patient_dict_measures':patient_dict_measures}
    return returnall

class NetworkXStatsInputSpec(TraitedSpec):
    in_group1 = InputMultiPath(File(exists=True), mandatory=True, desc='Networks for group 1')
    in_group2 = InputMultiPath(File(exists=True), mandatory=True, desc='Networks for group 2')
    significance = traits.Float(0.05, usedefault=True, desc='Significance threshold (default = 0.05).')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    subject_ids_group1 = traits.List(traits.Str, desc='Subject IDs for each input file')
    subject_ids_group2 = traits.List(traits.Str, desc='Subject IDs for each input file')
    output_prefix = traits.Str('nxstats_', usedefault=True, desc='Prefix to append to output files')
    group_id1 = traits.Str('group1', usedefault=True, desc='ID for group 1')
    group_id2 = traits.Str('group2', usedefault=True, desc='ID for group 2')
    out_stats_file = File('nxstats.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')
    out_group1_average = File('group1_average.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_group2_average = File('group2_average.mat', usedefault=True, desc='Group 2 measures saved as a Matlab .mat')
    out_group1_measures = File('group1_measures.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_group2_measures = File('group2_measures.mat', usedefault=True, desc='Group 2 measures saved as a Matlab .mat')
    out_pickled_extra_measures_group1 = File('group1_extra_measures.pck', usedefault=True, desc='Network measures for group 1 that return dictionaries stored as a Pickle.')
    out_pickled_extra_measures_group2 = File('group2_extra_measures.pck', usedefault=True, desc='Network measures for group 2 that return dictionaries stored as a Pickle.')

class NetworkXStatsOutputSpec(TraitedSpec):
    stats_file = File(desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')
    out_gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    out_gpickled_group1avg = File(desc='Average connectome for group 1 in gpickled format')
    out_gpickled_group2avg = File(desc='Average connectome for group 2 in gpickled format')
    out_gexf_network_files = OutputMultiPath(File(desc='Output gexf network files'))
    out_gexf_group1avg = File(desc='Average connectome for group 1 in gexf format (for Gephi)')
    out_gexf_group2avg = File(desc='Average connectome for group 2 in gexf format (for Gephi)')
    out_group1_measures = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_group2_measures = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_group1_average = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_group2_average = File(desc='Some simple image statistics saved as a Matlab .mat')
    out_pickled_extra_measures_group1 = File(desc='Network measures for group 1 that return dictionaries stored as a Pickle.')
    out_pickled_extra_measures_group2 = File(desc='Network measures for group 2 that return dictionaries stored as a Pickle.')

class NetworkXStats(BaseInterface):
    input_spec = NetworkXStatsInputSpec
    output_spec = NetworkXStatsOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.subject_ids_group1):
            subject_ids_group1 = self.inputs.subject_ids_group1
        else:
            subject_ids_group1 = 0
        if isdefined(self.inputs.subject_ids_group2):
            subject_ids_group2 = self.inputs.subject_ids_group2
        else:
            subject_ids_group2 = 0

        returnall = group_nx_stats(self.inputs.in_group1, self.inputs.in_group2, self.inputs.significance,
        self.inputs.output_prefix, self.inputs.group_id1, self.inputs.group_id2, subject_ids_group1, subject_ids_group2)

        stats = returnall['stats']
        subject_measures = returnall['subject_measures']
        patient_measures = returnall['patient_measures']
        subject_average = returnall['subject_average']
        patient_average = returnall['patient_average']
        subject_dict_measures = returnall['subject_dict_measures']
        patient_dict_measures = returnall['patient_dict_measures']

        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
            cmp_config.parcellation_scheme = "NativeFreesurfer"
            ntwk_res_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']
        global gpickled
        global gexf
        gpickled, gexf = makenetworks(stats, subject_average, patient_average, ntwk_res_file, 
        self.inputs.significance, self.inputs.group_id1, self.inputs.group_id2)

        out_stats_file = op.abspath(self.inputs.out_stats_file)
        out_subject_measures = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_measures', 'mat'))
        out_patient_measures = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_measures', 'mat'))
        out_subject_average = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_average', 'mat'))
        out_patient_average = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_average', 'mat'))
        out_pickled_extra_measures_group1 = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_extra_measures', 'pck'))
        out_pickled_extra_measures_group2 = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_extra_measures', 'pck'))
        print 'Saving image statistics as {stats}'.format(stats=out_stats_file)
        sio.savemat(out_stats_file, stats)
        print 'Saving subject measures as {file}'.format(file=out_subject_measures)
        sio.savemat(out_subject_measures, subject_measures)
        print 'Saving patient measures as {file}'.format(file=out_patient_measures)
        sio.savemat(out_patient_measures, patient_measures)
        print 'Saving subject average as {file}'.format(file=out_subject_average)
        sio.savemat(out_subject_average, subject_average)
        print 'Saving patient average as {file}'.format(file=out_patient_average)
        sio.savemat(out_patient_average, patient_average)
        print 'Saving extra measure File for group 1 to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures_group1))
        file = open(out_pickled_extra_measures_group1, 'w')
        pickle.dump(subject_dict_measures, file)
        file.close()
        print 'Saving extra measure File for group 2 to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures_group2))
        file = open(out_pickled_extra_measures_group2, 'w')
        pickle.dump(patient_dict_measures, file)
        file.close()
        return runtime

    def _list_outputs(self):
        global gpickled
        global gexf
        outputs = self.output_spec().get()
        outputs["out_group1_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_measures', 'mat'))
        outputs["out_group2_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_measures', 'mat'))
        outputs["out_group1_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_average', 'mat'))
        outputs["out_group2_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_average', 'mat'))
        outputs["out_pickled_extra_measures_group1"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_extra_measures', 'pck'))
        outputs["out_pickled_extra_measures_group2"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_extra_measures', 'pck'))
        outputs["out_gpickled_group1avg"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_average','pck'))
        outputs["out_gpickled_group2avg"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_average','pck'))
        outputs["out_gexf_group1avg"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_average','gexf'))
        outputs["out_gexf_group2avg"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_average','gexf'))
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
    path, name, ext = split_filename(ntwk)
    if ext == '.pck':
        ntwk = nx.read_gpickle(ntwk)
    elif ext == '.graphml':
        ntwk = nx.read_graphml(ntwk)
    node_ntwk = ntwk.copy()
    newdata = {}
    for idx, data in ntwk.nodes_iter(data=True):
        idx = idx - 1
        newdata['value'] = node_array[idx]
        data.update(newdata)
        node_ntwk.node[idx] = data
    return node_ntwk

def add_edge_data(edge_array, ntwk):
    path, name, ext = split_filename(ntwk)
    if ext == '.pck':
        ntwk = nx.read_gpickle(ntwk)
    elif ext == '.graphml':
        ntwk = nx.read_graphml(ntwk)
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
    subject_id = traits.Str(desc='Subject ID for the input network')
    out_k_core = File('k_core', usedefault=True, desc='Computed k-core network stored as a NetworkX pickle.')
    out_k_shell = File('k_shell', usedefault=True, desc='Computed k-shell network stored as a NetworkX pickle.')
    out_k_crust = File('k_crust', usedefault=True, desc='Computed k-crust network stored as a NetworkX pickle.')

class NetworkXMetricsOutputSpec(TraitedSpec):
    gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    k_core = File(desc='Computed k-core network stored as a NetworkX pickle.')
    k_shell = File(desc='Computed k-shell network stored as a NetworkX pickle.')
    k_crust = File(desc='Computed k-crust network stored as a NetworkX pickle.')

class NetworkXMetrics(BaseInterface):
    input_spec = NetworkXMetricsInputSpec
    output_spec = NetworkXMetricsOutputSpec

    def _run_interface(self, runtime):
        global gpickled
        gpickled = list()
        ntwk = nx.read_gpickle(op.abspath(self.inputs.in_file))
        #ntwk_res_file = nx.read_gpickle(self.inputs.resolution_network_file)

        node_measures = compute_node_measures(ntwk)
        for key in node_measures.keys():
            newntwk = add_node_data(node_measures[key],self.inputs.in_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            gpickled.append(out_file)

        edge_measures = compute_edge_measures(ntwk)          
        for key in edge_measures.keys():
            newntwk = add_edge_data(edge_measures[key],self.inputs.in_file)
            out_file = op.abspath(self._gen_outfilename(key, 'pck'))
            nx.write_gpickle(newntwk, out_file)
            gpickled.append(out_file)

        ntwk_measures = compute_network_measures(ntwk)
        for key in ntwk_measures.keys():
            if key == 'k_core':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_core, 'pck'))
            if key == 'k_shell':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_shell, 'pck'))
            if key == 'k_crust':
                out_file = op.abspath(self._gen_outfilename(self.inputs.out_k_crust, 'pck'))
            nx.write_gpickle(ntwk_measures[key], out_file)
            gpickled.append(out_file)
           
        return runtime

    def _list_outputs(self):
        global gpickled
        outputs = self.output_spec().get()
        outputs["k_core"] = op.abspath(self._gen_outfilename(self.inputs.out_k_core, 'pck'))
        outputs["k_shell"] = op.abspath(self._gen_outfilename(self.inputs.out_k_shell, 'pck'))
        outputs["k_crust"] = op.abspath(self._gen_outfilename(self.inputs.out_k_crust, 'pck'))
        outputs["gpickled_network_files"] = gpickled
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext
