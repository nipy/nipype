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
    """
    Random selection from itertools.combinations(iterable, r)
    Uses the itertools module to pick a random combination of length r
    using the given input values (as an iterable)
    See http://docs.python.org/library/itertools.html
    """
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(xrange(n), r))
    return tuple(pool[i] for i in indices)

def mean_difference(all_values, test_values):
    """Difference of means; note that the first list must be the concatenation of
    the two lists (because this is cheaper to work with).
    See http://rosettacode.org/wiki/Permutation_test and
    """
    sum_all_values = sum(all_values)
    sum_test_values = sum(test_values)
    mean_test_values = sum_test_values / len(test_values)
    mean_difference = (sum_all_values - sum_test_values) / (len(all_values) - len(test_values))
    mean_difference_from_tested = mean_test_values - mean_difference
    return mean_difference_from_tested

def average_measure(subject_values):
    average = np.mean(subject_values)
    min = np.min(subject_values)
    max = np.max(subject_values)
    deviation = np.std(subject_values)
    returnavg = {}
    returnavg['avg'] = average
    returnavg['min'] = min
    returnavg['max'] = max
    returnavg['std'] = deviation
    return returnavg

def permutation_test(subject_values, patient_values,iterations=1000):
    """ Permutation test
    See http://rosettacode.org/wiki/Permutation_test and
        http://docs.python.org/library/itertools.html
    """
    all_values = np.hstack([subject_values, patient_values])
    observed = mean_difference(all_values, patient_values)
    below = 0
    combos = []
    combos.append(random_combination(all_values, len(patient_values)))
    for count in range(1,iterations+1):
        permuted_values = random_combination(all_values, len(patient_values))
        combos.append(permuted_values)
        #Could be randomized better. Right now there is combinatoric replacement...
        meandiff = mean_difference(all_values, permuted_values)
        if meandiff <= observed:
            below += 1
    below = below * 100. / count
    above = 100. - below
    print("Iterations: %d Observed: %.2f Below: %.2f%%, Above: %.2f%%" % (count, observed, below, above))
    print "p(val>obs) < {val}".format(val=above / 100)
    return above / 100

