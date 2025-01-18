# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os.path as op

import numpy as np
import networkx as nx
import pickle

from ... import logging
from ..base import (
    LibraryBaseInterface,
    BaseInterfaceInputSpec,
    traits,
    File,
    TraitedSpec,
    InputMultiPath,
    OutputMultiPath,
    isdefined,
)

iflogger = logging.getLogger("nipype.interface")


def _read_pickle(fname):
    with open(fname, 'rb') as f:
        return pickle.load(f)


def ntwks_to_matrices(in_files, edge_key):
    first = _read_pickle(in_files[0])
    files = len(in_files)
    nodes = len(first.nodes())
    matrix = np.zeros((nodes, nodes, files))
    for idx, name in enumerate(in_files):
        graph = _read_pickle(name)
        for u, v, d in graph.edges(data=True):
            try:
                graph[u][v]["weight"] = d[
                    edge_key
                ]  # Setting the edge requested edge value as weight value
            except:
                raise KeyError(f"the graph edges do not have {edge_key} attribute")
        matrix[:, :, idx] = nx.to_numpy_array(graph)  # Retrieve the matrix
    return matrix


class NetworkBasedStatisticInputSpec(BaseInterfaceInputSpec):
    in_group1 = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc="Networks for the first group of subjects",
    )
    in_group2 = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc="Networks for the second group of subjects",
    )
    node_position_network = File(
        desc="An optional network used to position the nodes for the output networks"
    )
    number_of_permutations = traits.Int(
        1000, usedefault=True, desc="Number of permutations to perform"
    )
    threshold = traits.Float(3, usedefault=True, desc="T-statistic threshold")
    t_tail = traits.Enum(
        "left",
        "right",
        "both",
        usedefault=True,
        desc='Can be one of "left", "right", or "both"',
    )
    edge_key = traits.Str(
        "number_of_fibers",
        usedefault=True,
        desc='Usually "number_of_fibers, "fiber_length_mean", "fiber_length_std" for matrices made with CMTK'
        'Sometimes "weight" or "value" for functional networks.',
    )
    out_nbs_network = File(desc="Output network with edges identified by the NBS")
    out_nbs_pval_network = File(
        desc="Output network with p-values to weight the edges identified by the NBS"
    )


class NetworkBasedStatisticOutputSpec(TraitedSpec):
    nbs_network = File(
        exists=True, desc="Output network with edges identified by the NBS"
    )
    nbs_pval_network = File(
        exists=True,
        desc="Output network with p-values to weight the edges identified by the NBS",
    )
    network_files = OutputMultiPath(
        File(exists=True), desc="Output network with edges identified by the NBS"
    )


class NetworkBasedStatistic(LibraryBaseInterface):
    """
    Calculates and outputs the average network given a set of input NetworkX gpickle files

    See Also
    --------
    For documentation of Network-based statistic parameters:
    https://github.com/LTS5/connectomeviewer/blob/master/cviewer/libs/pyconto/groupstatistics/nbs/_nbs.py

    Example
    -------
    >>> import nipype.interfaces.cmtk as cmtk
    >>> nbs = cmtk.NetworkBasedStatistic()
    >>> nbs.inputs.in_group1 = ['subj1.pck', 'subj2.pck'] # doctest: +SKIP
    >>> nbs.inputs.in_group2 = ['pat1.pck', 'pat2.pck'] # doctest: +SKIP
    >>> nbs.run()                 # doctest: +SKIP

    """

    input_spec = NetworkBasedStatisticInputSpec
    output_spec = NetworkBasedStatisticOutputSpec
    _pkg = "cviewer"

    def _run_interface(self, runtime):
        from cviewer.libs.pyconto.groupstatistics import nbs

        THRESH = self.inputs.threshold
        K = self.inputs.number_of_permutations
        TAIL = self.inputs.t_tail
        edge_key = self.inputs.edge_key
        details = (
            edge_key
            + "-thresh-"
            + str(THRESH)
            + "-k-"
            + str(K)
            + "-tail-"
            + TAIL
            + ".pck"
        )

        # Fill in the data from the networks
        X = ntwks_to_matrices(self.inputs.in_group1, edge_key)
        Y = ntwks_to_matrices(self.inputs.in_group2, edge_key)

        PVAL, ADJ, _ = nbs.compute_nbs(X, Y, THRESH, K, TAIL)

        iflogger.info("p-values:")
        iflogger.info(PVAL)

        pADJ = ADJ.copy()
        for idx, _ in enumerate(PVAL):
            x, y = np.where(ADJ == idx + 1)
            pADJ[x, y] = PVAL[idx]

        # Create networkx graphs from the adjacency matrix
        nbsgraph = nx.from_numpy_array(ADJ)
        nbs_pval_graph = nx.from_numpy_array(pADJ)

        # Relabel nodes because they should not start at zero for our convention
        nbsgraph = nx.relabel_nodes(nbsgraph, lambda x: x + 1)
        nbs_pval_graph = nx.relabel_nodes(nbs_pval_graph, lambda x: x + 1)

        if isdefined(self.inputs.node_position_network):
            node_ntwk_name = self.inputs.node_position_network
        else:
            node_ntwk_name = self.inputs.in_group1[0]

        node_network = _read_pickle(node_ntwk_name)
        iflogger.info(
            "Populating node dictionaries with attributes from %s", node_ntwk_name
        )

        for nid, ndata in node_network.nodes(data=True):
            nbsgraph.nodes[nid] = ndata
            nbs_pval_graph.nodes[nid] = ndata

        path = op.abspath("NBS_Result_" + details)
        iflogger.info(path)
        with open(path, 'wb') as f:
            pickle.dump(nbsgraph, f, pickle.HIGHEST_PROTOCOL)
        iflogger.info("Saving output NBS edge network as %s", path)

        pval_path = op.abspath("NBS_P_vals_" + details)
        iflogger.info(pval_path)
        with open(pval_path, 'wb') as f:
            pickle.dump(nbs_pval_graph, f, pickle.HIGHEST_PROTOCOL)
        iflogger.info("Saving output p-value network as %s", pval_path)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()

        THRESH = self.inputs.threshold
        K = self.inputs.number_of_permutations
        TAIL = self.inputs.t_tail
        edge_key = self.inputs.edge_key
        details = (
            edge_key
            + "-thresh-"
            + str(THRESH)
            + "-k-"
            + str(K)
            + "-tail-"
            + TAIL
            + ".pck"
        )
        path = op.abspath("NBS_Result_" + details)
        pval_path = op.abspath("NBS_P_vals_" + details)

        outputs["nbs_network"] = path
        outputs["nbs_pval_network"] = pval_path
        outputs["network_files"] = [path, pval_path]
        return outputs

    def _gen_outfilename(self, name, ext):
        return name + "." + ext
