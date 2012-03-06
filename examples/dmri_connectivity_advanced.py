#!/usr/bin/env python
"""
=============================================
dMRI: Connectivity - MRtrix, CMTK, FreeSurfer
=============================================

Introduction
============

This script, connectivity_tutorial_advanced.py, demonstrates the ability to perform connectivity mapping
using Nipype for pipelining, Freesurfer for Reconstruction / Segmentation, MRtrix for spherical deconvolution
and tractography, and the Connectome Mapping Toolkit (CMTK) for further parcellation and connectivity analysis.

    python connectivity_tutorial_advanced.py

We perform this analysis using the FSL course data, which can be acquired from here:

    * http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

This pipeline also requires the Freesurfer directory for 'subj1' from the FSL course data.
To save time, this data can be downloaded from here:

    * http://dl.dropbox.com/u/315714/subj1.zip?dl=1

The result of this processing will be the connectome for subj1 as a Connectome File Format (CFF) File, using
the Lausanne2008 parcellation scheme. A data package containing the outputs of this pipeline can be obtained
from here:

    * http://db.tt/909Q3AC1

.. seealso::

	connectivity_tutorial.py
		Original tutorial using Camino and the NativeFreesurfer Parcellation Scheme

	www.cmtk.org
		For more info about the parcellation scheme

.. warning::

	The ConnectomeMapper (https://github.com/LTS5/cmp or www.cmtk.org) must be installed for this tutorial to function!

Packages and Data Setup
=======================

Import necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.mrtrix as mrtrix
import nipype.algorithms.misc as misc
import nipype.interfaces.cmtk as cmtk
import nipype.interfaces.dipy as dipy
import inspect
import os.path as op                      # system functions
from nipype.workflows.dmri.fsl.dti import create_eddy_correct_pipeline
from nipype.workflows.dmri.camino.connectivity_mapping import select_aparc_annot
from nipype.utils.misc import package_check
import warnings
from nipype.workflows.dmri.connectivity.nx import create_networkx_pipeline, create_cmats_to_csv_pipeline

try:
    package_check('cmp')
except Exception, e:
    warnings.warn('cmp not installed')
else:
    import cmp

"""
This needs to point to the freesurfer subjects directory (Recon-all must have been run on subj1 from the FSL course data)
Alternatively, the reconstructed subject data can be downloaded from:

	* http://dl.dropbox.com/u/315714/subj1.zip

"""

subjects_dir = op.abspath(op.join(op.curdir,'./subjects'))
fs.FSCommand.set_default_subjects_dir(subjects_dir)
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
This needs to point to the fdt folder you can find after extracting

	* http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

"""

data_dir = op.abspath(op.join(op.curdir,'exdata/'))
subject_list = ['subj1']

"""
Use infosource node to loop through the subject list and define the input files.
For our purposes, these are the diffusion-weighted MR image, b vectors, and b values.
"""

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])

"""
Use datasource node to perform the actual data grabbing.
Templates for the associated images are used to obtain the correct images.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"
datasource.inputs.base_directory = data_dir
datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz')
datasource.inputs.template_args = info

"""
The input node and Freesurfer sources declared here will be the main
conduits for the raw data to the rest of the processing pipeline.
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["subject_id","dwi", "bvecs", "bvals", "subjects_dir"]), name="inputnode")
inputnode.inputs.subjects_dir = subjects_dir

FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='fssource')
FreeSurferSourceLH = FreeSurferSource.clone('fssourceLH')
FreeSurferSourceLH.inputs.hemi = 'lh'
FreeSurferSourceRH = FreeSurferSource.clone('fssourceRH')
FreeSurferSourceRH.inputs.hemi = 'rh'

"""
Creating the workflow's nodes
=============================
"""

"""
Conversion nodes
----------------
"""