def perm_test_robust(X,Y):
    """ Runs a permutation test across the two input matrices X and Y.
    This function is used to computer the permutation test for each node / edge in the matrix.
    This means that X and Y can be vectors or matrices and the permutation will be run across
    the two groups X and Y at each index of the input. X and Y must be the same shape.
    """
    print 'Running permutation test and averaging...'
    t = 0
    X = np.array(X)
    Y = np.array(Y)
    print np.shape(X)
    X = np.squeeze(X)
    Y = np.squeeze(Y)
    print np.shape(X)
    if len(np.shape(X)) >= 3:
        n = max(np.shape(X))
        X = np.reshape(X, (n, n, -1))
        Y = np.reshape(Y, (n, n, -1))
        print np.shape(X)
        length = np.shape(X)[0]
        width = np.shape(X)[1]
        Nsubjects = np.shape(X)[2]
        Npatients = np.shape(Y)[2]
        p = np.zeros([length,width])
        avgA = np.zeros([length,width])
        avgB = np.zeros([length,width])
        minA = np.zeros([length,width])
        minB = np.zeros([length,width])
        maxA = np.zeros([length,width])
        maxB = np.zeros([length,width])
        stdA = np.zeros([length,width])
        stdB = np.zeros([length,width])
        print 'Input is a matrix of length {L} and width {W}'.format(L=length,W=width)
        for i in range(0,length):
            for j in range(0,width):
                if j >= i:
                    """The results should all be diagonally symmetric so we only need to compute half of the matrix"""
                    print i
                    print j
                    A = []
                    B = []
                    for subject in range(0,Nsubjects):
                        value = X[i][j][subject]
                        A = np.append(A,value)
                    for patient in range(0,Npatients):
                        value = Y[i][j][patient]
                        B = np.append(B,value)
                    p[i][j] = permutation_test(A,B)
                    returnavgA = average_measure(A)
                    returnavgB = average_measure(B)
                    avgA[i][j] = returnavgA['avg']
                    avgB[i][j] = returnavgB['avg']
                    minA[i][j] = returnavgA['min']
                    minB[i][j] = returnavgB['min']
                    maxA[i][j] = returnavgA['max']
                    maxB[i][j] = returnavgB['max']
                    stdA[i][j] = returnavgA['std']
                    stdB[i][j] = returnavgB['std']
    elif len(np.shape(X)) == 2 and not np.shape(X)[1] == 0 or np.shape(X)[0] == 0: #The input is a vector, per subject
        n = max(np.shape(X))
        print n
        X = np.reshape(X, (n, -1))
        Y = np.reshape(Y, (n, -1))
        length = np.shape(X)[0]
        Nsubjects = np.shape(X)[1]
        Npatients = np.shape(Y)[1]
        print np.shape(X)
        length = np.shape(X)[0]
        p = np.zeros(length)
        avgA = np.zeros(length)
        avgB = np.zeros(length)
        minA = np.zeros(length)
        minB = np.zeros(length)
        maxA = np.zeros(length)
        maxB = np.zeros(length)
        stdA = np.zeros(length)
        stdB = np.zeros(length)
        for i in range(0,length):
            A = []
            B = []
            for subject in range(0,Nsubjects):
                value = X[i][subject]
                A = np.append(A,value)
            for patient in range(0,Npatients):
                value = Y[i][patient]
                B = np.append(B,value)
            p[i] = permutation_test(A,B)
            returnavgA = average_measure(A)
            returnavgB = average_measure(B)
            avgA[i] = returnavgA['avg']
            avgB[i] = returnavgB['avg']
            minA[i] = returnavgA['min']
            minB[i] = returnavgB['min']
            maxA[i] = returnavgA['max']
            maxB[i] = returnavgB['max']
            stdA[i] = returnavgA['std']
            stdB[i] = returnavgB['std']
    elif len(np.shape(X)) == 1: #The input is a single value, per subject
        p = permutation_test(X,Y)
        returnavgA = average_measure(X)
        returnavgB = average_measure(Y)
        avgA = returnavgA['avg']
        avgB = returnavgB['avg']
        minA = returnavgA['min']
        minB = returnavgB['min']
        maxA = returnavgA['max']
        maxB = returnavgB['max']
        stdA = returnavgA['std']
        stdB = returnavgB['std']
    else:
        print 'Single-value per group, cannot run permutation test'
        return
    returnall = {}
    returnall['p'] = p
    returnall['avgA'] = avgA
    returnall['avgB'] = avgB
    #returnall = {'p':p,'avgA':avgA,'avgB':avgB,'minA':minA,'minB':minB,'maxB':maxB,'stdA':stdA,'stdB':stdB}
    return returnall

