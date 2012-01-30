# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec, traits,
                                    File, TraitedSpec, InputMultiPath,
                                    OutputMultiPath, isdefined)
from nipype.utils.filemanip import split_filename
import os, os.path as op
import numpy as np
import networkx as nx
import scipy.io as sio
import pickle
from nipype.utils.misc import package_check
import warnings

have_cmp = True
try:
    package_check('cmp')
except Exception, e:
    have_cmp = False
    warnings.warn('cmp not installed')
else:
    import cmp

def get_data_dims(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    datadims = hdr.get_data_shape()
    return [int(datadims[0]), int(datadims[1]), int(datadims[2])]

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
    """
    GEXF Networks can be read in Gephi, however, the keys for the node and edge IDs must be converted to strings
    """
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
    """
    Combines two dictionaries and adds the values for those keys that are shared
    """
    both = {}
    for key1 in in_dict1:
        for key2 in in_dict2:
            if key1 == key2:
                both[key1] = in_dict1[key1] + in_dict2[key2]
    return both

def average_networks(in_files, ntwk_res_file, group_id):
    """
    Sums the edges of input networks and divides by the number of networks
    Writes the average network as .pck and .gexf and returns the name of the written networks
    """
    import networkx as nx
    import os.path as op
    print "Creating average network for group: {grp}".format(grp=group_id)
    if len(in_files) == 1:
        ntwk = read_unknown_ntwk(in_files[0])
    else:
        ntwk_res_file = read_unknown_ntwk(ntwk_res_file)
        ntwk = remove_all_edges(ntwk_res_file)

    # Sums all the relevant variables
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

    # Divides each value by the number of files
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

    # Writes the networks and returns the name
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
    print '...Computing number of cliques for each node...'
    measures['number_of_cliques'] = np.array(nx.number_of_cliques(ntwk).values())
    print '...Computing load centrality...'
    measures['load_centrality'] = np.array(nx.load_centrality(ntwk).values())
    print '...Computing betweenness centrality...'
    measures['betweenness_centrality'] = np.array(nx.betweenness_centrality(ntwk).values())
    print '...Computing degree centrality...'
    measures['degree_centrality'] = np.array(nx.degree_centrality(ntwk).values())
    print '...Computing closeness centrality...'
    measures['closeness_centrality'] = np.array(nx.closeness_centrality(ntwk).values())
    #print '...Computing eigenvector centrality...'
    #measures['eigenvector_centrality'] = np.array(nx.eigenvector_centrality(ntwk).values())
    print '...Calculating node clique number'
    measures['node_clique_number'] = np.array(nx.node_clique_number(ntwk).values())
    print '...Computing triangles...'
    measures['triangles'] = np.array(nx.triangles(ntwk).values())
    print '...Computing clustering...'
    measures['clustering'] = np.array(nx.clustering(ntwk).values())
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
    print '...Computing authority matrix...'
    measures['authority_matrix'] = nx.authority_matrix(ntwk)
    return measures

def compute_dict_measures(ntwk):
    """
    Returns a dictionary
    """
    print 'Computing measures which return a dictionary:'
    weighted = True
    measures = {}
    print '...Computing rich club coefficient...'
    measures['rich_club_coef'] = nx.rich_club_coefficient(ntwk,1000)
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
    print '...Computing graph clique number...'
    measures['graph_clique_number'] = nx.graph_clique_number(ntwk)
    print '...Calculating average shortest path length...'
    measures['average_shortest_path_length'] = nx.average_shortest_path_length(ntwk, weighted)
    return measures

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

class NetworkXMetricsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='Input network')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as NetworkX graphs.')
    subject_id = traits.Str('subject', usedefault=True, desc='Subject ID for the input network')
    out_k_core = File('k_core', usedefault=True, desc='Computed k-core network stored as a NetworkX pickle.')
    out_k_shell = File('k_shell', usedefault=True, desc='Computed k-shell network stored as a NetworkX pickle.')
    out_k_crust = File('k_crust', usedefault=True, desc='Computed k-crust network stored as a NetworkX pickle.')
    out_node_metrics_matlab = File(genfile=True, desc='Output node metrics in MATLAB .mat format')
    out_edge_metrics_matlab = File(genfile=True, desc='Output edge metrics in MATLAB .mat format')
    out_pickled_extra_measures = File('extra_measures', usedefault=True, desc='Network measures for group 1 that return dictionaries stored as a Pickle.')

