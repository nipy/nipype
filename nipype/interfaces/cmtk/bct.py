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
import itertools as it
import random
import cmp

def random_combination(iterable, r):
    "Random selection from itertools.combinations(iterable, r)"
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(xrange(n), r))
    return tuple(pool[i] for i in indices)

def mean_difference(all_values, test_values):
    """Difference of means; note that the first list must be the concatenation of
    the two lists (because this is cheaper to work with)."""
    sum_all_values = sum(all_values)
    sum_test_values = sum(test_values)
    mean_test_values = sum_test_values / len(test_values)
    mean_difference = (sum_all_values - sum_test_values) / (len(all_values) - len(test_values))
    mean_difference_from_tested = mean_test_values - mean_difference
    return mean_difference_from_tested

def permutation_test(subject_values, patient_values,iterations=1000):
    print np.shape(subject_values)
    print np.shape(patient_values)
    all_values = np.hstack([subject_values, patient_values])
    #all_values = subject_values.append(patient_values)
    observed = mean_difference(all_values, patient_values)
    below = 0
    combos = []
    combos.append(random_combination(all_values, len(patient_values)))
    for count, permutation in enumerate(range(0,iterations+1)):
        #print "Iteration {idx}".format(idx=count)
        permuted_values = random_combination(all_values, len(patient_values))
        combos.append(permuted_values)
        #Could be randomized better. Right now there is combinatoric replacement...
        meandiff = mean_difference(all_values, permuted_values)
        if meandiff <= observed:
            below += 1

    below = 100. * below / count
    above = 100. - below
    print("Iterations: %d Observed: %.4f Below: %.4f%%, Above: %.4f%%" % (count, observed, below, above))
    print "p(val>obs) < {val}".format(val=above / 100)
    return above / 100

def perm_test_robust(X,Y):
    print 'Running permutation test...'
    #print 'X = {subject_measure}'.format(subject_measure=X)
    #print 'Y = {patient_measure}'.format(patient_measure=Y)
    t = 0
    if len(np.shape(X)) >= 3:
        length = np.shape(X)[1]
        width = np.shape(X)[2]
        p = np.zeros([length,width])
       # print 'Input is a matrix of length {L} and width {W}'.format(L=length,W=width)
        for i in range(0,length):
            for j in range(0,width):
                if i >= j:
                    """The results should all be diagonally symmetric so we only need to compute half of the matrix"""
                    A = []
                    B = []
                    for subject in range(0,np.shape(X)[0]):
                        value = X[subject][i][j]
                        A = np.append(A,value)
                    #    print 'X[subject][i][j] = {val}'.format(val=X[subject][i][j])
                    #print 'Across-subject vector for entry {I},{J} = {vec}'.format(I=i,J=j,vec=A)
                    for patient in range(0,np.shape(Y)[0]):
                        value = Y[patient][i][j]
                        B = np.append(B,value)
                     #   print 'Y[patient][i][j] = {val}'.format(val=Y[patient][i][j])
                    #print 'Across-patient vector for entry {I},{J} = {vec}'.format(I=i,J=j,vec=B)
                 #   p[i][j] = permutation_test(A,B)
                 #   print 'p value for entry {I},{J} = {val}'.format(I=i,J=j,val=p[i][j])
            #print 'p value for input matrices: {val}'.format(val=p)
    elif len(np.shape(X)) == 2: #The input is a vector, per subject
        #print 'Vector per subject'
        length = np.shape(X)[1]
        p = np.zeros(length)
        for i in range(0,length):
            A = []
            B = []
            for subject in range(0,np.shape(X)[0]):
                value = X[subject][i]
                A = np.append(A,value)
          #      print 'X[subject][i] = {val}'.format(val=X[subject][i])
        #    print 'Across-subject vector for entry {I} = {vec}'.format(I=i,vec=A)
            for patient in range(0,np.shape(Y)[0]):
                value = Y[patient][i]
                B = np.append(B,value)
          #      print 'Y[patient][i] = {val}'.format(val=Y[patient][i])
        #    print 'Across-patient vector for entry {I} = {vec}'.format(I=i,vec=B)
            p[i] = permutation_test(A,B)
        #    print 'p value for entry {I} = {val}'.format(I=i, val=p[i])
        #print 't-value for input matrices: {T}'.format(T=t)
    elif len(np.shape(X)) == 1: #The input is a single value, per subject
        #print 'Single-value per subject'
        p = permutation_test(X,Y)
        #print 'p value for measure = {val}'.format(val=p)
    else:
        print 'Single-value per group, cannot run permutation test'
        return
    return p