def compute_measures(cmatrix, ntwk_res_file, edgetype='undirected', weighted=True):
    print 'Computing BCT measures'
    measures = {}
    if edgetype == 'undirected':
        directed = False
    elif edgetype == 'directed':
        directed = True

    measures['degree'] = bct.degree(cmatrix,directed)
    measures['community_structure'] = community_structure = bct.modularity(cmatrix,edgetype)
    #measures['breadthdist'] = breadthdist = bct.breadthdist(cmatrix) #all zeros
    #measures['reachdist'] = reachdist = bct.reachdist(cmatrix) #all zeros
    #measures['matching_index'] = bct.matching_ind(cmatrix)  #all zeros

    # Characteristic path functions run on the distance matrix computed above
    measures['distance'] = bct.distance(cmatrix,weighted)
    measures['charpath'] = bct.charpath(measures['distance'])
    measures['normalized_path_length'] = bct.normalized_path_length(measures['distance'])
    measures['charpath_lambda'] = bct.charpath(measures['distance'])

    measures['clustering_coef'] = bct.clustering_coef(cmatrix,edgetype,weighted)
    measures['density'] = bct.density(cmatrix,edgetype)
    measures['modularity'] = bct.modularity(cmatrix,edgetype)
    #measures['motif3funct'] = bct.motif3funct(cmatrix,weighted) #weird shape
    #measures['motif3struct'] = bct.motif3struct(cmatrix,weighted) #weird shape
    measures['number_of_edges'] = bct.number_of_edges_und(cmatrix)
    measures['strengths'] = bct.strengths(cmatrix,edgetype)
    measures['edge_weight'] = cmatrix

    #---------------None of these seem to work!---------------#
    #measures['module_degree_zscore'] = bct.module_degree_zscore(cmatrix,community_structure) #broken?
    #measures['participation_coef'] = bct.participation_coef(cmatrix,community_structure) #binarize cmatrix first?
    #measures['assortativity'] = bct.assortativity(cmatrix,directed) #broken!
    #measures['edge_betweenness'] = bct.edge_betweenness(cmatrix,weighted) #broken
    #measures['local_efficiency'] = bct.efficiency(cmatrix,True,edgetype,weighted) #broken ?
    #measures['global_efficiency'] = bct.efficiency(cmatrix,False,edgetype,weighted) # seg fault
    #measures['edge_range'] = bct.erange(cmatrix)
    return measures

def run_stats(subject_measures, patient_measures, significance, group_id1, group_id2):
    """
    This function takes in two dictionaries and a float. The subject and patient dictionaries
    are are keyed by the subject measure id (i.e. 'degree') and
    """
    print 'Running subject-level stats...'
    p = {}
    subject_average = {}
    patient_average = {}
    minA = {}
    minB = {}
    maxA = {}
    maxB = {} 
    stdA = {}
    stdB = {}
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
        returnall = perm_test_robust(subject_group_measure[measure],patient_group_measure[measure])
        p[measure] = returnall['p']
        print "p-value for Measure: {metric}".format(metric=measure)
        print p[measure]
        subject_average[measure] = returnall['avgA']
        patient_average[measure] = returnall['avgB']
        del returnall
    returnall = {'p':p, 'subject_average':subject_average, 
    'patient_average':patient_average}
    print returnall
    return returnall

def average_networks(in_files, ntwk_res_file, group_id):
    ntwk = init_ntwk(ntwk_res_file)
    Nnodes = len(ntwk.node)
    allntwks = np.zeros((Nnodes,Nnodes),dtype=float)
    for index, subject in enumerate(in_files):
        tmp = sio.loadmat(subject)
        allntwks = np.dstack((allntwks, tmp['cmatrix']))
    meanntwk = np.mean(allntwks,2)
    print "Creating average network for group: {grp}".format(grp=group_id)
    newdata = []
    for u in range(0,np.shape(meanntwk)[0]):
        for v in range(0,np.shape(meanntwk)[1]):
            newdata = meanntwk[u][v]
            if newdata > 0:
                ntwk.add_edge(u+1,v+1)
                ntwk.edge[u+1][v+1]['weight'] = newdata
    ntwk = removenodezero(ntwk)
    network_name = group_id + '_average.pck'
    nx.write_gpickle(ntwk, op.abspath(network_name))
    ntwk = nx.read_gpickle(op.abspath(network_name))
    ntwk = fix_float_for_gexf(ntwk)
    network_name = group_id + '_average.gexf'
    nx.write_gexf(ntwk, op.abspath(network_name))
    network_name = group_id + '_average'
    return op.abspath(network_name)

