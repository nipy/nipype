import os.path as op
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.interfaces.cmtk as cmtk
import nipype.algorithms.misc as misc
import nipype.pipeline.engine as pe          # pypeline engine
from nipype.utils.misc import package_check
import warnings
try:
    package_check('cmp')
except Exception, e:
    warnings.warn('cmp not installed')
else:
    import cmp

def pullnodeIDs(in_network, name_key='dn_name'):
    """ This function will return the values contained, for each node in
    a network, given an input key. By default it will return the node names
    """
    import networkx as nx
    import numpy as np
    from nipype.interfaces.base import isdefined
    if not isdefined(in_network):
        raise ValueError
        return None
    try:
        ntwk = nx.read_graphml(in_network)
    except:
        ntwk = nx.read_gpickle(in_network)
    nodedata = ntwk.node
    ids = []
    integer_nodelist = []
    for node in nodedata.keys():
        integer_nodelist.append(int(node))
    for node in np.sort(integer_nodelist):
        try:
            nodeid = nodedata[node][name_key]
        except KeyError:
            nodeid = nodedata[str(node)][name_key]
        ids.append(nodeid)
    return ids


def concatcsv(in_files):
    """ This function will contatenate two "comma-separated value"
    text files, but remove the first row (usually column headers) from
    all but the first file.
    """
    import os.path as op
    from nipype.utils.filemanip import split_filename

    if not isinstance(in_files,list):
        return in_files
    if isinstance(in_files[0],list):
        in_files = in_files[0]
    first = open(in_files[0], 'r')
    path, name, ext = split_filename(in_files[0])
    out_name = op.join(path, 'concat.csv')
    out_file = open(out_name, 'w')
    out_file.write(first.readline())
    first.close()
    for in_file in in_files:
        file_to_read = open(in_file, 'r')
        scrap_first_line = file_to_read.readline()
        for line in file_to_read:
            out_file.write(line)
    return out_name


def create_merge_networks_by_group_workflow(group_list, group_id, data_dir, subjects_dir, output_dir):
    """Creates a second-level pipeline to merge the Connectome File Format (CFF) outputs from the group-level
    MRtrix structural connectivity processing pipeline into a single CFF file for each group.

    Example
    -------

    >>> import nipype.workflows.dmri.connectivity.group_connectivity as groupwork
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> group_id = 'group1'
    >>> l2pipeline = groupwork.create_merge_networks_by_group_workflow(group_list, group_id, data_dir, subjects_dir, output_dir)
    >>> l2pipeline.run()                 # doctest: +SKIP

    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        group_id: String containing the group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
    """
    group_infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name="group_infosource")
    group_infosource.inputs.group_id = group_id

    l2infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name='l2infosource')

    l2source = pe.Node(nio.DataGrabber(infields=['group_id'], outfields=['CFFfiles']), name='l2source')
    l2source.inputs.template_args = dict(CFFfiles=[['group_id']])
    l2source.inputs.template=op.join(output_dir,'%s/cff/*/connectome.cff')
    l2source.inputs.base_directory = data_dir

    l2inputnode = pe.Node(interface=util.IdentityInterface(fields=['CFFfiles']), name='l2inputnode')
    MergeCNetworks = pe.Node(interface=cmtk.MergeCNetworks(), name="MergeCNetworks")

    l2datasink = pe.Node(interface=nio.DataSink(), name="l2datasink")
    l2datasink.inputs.base_directory = output_dir
    l2datasink.inputs.container = group_id

    l2pipeline = pe.Workflow(name="l2output")
    l2pipeline.base_dir = op.join(output_dir, 'l2output')
    l2pipeline.connect([(group_infosource, l2infosource,[('group_id','group_id')])])

    l2pipeline.connect([
                        (l2infosource,l2source,[('group_id', 'group_id')]),
                        (l2source,l2inputnode,[('CFFfiles','CFFfiles')]),
                    ])

    l2pipeline.connect([(l2inputnode,MergeCNetworks,[('CFFfiles','in_files')])])
    l2pipeline.connect([(group_infosource,MergeCNetworks,[('group_id','out_file')])])
    l2pipeline.connect([(MergeCNetworks, l2datasink, [('connectome_file', '@l2output')])])
    l2pipeline.connect([(group_infosource, l2datasink,[('group_id','@group_id')])])
    return l2pipeline