class NetworkXMetricsOutputSpec(TraitedSpec):
    gpickled_network_files = OutputMultiPath(File(desc='Output gpickled network files'))
    matlab_matrix_files = OutputMultiPath(File(desc='Output network metrics in MATLAB .mat format'))
    node_measures_matlab = File(desc='Output node metrics in MATLAB .mat format')
    edge_measures_matlab = File(desc='Output edge metrics in MATLAB .mat format')
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
    >>> nxmetrics = cmtk.NetworkXMetrics()
    >>> nxmetrics.inputs.in_file = 'subj1.pck'
    >>> nxmetrics.inputs.subject_id = 'subj1'
    >>> #import cmp
    >>> #cmp_config = cmp.configuration.PipelineConfiguration()
    >>> #cmp_config.parcellation_scheme = "Lausanne2008"
    >>> #nxmetrics.inputs.resolution_network_file = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']
    >>> nxmetrics.run()                 # doctest: +SKIP
    """
    input_spec = NetworkXMetricsInputSpec
    output_spec = NetworkXMetricsOutputSpec

    def _run_interface(self, runtime):
		global gpickled, nodentwks, edgentwks, kntwks, matlab
		gpickled = list()
		nodentwks = list()
		edgentwks = list()
		kntwks = list()
		matlab = list()
		ntwk = nx.read_gpickle(op.abspath(self.inputs.in_file))

		# Each block computes, writes, and saves a measure
		# The names are then added to the output .pck file list
		# In the case of the degeneracy networks, they are given specified output names

		node_measures = compute_node_measures(ntwk)
		for key in node_measures.keys():
			newntwk = add_node_data(node_measures[key],self.inputs.in_file)
			out_file = op.abspath(self._gen_outfilename(key, 'pck'))
			nx.write_gpickle(newntwk, out_file)
			nodentwks.append(out_file)
		if isdefined(self.inputs.out_node_metrics_matlab):
			node_out_file = op.abspath(self.inputs.out_node_metrics_matlab)
		else:
			node_out_file = op.abspath(self._gen_outfilename('nodemetrics', 'mat'))
		sio.savemat(node_out_file, node_measures, oned_as='column')
		matlab.append(node_out_file)
		gpickled.extend(nodentwks)

		edge_measures = compute_edge_measures(ntwk)
		for key in edge_measures.keys():
			newntwk = add_edge_data(edge_measures[key],self.inputs.in_file)
			out_file = op.abspath(self._gen_outfilename(key, 'pck'))
			nx.write_gpickle(newntwk, out_file)
			edgentwks.append(out_file)
		if isdefined(self.inputs.out_edge_metrics_matlab):
			edge_out_file = op.abspath(self.inputs.out_edge_metrics_matlab)
		else:
			edge_out_file = op.abspath(self._gen_outfilename('edgemetrics', 'mat'))
		sio.savemat(edge_out_file, edge_measures, oned_as='column')
		matlab.append(edge_out_file)
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
		print 'Saving extra measure file to {path} in Pickle format'.format(path=op.abspath(out_pickled_extra_measures))
		file = open(out_pickled_extra_measures, 'w')
		pickle.dump(dict_measures, file)
		file.close()

		print 'Saving MATLAB measures as {m}'.format(m=matlab)

		# Loops through the measures which return a dictionary,
		# converts the keys and values to a Numpy array,
		# stacks them together, and saves them in a MATLAB .mat file via Scipy
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
			sio.savemat(out_file, npdict, oned_as='column')
			dicts.append(out_file)
		return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["k_core"] = op.abspath(self._gen_outfilename(self.inputs.out_k_core, 'pck'))
        outputs["k_shell"] = op.abspath(self._gen_outfilename(self.inputs.out_k_shell, 'pck'))
        outputs["k_crust"] = op.abspath(self._gen_outfilename(self.inputs.out_k_crust, 'pck'))
        outputs["gpickled_network_files"] = gpickled
        outputs["k_networks"] = kntwks
        outputs["node_measure_networks"] = nodentwks
        outputs["edge_measure_networks"] = edgentwks
        outputs["matlab_dict_measures"] = dicts
        outputs["matlab_matrix_files"] = [op.abspath(self._gen_outfilename('nodemetrics', 'mat')), op.abspath(self._gen_outfilename('edgemetrics', 'mat'))]
        outputs["node_measures_matlab"] = op.abspath(self._gen_outfilename('nodemetrics', 'mat'))
        outputs["edge_measures_matlab"] = op.abspath(self._gen_outfilename('edgemetrics', 'mat'))
        outputs["out_pickled_extra_measures"] = op.abspath(self._gen_outfilename(self.inputs.out_pickled_extra_measures, 'pck'))
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext

class AverageNetworksInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True, desc='Networks for a group of subjects')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    group_id = traits.Str('group1', usedefault=True, desc='ID for group')
    out_gpickled_groupavg = File('group1_average.pck', usedefault=True, desc='Average network saved as a NetworkX .pck')
    out_gexf_groupavg = File('group1_average.pck', usedefault=True, desc='Average network saved as a .gexf file')

class AverageNetworksOutputSpec(TraitedSpec):
    out_gpickled_groupavg = File(desc='Average network saved as a NetworkX .pck')
    out_gexf_groupavg = File(desc='Average network saved as a .gexf file')

class AverageNetworks(BaseInterface):
    """
    Calculates and outputs the average network given a set of input NetworkX gpickle files

    Example
    -------

    >>> avg = AverageNetworks()
    >>> avg.inputs.in_files = ['subj1.pck', 'subj2.pck']
    >>> avg.run()                 # doctest: +SKIP

    """
    input_spec = AverageNetworksInputSpec
    output_spec = AverageNetworksOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
            cmp_config.parcellation_scheme = "NativeFreesurfer"
            ntwk_res_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']

        groupavg = average_networks(self.inputs.in_files, ntwk_res_file, self.inputs.group_id)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_gpickled_groupavg"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average','pck'))
        outputs["out_gexf_groupavg"] = op.abspath(self._gen_outfilename(self.inputs.group_id + '_average','gexf'))
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext

class RegionalValuesInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='Functional (e.g. Positron Emission Tomography) image')
    segmentation_file = File(exists=True, mandatory=True, desc='Image with segmented regions (e.g. aparc+aseg.nii or the output from cmtk.Parcellate()')
    resolution_network_file = File(exists=True, desc='Parcellation files from Connectome Mapping Toolkit. This is not necessary' \
                                ', but if included, the interface will output the statistical maps as networkx graphs.')
    subject_id = traits.Str(desc='Subject ID')
    skip_unknown = traits.Bool(True, usedefault=True, desc='Skips calculation for regions with ID = 0 (default=True)')
    out_stats_file = File('stats.mat', usedefault=True, desc='Some simple image statistics for regions saved as a Matlab .mat')

class RegionalValuesOutputSpec(TraitedSpec):
    stats_file = File(desc='Some simple image statistics for the original and normalized images saved as a Matlab .mat')
    networks = OutputMultiPath(File(desc='Output gpickled network files for all statistical measures'))

class RegionalValues(BaseInterface):
    """
    Extracts the regional mean, max, min, and standard deviation for a functional image given a segmentated image.
    Output is saved in a MATLAB file, and if a network resolution file is provided (e.g. resolution1015.graphml), the regions are output as nodes in a NetworkX graph.

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> regval = cmtk.RegionalValues()
    >>> regval.inputs.in_file = 'pet_resliced.nii'
    >>> regval.inputs.segmentation_file = 'ROI_scale500.nii.gz'
    >>> regval.run() # doctest: +SKIP
    """
    input_spec = RegionalValuesInputSpec
    output_spec = RegionalValuesOutputSpec

    def _run_interface(self, runtime):
        print 'Functional image: {img}'.format(img=self.inputs.in_file)
        print 'Segmentation image: {img}'.format(img=self.inputs.segmentation_file)
        if not get_data_dims(self.inputs.in_file) == get_data_dims(self.inputs.segmentation_file):
            print 'Image dimensions are not the same, please reslice the images to the same dimensions'
            dx,dy,dz = get_data_dims(self.inputs.in_file)
            print 'Functional image dimensions: {dimx}, {dimy}, {dimz}'.format(dimx=dx,dimy=dy,dimz=dz)
            dx,dy,dz = get_data_dims(self.inputs.segmentation_file)
            print 'Segmentation image dimensions: {dimx}, {dimy}, {dimz}'.format(dimx=dx,dimy=dy,dimz=dz)


        """Record intensity values"""
        functional = nb.load(self.inputs.in_file)
        functionaldata = functional.get_data()
        segmentation = nb.load(self.inputs.segmentation_file)
        segmentationdata = segmentation.get_data()

        rois = np.unique(segmentationdata)
        print 'Found {roi} unique region values'.format(roi=len(rois))

        func_mean = []
        func_max = []
        func_min = []
        func_stdev = []
        voxels = []
        for idx, roi in enumerate(rois):
            values = []
            if self.inputs.skip_unknown:
                if not roi == 0:
                    x,y,z = np.where(segmentationdata == roi)
                    print 'Region ID: {id}'.format(id=roi)
                    for index in range(0,len(x)):
                        value = functionaldata[x[index]][y[index]][z[index]]
                        values.append(value)
                    func_mean.append(np.mean(values))
                    func_max.append(np.max(values))
                    func_min.append(np.min(values))
                    func_stdev.append(np.std(values))
                    voxels.append(len(values))
                    print 'Mean Value: {avg}'.format(avg=np.mean(values))
                    print 'Number of Voxels: {vox}'.format(vox=len(values))
            else:
                x,y,z = np.where(segmentationdata == roi)
                print 'Region ID: {id}'.format(id=roi)
                for index in range(0,len(x)):
                    value = functionaldata[x[index]][y[index]][z[index]]
                    values.append(value)
                func_mean.append(np.mean(values))
                func_max.append(np.max(values))
                func_min.append(np.min(values))
                func_stdev.append(np.std(values))
                voxels.append(len(values))
                print 'Mean Value: {avg}'.format(avg=np.mean(values))
                print 'Number of Voxels: {vox}'.format(vox=len(values))

        stats = {}
        stats['func_max'] = func_max
        stats['func_mean'] = func_mean
        stats['func_min'] = func_min
        stats['func_stdev'] = func_stdev
        stats['number_of_voxels'] = voxels

        if isdefined(self.inputs.resolution_network_file):
			gp = read_unknown_ntwk(self.inputs.resolution_network_file)
			nROIs = len(gp.nodes())
			nodesdict = gp.node
			if nodesdict.has_key('1'):
				nodedict = gp.node['1']
			elif nodesdict.has_key(1):
				nodedict = gp.node[1]
			else:
				nodedict = gp.node[gp.nodes()[0].key]
			if not nodedict.has_key('dn_position'):
				print "Creating node positions from segmentation"
				G = nx.Graph()
				for u,d in gp.nodes_iter(data=True):
					print 'Node ID {id}'.format(id=int(u))
					G.add_node(int(u), d)
					xyz = tuple(np.mean( np.where(segmentationdata == int(d["dn_correspondence_id"]) ) , axis = 1))
					tmp = tuple()
					a = float(xyz[0])
					b = float(xyz[2])
					c = float(xyz[1])
					tmp = tuple([a,b,c])
					xyz = tmp
					G.node[int(u)]['dn_position'] = tuple(xyz)
				ntwkname = op.abspath('nodepositions.pck')
				nx.write_gpickle(G,ntwkname)
			else:
				ntwkname = self.inputs.resolution_network_file

			global ntwks
			ntwks = list()
			for key in stats.keys():
				print key
				print np.shape(stats[key])
				newntwk = add_node_data(stats[key],ntwkname)
				out_file = op.abspath(self._gen_outfilename(key, 'pck'))
				nx.write_gpickle(newntwk, out_file)
				ntwks.append(out_file)

        if isdefined(self.inputs.subject_id):
            stats['subject_id'] = self.inputs.subject_id

        out_stats_file = op.abspath(self.inputs.out_stats_file)
        print 'Saving image statistics as {stats}'.format(stats=out_stats_file)
        sio.savemat(out_stats_file, stats)
        return runtime

    def _list_outputs(self):
		outputs = self.output_spec().get()
		out_stats_file = op.abspath(self.inputs.out_stats_file)
		outputs["stats_file"] = out_stats_file
		if isdefined(self.inputs.resolution_network_file):
			outputs["networks"] = ntwks
		else:
			outputs["networks"] = ''
		return outputs

    def _gen_outfilename(self, name, ext):
        return name + '.' + ext