def group_bct_stats(in_group1,in_group2,significance,output_prefix, ntwk_res_file, group_id1, group_id2, subject_ids_group1, subject_ids_group2):
    """
    This function takes in two lists of files; one for each input group. It also allows a prefix for the output files,
    a network resolution file (i.e. reslution83.graphml) for creating the output matrices, and the subject IDs for each input group.
        in_group1, ingroup2  -  List of strings (file paths)
        output_prefix  -  String (i.e. 'bct')
        significance  -  Float (i.e. 0.05)
        ntwk_res_file  -  String (path to i.e. resolution83.graphml)
        subject_ids_group1, subject_ids_group2  -  List of strings
    It calculates the network measures on each input file for each group. It then computes the statistics across each node/edge/matrix
    for the two groups and outputs three dictionaries:
        stats - Dictionary keyed by the network measure names (i.e. 'degree') containing p-values for each node/edge/matrix-based measure
                calculated between the two groups via permutation test.
        subject_measures, patient_measures - Dictionary keyed by patient ID (i.e. 'path/subj1.ext') containing another dictionary of the computed
                                             network measures keyed by measure name (i.e. 'degree').
        subject_average, patient_average  - Dictionary keyed by measure name (i.e. 'degree') containing the average for each measure for each group.
    """
    print 'Running group-level BCT stats...'
    if not ntwk_res_file == 0:
        print 'Network resolution file: {ntwk}'.format(ntwk=ntwk_res_file)
    if not subject_ids_group1 == 0: #Currently subject_ids do nothing. Should be used as keys instead of paths for the subject and patient dicts
        print 'Subject IDs: {subj_IDs}'.format(subj_IDs=subject_ids_group1)
    if not subject_ids_group2 == 0:
        print 'Patient IDs: {patient_IDs}'.format(subj_IDs=subject_ids_group2)
    subject_measures = {}
    patient_measures = {}
    for subject in in_group1:
        tmp = sio.loadmat(subject)
        subject_measures[subject] = compute_measures(tmp['cmatrix'], ntwk_res_file)
    for patient in in_group2:
        tmp = sio.loadmat(patient)
        patient_measures[patient] = compute_measures(tmp['cmatrix'], ntwk_res_file)
    returnall = run_stats(subject_measures, patient_measures, significance, group_id1, group_id2)
    stats = returnall['p']
    subject_average = returnall['subject_average']
    patient_average = returnall['patient_average']
    returnall = {'stats':stats, 'subject_measures':subject_measures, 'patient_measures':patient_measures, 'subject_average':subject_average,
    'patient_average':patient_average}
    return returnall

def init_ntwk(ntwk_res_file):
    gp = nx.read_graphml(ntwk_res_file)
    nROIs = len(gp.nodes())
    initial_network = nx.Graph()
    for u,d in gp.nodes_iter(data=True):
        initial_network.add_node(int(u), d)
    return initial_network

def init_ntwk_with_cmatrix(ntwk_res_file, cmatrix):
    initial_network = init_ntwk(ntwk_res_file)
    newdata = []
    for u in range(0,np.shape(cmatrix)[0]):
        for v in range(0,np.shape(cmatrix)[1]):
            newdata = cmatrix[u][v]
            if newdata > 0:
                initial_network.add_edge(u+1,v+1)
                initial_network.edge[u+1][v+1]['weight'] = newdata
    return initial_network

def removenodezero(network):
    if network.has_node(0):
        network.remove_node(0)
    return network

def fix_float_for_gexf(network):
    for u,v,d in network.edges_iter(data=True):
        for k,v in d.items():
            if isinstance(d[k], np.float64):
                d[k] = float( d[k] )
    for u,d in network.nodes_iter(data=True):
        for k,v in d.items():
            if isinstance(d[k], np.float64):
                d[k] = float( d[k] )
            if k == 'dn_correspondence_id':
                d['id'] = d[k]
            if k == 'dn_fsname':
                d['label'] = d[k]
    return network

