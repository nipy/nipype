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
#from cviewer.libs.pyconto.bct import measures as bct
from itertools import combinations as combo
import random
import pickle
from nipype.interfaces.cmtk.bct import perm_test_robust, permutation_test, run_stats, makenetworks
import cmp

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
        subject_dict_measures[subject] = compute_nx_dict_measures(tmp)
    tmp = []    
    for patient in in_group2:
        tmp = nx.read_gpickle(patient)
        patient_measures[patient] = compute_nx_measures(tmp)
        patient_dict_measures[patient] = compute_nx_dict_measures(tmp)
    returnall = run_stats(subject_measures, patient_measures, significance, group_id1, group_id2)
    stats = returnall['p']
    subject_average = returnall['subject_average']
    patient_average = returnall['patient_average']
    returnall = {'stats':stats, 'subject_measures':subject_measures, 'patient_measures':patient_measures, 'subject_average':subject_average,
    'patient_average':patient_average, 'subject_dict_measures':subject_dict_measures, 'patient_dict_measures':patient_dict_measures}
    return returnall

def compute_nx_measures(ntwk):
    print 'Computing NetworkX measures...'
    weighted = True
    measures = {}
    #measures['shortest_path_length'] = nx.shortest_path_length(ntwk, weighted)
    #measures['degree'] = ntwk.degree()
    measures['degree_assortativity'] = nx.degree_assortativity(ntwk)
    measures['degree_pearsonr'] = nx.degree_pearsonr(ntwk)
    #measures['degree_mixing_matrix'] = nx.degree_mixing_matrix(ntwk)
    measures['google_matrix'] = nx.google_matrix(ntwk)
    measures['hub_matrix'] = nx.hub_matrix(ntwk)
    measures['authority_matrix'] = nx.authority_matrix(ntwk)
    #measures['isolates'] = nx.isolates(ntwk) #returning nothing?
    #measures['k_core'] = nx.k_core(ntwk)
    #measures['k_shell'] = nx.k_shell(ntwk) #returns empty
    #measures['k_crust'] = nx.k_crust(ntwk)
    measures['number_connected_components'] = nx.number_connected_components(ntwk)
    measures['transitivity'] = nx.transitivity(ntwk)
    #measures['node_clique_number'] = nx.node_clique_number(ntwk)
    #measures['number_of_cliques'] = nx.number_of_cliques(ntwk)
    measures['graph_clique_number'] = nx.graph_clique_number(ntwk)
    #-----Broken------#
    #measures['average_shortest_path_length'] = nx.average_shortest_path_length(ntwk, weighted) #Keeps saying graph is not connected...
    return measures
    
def compute_nx_dict_measures(ntwk):
    print 'Computing extra NetworkX measures...'
    weighted = True
    dict_measures = {}       
    #----Returns a dictionary---#
    dict_measures['pagerank'] = nx.pagerank(ntwk)
    dict_measures['average_clustering'] = nx.average_clustering(ntwk)
    dict_measures['connected_components'] = nx.connected_components(ntwk) # list of lists, doesn't make sense to do stats
    dict_measures['edge_betweenness_centrality'] = nx.edge_betweenness_centrality(ntwk)
    dict_measures['core_number'] = nx.core_number(ntwk)
    dict_measures['neighbor_connectivity'] = nx.neighbor_connectivity(ntwk)    
    dict_measures['triangles'] = nx.triangles(ntwk)
    dict_measures['clustering'] = nx.clustering(ntwk)
    dict_measures['rich_club_coef'] = nx.rich_club_coefficient(ntwk)
    dict_measures['edge_load'] = nx.edge_load(ntwk)
    dict_measures['betweenness_centrality'] = nx.betweenness_centrality(ntwk)
    dict_measures['degree_centrality'] = nx.degree_centrality(ntwk)    
    dict_measures['closeness_centrality'] = nx.closeness_centrality(ntwk)
    dict_measures['eigenvector_centrality'] = nx.edge_betweenness_centrality(ntwk)
    dict_measures['load_centrality'] = nx.load_centrality(ntwk)
    dict_measures['closeness_vitality'] = nx.closeness_vitality(ntwk,weighted_edges=weighted)
    return dict_measures

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
    out_gexf_network_files = OutputMultiPath(File(desc='Output gexf network files'))
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
        outputs["stats_file"] = op.abspath(self.inputs.out_stats_file)
        outputs["out_gpickled_network_files"] = gpickled
        outputs["out_gexf_network_files"] = gexf
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext
