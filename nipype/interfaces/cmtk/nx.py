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
from cviewer.libs.pyconto.bct import measures as bct
from itertools import combinations as combo
import random
import pickle
from nipype.interfaces.cmtk.bct import perm_test_robust, permutation_test, run_stats

def run_nx_stats(subject_measures, patient_measures, significance, group_id1, group_id2):
    """
    This function takes in two dictionaries and a float. The subject and patient dictionaries
    are are keyed by the subject measure id (i.e. 'degree') and 
    """
    print 'Running subject-level stats...'
    p = subject_average = patient_average = minA = minB = maxA = maxB = stdA = stdB = {}
    subject_group_measure = patient_group_measure = {}
    measure_list = subject_measures[subject_measures.keys()[0]].keys()
    number_of_measures = len(measure_list)
    subject_list = subject_measures.keys()
    patient_list = patient_measures.keys()
    print measure_list
    for index, measure in enumerate(measure_list):
        print measure
        tmp = []
        for subject in subject_list:
            tmp.append(subject_measures[subject][measure])
        subject_group_measure[measure] = tmp
        tmp = []
        for patient in patient_list:
            tmp.append(patient_measures[patient][measure])
        patient_group_measure[measure] = tmp
        print "Measure no. {idx} of {N}: {metric}".format(idx=index+1, N=number_of_measures, metric=measure)
        [p[measure], subject_average[measure], patient_average[measure], minA[measure], minB[measure],
            maxA[measure], maxB[measure], stdA[measure], stdB[measure]] = perm_test_robust(
                        subject_group_measure[measure], patient_group_measure[measure])
        print "p-value for Measure: {metric}".format(metric=measure)
        print p[measure]
    return p, subject_average, patient_average

def group_nx_stats(in_group1,in_group2,significance,output_prefix, group_id1, group_id2, subject_ids_group1, subject_ids_group2):
    print 'Running group-level NetworkX stats...'
    if not subject_ids_group1 == 0:
        print 'Subject IDs: {subj_IDs}'.format(subj_IDs=subject_ids_group1)
    if not subject_ids_group2 == 0:
        print 'Patient IDs: {patient_IDs}'.format(subj_IDs=subject_ids_group1)
    subject_measures = patient_measures = subject_dict_measures = patient_dict_measures = {}
    tmp = []
    for subject in in_group1:
        tmp = nx.read_gpickle(subject)
        subject_measures[subject] = compute_nx_measures(tmp)
        #subject_dict_measures[subject] = compute_nx_dict_measures(tmp)
    tmp = []    
    for patient in in_group2:
        tmp = nx.read_gpickle(patient)
        patient_measures[patient] = compute_nx_measures(tmp)
        #patient_dict_measures[patient] = compute_nx_dict_measures(tmp)
        
    stats, subject_average, patient_average = run_nx_stats(subject_measures, patient_measures, significance, group_id1, group_id2)
    return stats, subject_measures, patient_measures, subject_average, patient_average, subject_dict_measures, patient_dict_measures

def compute_nx_measures(ntwk):
    print 'Computing NetworkX measures...'
    weighted = True
    measures = {}
    #measures['shortest_path_length'] = nx.shortest_path_length(ntwk, weighted)
    measures['degree'] = ntwk.degree()
    measures['degree_assortativity'] = nx.degree_assortativity(ntwk)
    measures['degree_pearsonr'] = nx.degree_pearsonr(ntwk)
    measures['degree_mixing_matrix'] = nx.degree_mixing_matrix(ntwk)
    measures['pagerank'] = nx.pagerank(ntwk)
    measures['google_matrix'] = nx.google_matrix(ntwk)
    measures['hub_matrix'] = nx.hub_matrix(ntwk)
    measures['authority_matrix'] = nx.authority_matrix(ntwk)
    measures['isolates'] = nx.isolates(ntwk)
    measures['k_core'] = nx.k_core(ntwk)
    #measures['k_shell'] = nx.k_shell(ntwk) #returns empty
    measures['k_crust'] = nx.k_crust(ntwk)
    measures['number_connected_components'] = nx.number_connected_components(ntwk)
    measures['transitivity'] = nx.transitivity(ntwk)
    #measures['node_clique_number'] = nx.node_clique_number(ntwk)
    measures['number_of_cliques'] = nx.number_of_cliques(ntwk)
    measures['graph_clique_number'] = nx.graph_clique_number(ntwk)
    #-----Broken------#
    #measures['average_shortest_path_length'] = nx.average_shortest_path_length(ntwk, weighted) #Keeps saying graph is not connected...
    return measures
    