def writenodemeasure(stats, measure, group_id, ntwk_res_file, key='p-value'):
    print "Node-based measure: {mtrc}".format(mtrc=measure)
    ntwk = init_ntwk(ntwk_res_file)
    newdata = []
    print np.shape(stats[measure])
    for u,d in ntwk.nodes_iter(data=True):
        newdata = d
        newdata[key] = stats[measure][u-1]
        ntwk.node[u]=newdata
        del newdata
    ntwk = removenodezero(ntwk)
    network_name = measure + '_' + group_id + '_nodes.pck'
    nx.write_gpickle(ntwk, op.abspath(network_name))
    ntwk = nx.read_gpickle(op.abspath(network_name))
    network_name = measure + '_' + group_id + '_nodes.gexf'
    ntwk = fix_float_for_gexf(ntwk)
    nx.write_gexf(ntwk, op.abspath(network_name))
    network_name = measure + '_' + group_id + '_nodes'
    return network_name

def writeedgemeasure(stats, measure, group_id, ntwk_res_file, significance, key='p-value'):
    print "Edge-based measure: {mtrc}".format(mtrc=measure)
    ntwk = init_ntwk(ntwk_res_file)
    newdata = []
    print np.shape(stats[measure])
    for u in range(0,np.shape(stats[measure])[0]):
        for v in range(0,np.shape(stats[measure])[1]):
            newdata = stats[measure][u][v]
            if newdata <= significance and newdata > 0:
                ntwk.add_edge(u+1,v+1)
                ntwk.edge[u+1][v+1][key] = newdata
    ntwk = removenodezero(ntwk)
    network_name = measure + '_' + group_id + '_edges.pck'
    nx.write_gpickle(ntwk, op.abspath(network_name))
    ntwk = nx.read_gpickle(op.abspath(network_name))
    network_name = measure + '_' + group_id + '_edges.gexf'
    ntwk = fix_float_for_gexf(ntwk)
    nx.write_gexf(ntwk, op.abspath(network_name))
    network_name = measure + '_' + group_id + '_edges'
    return network_name

def makenetworks(stats, subject_average, patient_average, ntwk_res_file, significance, group_id1, group_id2):
    print np.shape(stats)
    print np.shape(subject_average)
    gp = nx.read_graphml(ntwk_res_file)
    nROIs = len(gp.nodes())
    number_of_measures = len(subject_average.keys())
    global gexf, gpickled
    gexf = []
    gpickled = []
    ntwk = []
    for index, measure in enumerate(subject_average.keys()):
        if len(np.shape(subject_average[measure])) == 1:
            print stats
            stats_network_name = writenodemeasure(stats, measure, '', ntwk_res_file)
            print 'Writing stats for metric no. {idx} of {Nmetrics}: {metric} nodes as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=stats_network_name)

            subject_average_network_name = writenodemeasure(subject_average, measure, group_id1, ntwk_res_file)
            print 'Writing subject average for metric no. {idx} of {Nmetrics}: {metric} nodes as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=subject_average_network_name)

            patient_average_network_name = writenodemeasure(patient_average, measure, group_id2, ntwk_res_file)
            print 'Writing patient average for metric no. {idx} of {Nmetrics}: {metric} nodes as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=patient_average_network_name)

            gpickled.append(op.abspath(stats_network_name + '.pck'))
            gpickled.append(op.abspath(subject_average_network_name + '.pck'))
            gpickled.append(op.abspath(patient_average_network_name + '.pck'))
            gexf.append(op.abspath(stats_network_name + '.gexf'))
            gexf.append(op.abspath(subject_average_network_name + '.gexf'))
            gexf.append(op.abspath(patient_average_network_name + '.gexf'))
        elif len(np.shape(subject_average[measure])) == 2 and np.shape(subject_average[measure])[0] == np.shape(subject_average[measure])[1] and np.shape(subject_average[measure])[1] == nROIs:
            stats_network_name = writeedgemeasure(stats, measure, '', ntwk_res_file, significance)
            print 'Writing stats for metric no. {idx} of {Nmetrics}: {metric} edges as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=stats_network_name)

            subject_average_network_name = writeedgemeasure(subject_average, measure, group_id1, ntwk_res_file, significance)
            print 'Writing subject average for metric no. {idx} of {Nmetrics}: {metric} edges as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=subject_average_network_name)

            patient_average_network_name = writeedgemeasure(patient_average, measure, group_id2, ntwk_res_file, significance)
            print 'Writing patient average for metric no. {idx} of {Nmetrics}: {metric} edges as {ntwk}'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure, ntwk=patient_average_network_name)

            gpickled.append(op.abspath(stats_network_name + '.pck'))
            gpickled.append(op.abspath(subject_average_network_name + '.pck'))
            gpickled.append(op.abspath(patient_average_network_name + '.pck'))
            gexf.append(op.abspath(stats_network_name + '.gexf'))
            gexf.append(op.abspath(subject_average_network_name + '.gexf'))
            gexf.append(op.abspath(patient_average_network_name + '.gexf'))
        else:
            print 'Writing metric no. {idx} of {Nmetrics}: {metric} value into stats file'.format(idx=index+1,
            Nmetrics=number_of_measures, metric=measure)
    print '{num} gpickled networks written: {wrote}'.format(num=len(gpickled),wrote=gpickled)
    print '{num} gexf networks written: {wrote}'.format(num=len(gexf),wrote=gexf)
    return gpickled, gexf

