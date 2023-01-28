# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os.path as op
import pickle

import numpy as np
import networkx as nx

from ... import logging
from ...utils.filemanip import split_filename
from ..base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    traits,
    File,
    TraitedSpec,
    InputMultiPath,
    OutputMultiPath,
    isdefined,
)
from .base import have_cmp

iflogger = logging.getLogger("nipype.interface")


def _read_pickle(fname):
    with open(fname, 'rb') as f:
        return pickle.load(f)


def read_unknown_ntwk(ntwk):
    if not isinstance(ntwk, nx.classes.graph.Graph):
        _, _, ext = split_filename(ntwk)
        if ext == ".pck":
            ntwk = _read_pickle(ntwk)
        elif ext == ".graphml":
            ntwk = nx.read_graphml(ntwk)
    return ntwk


def remove_all_edges(ntwk):
    ntwktmp = ntwk.copy()
    edges = list(ntwktmp.edges())
    for edge in edges:
        ntwk.remove_edge(edge[0], edge[1])
    return ntwk


def fix_keys_for_gexf(orig):
    """
    GEXF Networks can be read in Gephi, however, the keys for the node and edge IDs must be converted to strings
    """
    import networkx as nx

    ntwk = nx.Graph()
    nodes = list(orig.nodes())
    edges = list(orig.edges())
    for node in nodes:
        newnodedata = {}
        newnodedata.update(orig.nodes[node])
        if "dn_fsname" in orig.nodes[node]:
            newnodedata["label"] = orig.nodes[node]["dn_fsname"]
        ntwk.add_node(str(node), **newnodedata)
        if "dn_position" in ntwk.nodes[str(node)] and "dn_position" in newnodedata:
            ntwk.nodes[str(node)]["dn_position"] = str(newnodedata["dn_position"])
    for edge in edges:
        data = {}
        data = orig.edge[edge[0]][edge[1]]
        ntwk.add_edge(str(edge[0]), str(edge[1]), **data)
        if "fiber_length_mean" in ntwk.edge[str(edge[0])][str(edge[1])]:
            ntwk.edge[str(edge[0])][str(edge[1])]["fiber_length_mean"] = str(
                data["fiber_length_mean"]
            )
        if "fiber_length_std" in ntwk.edge[str(edge[0])][str(edge[1])]:
            ntwk.edge[str(edge[0])][str(edge[1])]["fiber_length_std"] = str(
                data["fiber_length_std"]
            )
        if "number_of_fibers" in ntwk.edge[str(edge[0])][str(edge[1])]:
            ntwk.edge[str(edge[0])][str(edge[1])]["number_of_fibers"] = str(
                data["number_of_fibers"]
            )
        if "value" in ntwk.edge[str(edge[0])][str(edge[1])]:
            ntwk.edge[str(edge[0])][str(edge[1])]["value"] = str(data["value"])
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
    import scipy.io as sio

    iflogger.info("Creating average network for group: %s", group_id)
    matlab_network_list = []
    if len(in_files) == 1:
        avg_ntwk = read_unknown_ntwk(in_files[0])
    else:
        count_to_keep_edge = np.round(len(in_files) / 2.0)
        iflogger.info(
            "Number of networks: %i, an edge must occur in at "
            "least %i to remain in the average network",
            len(in_files),
            count_to_keep_edge,
        )
        ntwk_res_file = read_unknown_ntwk(ntwk_res_file)
        iflogger.info(
            "%i nodes found in network resolution file", ntwk_res_file.number_of_nodes()
        )
        ntwk = remove_all_edges(ntwk_res_file)
        counting_ntwk = ntwk.copy()
        # Sums all the relevant variables
        for index, subject in enumerate(in_files):
            tmp = _read_pickle(subject)
            iflogger.info("File %s has %i edges", subject, tmp.number_of_edges())
            edges = list(tmp.edges())
            for edge in edges:
                data = {}
                data = tmp.edge[edge[0]][edge[1]]
                data["count"] = 1
                if ntwk.has_edge(edge[0], edge[1]):
                    current = {}
                    current = ntwk.edge[edge[0]][edge[1]]
                    data = add_dicts_by_key(current, data)
                ntwk.add_edge(edge[0], edge[1], **data)
            nodes = list(tmp.nodes())
            for node in nodes:
                data = {}
                data = ntwk.nodes[node]
                if "value" in tmp.nodes[node]:
                    data["value"] = data["value"] + tmp.nodes[node]["value"]
                ntwk.add_node(node, **data)

        # Divides each value by the number of files
        nodes = list(ntwk.nodes())
        edges = list(ntwk.edges())
        iflogger.info("Total network has %i edges", ntwk.number_of_edges())
        avg_ntwk = nx.Graph()
        newdata = {}
        for node in nodes:
            data = ntwk.nodes[node]
            newdata = data
            if "value" in data:
                newdata["value"] = data["value"] / len(in_files)
                ntwk.nodes[node]["value"] = newdata
            avg_ntwk.add_node(node, **newdata)

        edge_dict = {}
        edge_dict["count"] = np.zeros(
            (avg_ntwk.number_of_nodes(), avg_ntwk.number_of_nodes())
        )
        for edge in edges:
            data = ntwk.edge[edge[0]][edge[1]]
            if ntwk.edge[edge[0]][edge[1]]["count"] >= count_to_keep_edge:
                for key in list(data.keys()):
                    if not key == "count":
                        data[key] = data[key] / len(in_files)
                ntwk.edge[edge[0]][edge[1]] = data
                avg_ntwk.add_edge(edge[0], edge[1], **data)
            edge_dict["count"][edge[0] - 1][edge[1] - 1] = ntwk.edge[edge[0]][edge[1]][
                "count"
            ]

        iflogger.info(
            "After thresholding, the average network has %i edges",
            avg_ntwk.number_of_edges(),
        )

        avg_edges = avg_ntwk.edges()
        for edge in avg_edges:
            data = avg_ntwk.edge[edge[0]][edge[1]]
            for key in list(data.keys()):
                if not key == "count":
                    edge_dict[key] = np.zeros(
                        (avg_ntwk.number_of_nodes(), avg_ntwk.number_of_nodes())
                    )
                    edge_dict[key][edge[0] - 1][edge[1] - 1] = data[key]

        for key in list(edge_dict.keys()):
            tmp = {}
            network_name = group_id + "_" + key + "_average.mat"
            matlab_network_list.append(op.abspath(network_name))
            tmp[key] = edge_dict[key]
            sio.savemat(op.abspath(network_name), tmp)
            iflogger.info(
                "Saving average network for key: %s as %s",
                key,
                op.abspath(network_name),
            )

    # Writes the networks and returns the name
    network_name = group_id + "_average.pck"
    with open(op.abspath(network_name), 'wb') as f:
        pickle.dump(avg_ntwk, f, pickle.HIGHEST_PROTOCOL)
    iflogger.info("Saving average network as %s", op.abspath(network_name))
    avg_ntwk = fix_keys_for_gexf(avg_ntwk)
    network_name = group_id + "_average.gexf"
    nx.write_gexf(avg_ntwk, op.abspath(network_name))
    iflogger.info("Saving average network as %s", op.abspath(network_name))
    return network_name, matlab_network_list