"""
A number of conversion operations are required to obtain NIFTI files from the FreesurferSource for each subject.
Nodes are used to convert the following:
    * Original structural image to NIFTI
    * Pial, white, inflated, and spherical surfaces for both the left and right hemispheres are converted to GIFTI for visualization in ConnectomeViewer
    * Parcellated annotation files for the left and right hemispheres are also converted to GIFTI

"""

mri_convert_Brain = pe.Node(interface=fs.MRIConvert(), name='mri_convert_Brain')
mri_convert_Brain.inputs.out_type = 'nii'
mri_convert_ROI_scale500 = mri_convert_Brain.clone('mri_convert_ROI_scale500')

mris_convertLH = pe.Node(interface=fs.MRIsConvert(), name='mris_convertLH')
mris_convertLH.inputs.out_datatype = 'gii'
mris_convertRH = mris_convertLH.clone('mris_convertRH')
mris_convertRHwhite = mris_convertLH.clone('mris_convertRHwhite')
mris_convertLHwhite = mris_convertLH.clone('mris_convertLHwhite')
mris_convertRHinflated = mris_convertLH.clone('mris_convertRHinflated')
mris_convertLHinflated = mris_convertLH.clone('mris_convertLHinflated')
mris_convertRHsphere = mris_convertLH.clone('mris_convertRHsphere')
mris_convertLHsphere = mris_convertLH.clone('mris_convertLHsphere')
mris_convertLHlabels = mris_convertLH.clone('mris_convertLHlabels')
mris_convertRHlabels = mris_convertLH.clone('mris_convertRHlabels')

"""
Diffusion processing nodes
--------------------------

.. seealso::

    dmri_mrtrix_dti.py
        Tutorial that focuses solely on the MRtrix diffusion processing

    http://www.brain.org.au/software/mrtrix/index.html
        MRtrix's online documentation



b-values and b-vectors stored in FSL's format are converted into a single encoding file for MRTrix.
"""

fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(),name='fsl2mrtrix')

"""
Distortions induced by eddy currents are corrected prior to fitting the tensors.
The first image is used as a reference for which to warp the others.
"""

eddycorrect = create_eddy_correct_pipeline(name='eddycorrect')
eddycorrect.inputs.inputnode.ref_num = 1

"""
Tensors are fitted to each voxel in the diffusion-weighted image and from these three maps are created:
    * Major eigenvector in each voxel
    * Apparent diffusion coefficient
    * Fractional anisotropy
"""

dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(),name='dwi2tensor')
tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(),name='tensor2vector')
tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(),name='tensor2adc')
tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(),name='tensor2fa')
MRconvert_fa = pe.Node(interface=mrtrix.MRConvert(),name='MRconvert_fa')
MRconvert_fa.inputs.extension = 'nii'

"""

These nodes are used to create a rough brain mask from the b0 image.
The b0 image is extracted from the original diffusion-weighted image,
put through a simple thresholding routine, and smoothed using a 3x3 median filter.
"""

MRconvert = pe.Node(interface=mrtrix.MRConvert(),name='MRconvert')
MRconvert.inputs.extract_at_axis = 3
MRconvert.inputs.extract_at_coordinate = [0]
threshold_b0 = pe.Node(interface=mrtrix.Threshold(),name='threshold_b0')
median3d = pe.Node(interface=mrtrix.MedianFilter3D(),name='median3d')

"""
The brain mask is also used to help identify single-fiber voxels.
This is done by passing the brain mask through two erosion steps,
multiplying the remaining mask with the fractional anisotropy map, and
thresholding the result to obtain some highly anisotropic within-brain voxels.
"""

erode_mask_firstpass = pe.Node(interface=mrtrix.Erode(),name='erode_mask_firstpass')
erode_mask_secondpass = pe.Node(interface=mrtrix.Erode(),name='erode_mask_secondpass')
MRmultiply = pe.Node(interface=mrtrix.MRMultiply(),name='MRmultiply')
MRmult_merge = pe.Node(interface=util.Merge(2), name='MRmultiply_merge')
threshold_FA = pe.Node(interface=mrtrix.Threshold(),name='threshold_FA')
threshold_FA.inputs.absolute_threshold_value = 0.7