class BCTStatsInputSpec(TraitedSpec):
    in_group1 = InputMultiPath(File(exists=True), mandatory=True, desc='Connectivity matrices for group 1')
    in_group2 = InputMultiPath(File(exists=True), mandatory=True, desc='Connectivity matrices for group 2')
    significance = traits.Float(0.05, usedefault=True, desc='Significance threshold (default = 0.05).')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    subject_ids_group1 = traits.List(traits.Str, desc='Subject IDs for each input file')
    subject_ids_group2 = traits.List(traits.Str, desc='Subject IDs for each input file')
    output_prefix = traits.Str('bctstats_', usedefault=True, desc='Prefix to append to output files')
    group_id1 = traits.Str('group1', usedefault=True, desc='ID for group 1')
    group_id2 = traits.Str('group2', usedefault=True, desc='ID for group 2')
    out_stats_file = File('BCTstats.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')
    out_group1_measures = File('group1_measures.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')
    out_group2_measures = File('group2_measures.mat', usedefault=True, desc='Some simple image statistics saved as a Matlab .mat')

class BCTStatsOutputSpec(TraitedSpec):
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

class BCTStats(BaseInterface):
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
        returnall = group_bct_stats(self.inputs.in_group1, self.inputs.in_group2, self.inputs.significance,
        self.inputs.output_prefix, ntwk_res_file, self.inputs.group_id1, self.inputs.group_id2, subject_ids_group1, subject_ids_group2)

        stats = returnall['stats']
        subject_measures = returnall['subject_measures']
        patient_measures = returnall['patient_measures']
        subject_average = returnall['subject_average']
        patient_average = returnall['patient_average']
        global gpickled
        global gexf
        gpickled, gexf = makenetworks(stats, subject_average, patient_average, 
        ntwk_res_file, self.inputs.significance, self.inputs.group_id1, self.inputs.group_id2)

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
        group1avg = average_networks(self.inputs.in_group1, ntwk_res_file, self.inputs.group_id1)
        group2avg = average_networks(self.inputs.in_group2, ntwk_res_file, self.inputs.group_id2)
        gpickled.append(group1avg + '.pck')
        gpickled.append(group2avg + '.pck')
        gexf.append(group1avg + '.gexf')
        gexf.append(group2avg + '.gexf')
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_group1_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_measures', 'mat'))
        outputs["out_group2_measures"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_measures', 'mat'))
        outputs["out_group1_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id1 + '_average', 'mat'))
        outputs["out_group2_average"] = op.abspath(self._gen_outfilename(self.inputs.group_id2 + '_average', 'mat'))
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