def compute_node_measures(ntwk, calculate_cliques=False):
    """
    These return node-based measures
    """
    iflogger.info("Computing node measures:")
    measures = {}
    iflogger.info("...Computing degree...")
    measures["degree"] = np.array(list(ntwk.degree().values()))
    iflogger.info("...Computing load centrality...")
    measures["load_centrality"] = np.array(list(nx.load_centrality(ntwk).values()))
    iflogger.info("...Computing betweenness centrality...")
    measures["betweenness_centrality"] = np.array(
        list(nx.betweenness_centrality(ntwk).values())
    )
    iflogger.info("...Computing degree centrality...")
    measures["degree_centrality"] = np.array(list(nx.degree_centrality(ntwk).values()))
    iflogger.info("...Computing closeness centrality...")
    measures["closeness_centrality"] = np.array(
        list(nx.closeness_centrality(ntwk).values())
    )
    #    iflogger.info('...Computing eigenvector centrality...')
    #    measures['eigenvector_centrality'] = np.array(nx.eigenvector_centrality(ntwk, max_iter=100000).values())
    iflogger.info("...Computing triangles...")
    measures["triangles"] = np.array(list(nx.triangles(ntwk).values()))
    iflogger.info("...Computing clustering...")
    measures["clustering"] = np.array(list(nx.clustering(ntwk).values()))
    iflogger.info("...Computing k-core number")
    measures["core_number"] = np.array(list(nx.core_number(ntwk).values()))
    iflogger.info("...Identifying network isolates...")
    isolate_list = nx.isolates(ntwk)
    binarized = np.zeros((ntwk.number_of_nodes(), 1))
    for value in isolate_list:
        value = value - 1  # Zero indexing
        binarized[value] = 1
    measures["isolates"] = binarized
    if calculate_cliques:
        iflogger.info("...Calculating node clique number")
        measures["node_clique_number"] = np.array(
            list(nx.node_clique_number(ntwk).values())
        )
        iflogger.info("...Computing number of cliques for each node...")
        measures["number_of_cliques"] = np.array(
            list(nx.number_of_cliques(ntwk).values())
        )
    return measures