"""
For whole-brain tracking we also require a broad white-matter seed mask.
This is created by generating a white matter mask, given a brainmask, and
thresholding it at a reasonably high level.
"""

bet = pe.Node(interface=fsl.BET(mask = True), name = 'bet_b0')
gen_WM_mask = pe.Node(interface=mrtrix.GenerateWhiteMatterMask(),name='gen_WM_mask')
threshold_wmmask = pe.Node(interface=mrtrix.Threshold(),name='threshold_wmmask')
threshold_wmmask.inputs.absolute_threshold_value = 0.4

"""
The spherical deconvolution step depends on the estimate of the response function
in the highly anisotropic voxels we obtained above.

.. warning::

    For damaged or pathological brains one should take care to lower the maximum harmonic order of these steps.

"""

estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(),name='estimateresponse')
estimateresponse.inputs.maximum_harmonic_order = 6
csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(),name='csdeconv')
csdeconv.inputs.maximum_harmonic_order = 6

"""
Finally, we track probabilistically using the orientation distribution functions obtained earlier.
The tracts are then used to generate a tract-density image, and they are also converted to TrackVis format.
"""

probCSDstreamtrack = pe.Node(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(),name='probCSDstreamtrack')
probCSDstreamtrack.inputs.inputmodel = 'SD_PROB'
probCSDstreamtrack.inputs.maximum_number_of_tracks = 150000
tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(),name='tracks2prob')
tracks2prob.inputs.colour = True
MRconvert_tracks2prob = MRconvert_fa.clone(name='MRconvert_tracks2prob')
tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(),name='tck2trk')
trk2tdi = pe.Node(interface=dipy.TrackDensityMap(),name='trk2tdi')

"""
Structural segmentation nodes
-----------------------------
"""

"""
The following node identifies the transformation between the diffusion-weighted
image and the structural image. This transformation is then applied to the tracts
so that they are in the same space as the regions of interest.
"""

coregister = pe.Node(interface=fsl.FLIRT(dof=6), name = 'coregister')
coregister.inputs.cost = ('normmi')

"""
Parcellation is performed given the aparc+aseg image from Freesurfer.
The CMTK Parcellation step subdivides these regions to return a higher-resolution parcellation scheme.
The parcellation used here is entitled "scale500" and returns 1015 regions.
"""

parcellation_name = 'scale500'
parcellate = pe.Node(interface=cmtk.Parcellate(), name="Parcellate")
parcellate.inputs.parcellation_name = parcellation_name

"""
The CreateMatrix interface takes in the remapped aparc+aseg image as well as the label dictionary and fiber tracts
and outputs a number of different files. The most important of which is the connectivity network itself, which is stored
as a 'gpickle' and can be loaded using Python's NetworkX package (see CreateMatrix docstring). Also outputted are various
NumPy arrays containing detailed tract information, such as the start and endpoint regions, and statistics on the mean and
standard deviation for the fiber length of each connection. These matrices can be used in the ConnectomeViewer to plot the
specific tracts that connect between user-selected regions.

Here we choose the Lausanne2008 parcellation scheme, since we are incorporating the CMTK parcellation step.
"""

parcellation_name = 'scale500'
cmp_config = cmp.configuration.PipelineConfiguration()
cmp_config.parcellation_scheme = "Lausanne2008"
createnodes = pe.Node(interface=cmtk.CreateNodes(), name="CreateNodes")
createnodes.inputs.resolution_network_file = cmp_config._get_lausanne_parcellation('Lausanne2008')[parcellation_name]['node_information_graphml']

creatematrix = pe.Node(interface=cmtk.CreateMatrix(), name="CreateMatrix")
creatematrix.inputs.count_region_intersections = True

"""
Next we define the endpoint of this tutorial, which is the CFFConverter node, as well as a few nodes which use
the Nipype Merge utility. These are useful for passing lists of the files we want packaged in our CFF file.
The inspect.getfile command is used to package this script into the resulting CFF file, so that it is easy to
look back at the processing parameters that were used.
"""