def create_merge_network_results_by_group_workflow(group_list, group_id, data_dir, subjects_dir, output_dir):
    """Creates a second-level pipeline to merge the Connectome File Format (CFF) outputs from the group-level
    MRtrix structural connectivity processing pipeline into a single CFF file for each group.

    Example
    -------

    >>> import nipype.workflows.dmri.connectivity.group_connectivity as groupwork
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> group_id = 'group1'
    >>> l2pipeline = groupwork.create_merge_network_results_by_group_workflow(group_list, group_id, data_dir, subjects_dir, output_dir)
    >>> l2pipeline.run()                 # doctest: +SKIP

    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        group_id: String containing the group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
    """
    group_infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name="group_infosource")
    group_infosource.inputs.group_id = group_id

    l2infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id',
    'merged',
    ]), name='l2infosource')

    l2source = pe.Node(nio.DataGrabber(infields=['group_id'], outfields=['CFFfiles',
    'merged',
    ]), name='l2source')

    l2source.inputs.template_args = dict(CFFfiles=[['group_id']],
        merged=[['group_id']])
    l2source.inputs.base_directory = data_dir
    l2source.inputs.template = '%s/%s'
    l2source.inputs.field_template=dict(CFFfiles=op.join(output_dir,'%s/cff/*/connectome.cff'),
        merged=op.join(output_dir,'%s/nxcsv/*/*.csv'))

    l2inputnode = pe.Node(interface=util.IdentityInterface(fields=['CFFfiles',
    'merged',
    'network_file',
     ]), name='l2inputnode')

    MergeCNetworks = pe.Node(interface=cmtk.MergeCNetworks(), name="MergeCNetworks")

    l2datasink = pe.Node(interface=nio.DataSink(), name="l2datasink")
    l2datasink.inputs.base_directory = output_dir
    l2datasink.inputs.container = group_id

    l2pipeline = pe.Workflow(name="l2output")
    l2pipeline.base_dir = op.join(output_dir, 'l2output')
    l2pipeline.connect([(group_infosource, l2infosource,[('group_id','group_id')])])

    l2pipeline.connect([
                        (l2infosource,l2source,[('group_id', 'group_id')]),
                        (l2source,l2inputnode,[('CFFfiles','CFFfiles')]),
                        (l2source,l2inputnode,[('merged','merged')]),
                    ])

    l2pipeline.connect([(l2inputnode,MergeCNetworks,[('CFFfiles','in_files')])])

    l2pipeline.connect([(group_infosource,MergeCNetworks,[('group_id','out_file')])])
    l2pipeline.connect([(MergeCNetworks, l2datasink, [('connectome_file', '@l2output')])])

    AddCSVColumn_metrics = pe.Node(interface=misc.AddCSVColumn(), name="AddCSVColumn_metrics")
    AddCSVColumn_metrics.inputs.extra_column_heading = 'group'
    AddCSVColumn_matrices = AddCSVColumn_metrics.clone(name="AddCSVColumn_matrices")

    l2pipeline.connect([(l2inputnode, AddCSVColumn_metrics,[(('merged', concatcsv), 'in_file')])])
    l2pipeline.connect([(group_infosource, AddCSVColumn_metrics,[('group_id','extra_field')])])
    l2pipeline.connect([(AddCSVColumn_metrics, l2datasink,[('csv_file','@l2output.csv')])])
    l2pipeline.connect([(group_infosource, l2datasink,[('group_id','@group_id')])])

    l2pipeline.connect([(l2inputnode, AddCSVColumn_matrices,[(('merged', concatcsv), 'in_file')])])
    l2pipeline.connect([(group_infosource, AddCSVColumn_matrices,[('group_id','extra_field')])])
    l2pipeline.connect([(AddCSVColumn_matrices, l2datasink,[('csv_file','@l2output.cmatrices_csv')])])
    return l2pipeline


def create_merge_group_networks_workflow(group_list, data_dir, subjects_dir, output_dir, title='group'):
    """Creates a third-level pipeline to merge the Connectome File Format (CFF) outputs from each group
    and combines them into a single CFF file for each group.

    Example
    -------

    >>> import nipype.workflows.dmri.connectivity.group_connectivity as groupwork
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> l3pipeline = groupwork.create_merge_group_networks_workflow(group_list, data_dir, subjects_dir, output_dir)
    >>> l3pipeline.run()                 # doctest: +SKIP

    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
        title: String to use as a title for the output merged CFF file (default 'group')
    """
    l3infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name='l3infosource')
    l3infosource.inputs.group_id = group_list.keys()

    l3source = pe.Node(nio.DataGrabber(infields=['group_id'], outfields=['CFFfiles']), name='l3source')
    l3source.inputs.template_args = dict(CFFfiles=[['group_id','group_id']])
    l3source.inputs.template=op.join(output_dir,'%s/%s.cff')

    l3inputnode = pe.Node(interface=util.IdentityInterface(fields=['Group_CFFs']), name='l3inputnode')

    MergeCNetworks_grp = pe.Node(interface=cmtk.MergeCNetworks(), name="MergeCNetworks_grp")
    MergeCNetworks_grp.inputs.out_file = title

    l3datasink = pe.Node(interface=nio.DataSink(), name="l3datasink")
    l3datasink.inputs.base_directory = output_dir

    l3pipeline = pe.Workflow(name="l3output")
    l3pipeline.base_dir = output_dir
    l3pipeline.connect([
                        (l3infosource,l3source,[('group_id', 'group_id')]),
                        (l3source,l3inputnode,[('CFFfiles','Group_CFFs')]),
                    ])

    l3pipeline.connect([(l3inputnode,MergeCNetworks_grp,[('Group_CFFs','in_files')])])
    l3pipeline.connect([(MergeCNetworks_grp, l3datasink, [('connectome_file', '@l3output')])])
    return l3pipeline


