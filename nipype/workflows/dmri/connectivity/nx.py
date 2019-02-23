# -*- coding: utf-8 -*-
from ....pipeline import engine as pe
from ....interfaces import utility as util
from ....interfaces import cmtk as cmtk
from ....algorithms import misc as misc
from ....algorithms.misc import remove_identical_paths
from .group_connectivity import pullnodeIDs


def add_global_to_filename(in_file):
    from nipype.utils.filemanip import split_filename
    path, name, ext = split_filename(in_file)
    return name + '_global' + ext


def add_nodal_to_filename(in_file):
    from nipype.utils.filemanip import split_filename
    path, name, ext = split_filename(in_file)
    return name + '_nodal' + ext


def create_networkx_pipeline(name="networkx", extra_column_heading="subject"):
    """Creates a workflow to calculate various graph measures (via NetworkX) on
    an input network. The output measures are then converted to comma-separated value
    text files, and an extra column / field is also added. Typically, the user would
    connect the subject name to this field.

    Example
    -------

    >>> from nipype.workflows.dmri.connectivity.nx import create_networkx_pipeline
    >>> nx = create_networkx_pipeline("networkx", "subject_id")
    >>> nx.inputs.inputnode.extra_field = 'subj1'
    >>> nx.inputs.inputnode.network_file = 'subj1.pck'
    >>> nx.run()                 # doctest: +SKIP

    Inputs::

        inputnode.extra_field
        inputnode.network_file

    Outputs::

        outputnode.network_files
        outputnode.csv_files
        outputnode.matlab_files

    """
    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["extra_field", "network_file"]),
        name="inputnode")

    pipeline = pe.Workflow(name=name)

    ntwkMetrics = pe.Node(
        interface=cmtk.NetworkXMetrics(), name="NetworkXMetrics")
    Matlab2CSV_node = pe.Node(
        interface=misc.Matlab2CSV(), name="Matlab2CSV_node")
    MergeCSVFiles_node = pe.Node(
        interface=misc.MergeCSVFiles(), name="MergeCSVFiles_node")
    MergeCSVFiles_node.inputs.extra_column_heading = extra_column_heading

    Matlab2CSV_global = Matlab2CSV_node.clone(name="Matlab2CSV_global")
    MergeCSVFiles_global = MergeCSVFiles_node.clone(
        name="MergeCSVFiles_global")
    MergeCSVFiles_global.inputs.extra_column_heading = extra_column_heading

    mergeNetworks = pe.Node(interface=util.Merge(2), name="mergeNetworks")
    mergeCSVs = mergeNetworks.clone("mergeCSVs")

    pipeline.connect([(inputnode, ntwkMetrics, [("network_file", "in_file")])])
    pipeline.connect([(ntwkMetrics, Matlab2CSV_node, [("node_measures_matlab",
                                                       "in_file")])])
    pipeline.connect([(ntwkMetrics, Matlab2CSV_global,
                       [("global_measures_matlab", "in_file")])])

    pipeline.connect([(Matlab2CSV_node, MergeCSVFiles_node, [("csv_files",
                                                              "in_files")])])
    pipeline.connect([(inputnode, MergeCSVFiles_node,
                       [(("extra_field", add_nodal_to_filename),
                         "out_file")])])
    pipeline.connect([(inputnode, MergeCSVFiles_node, [("extra_field",
                                                        "extra_field")])])
    pipeline.connect([(inputnode, MergeCSVFiles_node,
                       [(("network_file", pullnodeIDs), "row_headings")])])

    pipeline.connect([(Matlab2CSV_global, MergeCSVFiles_global,
                       [("csv_files", "in_files")])])
    pipeline.connect([(Matlab2CSV_global, MergeCSVFiles_global,
                       [(("csv_files", remove_identical_paths),
                         "column_headings")])])
    # MergeCSVFiles_global.inputs.row_heading_title = 'metric'
    # MergeCSVFiles_global.inputs.column_headings = ['average']

    pipeline.connect([(inputnode, MergeCSVFiles_global,
                       [(("extra_field", add_global_to_filename),
                         "out_file")])])
    pipeline.connect([(inputnode, MergeCSVFiles_global, [("extra_field",
                                                          "extra_field")])])

    pipeline.connect([(inputnode, mergeNetworks, [("network_file", "in1")])])
    pipeline.connect([(ntwkMetrics, mergeNetworks, [("gpickled_network_files",
                                                     "in2")])])

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=[
            "network_files", "csv_files", "matlab_files", "node_csv",
            "global_csv"
        ]),
        name="outputnode")

    pipeline.connect([(MergeCSVFiles_node, outputnode, [("csv_file",
                                                         "node_csv")])])
    pipeline.connect([(MergeCSVFiles_global, outputnode, [("csv_file",
                                                           "global_csv")])])

    pipeline.connect([(MergeCSVFiles_node, mergeCSVs, [("csv_file", "in1")])])
    pipeline.connect([(MergeCSVFiles_global, mergeCSVs, [("csv_file",
                                                          "in2")])])
    pipeline.connect([(mergeNetworks, outputnode, [("out", "network_files")])])
    pipeline.connect([(mergeCSVs, outputnode, [("out", "csv_files")])])
    pipeline.connect([(ntwkMetrics, outputnode, [("matlab_matrix_files",
                                                  "matlab_files")])])
    return pipeline


def create_cmats_to_csv_pipeline(name="cmats_to_csv",
                                 extra_column_heading="subject"):
    """Creates a workflow to convert the outputs from CreateMatrix into a single
    comma-separated value text file. An extra column / field is also added to the
    text file. Typically, the user would connect the subject name to this field.

    Example
    -------

    >>> from nipype.workflows.dmri.connectivity.nx import create_cmats_to_csv_pipeline
    >>> csv = create_cmats_to_csv_pipeline("cmats_to_csv", "subject_id")
    >>> csv.inputs.inputnode.extra_field = 'subj1'
    >>> csv.inputs.inputnode.matlab_matrix_files = ['subj1_cmatrix.mat', 'subj1_mean_fiber_length.mat', 'subj1_median_fiber_length.mat', 'subj1_fiber_length_std.mat']
    >>> csv.run()                 # doctest: +SKIP

    Inputs::

        inputnode.extra_field
        inputnode.matlab_matrix_files

    Outputs::

        outputnode.csv_file

    """
    inputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["extra_field", "matlab_matrix_files"]),
        name="inputnode")

    pipeline = pe.Workflow(name=name)

    Matlab2CSV = pe.MapNode(
        interface=misc.Matlab2CSV(), name="Matlab2CSV", iterfield=["in_file"])
    MergeCSVFiles = pe.Node(
        interface=misc.MergeCSVFiles(), name="MergeCSVFiles")
    MergeCSVFiles.inputs.extra_column_heading = extra_column_heading

    pipeline.connect([(inputnode, Matlab2CSV, [("matlab_matrix_files",
                                                "in_file")])])
    pipeline.connect([(Matlab2CSV, MergeCSVFiles, [("csv_files",
                                                    "in_files")])])
    pipeline.connect([(inputnode, MergeCSVFiles, [("extra_field",
                                                   "extra_field")])])

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=["csv_file"]),
        name="outputnode")

    pipeline.connect([(MergeCSVFiles, outputnode, [("csv_file", "csv_file")])])
    return pipeline