def ttest2_robust(X,Y):
    """ Compute the two-sided t-statistic of X,Y
    """
    print 'Running two-sample t-test...'
    print 'X = {subject_measure}'.format(subject_measure=X)
    print 'Y = {patient_measure}'.format(patient_measure=Y)
    t = 0
    if len(np.shape(X)) >= 3:
        length = np.shape(X)[1]
        width = np.shape(X)[2]
        t = np.zeros(length)
        print 'Input is a matrix of length {L} and width {W}'.format(L=length,W=width)
        for i in range(0,length):
            for j in range(0,width):
                A = []
                B = []
                for subject in range(0,np.shape(X)[0]):
                    value = X[subject][i][j]
                    A = np.append(A,value)
                    print 'X[subject][i][j] = {val}'.format(val=X[subject][i][j])
                print 'Across-subject vector for entry {I},{J} = {vec}'.format(I=i,J=j,vec=A)
                for patient in range(0,np.shape(Y)[0]):
                    value = Y[patient][i][j]
                    B = np.append(B,value)
                    print 'Y[patient][i][j] = {val}'.format(val=Y[patient][i][j])
                print 'Across-patient vector for entry {I},{J} = {vec}'.format(I=i,J=j,vec=B)
                t[i][j] = np.mean(A) - np.mean(B)
                n1 = len(A) * 1.
                n2 = len(B) * 1.
                s = np.sqrt( ( (n1-1) * np.var(A,ddof=1) + (n2-1)*np.var(B,ddof=1) ) / (n1+n2-2.) )
                t[i][j] = t[i][j] / (s*np.sqrt(1/n1+1/n2))
                print 't-value for entry {I},{J} = {T}'.format(I=i,J=j,T=t[i][j])
        print 't-value for input matrices: {T}'.format(T=t)
    elif len(np.shape(X)) == 2: #The input is a vector, per subject
        print 'Vector per subject'
        length = np.shape(X)[1]
        t = np.zeros(length)
        for i in range(0,length):
            A = []
            B = []
            for subject in range(0,np.shape(X)[0]):
                value = X[subject][i]
                A = np.append(A,value)
                print 'X[subject][i] = {val}'.format(val=X[subject][i])
            print 'Across-subject vector for entry {I} = {vec}'.format(I=i,vec=A)
            for patient in range(0,np.shape(Y)[0]):
                value = Y[patient][i]
                B = np.append(B,value)
                print 'Y[patient][i] = {val}'.format(val=Y[patient][i])
            print 'Across-patient vector for entry {I} = {vec}'.format(I=i,vec=B)
            t[i] = np.mean(A) - np.mean(B)
            n1 = len(A) * 1.
            n2 = len(B) * 1.
            s = np.sqrt( ( (n1-1) * np.var(A,ddof=1) + (n2-1)*np.var(B,ddof=1) ) / (n1+n2-2.) )
            t[i] = t[i] / (s*np.sqrt(1/n1+1/n2))
            print 't-value for entry {I} = {T}'.format(I=i, T=t[i])
        print 't-value for input matrices: {T}'.format(T=t)
    elif len(np.shape(X)) == 1: #The input is a single value, per subject
        print 'Single-value per subject'
        for length in range(0,len(np.shape(X))):
            t = np.mean(X) - np.mean(Y)
            n1 = len(X) * 1.
            n2 = len(Y) * 1.
            s = np.sqrt( ( (n1-1) * np.var(X,ddof=1) + (n2-1)*np.var(Y,ddof=1) ) / (n1+n2-2.) )
            t = t / (s*np.sqrt(1/n1+1/n2))
        print 't-value for measure = {T}'.format(T=t)
    else:
        print 'Single-value per group, cannot run t-test'
        return
    return t

