"""
============================================
Group connectivity - MRtrix, FSL, FreeSurfer
============================================

Introduction
============

This script, group_connectivity.py, runs group-based connectivity analysis using
the connectivity_mapping_advanced Nipype workflow. Further detail on the processing can be
found in connectivity_tutorial.py. This tutorial can be run using:

    python group_mrtrix_connectivity_workflowed.py

We perform this analysis using two healthy subjects: subj1 (from the FSL course data) and subj2.
We also process one coma patient who has suffers from traumatic brain damage.

The whole package (845 MB zipped, 1.2 GB unzipped) including the Freesurfer directories for these subjects, can be acquired from here:

    http://dl.dropbox.com/u/315714/groupcondatapackage.zip?dl=1

Along with MRtrix, FSL, and Freesurfer, you must also have the Connectome File Format
library installed as well as the Connectome Mapper (cmp).

    MRtrix: http://www.brain.org.au/software/mrtrix/
    FSL: http://www.fmrib.ox.ac.uk/fsl/
    Freesurfer: http://surfer.nmr.mgh.harvard.edu/
    CTMK: http://www.cmtk.org/
    CFF: sudo apt-get install python-cfflib

Or on github at:

    CFFlib: https://github.com/LTS5/cfflib
    CMP: https://github.com/LTS5/cmp

Output data can be visualized in ConnectomeViewer, TrackVis, Gephi,
the MRtrix Viewer (mrview), and anything that can view Nifti files.

    ConnectomeViewer: https://github.com/LTS5/connectomeviewer
    TrackVis: http://trackvis.org/
    Gephi: http://gephi.org/

The fiber data is available in Numpy arrays, and the connectivity matrix
is also produced as a MATLAB matrix.



Import the workflows
--------------------
First, we import the necessary modules from nipype.
"""

import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import  os.path as op                     # system functions
import cmp
from nipype.workflows.dmri.mrtrix.group_connectivity import create_mrtrix_group_cff_pipeline_part1
from nipype.workflows.dmri.camino.group_connectivity import (create_group_cff_pipeline_part2_with_CSVstats,
create_group_cff_pipeline_part3_with_CSVstats, create_group_cff_pipeline_part4)

"""
Set the proper directories
--------------------------
First, we import the necessary modules from nipype.
"""

subjects_dir = op.abspath('groupcondatapackage/subjects/')
data_dir = op.abspath('groupcondatapackage/data/')
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
Define the groups
-----------------
Here we define the groups for this study. We would like to search for differences between the healthy subject and the two
vegetative patients. The group list is defined as a Python dictionary (see http://docs.python.org/tutorial/datastructures.html),
with group IDs ('controls', 'coma') as keys, and subject/patient names as values. We set the main output directory as 'groupcon'.
"""

group_list = {}
group_list['controls'] = ['subj1', 'subj2']
group_list['coma'] = ['traumatic']

"""
The output directory must be named as well.
"""

global output_dir
output_dir = op.abspath('mrtrix_groupcon_workflowed')

"""
Main processing loop
====================
The title for the final grouped-network connectome file is dependent on the group names. The resulting file for this example
is 'coma-controls.cff'. The following code implements the format a-b-c-...x.cff for an arbitary number of groups.
"""

title = ''
for idx, group_id in enumerate(group_list.keys()):
    title += group_id
    if not idx == len(group_list.keys()) - 1:
        title += '-'

    """

    .. warning::
        The 'info' dictionary below is used to define the input files. In this case, the diffusion weighted image contains the string 'dwi'.
        The same applies to the b-values and b-vector files, and this must be changed to fit your naming scheme.


    """
    info = dict(dwi=[['subject_id', 'dwi']],
                    bvecs=[['subject_id', 'bvecs']],
                    bvals=[['subject_id', 'bvals']])

    """
    This line creates the processing workflow given the information input about the groups and subjects.

    .. seealso::
        * nipype/workflows/mrtrix/group_connectivity.py
        * nipype/workflows/mrtrix/connectivity_mapping.py
        * connectivity_tutorial_advanced.py

    """

    l1pipeline = create_mrtrix_group_cff_pipeline_part1(group_list, group_id, data_dir, subjects_dir, output_dir, info)

    """
This is used to demonstrate the ease through which different parameters can be set for each group.
These values relate to the absolute threshold used on the fractional anisotropy map. This is done
in order to identify single-fiber voxels. In brains with more damage, however, it may be necessary
to reduce the threshold, since their brains are have lower average fractional anisotropy values.
    """

    if group_id == 'coma':
        print 'Coma'
        l1pipeline.inputs.connectivity.mapping.threshold_FA.absolute_threshold_value = 0.5
        l1pipeline.inputs.connectivity.mapping.fsl2mrtrix.invert_x = True
        l1pipeline.inputs.connectivity.mapping.coregister.dof = 12
    else:
        print 'Control'
        l1pipeline.inputs.connectivity.mapping.threshold_FA.absolute_threshold_value = 0.7
        l1pipeline.inputs.connectivity.mapping.fsl2mrtrix.invert_y = True

    """
These lines relate to inverting the b-vectors in the encoding file, and setting the
maximum harmonic order of the pre-tractography spherical deconvolution step. This is
done to show how to set inputs that will affect both groups.
    """

    l1pipeline.inputs.connectivity.mapping.csdeconv.maximum_harmonic_order = 6
    l1pipeline.inputs.connectivity.mapping.tck2trk.flipy = True
    l1pipeline.inputs.connectivity.mapping.tck2trk.flipz = True

    """
Define the parcellation scheme to use.
    """

    parcellation_name = 'scale500'
    l1pipeline.inputs.connectivity.mapping.Parcellate.parcellation_name = parcellation_name
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = "Lausanne2008"
    l1pipeline.inputs.connectivity.mapping.CreateMatrix.resolution_network_file = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']

    """
Set the maximum number of tracks to obtain
    """

    l1pipeline.inputs.connectivity.mapping.probCSDstreamtrack.maximum_number_of_tracks = 100000

    """
The first level pipeline we have tweaked here is run within the for loop.
    """

    l1pipeline.run()
    l1pipeline.write_graph(format='eps', graph2use='flat')

    """
    Next we create and run the second-level pipeline. The purpose of this workflow is simple:
    It is used to merge each subject's CFF file into one, so that there is a single file containing
    all of the networks for each group. This can be useful for performing Network Brain Statistics
    using the NBS plugin in ConnectomeViewer.

    .. seealso::

        http://www.connectomeviewer.org/documentation/users/tutorials/tut_nbs.html

    """

    l2pipeline = create_group_cff_pipeline_part2_with_CSVstats(group_list, group_id, data_dir, subjects_dir, output_dir)
    l2pipeline.run()
    l2pipeline.write_graph(format='eps', graph2use='flat')

"""
Now that the for loop is complete there are two grouped CFF files each containing the appropriate subjects.
It is also convenient to have every subject in a single CFF file, so that is what the third-level pipeline does.
"""

l3pipeline = create_group_cff_pipeline_part3_with_CSVstats(group_list, data_dir, subjects_dir, output_dir, title)
l3pipeline.run()
l3pipeline.write_graph(format='eps', graph2use='flat')

"""
The fourth and final workflow averages the networks and saves them in another CFF file
"""

l4pipeline = create_group_cff_pipeline_part4(group_list, data_dir, subjects_dir, output_dir, title)
l4pipeline.run()
l4pipeline.write_graph(format='eps', graph2use='flat')
