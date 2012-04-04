#!/usr/bin/env python
"""
=============================================
dMRI: Connectivity - Camino, CMTK, FreeSurfer
=============================================

Introduction
============

This script, connectivity_tutorial.py, demonstrates the ability to perform connectivity mapping
using Nipype for pipelining, Freesurfer for Reconstruction / Parcellation, Camino for tensor-fitting
and tractography, and the Connectome Mapping Toolkit (CMTK) for connectivity analysis.

    python connectivity_tutorial.py

We perform this analysis using the FSL course data, which can be acquired from here:

    * http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

This pipeline also requires the Freesurfer directory for 'subj1' from the FSL course data.
To save time, this data can be downloaded from here:

    * http://dl.dropbox.com/u/315714/subj1.zip?dl=1

A data package containing the outputs of this pipeline can be obtained from here:

    * http://db.tt/1vx4vLeP

Along with Camino (http://web4.cs.ucl.ac.uk/research/medic/camino/pmwiki/pmwiki.php?n=Main.HomePage),
Camino-Trackvis (http://www.nitrc.org/projects/camino-trackvis/), FSL (http://www.fmrib.ox.ac.uk/fsl/),
and Freesurfer (http://surfer.nmr.mgh.harvard.edu/), you must also have the Connectome File Format
library installed as well as the Connectome Mapper.

These are written by Stephan Gerhard and can be obtained from:

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
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.cmtk as cmtk
import nipype.algorithms.misc as misc
import inspect

import os.path as op                      # system functions
import cmp                                    # connectome mapper

"""
We define the following functions to scrape the voxel and data dimensions of the input images. This allows the
pipeline to be flexible enough to accept and process images of varying size. The SPM Face tutorial
(fmri_spm_face.py) also implements this inferral of voxel size from the data. We also define functions to
select the proper parcellation/segregation file from Freesurfer's output for each subject. For the mapping in
this tutorial, we use the aparc+seg.mgz file. While it is possible to change this to use the regions defined in
aparc.a2009s+aseg.mgz, one would also have to write/obtain a network resolution map defining the nodes based on those
regions.
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
These need to point to the main Freesurfer directory as well as the freesurfer subjects directory.
No assumptions are made about where the directory of subjects is placed.
Recon-all must have been run on subj1 from the FSL course data.
"""

fs_dir = op.abspath('/usr/local/freesurfer')
subjects_dir = op.abspath(op.join(op.curdir,'./subjects'))
fsl.FSLCommand.set_default_output_type('NIFTI')

"""
This needs to point to the fdt folder you can find after extracting
http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
"""

data_dir = op.abspath('fsl_course_data/fdt/')
fs.FSCommand.set_default_subjects_dir(subjects_dir)
subject_list = ['subj1']

"""
An infosource node is used to loop through the subject list and define the input files.
For our purposes, these are the diffusion-weighted MR image, b vectors, and b values.
The info dictionary is used to provide a template of the naming of these files. For instance,
the 4D nifti diffusion image is stored in the FSL course data as data.nii.gz.
"""

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])

"""
A datasource node is used to perform the actual data grabbing.
Templates for the associated images are used to obtain the correct images.
The data are assumed to lie in data_dir/subject_id/.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"
datasource.inputs.base_directory = data_dir
datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz')
datasource.inputs.template_args = info
datasource.inputs.base_directory = data_dir

"""
FreeSurferSource nodes are used to retrieve a number of image
files that were automatically generated by the recon-all process.
Here we use three of these nodes, two of which are defined to return files for solely the left and right hemispheres.
"""

FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='fssource')
FreeSurferSource.inputs.subjects_dir = subjects_dir

FreeSurferSourceLH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceLH')
FreeSurferSourceLH.inputs.subjects_dir = subjects_dir
FreeSurferSourceLH.inputs.hemi = 'lh'

FreeSurferSourceRH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceRH')
FreeSurferSourceRH.inputs.subjects_dir = subjects_dir
FreeSurferSourceRH.inputs.hemi = 'rh'

"""
Since the b values and b vectors come from the FSL course, we must convert it to a scheme file
for use in Camino.
"""

fsl2scheme = pe.Node(interface=camino.FSL2Scheme(), name="fsl2scheme")
fsl2scheme.inputs.usegradmod = True

"""
FSL's Brain Extraction tool is used to create a mask from the b0 image
"""

b0Strip = pe.Node(interface=fsl.BET(mask = True), name = 'bet_b0')

