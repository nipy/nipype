"""
==================================================
dMRI: Group connectivity - Camino, FSL, FreeSurfer
==================================================

Introduction
============

This script, dmri_group_connectivity_camino.py, runs group-based connectivity analysis using
the dmri.camino.connectivity_mapping Nipype workflow. Further detail on the processing can be
found in :ref:`dmri_connectivity. This tutorial can be run using:

    python dmri_group_connectivity_camino.py

We perform this analysis using one healthy subject and two subjects who suffer from Parkinson's disease.

The whole package (960 mb as .tar.gz / 1.3 gb uncompressed) including the Freesurfer directories for these subjects, can be acquired from here:

    * http://db.tt/b6F1t0QV

A data package containing the outputs of this pipeline can be obtained from here:

    * http://db.tt/kNvAI751

Along with Camino, Camino-Trackvis, FSL, and Freesurfer, you must also have the Connectome File Format
library installed as well as the Connectome Mapper.

    * Camino: http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Main.HomePage
    * Camino-Trackvis: http://www.nitrc.org/projects/camino-trackvis/
    * FSL: http://www.fmrib.ox.ac.uk/fsl/
    * Freesurfer: http://surfer.nmr.mgh.harvard.edu/
    * CTMK: http://www.cmtk.org/
    * CFF: sudo apt-get install python-cfflib

Or on github at:

    * CFFlib: https://github.com/LTS5/cfflib
    * CMP: https://github.com/LTS5/cmp

Output data can be visualized in ConnectomeViewer, TrackVis,
and anything that can view Nifti files.

    * ConnectomeViewer: https://github.com/LTS5/connectomeviewer
    * TrackVis: http://trackvis.org/

The fiber data is available in Numpy arrays, and the connectivity matrix
is also produced as a MATLAB matrix.



Import the workflows
--------------------
First, we import the necessary modules from nipype.
"""

import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import os.path as op                      # system functions
import cmp
from nipype.workflows.dmri.camino.group_connectivity import create_group_connectivity_pipeline
from nipype.workflows.dmri.connectivity.group_connectivity import (create_merge_networks_by_group_workflow,
create_merge_group_networks_workflow, create_average_networks_by_group_workflow)

"""
Set the proper directories
--------------------------
First, we import the necessary modules from nipype.
"""

fs_dir = op.abspath('/usr/local/freesurfer')
subjects_dir = op.abspath('groupcondatapackage/subjects/')
data_dir = op.abspath('groupcondatapackage/data/')
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
Define the groups
-----------------
Here we define the groups for this study. We would like to search for differences between the healthy subject and the two
vegetative patients. The group list is defined as a Python dictionary (see http://docs.python.org/tutorial/datastructures.html),
with group IDs ('controls', 'parkinsons') as keys, and subject/patient names as values. We set the main output directory as 'groupcon'.
"""

group_list = {}
group_list['controls'] = ['cont17']
group_list['parkinsons'] = ['pat10', 'pat20']

"""
The output directory must be named as well.
"""

global output_dir
output_dir = op.abspath('dmri_group_connectivity_camino')

"""
Main processing loop
====================
The title for the final grouped-network connectome file is dependent on the group names. The resulting file for this example
is 'parkinsons-controls.cff'. The following code implements the format a-b-c-...x.cff for an arbitary number of groups.

.. warning::

    The 'info' dictionary below is used to define the input files. In this case, the diffusion weighted image contains the string 'dwi'.
    The same applies to the b-values and b-vector files, and this must be changed to fit your naming scheme.

This line creates the processing workflow given the information input about the groups and subjects.

.. seealso::

    * nipype/workflows/dmri/mrtrix/group_connectivity.py
    * nipype/workflows/dmri/camino/connectivity_mapping.py
    * :ref:`dmri_connectivity`

The purpose of the second-level workflow is simple: It is used to merge each
subject's CFF file into one, so that there is a single file containing all of the
networks for each group. This can be useful for performing Network Brain Statistics
using the NBS plugin in ConnectomeViewer.

.. seealso::

    http://www.connectomeviewer.org/documentation/users/tutorials/tut_nbs.html

"""


title = ''
for idx, group_id in enumerate(group_list.keys()):
    title += group_id
    if not idx == len(group_list.keys()) - 1:
        title += '-'

    info = dict(dwi=[['subject_id', 'dti']],
                bvecs=[['subject_id', 'bvecs']],
                bvals=[['subject_id', 'bvals']])

    l1pipeline = create_group_connectivity_pipeline(group_list, group_id, data_dir, subjects_dir, output_dir, info)

    # Here we define the parcellation scheme and the number of tracks to produce
    parcellation_scheme = 'NativeFreesurfer'
    cmp_config = cmp.configuration.PipelineConfiguration()
    cmp_config.parcellation_scheme = parcellation_scheme
    l1pipeline.inputs.connectivity.inputnode.resolution_network_file = cmp_config._get_lausanne_parcellation(parcellation_scheme)['freesurferaparc']['node_information_graphml']

    l1pipeline.run()
    l1pipeline.write_graph(format='eps', graph2use='flat')

    # The second-level pipeline is created here
    l2pipeline = create_merge_networks_by_group_workflow(group_list, group_id, data_dir, subjects_dir, output_dir)
    l2pipeline.run()
    l2pipeline.write_graph(format='eps', graph2use='flat')

"""
Now that the for loop is complete there are two grouped CFF files each containing the appropriate subjects.
It is also convenient to have every subject in a single CFF file, so that is what the third-level pipeline does.
"""

l3pipeline = create_merge_group_networks_workflow(group_list, data_dir, subjects_dir, output_dir, title)
l3pipeline.run()
l3pipeline.write_graph(format='eps', graph2use='flat')

"""
The fourth and final workflow averages the networks and saves them in another CFF file
"""

l4pipeline = create_average_networks_by_group_workflow(group_list, data_dir, subjects_dir, output_dir, title)
l4pipeline.run()
l4pipeline.write_graph(format='eps', graph2use='flat')