def compute_measures(cmatrix,edgetype='undirected',weighted=True):
    print 'Computing BCT measures'
    # Force subject / patient dimension as first index
    measures = {}
    if edgetype == 'undirected':
        directed = False
    elif edgetype == 'directed':
        directed = True

    degree = bct.degree(cmatrix,directed)
    community_structure = bct.modularity(cmatrix,edgetype)
    #module_degree_zscore = bct.module_degree_zscore(cmatrix,community_structure)
    #participation_coef = bct.participation_coef(cmatrix,community_structure) #binarize cmatrix first?

    #assortativity = bct.assortativity(cmatrix,directed)
    breadthdist = bct.breadthdist(cmatrix)
    reachdist = bct.reachdist(cmatrix)

    distance = bct.distance(cmatrix,weighted)
    # Characteristic path functions run on the distance matrix computed above
    charpath = bct.charpath(distance)
    normalized_path_length = bct.normalized_path_length(distance)
    #normalized_path_length = bct.normalized_path_length(cmatrix)
    charpath_lambda = bct.charpath(distance)
    clustering_coef = bct.clustering_coef(cmatrix,edgetype,weighted)
    density = bct.density(cmatrix,edgetype)
    #edge_betweenness = bct.edge_betweenness(cmatrix,weighted)
    local_efficiency = bct.efficiency(cmatrix,True,edgetype,weighted)
    global_efficiency = bct.efficiency(cmatrix,False,edgetype,weighted)
    #edge_range = bct.erange(cmatrix)
    matching_index = bct.matching_ind(cmatrix)
    modularity = bct.modularity(cmatrix,edgetype)
    motif3funct = bct.motif3funct(cmatrix,weighted)
    motif3struct = bct.motif3struct(cmatrix,weighted)
    number_of_edges = bct.number_of_edges_und(cmatrix)
    strengths = bct.strengths(cmatrix,edgetype)

    measures['community_structure'] = community_structure
    #measures['module_degree_zscore'] = module_degree_zscore
    #measures['participation_coef'] = participation_coef
    #measures['assortativity'] = assortativity
    measures['breadthdist'] = breadthdist
    measures['reachdist'] = reachdist
    measures['distance'] = distance
    measures['charpath'] = charpath
    #measures['normalized_path_length'] = normalized_path_length
    measures['charpath_lambda'] = charpath_lambda
    measures['clustering_coef'] = clustering_coef
    measures['density'] = density
    #measures['edge_betweenness'] = edge_betweenness
    #measures['local_efficiency'] = local_efficiency
    #measures['global_efficiency'] = global_efficiency
    #measures['edge_range'] = edge_range
    measures['matching_index'] = matching_index
    measures['modularity'] = modularity
    measures['motif3funct'] = motif3funct
    measures['motif3struct'] = motif3struct
    measures['number_of_edges'] = number_of_edges
    measures['strengths'] = strengths
    measures['degree'] = degree
    measures['community_structure'] = community_structure
    return measures

def run_bct_stats(subject_measures, patient_measures, significance):
    print 'Running subject-level BCT stats...'
    subject_group_measure = {}
    patient_group_measure = {}
    stats = {}
    number_of_measures = len(subject_measures[subject_measures.keys()[0]].keys())
    for index, measure in enumerate(subject_measures[subject_measures.keys()[0]].keys()):
        tmp = []
        for subject in subject_measures.keys():
                tmp.append(subject_measures[subject][measure])
                subject_group_measure[measure] = tmp
        tmp = []
        for patient in patient_measures.keys():
                tmp.append(patient_measures[patient][measure])
                patient_group_measure[measure] = tmp
        #stats[measure] = ttest2_robust(subject_group_measure[measure], patient_group_measure[measure])
        #print "Subject Group Measure: {metric}".format(metric=measure)
        #print subject_group_measure[measure]

        #print "Patient Group Measure: {metric}".format(metric=measure)
        #print patient_group_measure[measure]

        print "Measure no. {idx} of {N}: {metric}".format(idx=index+1, N=number_of_measures, metric=measure)
        stats[measure] = perm_test_robust(subject_group_measure[measure], patient_group_measure[measure])

        print "p-value for Measure: {metric}".format(metric=measure)
        print stats[measure]
    return stats