"""
FSL's FLIRT function is used to coregister the b0 mask and the structural image.
A convert_xfm node is then used to obtain the inverse of the transformation matrix.
FLIRT is used once again to apply the inverse transformation to the parcellated brain image.
"""

coregister = pe.Node(interface=fsl.FLIRT(dof=6), name = 'coregister')
coregister.inputs.cost = ('corratio')

convertxfm = pe.Node(interface=fsl.ConvertXFM(), name = 'convertxfm')
convertxfm.inputs.invert_xfm = True

inverse = pe.Node(interface=fsl.FLIRT(), name = 'inverse')
inverse.inputs.interp = ('nearestneighbour')

inverse_AparcAseg = pe.Node(interface=fsl.FLIRT(), name = 'inverse_AparcAseg')
inverse_AparcAseg.inputs.interp = ('nearestneighbour')

"""
A number of conversion operations are required to obtain NIFTI files from the FreesurferSource for each subject.
Nodes are used to convert the following:

    * Original structural image to NIFTI
    * Parcellated white matter image to NIFTI
    * Parcellated whole-brain image to NIFTI
    * Pial, white, inflated, and spherical surfaces for both the left and right hemispheres
        are converted to GIFTI for visualization in ConnectomeViewer
    * Parcellated annotation files for the left and right hemispheres are also converted to GIFTI
"""

mri_convert_Brain = pe.Node(interface=fs.MRIConvert(), name='mri_convert_Brain')
mri_convert_Brain.inputs.out_type = 'nii'

mri_convert_WMParc = mri_convert_Brain.clone('mri_convert_WMParc')
mri_convert_AparcAseg = mri_convert_Brain.clone('mri_convert_AparcAseg')

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
An inputnode is used to pass the data obtained by the data grabber to the actual processing functions
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals", "subject_id"]), name="inputnode")

"""
In this section we create the nodes necessary for diffusion analysis.
First, the diffusion image is converted to voxel order, since this is the format in which Camino does
its processing.
"""

image2voxel = pe.Node(interface=camino.Image2Voxel(), name="image2voxel")

"""
Second, diffusion tensors are fit to the voxel-order data.
If desired, these tensors can be converted to a Nifti tensor image using the DT2NIfTI interface.
"""

dtifit = pe.Node(interface=camino.DTIFit(),name='dtifit')

"""
Next, a lookup table is generated from the schemefile and the
signal-to-noise ratio (SNR) of the unweighted (q=0) data.
"""

dtlutgen = pe.Node(interface=camino.DTLUTGen(), name="dtlutgen")
dtlutgen.inputs.snr = 16.0
dtlutgen.inputs.inversion = 1

"""
In this tutorial we implement probabilistic tractography using the PICo algorithm.
PICo tractography requires an estimate of the fibre direction and a model of its uncertainty in each voxel;
this probabilitiy distribution map is produced using the following node.
"""

picopdfs = pe.Node(interface=camino.PicoPDFs(), name="picopdfs")
picopdfs.inputs.inputmodel = 'dt'

"""
Finally, tractography is performed. In this tutorial, we will use only one iteration for time-saving purposes.
It is important to note that we use the TrackPICo interface here. This interface now expects the files required
for PICo tracking (i.e. the output from picopdfs). Similar interfaces exist for alternative types of tracking,
such as Bayesian tracking with Dirac priors (TrackBayesDirac).
"""

track = pe.Node(interface=camino.TrackPICo(), name="track")
track.inputs.iterations = 1


"""
Currently, the best program for visualizing tracts is TrackVis. For this reason, a node is included to
convert the raw tract data to .trk format. Solely for testing purposes, another node is added to perform the reverse.
"""

camino2trackvis = pe.Node(interface=cam2trk.Camino2Trackvis(), name="camino2trk")
camino2trackvis.inputs.min_length = 30
camino2trackvis.inputs.voxel_order = 'LAS'
trk2camino = pe.Node(interface=cam2trk.Trackvis2Camino(), name="trk2camino")

"""
Tracts can also be converted to VTK and OOGL formats, for use in programs such as GeomView and Paraview,
using the following two nodes.
"""

vtkstreamlines = pe.Node(interface=camino.VtkStreamlines(), name="vtkstreamlines")
procstreamlines = pe.Node(interface=camino.ProcStreamlines(), name="procstreamlines")
procstreamlines.inputs.outputtracts = 'oogl'

