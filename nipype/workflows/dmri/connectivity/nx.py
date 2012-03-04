import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
import nipype.interfaces.cmtk as cmtk
import nipype.algorithms.misc as misc

def create_networkx_pipeline(name="networkx", extra_column_heading="subject"):
    inputnode = pe.Node(interface = util.IdentityInterface(fields=["extra_field", "network_file"]),
                        name="inputnode")

    pipeline = pe.Workflow(name=name)
  
    ntwkMetrics = pe.Node(interface=cmtk.NetworkXMetrics(), name="NetworkXMetrics")
    Matlab2CSV_node = pe.Node(interface=misc.Matlab2CSV(), name="Matlab2CSV_node")
    MergeCSVFiles_node = pe.Node(interface=misc.MergeCSVFiles(), name="MergeCSVFiles_node")
    MergeCSVFiles_node.inputs.extra_column_heading = extra_column_heading

    Matlab2CSV_global = Matlab2CSV_node.clone(name="Matlab2CSV_global")

    mergeNetworks = pe.Node(interface=util.Merge(2), name="mergeNetworks")
    mergeCSVs = mergeNetworks.clone("mergeCSVs")

    pipeline.connect([(inputnode, ntwkMetrics,[("network_file","in_file")])])
    pipeline.connect([(ntwkMetrics, Matlab2CSV_node,[("node_measures_matlab","in_file")])])
    pipeline.connect([(ntwkMetrics, Matlab2CSV_global,[("global_measures_matlab","in_file")])])
    
    pipeline.connect([(Matlab2CSV_node, MergeCSVFiles_node,[("csv_files","in_files")])])
    pipeline.connect([(inputnode, MergeCSVFiles_node,[("extra_field","out_file")])])
    pipeline.connect([(inputnode, MergeCSVFiles_node,[("extra_field","extra_field")])])

    pipeline.connect([(inputnode, mergeNetworks,[("network_file","in1")])])
    pipeline.connect([(ntwkMetrics, mergeNetworks,[("gpickled_network_files","in2")])])
    
    outputnode = pe.Node(interface = util.IdentityInterface(fields=["network_files",
    "csv_files", "matlab_files", "node_csv", "global_csv"]),
                        name="outputnode")

    pipeline.connect([(MergeCSVFiles_node, outputnode, [("csv_file", "node_csv")])])
    pipeline.connect([(Matlab2CSV_global, outputnode, [("csv_files", "global_csv")])])

    pipeline.connect([(MergeCSVFiles_node, mergeCSVs, [("csv_file", "in1")])])
    pipeline.connect([(Matlab2CSV_global, mergeCSVs, [("csv_files", "in2")])])    
    pipeline.connect([(mergeNetworks, outputnode, [("out", "network_files")])])
    pipeline.connect([(mergeCSVs, outputnode, [("out", "csv_files")])])
    pipeline.connect([(ntwkMetrics, outputnode,[("matlab_matrix_files","matlab_files")])])
    return pipeline

def create_cmats_to_csv_pipeline(name="cmats_to_csv", extra_column_heading="subject"):
    inputnode = pe.Node(interface = util.IdentityInterface(fields=["extra_field", "matlab_matrix_files"]),
                        name="inputnode")

    pipeline = pe.Workflow(name=name)
   
    Matlab2CSV = pe.MapNode(interface=misc.Matlab2CSV(), name="Matlab2CSV", iterfield=["in_file"])
    MergeCSVFiles = pe.Node(interface=misc.MergeCSVFiles(), name="MergeCSVFiles")
    MergeCSVFiles.inputs.extra_column_heading = extra_column_heading
   
    pipeline.connect([(inputnode, Matlab2CSV,[("matlab_matrix_files","in_file")])])
    pipeline.connect([(Matlab2CSV, MergeCSVFiles,[("csv_files","in_files")])])
    pipeline.connect([(inputnode, MergeCSVFiles,[("extra_field","extra_field")])])
    
    outputnode = pe.Node(interface = util.IdentityInterface(fields=["csv_file"]),
                        name="outputnode")

    pipeline.connect([(MergeCSVFiles, outputnode, [("csv_file", "csv_file")])])
    return pipeline