def compute_edge_measures(ntwk):
    """
    These return edge-based measures
    """
    iflogger.info("Computing edge measures:")
    measures = {}
    # iflogger.info('...Computing google matrix...' #Makes really large networks (500k+ edges))
    # measures['google_matrix'] = nx.google_matrix(ntwk)
    # iflogger.info('...Computing hub matrix...')
    # measures['hub_matrix'] = nx.hub_matrix(ntwk)
    # iflogger.info('...Computing authority matrix...')
    # measures['authority_matrix'] = nx.authority_matrix(ntwk)
    return measures


def compute_dict_measures(ntwk):
    """
    Returns a dictionary
    """
    iflogger.info("Computing measures which return a dictionary:")
    measures = {}
    iflogger.info("...Computing rich club coefficient...")
    measures["rich_club_coef"] = nx.rich_club_coefficient(ntwk)
    return measures


def compute_singlevalued_measures(ntwk, weighted=True, calculate_cliques=False):
    """
    Returns a single value per network
    """
    iflogger.info("Computing single valued measures:")
    measures = {}
    iflogger.info("...Computing degree assortativity (pearson number) ...")
    measures["degree_pearsonr"] = nx.degree_pearson_correlation_coefficient(ntwk)
    iflogger.info("...Computing degree assortativity...")
    measures["degree_assortativity"] = nx.degree_assortativity_coefficient(ntwk)
    iflogger.info("...Computing transitivity...")
    measures["transitivity"] = nx.transitivity(ntwk)
    iflogger.info("...Computing number of connected_components...")
    measures["number_connected_components"] = nx.number_connected_components(ntwk)
    iflogger.info("...Computing graph density...")
    measures["graph_density"] = nx.density(ntwk)
    iflogger.info("...Recording number of edges...")
    measures["number_of_edges"] = nx.number_of_edges(ntwk)
    iflogger.info("...Recording number of nodes...")
    measures["number_of_nodes"] = nx.number_of_nodes(ntwk)
    iflogger.info("...Computing average clustering...")
    measures["average_clustering"] = nx.average_clustering(ntwk)
    if nx.is_connected(ntwk):
        iflogger.info("...Calculating average shortest path length...")
        measures["average_shortest_path_length"] = nx.average_shortest_path_length(
            ntwk, weighted
        )
    else:
        iflogger.info("...Calculating average shortest path length...")
        measures["average_shortest_path_length"] = nx.average_shortest_path_length(
            nx.connected_component_subgraphs(ntwk)[0], weighted
        )
    if calculate_cliques:
        iflogger.info("...Computing graph clique number...")
        measures["graph_clique_number"] = nx.graph_clique_number(
            ntwk
        )  # out of memory error
    return measures


def compute_network_measures(ntwk):
    measures = {}
    # iflogger.info('Identifying k-core')
    # measures['k_core'] = nx.k_core(ntwk)
    # iflogger.info('Identifying k-shell')
    # measures['k_shell'] = nx.k_shell(ntwk)
    # iflogger.info('Identifying k-crust')
    # measures['k_crust'] = nx.k_crust(ntwk)
    return measures