"""
We can easily produce a variety of scalar values from our fitted tensors. The following nodes generate the
fractional anisotropy and diffusivity trace maps and their associated headers, and then merge them back
into a single .nii file.
"""

fa = pe.Node(interface=camino.ComputeFractionalAnisotropy(),name='fa')
trace = pe.Node(interface=camino.ComputeTensorTrace(),name='trace')
dteig = pe.Node(interface=camino.ComputeEigensystem(), name='dteig')

analyzeheader_fa = pe.Node(interface=camino.AnalyzeHeader(),name='analyzeheader_fa')
analyzeheader_fa.inputs.datatype = 'double'
analyzeheader_trace = pe.Node(interface=camino.AnalyzeHeader(),name='analyzeheader_trace')
analyzeheader_trace.inputs.datatype = 'double'

fa2nii = pe.Node(interface=misc.CreateNifti(),name='fa2nii')
trace2nii = fa2nii.clone("trace2nii")

"""
This section adds the Connectome Mapping Toolkit (CMTK) nodes.
These interfaces are fairly experimental and may not function properly.
In order to perform connectivity mapping using CMTK, the parcellated structural data is rewritten
using the indices and parcellation scheme from the connectome mapper (CMP). This process has been
written into the ROIGen interface, which will output a remapped aparc+aseg image as well as a
dictionary of label information (i.e. name, display colours) pertaining to the original and remapped regions.
These label values are input from a user-input lookup table, if specified, and otherwise the default
Freesurfer LUT (/freesurfer/FreeSurferColorLUT.txt).
"""

roigen = pe.Node(interface=cmtk.ROIGen(), name="ROIGen")
cmp_config = cmp.configuration.PipelineConfiguration(parcellation_scheme = "NativeFreesurfer")
cmp_config.parcellation_scheme = "NativeFreesurfer"
roigen.inputs.LUT_file = cmp_config.get_freeview_lut("NativeFreesurfer")['freesurferaparc']
roigen_structspace = roigen.clone('ROIGen_structspace')

"""
The CreateMatrix interface takes in the remapped aparc+aseg image as well as the label dictionary and fiber tracts
and outputs a number of different files. The most important of which is the connectivity network itself, which is stored
as a 'gpickle' and can be loaded using Python's NetworkX package (see CreateMatrix docstring). Also outputted are various
NumPy arrays containing detailed tract information, such as the start and endpoint regions, and statistics on the mean and
standard deviation for the fiber length of each connection. These matrices can be used in the ConnectomeViewer to plot the
specific tracts that connect between user-selected regions.
"""

creatematrix = pe.Node(interface=cmtk.CreateMatrix(), name="CreateMatrix")
creatematrix.inputs.count_region_intersections = True
createnodes = pe.Node(interface=cmtk.CreateNodes(), name="CreateNodes")
createnodes.inputs.resolution_network_file = cmp_config.parcellation['freesurferaparc']['node_information_graphml']

"""
Here we define the endpoint of this tutorial, which is the CFFConverter node, as well as a few nodes which use
the Nipype Merge utility. These are useful for passing lists of the files we want packaged in our CFF file.
"""

CFFConverter = pe.Node(interface=cmtk.CFFConverter(), name="CFFConverter")

giftiSurfaces = pe.Node(interface=util.Merge(8), name="GiftiSurfaces")
giftiLabels = pe.Node(interface=util.Merge(2), name="GiftiLabels")
niftiVolumes = pe.Node(interface=util.Merge(3), name="NiftiVolumes")
fiberDataArrays = pe.Node(interface=util.Merge(4), name="FiberDataArrays")
gpickledNetworks = pe.Node(interface=util.Merge(1), name="NetworkFiles")

"""
Since we have now created all our nodes, we can define our workflow and start making connections.
"""

mapping = pe.Workflow(name='mapping')

"""
First, we connect the input node to the early conversion functions.
FreeSurfer input nodes:
"""

mapping.connect([(inputnode, FreeSurferSource,[("subject_id","subject_id")])])
mapping.connect([(inputnode, FreeSurferSourceLH,[("subject_id","subject_id")])])
mapping.connect([(inputnode, FreeSurferSourceRH,[("subject_id","subject_id")])])

"""
Required conversions for processing in Camino:
"""