def create_merge_group_network_results_workflow(group_list, data_dir, subjects_dir, output_dir, title='group'):
    """Creates a third-level pipeline to merge the Connectome File Format (CFF) outputs from each group
    and combines them into a single CFF file for each group. This version of the third-level pipeline also
    concatenates the comma-separated value files for the NetworkX metrics and the connectivity matrices
    into single files.

    Example
    -------

    >>> import nipype.workflows.dmri.connectivity.group_connectivity as groupwork
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> l3pipeline = groupwork.create_merge_group_network_results_workflow(group_list, data_dir, subjects_dir, output_dir)
    >>> l3pipeline.run()                 # doctest: +SKIP

    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
        title: String to use as a title for the output merged CFF file (default 'group')
    """
    l3infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name='l3infosource')
    l3infosource.inputs.group_id = group_list.keys()

    l3source = pe.Node(nio.DataGrabber(infields=['group_id'], outfields=['CFFfiles', 'CSVmetrics', 'CSVmatrices']), name='l3source')
    l3source.inputs.template_args = dict(CFFfiles=[['group_id']], CSVmetrics=[['group_id']], CSVmatrices=[['group_id']])
    l3source.inputs.template = op.join(output_dir,'%s/%s')

    l3source.inputs.field_template=dict(CFFfiles=op.join(output_dir,'%s/*.cff'), CSVmetrics=op.join(output_dir,'%s/csv/*.csv'), CSVmatrices=op.join(output_dir,'%s/cmatrices_csv/*/*.csv'))

    l3inputnode = pe.Node(interface=util.IdentityInterface(fields=['Group_CFFs', 'Group_CSVmetrics', 'Group_CSVmatrices']), name='l3inputnode')

    MergeCNetworks_grp = pe.Node(interface=cmtk.MergeCNetworks(), name="MergeCNetworks_grp")
    MergeCNetworks_grp.inputs.out_file = title

    l3datasink = pe.Node(interface=nio.DataSink(), name="l3datasink")
    l3datasink.inputs.base_directory = output_dir

    l3pipeline = pe.Workflow(name="l3output")
    l3pipeline.base_dir = output_dir
    l3pipeline.connect([
                        (l3infosource,l3source,[('group_id', 'group_id')]),
                        (l3source,l3inputnode,[('CFFfiles','Group_CFFs')]),
                        (l3source,l3inputnode,[('CSVmetrics','Group_CSVmetrics')]),
                        (l3source,l3inputnode,[('CSVmatrices','Group_CSVmatrices')]),
                    ])

    l3pipeline.connect([(l3inputnode,MergeCNetworks_grp,[('Group_CFFs','in_files')])])
    l3pipeline.connect([(MergeCNetworks_grp, l3datasink, [('connectome_file', '@l3output')])])
    l3pipeline.connect([(l3inputnode, l3datasink,[(('Group_CSVmetrics', concatcsv), '@l3output.csvmetrics')])])
    l3pipeline.connect([(l3inputnode, l3datasink,[(('Group_CSVmatrices', concatcsv), '@l3output.csvmatrices')])])
    return l3pipeline


