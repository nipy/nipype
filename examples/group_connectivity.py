"""
==================================================
Using Camino and CMTK for group connectivity analysis
==================================================

Introduction
============

This script, group_connectivity.py, runs group-based connectivity analysis using
the connectivity mapping Nipype workflow. Further detail on the processing can be
found in connectivity_tutorial.py. This tutorial can be run using:

    python group_connectivity.py

We perform this analysis using the FSL course data, as well as a set of two patients diagnosed as
in a vegetative state. The whole package (roughly 825 mb), including the Freesurfer directories
for these subjects, can be acquired from here:

    make a data package

Along with Camino (http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Main.HomePage),
Camino-Trackvis (http://www.nitrc.org/projects/camino-trackvis/), FSL (http://www.fmrib.ox.ac.uk/fsl/),
and Freesurfer (http://surfer.nmr.mgh.harvard.edu/), you must also have the Connectome File Format
library installed as well as the Connectome Mapper.

    http://www.cmtk.org/

Or on github at:

    CFFlib: https://github.com/LTS5/cfflib
    CMP: https://github.com/LTS5/cmp

Output data can be visualized in the ConnectomeViewer

    ConnectomeViewer: https://github.com/LTS5/connectomeviewer

First, we import the necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.cmtk as cmtk
import nipype.workflows.camino as cmonwk
import os, os.path as op                      # system functions

"""
We use the following functions to scrape the voxel and data dimensions of the input images. This allows the
pipeline to be flexible enough to accept and process images of varying size. The SPM Face tutorial
(spm_face_tutorial.py) also implements this inferral of voxel size from the data.
"""

def get_vox_dims(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]

def get_data_dims(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    datadims = hdr.get_data_shape()
    return [int(datadims[0]), int(datadims[1]), int(datadims[2])]

def get_affine(volume):
    import nibabel as nb
    nii = nb.load(volume)
    return nii.get_affine()

"""
We also define functions to select the proper parcellation/segregation file from Freesurfer's output for each subject.
For the mapping in this tutorial, we use the aparc+seg.mgz file. While it is possible to change this to use the regions
defined in aparc.a2009s+aseg.mgz, one would also have to write/obtain a network resolution map defining the nodes based
on those regions.
"""

def select_aparc(list_of_files):
    for in_file in list_of_files:
        if 'aparc+aseg.mgz' in in_file:
            idx = list_of_files.index(in_file)
    return list_of_files[idx]

def select_aparc_annot(list_of_files):
    for in_file in list_of_files:
        if '.aparc.annot' in in_file:
            idx = list_of_files.index(in_file)
    return list_of_files[idx]

"""
This needs to point to the freesurfer subjects directory. The data package linked above can be extracted in the Nipype
examples directory. It contains two folders; one containing the Freesurfer directories for each subject, titled 'freesurfer',
and another containing the 4D diffusion-weighted image and associated bvecs and bvals, titled 'exdata'.
"""

fs_dir = op.abspath('/usr/local/freesurfer')
subjects_dir = op.abspath('subjects/')
data_dir = op.abspath('exdata/')
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
Here we define the groups for this study. We would like to search for differences between the healthy subject and the two
vegetative patients. The group list is defined as a Python dictionary (see http://docs.python.org/tutorial/datastructures.html),
with group IDs ('controls', 'coma') as keys, and subject/patient names as values. We set the main output directory as 'groupcon'.
"""

group_list = {}
group_list['controls']=['subj1']
group_list['coma']=['BT_VS','DF_VS']

global output_dir
output_dir = op.abspath('groupcon')

"""
We also define a short function to return the desired working directory given an input group ID.
"""

def getoutdir(group_id):
    import os
    global output_dir
    return op.join(op.join(output_dir, 'workingdir'),'%s' % group_id)