CFFConverter = pe.Node(interface=cmtk.CFFConverter(), name="CFFConverter")
CFFConverter.inputs.script_files = op.abspath(inspect.getfile(inspect.currentframe()))
giftiSurfaces = pe.Node(interface=util.Merge(8), name="GiftiSurfaces")
giftiLabels = pe.Node(interface=util.Merge(2), name="GiftiLabels")
niftiVolumes = pe.Node(interface=util.Merge(3), name="NiftiVolumes")
fiberDataArrays = pe.Node(interface=util.Merge(4), name="FiberDataArrays")
gpickledNetworks = pe.Node(interface=util.Merge(2), name="NetworkFiles")

"""
We also create a workflow to calculate several network metrics on our resulting file, and another CFF converter
which will be used to package these networks into a single file.
"""

networkx = create_networkx_pipeline(name='networkx')
cmats_to_csv = create_cmats_to_csv_pipeline(name='cmats_to_csv')
NxStatsCFFConverter = pe.Node(interface=cmtk.CFFConverter(), name="NxStatsCFFConverter")
NxStatsCFFConverter.inputs.script_files = op.abspath(inspect.getfile(inspect.currentframe()))

"""
Connecting the workflow
=======================
Here we connect our processing pipeline.
"""


"""
Connecting the inputs, FreeSurfer nodes, and conversions
--------------------------------------------------------
"""

mapping = pe.Workflow(name='mapping')

"""
First, we connect the input node to the FreeSurfer input nodes.
"""

mapping.connect([(inputnode, FreeSurferSource,[("subjects_dir","subjects_dir")])])
mapping.connect([(inputnode, FreeSurferSource,[("subject_id","subject_id")])])

mapping.connect([(inputnode, FreeSurferSourceLH,[("subjects_dir","subjects_dir")])])
mapping.connect([(inputnode, FreeSurferSourceLH,[("subject_id","subject_id")])])

mapping.connect([(inputnode, FreeSurferSourceRH,[("subjects_dir","subjects_dir")])])
mapping.connect([(inputnode, FreeSurferSourceRH,[("subject_id","subject_id")])])

mapping.connect([(inputnode, parcellate,[("subjects_dir","subjects_dir")])])
mapping.connect([(inputnode, parcellate,[("subject_id","subject_id")])])
mapping.connect([(parcellate, mri_convert_ROI_scale500,[('roi_file','in_file')])])

"""
Nifti conversion for subject's stripped brain image from Freesurfer:
"""

mapping.connect([(FreeSurferSource, mri_convert_Brain,[('brain','in_file')])])

"""
Surface conversions to GIFTI (pial, white, inflated, and sphere for both hemispheres)
"""