def compute_nx_dict_measures(ntwk):
    print 'Computing extra NetworkX measures...'
    weighted = True
    dict_measures = {}       
    #----Returns a dictionary---#
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
    subject_ids_group1 = traits.List(traits.Str, desc='Subject IDs for each input file')
    subject_ids_group2 = traits.List(traits.Str, desc='Subject IDs for each input file')
    output_prefix = traits.Str('nxstats_', usedefault=True, desc='Prefix to append to output files')
    group_id1 = traits.Str('group1', usedefault=True, desc='ID for group 1')
    group_id2 = traits.Str('group2', usedefault=True, desc='ID for group 2')
    out_stats_file = File('nxstats.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')
    out_group1_measures_file = File('group1.mat', usedefault=True, desc='Group 1 measures saved as a Matlab .mat')
    out_group2_measures_file = File('group2.mat', usedefault=True, desc='Group 2 measures saved as a Matlab .mat')
    out_pickled_extra_measures_group1 = File('group1.pck', usedefault=True, desc='Network measures for group 1 that return dictionaries stored as a Pickle.')
    out_pickled_extra_measures_group2 = File('group1.pck', usedefault=True, desc='Network measures for group 2 that return dictionaries stored as a Pickle.')

class NetworkXStatsOutputSpec(TraitedSpec):
    out_matrix_files = OutputMultiPath(File(desc='Output matrix files'))
    stats_file = File(desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')
    out_gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    out_gpickled_group1avg = File(desc='Average connectome for group 1 in gpickled format')
    out_gpickled_group2avg = File(desc='Average connectome for group 2 in gpickled format')
    out_gexf_network_files = OutputMultiPath(File(desc='Output gexf network files'))
    out_gexf_group1avg = File(desc='Average connectome for group 1 in gexf format (for Gephi)')
    out_gexf_group2avg = File(desc='Average connectome for group 2 in gexf format (for Gephi)')
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

        stats, subject_measures, patient_measures, subject_average, patient_average, subject_dict_measures, patient_dict_measures = group_nx_stats(self.inputs.in_group1, self.inputs.in_group2, self.inputs.significance, 
            self.inputs.output_prefix, self.inputs.group_id1, self.inputs.group_id2, subject_ids_group1, subject_ids_group2)

        global out_subject_measures, out_patient_measures
        global out_subject_average, out_patient_average
        out_stats_file = op.abspath(self.inputs.out_stats_file)
        out_subject_measures = op.abspath(self.inputs.group_id1 + '_measures.mat')
        out_patient_measures = op.abspath(self.inputs.group_id2 + '_measures.mat')
        out_subject_average = op.abspath(self.inputs.group_id1 + '_average.mat')
        out_patient_average = op.abspath(self.inputs.group_id2 + '_average.mat')
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
        print stats
        global out_gpickled_network_files, out_gexf_network_files
        global out_gpickled_group1avg, out_gexf_group1avg
        global out_gpickled_group2avg, out_gexf_group2avg
        out_gpickled_network_files, out_gexf_network_files = makenetworks(stats, subject_average, 
            patient_average, ntwk_res_file, self.inputs.significance, self.inputs.group_id1, self.inputs.group_id2)
        global out_pickled_extra_measures_group1, out_pickled_extra_measures_group2      
        out_pickled_extra_measures_group1 = os.abspath(self.inputs.group_id1 + '_extra_measures.pck')
        out_pickled_extra_measures_group2 = os.abspath(self.inputs.group_id2 + '_extra_measures.pck')
        print 'Saving extra measure File for group 1 to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures_group1))
        file = open(os.path.abspath(out_pickled_extra_measures_group1), 'w')
        pickle.dump(labelDict, file)
        file.close()
        print 'Saving extra measure File for group 2 to {path} in Pickle format'.format(path=os.path.abspath(out_pickled_extra_measures_group2))
        file = open(os.path.abspath(out_pickled_extra_measures_group2), 'w')
        pickle.dump(labelDict, file)
        file.close()
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_gpickled_network_files"] = out_gpickled_network_files
        outputs["out_gexf_network_files"] = out_gexf_network_files
        outputs["out_pickled_extra_measures_group1"] = out_pickled_extra_measures_group1
        outputs["out_pickled_extra_measures_group2"] = out_pickled_extra_measures_group2
        out_stats_file = op.abspath(self.inputs.out_stats_file)
        outputs["stats_file"] = out_stats_file
        return outputs