"""
Main processing loop.
"""
title = ''
for idx, group_id in enumerate(group_list.keys()):
    """
    The title for the final grouped-network connectome file is dependent on the group names. The resulting file for this example
    is 'coma-controls.cff'. The following code implements the format a-b-c-...x.cff for an arbitary number of groups.
    """
    title += group_id
    if not idx == len(group_list.keys())-1:
        title += '-'
    group_infosource = pe.Node(interface=util.IdentityInterface(fields=['group_id']), name="group_infosource")
    group_infosource.inputs.group_id = group_id

    subject_list = group_list[group_id]

    subj_infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="subj_infosource")
    subj_infosource.iterables = ('subject_id', subject_list)

    info = dict(dwi=[['subject_id', 'dwi']],
                bvecs=[['subject_id','bvecs']],
                bvals=[['subject_id','bvals']])

    datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                   outfields=info.keys()),
                         name = 'datasource')

    datasource.inputs.template = "%s/%s"
    datasource.inputs.base_directory = data_dir
    datasource.inputs.field_template = dict(dwi='%s/%s.nii')
    datasource.inputs.template_args = info
    datasource.inputs.base_directory = data_dir

    """
    Create a connectivity mapping workflow
    """
    conmapper = cmonwk.create_connectivity_pipeline("nipype_conmap")
    conmapper.inputs.inputnode.subjects_dir = subjects_dir
    conmapper.base_dir = op.abspath('conmapper')

    datasink = pe.Node(interface=nio.DataSink(), name="datasink")
    datasink.inputs.base_directory = output_dir
    datasink.inputs.container = group_id
    datasink.inputs.cff_dir = getoutdir(group_id)

    l1pipeline = pe.Workflow(name="l1pipeline")
    l1pipeline.base_dir = output_dir
    l1pipeline.base_output_dir=group_id
    l1pipeline.connect([(subj_infosource, conmapper,[('subject_id', 'inputnode.subject_id')])])
    l1pipeline.connect([(subj_infosource, datasource,[('subject_id', 'subject_id')])])
    l1pipeline.connect([(datasource, conmapper, [("dwi", "inputnode.dwi"),
                                              ("bvals", "inputnode.bvals"),
                                              ("bvecs", "inputnode.bvecs"),
                                              ])])
    l1pipeline.connect([(conmapper, datasink, [("outputnode.connectome", "@l1output.cff"),
                                              ("outputnode.fa", "@l1output.fa"),
                                              ("outputnode.tracts", "@l1output.tracts"),
                                              ("outputnode.trace", "@l1output.trace"),
                                              ("outputnode.cmatrix", "@l1output.cmatrix"),
                                              ])])
    l1pipeline.connect([(group_infosource, datasink,[('group_id','@group_id')])])

    if __name__ == '__main__':
        l1pipeline.run()
        l1pipeline.write_graph(format='eps',graph2use='flat')

    """
    Level 2 pipeline starts here
    """

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
    l2datasink.inputs.cff_dir = getoutdir(group_id)

    l2pipeline = pe.Workflow(name="l2output")
    l2pipeline.base_dir = op.abspath('groupcon/l2output')
    l2pipeline.connect([(group_infosource, l2infosource,[('group_id','group_id')])])

    l2pipeline.connect([
                        (l2infosource,l2source,[('group_id', 'group_id')]),
                        (l2source,l2inputnode,[('CFFfiles','CFFfiles')]),
                    ])

    l2pipeline.connect([(l2inputnode,MergeCNetworks,[('CFFfiles','in_files')])])
    l2pipeline.connect([(group_infosource,MergeCNetworks,[('group_id','out_file')])])
    l2pipeline.connect([(MergeCNetworks, l2datasink, [('connectome_file', '@l2output')])])
    l2pipeline.connect([(group_infosource, l2datasink,[('group_id','@group_id')])])

    if __name__ == '__main__':
        l2pipeline.run()
        l2pipeline.write_graph(format='eps',graph2use='flat')

"""
Next the groups are combined in the 3rd level pipeline.
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

if __name__ == '__main__':
    l3pipeline.run()
    l3pipeline.write_graph(format='eps',graph2use='flat')