mapping.connect([(FreeSurferSourceLH, mris_convertLH,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRH,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceLH, mris_convertLHwhite,[('white','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHwhite,[('white','in_file')])])
mapping.connect([(FreeSurferSourceLH, mris_convertLHinflated,[('inflated','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHinflated,[('inflated','in_file')])])
mapping.connect([(FreeSurferSourceLH, mris_convertLHsphere,[('sphere','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHsphere,[('sphere','in_file')])])

"""
The annotation files are converted using the pial surface as a map via the MRIsConvert interface.
One of the functions defined earlier is used to select the lh.aparc.annot and rh.aparc.annot files
specifically (rather than e.g. rh.aparc.a2009s.annot) from the output list given by the FreeSurferSource.
"""

mapping.connect([(FreeSurferSourceLH, mris_convertLHlabels,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHlabels,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceLH, mris_convertLHlabels, [(('annot', select_aparc_annot), 'annot_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHlabels, [(('annot', select_aparc_annot), 'annot_file')])])


"""
Diffusion Processing
--------------------
Now we connect the tensor computations:
"""

mapping.connect([(inputnode, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")])])
mapping.connect([(inputnode, eddycorrect,[("dwi","inputnode.in_file")])])
mapping.connect([(eddycorrect, dwi2tensor,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

mapping.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                       (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                       (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                      ])
mapping.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])
mapping.connect([(tensor2fa, MRconvert_fa,[("FA","in_file")])])

"""

This block creates the rough brain mask to be multiplied, mulitplies it with the
fractional anisotropy image, and thresholds it to get the single-fiber voxels.
"""

mapping.connect([(eddycorrect, MRconvert,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(MRconvert, threshold_b0,[("converted","in_file")])])
mapping.connect([(threshold_b0, median3d,[("out_file","in_file")])])
mapping.connect([(median3d, erode_mask_firstpass,[("out_file","in_file")])])
mapping.connect([(erode_mask_firstpass, erode_mask_secondpass,[("out_file","in_file")])])
mapping.connect([(erode_mask_secondpass, MRmult_merge,[("out_file","in2")])])
mapping.connect([(MRmult_merge, MRmultiply,[("out","in_files")])])
mapping.connect([(MRmultiply, threshold_FA,[("out_file","in_file")])])

"""
Here the thresholded white matter mask is created for seeding the tractography.
"""

mapping.connect([(eddycorrect, bet,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(eddycorrect, gen_WM_mask,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
mapping.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])
mapping.connect([(gen_WM_mask, threshold_wmmask,[("WMprobabilitymap","in_file")])])

"""
Next we estimate the fiber response distribution.
"""

mapping.connect([(eddycorrect, estimateresponse,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])
mapping.connect([(threshold_FA, estimateresponse,[("out_file","mask_image")])])

"""
Run constrained spherical deconvolution.
"""

mapping.connect([(eddycorrect, csdeconv,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
mapping.connect([(estimateresponse, csdeconv,[("response","response_file")])])
mapping.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

"""
Connect the tractography and compute the tract density image.
"""

mapping.connect([(threshold_wmmask, probCSDstreamtrack,[("out_file","seed_file")])])
mapping.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])
mapping.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
mapping.connect([(eddycorrect, tracks2prob,[("outputnode.eddy_corrected","template_file")])])
mapping.connect([(tracks2prob, MRconvert_tracks2prob,[("tract_image","in_file")])])

"""
Structural Processing
---------------------
First, we coregister the diffusion image to the structural image
"""

mapping.connect([(eddycorrect, coregister,[("outputnode.eddy_corrected","in_file")])])
mapping.connect([(mri_convert_Brain, coregister,[('out_file','reference')])])

"""
The MRtrix-tracked fibers are converted to TrackVis format (with voxel and data dimensions grabbed from the DWI).
The connectivity matrix is created with the transformed .trk fibers and the parcellation file.
"""

mapping.connect([(eddycorrect, tck2trk,[("outputnode.eddy_corrected","image_file")])])
mapping.connect([(mri_convert_Brain, tck2trk,[("out_file","registration_image_file")])])
mapping.connect([(coregister, tck2trk,[("out_matrix_file","matrix_file")])])
mapping.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])
mapping.connect([(tck2trk, creatematrix,[("out_file","tract_file")])])
mapping.connect([(tck2trk, trk2tdi,[("out_file","in_file")])])
mapping.connect([(inputnode, creatematrix,[("subject_id","out_matrix_file")])])
mapping.connect([(inputnode, creatematrix,[("subject_id","out_matrix_mat_file")])])
mapping.connect([(parcellate, creatematrix,[("roi_file","roi_file")])])
mapping.connect([(parcellate, createnodes,[("roi_file","roi_file")])])
mapping.connect([(createnodes, creatematrix,[("node_network","resolution_network_file")])])

"""
The merge nodes defined earlier are used here to create lists of the files which are
destined for the CFFConverter.
"""

mapping.connect([(mris_convertLH, giftiSurfaces,[("converted","in1")])])
mapping.connect([(mris_convertRH, giftiSurfaces,[("converted","in2")])])
mapping.connect([(mris_convertLHwhite, giftiSurfaces,[("converted","in3")])])
mapping.connect([(mris_convertRHwhite, giftiSurfaces,[("converted","in4")])])
mapping.connect([(mris_convertLHinflated, giftiSurfaces,[("converted","in5")])])
mapping.connect([(mris_convertRHinflated, giftiSurfaces,[("converted","in6")])])
mapping.connect([(mris_convertLHsphere, giftiSurfaces,[("converted","in7")])])
mapping.connect([(mris_convertRHsphere, giftiSurfaces,[("converted","in8")])])

mapping.connect([(mris_convertLHlabels, giftiLabels,[("converted","in1")])])
mapping.connect([(mris_convertRHlabels, giftiLabels,[("converted","in2")])])

mapping.connect([(parcellate, niftiVolumes,[("roi_file","in1")])])
mapping.connect([(eddycorrect, niftiVolumes,[("outputnode.eddy_corrected","in2")])])
mapping.connect([(mri_convert_Brain, niftiVolumes,[("out_file","in3")])])

mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file","in1")])])
mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file_mm","in2")])])
mapping.connect([(creatematrix, fiberDataArrays,[("fiber_length_file","in3")])])
mapping.connect([(creatematrix, fiberDataArrays,[("fiber_label_file","in4")])])

"""
This block actually connects the merged lists to the CFF converter. We pass the surfaces
and volumes that are to be included, as well as the tracts and the network itself. The currently
running pipeline (dmri_connectivity_advanced.py) is also scraped and included in the CFF file. This
makes it easy for the user to examine the entire processing pathway used to generate the end
product.
"""

mapping.connect([(giftiSurfaces, CFFConverter,[("out","gifti_surfaces")])])
mapping.connect([(giftiLabels, CFFConverter,[("out","gifti_labels")])])
mapping.connect([(creatematrix, CFFConverter,[("matrix_files","gpickled_networks")])])
mapping.connect([(niftiVolumes, CFFConverter,[("out","nifti_volumes")])])
mapping.connect([(fiberDataArrays, CFFConverter,[("out","data_files")])])
mapping.connect([(creatematrix, CFFConverter,[("filtered_tractography","tract_files")])])
mapping.connect([(inputnode, CFFConverter,[("subject_id","title")])])

"""
The graph theoretical metrics are computed using the networkx workflow and placed in another CFF file
"""

mapping.connect([(inputnode, networkx,[("subject_id","inputnode.extra_field")])])
mapping.connect([(creatematrix, networkx,[("intersection_matrix_file","inputnode.network_file")])])

mapping.connect([(networkx, NxStatsCFFConverter,[("outputnode.network_files","gpickled_networks")])])
mapping.connect([(giftiSurfaces, NxStatsCFFConverter,[("out","gifti_surfaces")])])
mapping.connect([(giftiLabels, NxStatsCFFConverter,[("out","gifti_labels")])])
mapping.connect([(niftiVolumes, NxStatsCFFConverter,[("out","nifti_volumes")])])
mapping.connect([(fiberDataArrays, NxStatsCFFConverter,[("out","data_files")])])
mapping.connect([(inputnode, NxStatsCFFConverter,[("subject_id","title")])])

mapping.connect([(inputnode, cmats_to_csv,[("subject_id","inputnode.extra_field")])])
mapping.connect([(creatematrix, cmats_to_csv,[("matlab_matrix_files","inputnode.matlab_matrix_files")])])

"""
Create a higher-level workflow
------------------------------
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

connectivity = pe.Workflow(name="connectivity")

connectivity.base_dir = op.abspath('dmri_connectivity_advanced')
connectivity.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,mapping,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ]),
        (infosource,mapping,[('subject_id','inputnode.subject_id')])
                ])

"""
The following functions run the whole workflow and produce a .dot and .png graph of the processing pipeline.
"""

if __name__ == '__main__':
    connectivity.run()
    connectivity.write_graph()