def add_node_data(node_array, ntwk):
    node_ntwk = nx.Graph()
    newdata = {}
    for idx, data in ntwk.nodes(data=True):
        if not int(idx) == 0:
            newdata["value"] = node_array[int(idx) - 1]
            data.update(newdata)
            node_ntwk.add_node(int(idx), **data)
    return node_ntwk


def add_edge_data(edge_array, ntwk, above=0, below=0):
    edge_ntwk = ntwk.copy()
    data = {}
    for x, row in enumerate(edge_array):
        for y in range(0, np.max(np.shape(edge_array[x]))):
            if not edge_array[x, y] == 0:
                data["value"] = edge_array[x, y]
                if data["value"] <= below or data["value"] >= above:
                    if edge_ntwk.has_edge(x + 1, y + 1):
                        old_edge_dict = edge_ntwk.edge[x + 1][y + 1]
                        edge_ntwk.remove_edge(x + 1, y + 1)
                        data.update(old_edge_dict)
                    edge_ntwk.add_edge(x + 1, y + 1, **data)
    return edge_ntwk


class NetworkXMetricsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Input network")
    out_k_core = File(
        "k_core",
        usedefault=True,
        desc="Computed k-core network stored as a NetworkX pickle.",
    )
    out_k_shell = File(
        "k_shell",
        usedefault=True,
        desc="Computed k-shell network stored as a NetworkX pickle.",
    )
    out_k_crust = File(
        "k_crust",
        usedefault=True,
        desc="Computed k-crust network stored as a NetworkX pickle.",
    )
    treat_as_weighted_graph = traits.Bool(
        True,
        usedefault=True,
        desc="Some network metrics can be calculated while considering only a binarized version of the graph",
    )
    compute_clique_related_measures = traits.Bool(
        False,
        usedefault=True,
        desc="Computing clique-related measures (e.g. node clique number) can be very time consuming",
    )
    out_global_metrics_matlab = File(
        genfile=True, desc="Output node metrics in MATLAB .mat format"
    )
    out_node_metrics_matlab = File(
        genfile=True, desc="Output node metrics in MATLAB .mat format"
    )
    out_edge_metrics_matlab = File(
        genfile=True, desc="Output edge metrics in MATLAB .mat format"
    )
    out_pickled_extra_measures = File(
        "extra_measures",
        usedefault=True,
        desc="Network measures for group 1 that return dictionaries stored as a Pickle.",
    )


class NetworkXMetricsOutputSpec(TraitedSpec):
    gpickled_network_files = OutputMultiPath(File(desc="Output gpickled network files"))
    matlab_matrix_files = OutputMultiPath(
        File(desc="Output network metrics in MATLAB .mat format")
    )
    global_measures_matlab = File(desc="Output global metrics in MATLAB .mat format")
    node_measures_matlab = File(desc="Output node metrics in MATLAB .mat format")
    edge_measures_matlab = File(desc="Output edge metrics in MATLAB .mat format")
    node_measure_networks = OutputMultiPath(
        File(desc="Output gpickled network files for all node-based measures")
    )
    edge_measure_networks = OutputMultiPath(
        File(desc="Output gpickled network files for all edge-based measures")
    )
    k_networks = OutputMultiPath(
        File(
            desc="Output gpickled network files for the k-core, k-shell, and k-crust networks"
        )
    )
    k_core = File(desc="Computed k-core network stored as a NetworkX pickle.")
    k_shell = File(desc="Computed k-shell network stored as a NetworkX pickle.")
    k_crust = File(desc="Computed k-crust network stored as a NetworkX pickle.")
    pickled_extra_measures = File(
        desc="Network measures for the group that return dictionaries, stored as a Pickle."
    )
    matlab_dict_measures = OutputMultiPath(
        File(
            desc="Network measures for the group that return dictionaries, stored as matlab matrices."
        )
    )