def average_networks(in_files, ntwk_res_file, group_id):
    ntwk = init_ntwk(ntwk_res_file)
    Nnodes = len(ntwk.node)
    allntwks = np.zeros((Nnodes,Nnodes),dtype=float)
    for index, subject in enumerate(in_files):
        tmp = sio.loadmat(subject)
        print np.shape(allntwks)
        print np.shape(tmp['cmatrix'])
        allntwks = np.dstack((allntwks, tmp['cmatrix']))
    meanntwk = np.mean(allntwks,2)
    print "Creating average network for group: {grp}".format(grp=group_id)
    network_name = group_id + '_average.pck'
    newdata = []
    for u in range(0,np.shape(meanntwk)[0]):
        for v in range(0,np.shape(meanntwk)[1]):
            newdata = meanntwk[u][v]
            if newdata > 0:
                ntwk.add_edge(u,v)
                ntwk.edge[u][v]['weight'] = newdata
    ntwk = removenodezero(ntwk)
    nx.write_gpickle(ntwk, op.abspath(network_name))
    return op.abspath(network_name)


def group_bct_stats(in_group1,in_group2,significance,output_prefix, ntwk_res_file, subject_ids_group1, subject_ids_group2):
    print 'Running group-level BCT stats...'
    if not ntwk_res_file == 0:
        print 'Network resolution file: {ntwk}'.format(ntwk=ntwk_res_file)
    if not subject_ids_group1 == 0:
        print 'Subject IDs: {subj_IDs}'.format(subj_IDs=subject_ids_group1)
    if not subject_ids_group2 == 0:
        print 'Patient IDs: {patient_IDs}'.format(subj_IDs=subject_ids_group1)
    subject_measures = {}
    patient_measures = {}
    for subject in in_group1:
        tmp = sio.loadmat(subject)
        print tmp['cmatrix']
        subject_measures[subject] = compute_measures(tmp['cmatrix'])
    for patient in in_group2:
        tmp = sio.loadmat(patient)
        print tmp['cmatrix']
        patient_measures[patient] = compute_measures(tmp['cmatrix'])
    stats = run_bct_stats(subject_measures, patient_measures,significance)
    return stats

def init_ntwk(ntwk_res_file):
    gp = nx.read_graphml(ntwk_res_file)
    nROIs = len(gp.nodes())
    initial_network = nx.Graph()
    for u,d in gp.nodes_iter(data=True):
        initial_network.add_node(int(u), d)
    return initial_network

def removenodezero(network):
    if network.has_node(0):
        network.remove_node(0)
    return network

def writenodemeasure(stats, measure, ntwk_res_file):
    print "Node-based measure: {mtrc}".format(mtrc=measure)
    network_name = measure + '_nodes.pck'
    ntwk = init_ntwk(ntwk_res_file)
    newdata = []
    for u,d in ntwk.nodes_iter(data=True):
        newdata = d
        newdata['p-value'] = stats[measure][u-1]
        ntwk.node[u]=newdata
        del newdata
    ntwk = removenodezero(ntwk)
    nx.write_gpickle(ntwk, op.abspath(network_name))
    return network_name

def writeedgemeasure(stats, measure, ntwk_res_file, significance):
    print "Edge-based measure: {mtrc}".format(mtrc=measure)
    network_name = measure + '_edges.pck'
    ntwk = init_ntwk(ntwk_res_file)
    newdata = []
    for u in range(0,np.shape(stats[measure])[0]):
        for v in range(0,np.shape(stats[measure])[1]):
            newdata = stats[measure][u][v]
            if newdata <= significance:
                ntwk.add_edge(u,v)
                ntwk.edge[u][v]['p-value'] = newdata
    ntwk = removenodezero(ntwk)
    nx.write_gpickle(ntwk, op.abspath(network_name))
    return network_name