mapping.connect([(inputnode, image2voxel, [("dwi", "in_file")]),
                       (inputnode, fsl2scheme, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")]),
                       (image2voxel, dtifit,[['voxel_order','in_file']]),
                       (fsl2scheme, dtifit,[['scheme','scheme_file']])
                      ])

"""
Nifti conversions for the parcellated white matter image (used in Camino's conmap),
and the subject's stripped brain image from Freesurfer:
"""

mapping.connect([(FreeSurferSource, mri_convert_WMParc,[('wmparc','in_file')])])
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
specifically (rather than i.e. rh.aparc.a2009s.annot) from the output list given by the FreeSurferSource.
"""

mapping.connect([(FreeSurferSourceLH, mris_convertLHlabels,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHlabels,[('pial','in_file')])])
mapping.connect([(FreeSurferSourceLH, mris_convertLHlabels, [(('annot', select_aparc_annot), 'annot_file')])])
mapping.connect([(FreeSurferSourceRH, mris_convertRHlabels, [(('annot', select_aparc_annot), 'annot_file')])])

"""
This section coregisters the diffusion-weighted and parcellated white-matter / whole brain images.
At present the conmap node connection is left commented, as there have been recent changes in Camino
code that have presented some users with errors.
"""

mapping.connect([(inputnode, b0Strip,[('dwi','in_file')])])
mapping.connect([(b0Strip, coregister,[('out_file','in_file')])])
mapping.connect([(mri_convert_Brain, coregister,[('out_file','reference')])])
mapping.connect([(coregister, convertxfm,[('out_matrix_file','in_file')])])
mapping.connect([(b0Strip, inverse,[('out_file','reference')])])
mapping.connect([(convertxfm, inverse,[('out_file','in_matrix_file')])])
mapping.connect([(mri_convert_WMParc, inverse,[('out_file','in_file')])])

"""
The tractography pipeline consists of the following nodes. Further information about the tractography
can be found in nipype/examples/dmri_camino_dti.py.
"""

mapping.connect([(b0Strip, track,[("mask_file","seed_file")])])
mapping.connect([(fsl2scheme, dtlutgen,[("scheme","scheme_file")])])
mapping.connect([(dtlutgen, picopdfs,[("dtLUT","luts")])])
mapping.connect([(dtifit, picopdfs,[("tensor_fitted","in_file")])])
mapping.connect([(picopdfs, track,[("pdfs","in_file")])])

"""
Connecting the Fractional Anisotropy and Trace nodes is simple, as they obtain their input from the
tensor fitting. This is also where our voxel- and data-grabbing functions come in. We pass these functions,
along with the original DWI image from the input node, to the header-generating nodes. This ensures that the
files will be correct and readable.
"""

mapping.connect([(dtifit, fa,[("tensor_fitted","in_file")])])
mapping.connect([(fa, analyzeheader_fa,[("fa","in_file")])])
mapping.connect([(inputnode, analyzeheader_fa,[(('dwi', get_vox_dims), 'voxel_dims'),
    (('dwi', get_data_dims), 'data_dims')])])
mapping.connect([(fa, fa2nii,[('fa','data_file')])])
mapping.connect([(inputnode, fa2nii,[(('dwi', get_affine), 'affine')])])
mapping.connect([(analyzeheader_fa, fa2nii,[('header', 'header_file')])])


mapping.connect([(dtifit, trace,[("tensor_fitted","in_file")])])
mapping.connect([(trace, analyzeheader_trace,[("trace","in_file")])])
mapping.connect([(inputnode, analyzeheader_trace,[(('dwi', get_vox_dims), 'voxel_dims'),
    (('dwi', get_data_dims), 'data_dims')])])
mapping.connect([(trace, trace2nii,[('trace','data_file')])])
mapping.connect([(inputnode, trace2nii,[(('dwi', get_affine), 'affine')])])
mapping.connect([(analyzeheader_trace, trace2nii,[('header', 'header_file')])])

mapping.connect([(dtifit, dteig,[("tensor_fitted","in_file")])])

"""
The output tracts are converted to Trackvis format (and back). Here we also use the voxel- and data-grabbing
functions defined at the beginning of the pipeline.
"""

mapping.connect([(track, camino2trackvis, [('tracked','in_file')]),
                       (track, vtkstreamlines,[['tracked','in_file']]),
                       (camino2trackvis, trk2camino,[['trackvis','in_file']])
                      ])
mapping.connect([(inputnode, camino2trackvis,[(('dwi', get_vox_dims), 'voxel_dims'),
    (('dwi', get_data_dims), 'data_dims')])])

"""
Here the CMTK connectivity mapping nodes are connected.
The original aparc+aseg image is converted to NIFTI, then registered to
the diffusion image and delivered to the ROIGen node. The remapped parcellation,
original tracts, and label file are then given to CreateMatrix.
"""

mapping.connect(createnodes, 'node_network',
                creatematrix, 'resolution_network_file')
mapping.connect([(FreeSurferSource, mri_convert_AparcAseg, [(('aparc_aseg', select_aparc), 'in_file')])])

mapping.connect([(b0Strip, inverse_AparcAseg,[('out_file','reference')])])
mapping.connect([(convertxfm, inverse_AparcAseg,[('out_file','in_matrix_file')])])
mapping.connect([(mri_convert_AparcAseg, inverse_AparcAseg,[('out_file','in_file')])])
mapping.connect([(mri_convert_AparcAseg, roigen_structspace,[('out_file','aparc_aseg_file')])])
mapping.connect([(roigen_structspace, createnodes,[("roi_file","roi_file")])])

mapping.connect([(inverse_AparcAseg, roigen,[("out_file","aparc_aseg_file")])])
mapping.connect([(roigen, creatematrix,[("roi_file","roi_file")])])
mapping.connect([(camino2trackvis, creatematrix,[("trackvis","tract_file")])])
mapping.connect([(inputnode, creatematrix,[("subject_id","out_matrix_file")])])
mapping.connect([(inputnode, creatematrix,[("subject_id","out_matrix_mat_file")])])

"""
The merge nodes defined earlier are used here to create lists of the files which are
destined for the CFFConverter.
"""

mapping.connect([(creatematrix, gpickledNetworks,[("matrix_files","in1")])])

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

mapping.connect([(roigen, niftiVolumes,[("roi_file","in1")])])
mapping.connect([(inputnode, niftiVolumes,[("dwi","in2")])])
mapping.connect([(mri_convert_Brain, niftiVolumes,[("out_file","in3")])])

mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file","in1")])])
mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file_mm","in2")])])
mapping.connect([(creatematrix, fiberDataArrays,[("fiber_length_file","in3")])])
mapping.connect([(creatematrix, fiberDataArrays,[("fiber_label_file","in4")])])

"""
This block actually connects the merged lists to the CFF converter. We pass the surfaces
and volumes that are to be included, as well as the tracts and the network itself. The currently
running pipeline (dmri_connectivity.py) is also scraped and included in the CFF file. This
makes it easy for the user to examine the entire processing pathway used to generate the end
product.
"""

CFFConverter.inputs.script_files = op.abspath(inspect.getfile(inspect.currentframe()))
mapping.connect([(giftiSurfaces, CFFConverter,[("out","gifti_surfaces")])])
mapping.connect([(giftiLabels, CFFConverter,[("out","gifti_labels")])])
mapping.connect([(gpickledNetworks, CFFConverter,[("out","gpickled_networks")])])
mapping.connect([(niftiVolumes, CFFConverter,[("out","nifti_volumes")])])
mapping.connect([(fiberDataArrays, CFFConverter,[("out","data_files")])])
mapping.connect([(creatematrix, CFFConverter,[("filtered_tractographies","tract_files")])])
mapping.connect([(inputnode, CFFConverter,[("subject_id","title")])])

"""
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial can is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

connectivity = pe.Workflow(name="connectivity")
connectivity.base_dir = op.abspath('dmri_connectivity')
connectivity.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,mapping,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ]),
        (infosource,mapping,[('subject_id','inputnode.subject_id')])
                ])

"""
The following functions run the whole workflow and produce graphs describing the processing pipeline.
By default, write_graph outputs a .dot file and a .png image, but here we set it to output the image
as a vector graphic, by passing the format='eps' argument.
"""

if __name__ == '__main__':
    connectivity.run()
    connectivity.write_graph(format='eps')

"""
The output CFF file of this pipeline can be loaded in the Connectome Viewer (http://www.cmtk.org)
After loading the network into memory it can be examined in 3D or as a connectivity matrix
using the default scripts produced by the Code Oracle.
To compare networks, one must use the MergeCNetworks interface to merge two networks into
a single CFF file. Statistics can then be run using the Network Brain Statistics (NBS) plugin
Surfaces can also be loaded along with their labels from the aparc+aseg file. The tractography
is included in the file so that region-to-region fibers can be individually plotted using the
Code Oracle.

"""