def create_average_networks_by_group_workflow(group_list, data_dir, subjects_dir, output_dir, title='group_average'):
    """Creates a fourth-level pipeline to average the networks for two groups and merge them into a single
    CFF file. This pipeline will also output the average networks in .gexf format, for visualization in other
    graph viewers, such as Gephi.

    Example
    -------

    >>> import nipype.workflows.dmri.connectivity.group_connectivity as groupwork
    >>> from nipype.testing import example_data
    >>> subjects_dir = '.'
    >>> data_dir = '.'
    >>> output_dir = '.'
    >>> group_list = {}
    >>> group_list['group1'] = ['subj1', 'subj2']
    >>> group_list['group2'] = ['subj3', 'subj4']
    >>> l4pipeline = groupwork.create_average_networks_by_group_workflow(group_list, data_dir, subjects_dir, output_dir)
    >>> l4pipeline.run()                 # doctest: +SKIP

    Inputs::

        group_list: Dictionary of subject lists, keyed by group name
        data_dir: Path to the data directory
        subjects_dir: Path to the Freesurfer 'subjects' directory
        output_dir: Path for the output files
        title: String to use as a title for the output merged CFF file (default 'group')
    """
    l4infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id1', 'group_id2']), name='l4infosource')
    l4infosource.inputs.group_id1 = group_list.keys()[0]
    l4infosource.inputs.group_id2 = group_list.keys()[1]

    l4info = dict(networks=[['group_id', '']], CMatrices=[['group_id', '']], fibmean=[['group_id', 'mean_fiber_length']],
        fibdev=[['group_id', 'fiber_length_std']])

    l4source_grp1 = pe.Node(nio.DataGrabber(infields=['group_id'], outfields=l4info.keys()), name='l4source_grp1')
    l4source_grp1.inputs.template = '%s/%s'
    l4source_grp1.inputs.field_template=dict(networks=op.join(output_dir,'%s/networks/*/*%s*.pck'), CMatrices=op.join(output_dir,'%s/cmatrix/*/*%s*.mat'),
        fibmean=op.join(output_dir,'%s/mean_fiber_length/*/*%s*.mat'), fibdev=op.join(output_dir,'%s/fiber_length_std/*/*%s*.mat'))
    l4source_grp1.inputs.base_directory = output_dir
    l4source_grp1.inputs.template_args = l4info

    l4source_grp2 = l4source_grp1.clone(name='l4source_grp2')

    l4inputnode = pe.Node(interface=util.IdentityInterface(fields=['networks_grp1','networks_grp2','CMatrices_grp1','CMatrices_grp2',
        'fibmean_grp1','fibmean_grp2','fibdev_grp1','fibdev_grp2']), name='l4inputnode')

    average_networks_grp1 = pe.Node(interface=cmtk.AverageNetworks(), name='average_networks_grp1')
    average_networks_grp2 = average_networks_grp1.clone('average_networks_grp2')

    averagecff = pe.Node(interface=cmtk.CFFConverter(), name="averagecff")
    averagecff.inputs.out_file = title

    merge_gpickled_averages = pe.Node(interface=util.Merge(2), name='merge_gpickled_averages')
    merge_gexf_averages = merge_gpickled_averages.clone('merge_gexf_averages')

    l4datasink = pe.Node(interface=nio.DataSink(), name="l4datasink")
    l4datasink.inputs.base_directory = output_dir

    l4pipeline = pe.Workflow(name="l4output")
    l4pipeline.base_dir = output_dir
    l4pipeline.connect([
                        (l4infosource,l4source_grp1,[('group_id1', 'group_id')]),
                        (l4infosource,l4source_grp2,[('group_id2', 'group_id')]),
                        (l4source_grp1,l4inputnode,[('CMatrices','CMatrices_grp1')]),
                        (l4source_grp2,l4inputnode,[('CMatrices','CMatrices_grp2')]),
                        (l4source_grp1,l4inputnode,[('networks','networks_grp1')]),
                        (l4source_grp2,l4inputnode,[('networks','networks_grp2')]),
                        (l4source_grp1,l4inputnode,[('fibmean','fibmean_grp1')]),
                        (l4source_grp2,l4inputnode,[('fibmean','fibmean_grp2')]),
                        (l4source_grp1,l4inputnode,[('fibdev','fibdev_grp1')]),
                        (l4source_grp2,l4inputnode,[('fibdev','fibdev_grp2')]),
                    ])

    l4pipeline.connect([(l4inputnode, average_networks_grp1,[('networks_grp1','in_files')])])
    l4pipeline.connect([(l4infosource, average_networks_grp1,[('group_id1','group_id')])])

    l4pipeline.connect([(l4inputnode, average_networks_grp2,[('networks_grp2','in_files')])])
    l4pipeline.connect([(l4infosource, average_networks_grp2,[('group_id2','group_id')])])

    l4pipeline.connect([(average_networks_grp1, merge_gpickled_averages,[('gpickled_groupavg','in1')])])
    l4pipeline.connect([(average_networks_grp2, merge_gpickled_averages,[('gpickled_groupavg','in2')])])

    l4pipeline.connect([(average_networks_grp1, merge_gexf_averages,[('gexf_groupavg','in1')])])
    l4pipeline.connect([(average_networks_grp2, merge_gexf_averages,[('gexf_groupavg','in2')])])

    l4pipeline.connect([(merge_gpickled_averages, l4datasink, [('out', '@l4output.gpickled')])])
    l4pipeline.connect([(merge_gpickled_averages, averagecff, [('out', 'gpickled_networks')])])
    l4pipeline.connect([(averagecff, l4datasink, [('connectome_file', '@l4output.averagecff')])])

    l4pipeline.connect([(merge_gexf_averages, l4datasink, [('out', '@l4output.gexf')])])
    return l4pipeline