def makenetworks(stats, ntwk_res_file, significance):
    gp = nx.read_graphml(ntwk_res_file)
    nROIs = len(gp.nodes())
    number_of_measures = len(stats.keys())
    written = []
    ntwk = []
    for index, measure in enumerate(stats.keys()):
        if len(np.shape(stats[measure])) == 1:
            network_name = writenodemeasure(stats, measure, ntwk_res_file)
            print 'Writing metric no. {idx} of {Nmetrics}: {metric} nodes as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=network_name)
            written.append(op.abspath(network_name))
        elif len(np.shape(stats[measure])) == 2 and np.shape(stats[measure])[0] == np.shape(stats[measure])[1] and np.shape(stats[measure])[1] == nROIs:
            network_name = writeedgemeasure(stats, measure, ntwk_res_file, significance)
            print 'Writing metric no. {idx} of {Nmetrics}: {metric} network as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=network_name)
            written.append(op.abspath(network_name))
        else:
            print 'Writing metric no. {idx} of {Nmetrics}: {metric} value into stats file'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure)
    print '{num} networks written: {wrote}'.format(num=len(written),wrote=written)
    return written

class BCTStatsInputSpec(TraitedSpec):
    in_group1 = InputMultiPath(File(exists=True), mandatory=True, desc='Connectivity matrices for group 1')
    in_group2 = InputMultiPath(File(exists=True), mandatory=True, desc='Connectivity matrices for group 2')
    significance = traits.Float(0.05, usedefault=True, desc='Significance threshold (default = 0.05).')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the node will output the statistical maps as networkx graphs.')
    subject_ids_group1 = traits.List(traits.Str, desc='Subject IDs for each input file')
    subject_ids_group2 = traits.List(traits.Str, desc='Subject IDs for each input file')
    output_prefix = traits.Str('bctstats_', usedefault=True, desc='Prefix to append to output files')
    group_id1 = traits.Str('group1', usedefault=True, desc='ID for group 1')
    group_id2 = traits.Str('group2', usedefault=True, desc='ID for group 2')
    out_stats_file = File('BCTstats.mat', usedefault=True, desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')

class BCTStatsOutputSpec(TraitedSpec):
    out_matrix_files = OutputMultiPath(File(desc='Output matrix files'))
    out_network_files = OutputMultiPath(File(desc='Output network files'))
    stats_file = File(desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')
    out_group1avg = File(desc='Average connectome for group 1.')
    out_group2avg = File(desc='Average connectome for group 2.')

class BCTStats(BaseInterface):
    """
    Performs intensity normalization on image intensity given marked ROI images.
    """

    input_spec = BCTStatsInputSpec
    output_spec = BCTStatsOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            #Try to import the Native Freesurfer atlas from the Connectome Mapper
            cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
            cmp_config.parcellation_scheme = "NativeFreesurfer"
            ntwk_res_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']
        if isdefined(self.inputs.subject_ids_group1):
            subject_ids_group1 = self.inputs.subject_ids_group1
        else:
            subject_ids_group1 = 0
        if isdefined(self.inputs.subject_ids_group2):
            subject_ids_group2 = self.inputs.subject_ids_group2
        else:
            subject_ids_group2 = 0

        stats = group_bct_stats(self.inputs.in_group1,self.inputs.in_group2,self.inputs.significance,self.inputs.output_prefix,
            ntwk_res_file, subject_ids_group1, subject_ids_group2)

        out_stats_file = op.abspath(self.inputs.out_stats_file)
        print 'Saving image statistics as {stats}'.format(stats=out_stats_file)
        sio.savemat(out_stats_file, stats)
        print stats
        global out_network_files
        out_network_files = makenetworks(stats, ntwk_res_file, self.inputs.significance)
        global out_group1avg
        global out_group2avg
        out_group1avg = average_networks(self.inputs.in_group1, ntwk_res_file, self.inputs.group_id1)
        out_group2avg = average_networks(self.inputs.in_group2, ntwk_res_file, self.inputs.group_id2)
        out_network_files.append(out_group1avg)
        out_network_files.append(out_group2avg)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        out_matrix_list = []
        out_network_list = []
        for idx, in_file in enumerate(self.inputs.in_group1):
            _, name, _ = split_filename(in_file)
            if isdefined(self.inputs.subject_ids_group1):
                name = op.abspath(self.inputs.output_prefix + self.inputs.subject_ids_group1[idx] + name)
            else:
                name = op.abspath(self.inputs.output_prefix + name)

            out_matrix_list.append(name + '.mat')
        outputs["out_matrix_files"] = list_to_filename(out_matrix_list)
        outputs["out_network_files"] = out_network_files

        out_stats_file = op.abspath(self.inputs.out_stats_file)
        outputs["stats_file"] = out_stats_file
        return outputs