class NetworkXMetrics(BaseInterface):
    """
    Calculates and outputs NetworkX-based measures for an input network

    Example
    -------
    >>> import nipype.interfaces.cmtk as cmtk
    >>> nxmetrics = cmtk.NetworkXMetrics()
    >>> nxmetrics.inputs.in_file = 'subj1.pck'
    >>> nxmetrics.run()                 # doctest: +SKIP

    """

    input_spec = NetworkXMetricsInputSpec
    output_spec = NetworkXMetricsOutputSpec

    def _run_interface(self, runtime):
        import scipy.io as sio

        global gpickled, nodentwks, edgentwks, kntwks, matlab
        gpickled = list()
        nodentwks = list()
        edgentwks = list()
        kntwks = list()
        matlab = list()
        ntwk = _read_pickle(self.inputs.in_file)

        # Each block computes, writes, and saves a measure
        # The names are then added to the output .pck file list
        # In the case of the degeneracy networks, they are given specified output names

        calculate_cliques = self.inputs.compute_clique_related_measures
        weighted = self.inputs.treat_as_weighted_graph

        global_measures = compute_singlevalued_measures(
            ntwk, weighted, calculate_cliques
        )
        if isdefined(self.inputs.out_global_metrics_matlab):
            global_out_file = op.abspath(self.inputs.out_global_metrics_matlab)
        else:
            global_out_file = op.abspath(self._gen_outfilename("globalmetrics", "mat"))
        sio.savemat(global_out_file, global_measures, oned_as="column")
        matlab.append(global_out_file)

        node_measures = compute_node_measures(ntwk, calculate_cliques)
        for key in list(node_measures.keys()):
            newntwk = add_node_data(node_measures[key], ntwk)
            out_file = op.abspath(self._gen_outfilename(key, "pck"))
            with open(out_file, 'wb') as f:
                pickle.dump(newntwk, f, pickle.HIGHEST_PROTOCOL)
            nodentwks.append(out_file)
        if isdefined(self.inputs.out_node_metrics_matlab):
            node_out_file = op.abspath(self.inputs.out_node_metrics_matlab)
        else:
            node_out_file = op.abspath(self._gen_outfilename("nodemetrics", "mat"))
        sio.savemat(node_out_file, node_measures, oned_as="column")
        matlab.append(node_out_file)
        gpickled.extend(nodentwks)

        edge_measures = compute_edge_measures(ntwk)
        for key in list(edge_measures.keys()):
            newntwk = add_edge_data(edge_measures[key], ntwk)
            out_file = op.abspath(self._gen_outfilename(key, "pck"))
            with open(out_file, 'wb') as f:
                pickle.dump(newntwk, f, pickle.HIGHEST_PROTOCOL)
            edgentwks.append(out_file)
        if isdefined(self.inputs.out_edge_metrics_matlab):
            edge_out_file = op.abspath(self.inputs.out_edge_metrics_matlab)
        else:
            edge_out_file = op.abspath(self._gen_outfilename("edgemetrics", "mat"))
        sio.savemat(edge_out_file, edge_measures, oned_as="column")
        matlab.append(edge_out_file)
        gpickled.extend(edgentwks)

        ntwk_measures = compute_network_measures(ntwk)
        for key in list(ntwk_measures.keys()):
            if key == "k_core":
                out_file = op.abspath(
                    self._gen_outfilename(self.inputs.out_k_core, "pck")
                )
            if key == "k_shell":
                out_file = op.abspath(
                    self._gen_outfilename(self.inputs.out_k_shell, "pck")
                )
            if key == "k_crust":
                out_file = op.abspath(
                    self._gen_outfilename(self.inputs.out_k_crust, "pck")
                )
            with open(out_file, 'wb') as f:
                pickle.dump(ntwk_measures[key], f, pickle.HIGHEST_PROTOCOL)
            kntwks.append(out_file)
        gpickled.extend(kntwks)

        out_pickled_extra_measures = op.abspath(
            self._gen_outfilename(self.inputs.out_pickled_extra_measures, "pck")
        )
        dict_measures = compute_dict_measures(ntwk)
        iflogger.info(
            "Saving extra measure file to %s in Pickle format",
            op.abspath(out_pickled_extra_measures),
        )
        with open(out_pickled_extra_measures, "w") as fo:
            pickle.dump(dict_measures, fo)

        iflogger.info("Saving MATLAB measures as %s", matlab)

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
                    nparraykeys = np.append(nparraykeys, np.array(keyd))
                    values = np.array(dict_measures[key][keyd])
                    nparrayvalues = np.append(nparrayvalues, values)
            nparray = np.vstack((nparraykeys, nparrayvalues))
            out_file = op.abspath(self._gen_outfilename(key, "mat"))
            npdict = {}
            npdict[key] = nparray
            sio.savemat(out_file, npdict, oned_as="column")
            dicts.append(out_file)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["k_core"] = op.abspath(
            self._gen_outfilename(self.inputs.out_k_core, "pck")
        )
        outputs["k_shell"] = op.abspath(
            self._gen_outfilename(self.inputs.out_k_shell, "pck")
        )
        outputs["k_crust"] = op.abspath(
            self._gen_outfilename(self.inputs.out_k_crust, "pck")
        )
        outputs["gpickled_network_files"] = gpickled
        outputs["k_networks"] = kntwks
        outputs["node_measure_networks"] = nodentwks
        outputs["edge_measure_networks"] = edgentwks
        outputs["matlab_dict_measures"] = dicts
        outputs["global_measures_matlab"] = op.abspath(
            self._gen_outfilename("globalmetrics", "mat")
        )
        outputs["node_measures_matlab"] = op.abspath(
            self._gen_outfilename("nodemetrics", "mat")
        )
        outputs["edge_measures_matlab"] = op.abspath(
            self._gen_outfilename("edgemetrics", "mat")
        )
        outputs["matlab_matrix_files"] = [
            outputs["global_measures_matlab"],
            outputs["node_measures_matlab"],
            outputs["edge_measures_matlab"],
        ]
        outputs["pickled_extra_measures"] = op.abspath(
            self._gen_outfilename(self.inputs.out_pickled_extra_measures, "pck")
        )
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + "." + ext


class AverageNetworksInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(
        File(exists=True), mandatory=True, desc="Networks for a group of subjects"
    )
    resolution_network_file = File(
        exists=True,
        desc="Parcellation files from Connectome Mapping Toolkit. This is not necessary"
        ", but if included, the interface will output the statistical maps as networkx graphs.",
    )
    group_id = traits.Str("group1", usedefault=True, desc="ID for group")
    out_gpickled_groupavg = File(desc="Average network saved as a NetworkX .pck")
    out_gexf_groupavg = File(desc="Average network saved as a .gexf file")


class AverageNetworksOutputSpec(TraitedSpec):
    gpickled_groupavg = File(desc="Average network saved as a NetworkX .pck")
    gexf_groupavg = File(desc="Average network saved as a .gexf file")
    matlab_groupavgs = OutputMultiPath(
        File(desc="Average network saved as a .gexf file")
    )


class AverageNetworks(BaseInterface):
    """
    Calculates and outputs the average network given a set of input NetworkX gpickle files

    This interface will only keep an edge in the averaged network if that edge is present in
    at least half of the input networks.

    Example
    -------
    >>> import nipype.interfaces.cmtk as cmtk
    >>> avg = cmtk.AverageNetworks()
    >>> avg.inputs.in_files = ['subj1.pck', 'subj2.pck']
    >>> avg.run()                 # doctest: +SKIP

    """

    input_spec = AverageNetworksInputSpec
    output_spec = AverageNetworksOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.resolution_network_file):
            ntwk_res_file = self.inputs.resolution_network_file
        else:
            ntwk_res_file = self.inputs.in_files[0]

        global matlab_network_list
        network_name, matlab_network_list = average_networks(
            self.inputs.in_files, ntwk_res_file, self.inputs.group_id
        )
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.out_gpickled_groupavg):
            outputs["gpickled_groupavg"] = op.abspath(
                self._gen_outfilename(self.inputs.group_id + "_average", "pck")
            )
        else:
            outputs["gpickled_groupavg"] = op.abspath(self.inputs.out_gpickled_groupavg)

        if not isdefined(self.inputs.out_gexf_groupavg):
            outputs["gexf_groupavg"] = op.abspath(
                self._gen_outfilename(self.inputs.group_id + "_average", "gexf")
            )
        else:
            outputs["gexf_groupavg"] = op.abspath(self.inputs.out_gexf_groupavg)

        outputs["matlab_groupavgs"] = matlab_network_list
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + "." + ext
