import inspect
import os.path as op                      # system functions

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.mrtrix as mrtrix
import nipype.interfaces.camino as camino
import nipype.algorithms.misc as misc
import nipype.interfaces.cmtk as cmtk

from ..camino.connectivity_mapping import (select_aparc_annot, get_vox_dims,
                                           get_data_dims, get_affine)
from ..camino.group_connectivity import pullnodeIDs
from ..fsl.dti import create_eddy_correct_pipeline

def create_connectivity_pipeline(name="connectivity"):
    """Creates a pipeline that does the same connectivity processing as in the
    connectivity_tutorial_advanced example script. Given a subject id (and completed Freesurfer reconstruction)
    diffusion-weighted image, b-values, and b-vectors, the workflow will return the subject's connectome
    as a Connectome File Format (CFF) file for use in Connectome Viewer (http://www.cmtk.org).

    Example
    -------

    >>> conmapper = create_connectivity_pipeline("nipype_conmap")
    >>> conmapper.inputs.inputnode.subjects_dir = '.'
    >>> conmapper.inputs.inputnode.subject_id = 'subj1'
    >>> conmapper.inputs.inputnode.dwi = 'data.nii.gz'
    >>> conmapper.inputs.inputnode.bvecs = 'bvecs'
    >>> conmapper.inputs.inputnode.bvals = 'bvals'
    >>> conmapper.run()                 # doctest: +SKIP

    Inputs::

        inputnode.subject_id
        inputnode.subjects_dir
        inputnode.dwi
        inputnode.bvecs
        inputnode.bvals
        inputnode.resolution_network_file
        inputnode.network_file

    Outputs::

        outputnode.connectome
        outputnode.nxstatscff
        outputnode.nxmatlab
        outputnode.nxcsv
        outputnode.nxmergedcsv
        outputnode.fa
        outputnode.tracts
        outputnode.filtered_tractography
        outputnode.cmatrix
        outputnode.cmatrix_csv
        outputnode.meanfib_csv
        outputnode.fibstd_csv
        outputnode.cmatrices_csv
        outputnode.b0resampled
        outputnode.rois
        outputnode.rois_orig
        outputnode.odfs
        outputnode.struct
        outputnode.gpickled_network
        outputnode.mean_fiber_length
        outputnode.fiber_length_std
    """

    inputnode_within = pe.Node(util.IdentityInterface(fields=["subject_id",
                                                              "dwi",
                                                              "bvecs",
                                                              "bvals",
                                                              "subjects_dir",
                                                              "resolution_network_file",
                                                              "network_file"]),
                               name="inputnode_within")

    FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='fssource')
    FreeSurferSourceLH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceLH')
    FreeSurferSourceLH.inputs.hemi = 'lh'

    FreeSurferSourceRH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceRH')
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

        mrtrix_dti_tutorial.py
            Tutorial that focuses solely on the MRtrix diffusion processing

        http://www.brain.org.au/software/mrtrix/index.html
            MRtrix's online documentation
    """

    """
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


    """
    A few Camino Nodes
    ------------------
	There are currently issues converting scalar maps from MRtrix's .mif format to Nifti, so we will use the Camino nodes for now
    """

    """
    Since the b values and b vectors come from the FSL course, we must convert it to a scheme file
    for use in Camino.
    """

    fsl2scheme = pe.Node(interface=camino.FSL2Scheme(), name="fsl2scheme")
    fsl2scheme.inputs.usegradmod = True

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
    MRmult_merge = pe.Node(interface=util.Merge(2), name="MRmultiply_merge")
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
    tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(),name='tck2trk')

    """
    Structural segmentation nodes
    -----------------------------
    """

    """
    In order to improve the coregistration of the parcellation scheme
    with the diffusion-weighted image, we resample the b0 image to use
    as a reference in the FLIRT steps below.
    """

    resampleb0 = pe.Node(interface=fs.MRIConvert(), name='resampleb0')
    resampleb0.inputs.out_type = 'nii'
    resampleb0.inputs.vox_size = (1, 1, 1)

    """
    The following nodes identify the transformation between the diffusion-weighted
    image and the structural image. This transformation is then inverted and applied
    to the structural image and it's parcellated equivalent, in order to get the parcellation
    and the tractography into the same space.
    """

    coregister = pe.Node(interface=fsl.FLIRT(dof=6), name = 'coregister')
    coregister.inputs.cost = ('normmi')
    convertxfm = pe.Node(interface=fsl.ConvertXFM(), name = 'convertxfm')
    convertxfm.inputs.invert_xfm = True
    inverse = pe.Node(interface=fsl.FLIRT(), name = 'inverse')
    inverse.inputs.interp = ('nearestneighbour')
    inverse.inputs.apply_xfm = True
    inverse_AparcAseg = inverse.clone('inverse_AparcAseg')
    inverseROIsToB0 = inverse.clone('inverseROIsToB0')

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

    creatematrix = pe.Node(interface=cmtk.CreateMatrix(), name="CreateMatrix")

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
    trkTracts = pe.Node(interface=util.Merge(2), name="trkTracts")

    """
    We also create a node to calculate several network metrics on our resulting file, and another CFF converter
    which will be used to package these networks into a single file.
    """

    ntwkMetrics = pe.Node(interface=cmtk.NetworkXMetrics(), name="NetworkXMetrics")
    NxStatsCFFConverter = pe.Node(interface=cmtk.CFFConverter(), name="NxStatsCFFConverter")
    NxStatsCFFConverter.inputs.script_files = op.abspath(inspect.getfile(inspect.currentframe()))

    Matlab2CSV_node = pe.Node(interface=misc.Matlab2CSV(), name="Matlab2CSV_node")
    Matlab2CSV_cmatrix = Matlab2CSV_node.clone(name="Matlab2CSV_cmatrix")
    Matlab2CSV_meanfib = Matlab2CSV_node.clone(name="Matlab2CSV_meanfib")
    Matlab2CSV_fibstd = Matlab2CSV_node.clone(name="Matlab2CSV_fibstd")

    MergeCSVFiles_node = pe.Node(interface=misc.MergeCSVFiles(), name="MergeCSVFiles_node")
    MergeCSVFiles_node.inputs.extra_column_heading = 'subject'
    mergeCSVMatrices = pe.Node(interface=util.Merge(3), name="mergeCSVMatrices")
    MergeCSVFiles_cmatrices = pe.Node(interface=misc.MergeCSVFiles(), name="MergeCSVFiles_cmatrices")
    MergeCSVFiles_cmatrices.inputs.extra_column_heading = 'subject'

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

    mapping.connect([(inputnode_within, FreeSurferSource,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode_within, FreeSurferSource,[("subject_id","subject_id")])])

    mapping.connect([(inputnode_within, FreeSurferSourceLH,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode_within, FreeSurferSourceLH,[("subject_id","subject_id")])])

    mapping.connect([(inputnode_within, FreeSurferSourceRH,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode_within, FreeSurferSourceRH,[("subject_id","subject_id")])])

    mapping.connect([(inputnode_within, parcellate,[("subjects_dir","subjects_dir")])])

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

    mapping.connect([(inputnode_within, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                    ("bvals", "bval_file")])])
    mapping.connect([(inputnode_within, eddycorrect,[("dwi","inputnode.in_file")])])
    mapping.connect([(eddycorrect, dwi2tensor,[("outputnode.eddy_corrected","in_file")])])
    mapping.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

    mapping.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                           (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                           (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                          ])
    mapping.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])

    """
    Required conversions for processing in Camino:
    """

    mapping.connect([(inputnode_within, image2voxel, [("dwi", "in_file")]),
                           (inputnode_within, fsl2scheme, [("bvecs", "bvec_file"),
                                                    ("bvals", "bval_file")]),
                           (image2voxel, dtifit,[['voxel_order','in_file']]),
                           (fsl2scheme, dtifit,[['scheme','scheme_file']])
                          ])

    """
    Connecting the Fractional Anisotropy and Trace nodes is simple, as they obtain their input from the
    tensor fitting. This is also where our voxel- and data-grabbing functions come in. We pass these functions,
    along with the original DWI image from the input node, to the header-generating nodes. This ensures that the
    files will be correct and readable.
    """

    mapping.connect([(dtifit, fa,[("tensor_fitted","in_file")])])
    mapping.connect([(fa, analyzeheader_fa,[("fa","in_file")])])
    mapping.connect([(inputnode_within, analyzeheader_fa,[(('dwi', get_vox_dims), 'voxel_dims'),
        (('dwi', get_data_dims), 'data_dims')])])
    mapping.connect([(fa, fa2nii,[('fa','data_file')])])
    mapping.connect([(inputnode_within, fa2nii,[(('dwi', get_affine), 'affine')])])
    mapping.connect([(analyzeheader_fa, fa2nii,[('header', 'header_file')])])


    mapping.connect([(dtifit, trace,[("tensor_fitted","in_file")])])
    mapping.connect([(trace, analyzeheader_trace,[("trace","in_file")])])
    mapping.connect([(inputnode_within, analyzeheader_trace,[(('dwi', get_vox_dims), 'voxel_dims'),
        (('dwi', get_data_dims), 'data_dims')])])
    mapping.connect([(trace, trace2nii,[('trace','data_file')])])
    mapping.connect([(inputnode_within, trace2nii,[(('dwi', get_affine), 'affine')])])
    mapping.connect([(analyzeheader_trace, trace2nii,[('header', 'header_file')])])

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

    """
    Structural Processing
    ---------------------
    First, we coregister the structural image to the diffusion image and then obtain the inverse of transformation.
    """

    mapping.connect([(eddycorrect, coregister,[("outputnode.eddy_corrected","in_file")])])
    mapping.connect([(mri_convert_Brain, coregister,[('out_file','reference')])])
    mapping.connect([(coregister, convertxfm,[('out_matrix_file','in_file')])])
    mapping.connect([(eddycorrect, inverse,[("outputnode.eddy_corrected","reference")])])
    mapping.connect([(convertxfm, inverse,[('out_file','in_matrix_file')])])
    mapping.connect([(mri_convert_Brain, inverse,[('out_file','in_file')])])

    """
    The b0 image is upsampled to the same dimensions as the parcellated structural image to improve their coregistration.
    """

    mapping.connect([(eddycorrect, resampleb0,[('pick_ref.out', 'in_file')])])
    mapping.connect([(resampleb0, inverse_AparcAseg,[('out_file','reference')])])
    mapping.connect([(convertxfm, inverse_AparcAseg,[('out_file','in_matrix_file')])])
    mapping.connect([(eddycorrect, inverseROIsToB0,[('pick_ref.out', 'reference')])])
    mapping.connect([(convertxfm, inverseROIsToB0,[('out_file','in_matrix_file')])])

    """
    The parcellation is connected for transformation into diffusion space.
    """

    mapping.connect([(inputnode_within, parcellate,[("subject_id","subject_id")])])
    mapping.connect([(parcellate, inverse_AparcAseg,[('roi_file','in_file')])])
    mapping.connect([(parcellate, inverseROIsToB0,[('roi_file','in_file')])])

    """
    The MRtrix-tracked fibers are converted to TrackVis format (with voxel and data dimensions grabbed from the DWI).
    The connectivity matrix is created with the .trk fibers and the coregistered parcellation file.
    """

    mapping.connect([(eddycorrect, tck2trk,[("outputnode.eddy_corrected","image_file")])])
    mapping.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])
    mapping.connect([(tck2trk, creatematrix,[("out_file","tract_file")])])
    mapping.connect(inputnode_within, 'resolution_network_file',
                    creatematrix, 'resolution_network_file')
    mapping.connect([(inputnode_within, creatematrix,[("subject_id","out_matrix_file")])])
    mapping.connect([(inputnode_within, creatematrix,[("subject_id","out_matrix_mat_file")])])
    mapping.connect([(inverse_AparcAseg, creatematrix,[("out_file","roi_file")])])

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

    mapping.connect([(eddycorrect, niftiVolumes,[("outputnode.eddy_corrected","in2")])])
    mapping.connect([(mri_convert_Brain, niftiVolumes,[("out_file","in3")])])
    mapping.connect([(inverse_AparcAseg, niftiVolumes,[("out_file","in1")])])

    mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file","in1")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file_mm","in2")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("fiber_length_file","in3")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("fiber_label_file","in4")])])

    mapping.connect([(tck2trk, trkTracts,[("out_file","in1")])])
    mapping.connect([(creatematrix, trkTracts,[("filtered_tractography","in2")])])

    """
    This block actually connects the merged lists to the CFF converter. We pass the surfaces
    and volumes that are to be included, as well as the tracts and the network itself. The currently
    running pipeline (connectivity_tutorial_advanced.py) is also scraped and included in the CFF file. This
    makes it easy for the user to examine the entire processing pathway used to generate the end
    product.
    """

    mapping.connect([(giftiSurfaces, CFFConverter,[("out","gifti_surfaces")])])
    mapping.connect([(giftiLabels, CFFConverter,[("out","gifti_labels")])])
    mapping.connect([(creatematrix, CFFConverter,[("matrix_file","gpickled_networks")])])
    mapping.connect([(niftiVolumes, CFFConverter,[("out","nifti_volumes")])])
    mapping.connect([(fiberDataArrays, CFFConverter,[("out","data_files")])])
    mapping.connect([(trkTracts, CFFConverter,[("out","tract_files")])])
    mapping.connect([(inputnode_within, CFFConverter,[("subject_id","title")])])

    """
    The graph theoretical metrics which have been generated are placed into another CFF file.
    """

    mapping.connect([(creatematrix, ntwkMetrics,[("matrix_file","in_file")])])
    mapping.connect([(creatematrix, gpickledNetworks,[("matrix_file","in1")])])
    mapping.connect([(ntwkMetrics, gpickledNetworks,[("gpickled_network_files","in2")])])
    mapping.connect([(gpickledNetworks, NxStatsCFFConverter,[("out","gpickled_networks")])])

    mapping.connect([(giftiSurfaces, NxStatsCFFConverter,[("out","gifti_surfaces")])])
    mapping.connect([(giftiLabels, NxStatsCFFConverter,[("out","gifti_labels")])])
    mapping.connect([(niftiVolumes, NxStatsCFFConverter,[("out","nifti_volumes")])])
    mapping.connect([(fiberDataArrays, NxStatsCFFConverter,[("out","data_files")])])
    mapping.connect([(inputnode_within, NxStatsCFFConverter,[("subject_id","title")])])

    mapping.connect([(ntwkMetrics, Matlab2CSV_node,[("node_measures_matlab","in_file")])])
    mapping.connect([(creatematrix, Matlab2CSV_cmatrix,[("matrix_mat_file","in_file")])])
    mapping.connect([(creatematrix, Matlab2CSV_meanfib,[("mean_fiber_length_matrix_mat_file","in_file")])])
    mapping.connect([(creatematrix, Matlab2CSV_fibstd,[("fiber_length_std_matrix_mat_file","in_file")])])
    mapping.connect([(Matlab2CSV_node, MergeCSVFiles_node,[("csv_files","in_files")])])
    mapping.connect([(inputnode_within, MergeCSVFiles_node,[("subject_id","out_file")])])
    mapping.connect([(inputnode_within, MergeCSVFiles_node,[("subject_id","extra_field")])])
    mapping.connect(inputnode_within, ('network_file', pullnodeIDs),
                    MergeCSVFiles_node, 'row_headings')

    mapping.connect([(Matlab2CSV_cmatrix, mergeCSVMatrices,[("csv_files","in1")])])
    mapping.connect([(Matlab2CSV_meanfib, mergeCSVMatrices,[("csv_files","in2")])])
    mapping.connect([(Matlab2CSV_fibstd, mergeCSVMatrices,[("csv_files","in3")])])
    mapping.connect([(mergeCSVMatrices, MergeCSVFiles_cmatrices,[("out","in_files")])])
    mapping.connect([(inputnode_within, MergeCSVFiles_cmatrices,[("subject_id","out_file")])])
    mapping.connect([(inputnode_within, MergeCSVFiles_cmatrices,[("subject_id","extra_field")])])
    """
    Create a higher-level workflow
    --------------------------------------
    Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
    declared at the beginning. Our tutorial can is now extensible to any arbitrary number of subjects by simply adding
    their names to the subject list and their data to the proper folders.
    """

    inputnode = pe.Node(interface=util.IdentityInterface(fields=["subject_id", "dwi", "bvecs", "bvals", "subjects_dir"]), name="inputnode")

    outputnode = pe.Node(interface = util.IdentityInterface(fields=["fa",
                                                                "struct",
                                                                "tracts",
                                                                "connectome",
                                                                "nxstatscff",
                                                                "nxmatlab",
                                                                "nxcsv",
                                                                "cmatrix_csv",
                                                                "meanfib_csv",
                                                                "fibstd_csv",
                                                                "cmatrices_csv",
                                                                "nxmergedcsv",
                                                                "cmatrix",
                                                                "gpickled_network",
                                                                "filtered_tracts",
                                                                "b0_resampled",
                                                                "rois",
                                                                "brain_overlay",
                                                                "GM_overlay",
                                                                "rois_orig",
                                                                "odfs",
                                                                "warped",
                                                                "trace",
                                                                "mean_fiber_length",
                                                                "fiber_length_std"]),
                                        name="outputnode")

    connectivity = pe.Workflow(name="connectivity")
    connectivity.base_output_dir=name
    connectivity.base_dir=name

    connectivity.connect([(inputnode, mapping, [("dwi", "inputnode_within.dwi"),
                                              ("bvals", "inputnode_within.bvals"),
                                              ("bvecs", "inputnode_within.bvecs"),
                                              ("subject_id", "inputnode_within.subject_id"),
                                              ("subjects_dir", "inputnode_within.subjects_dir")])
                                              ])

    connectivity.connect([(mapping, outputnode, [("tck2trk.out_file", "tracts"),
		("CFFConverter.connectome_file", "connectome"),
		("NxStatsCFFConverter.connectome_file", "nxstatscff"),
		("NetworkXMetrics.matlab_matrix_files", "nxmatlab"),
        ("Matlab2CSV_node.csv_files", "nxcsv"),
        ("Matlab2CSV_cmatrix.csv_files", "cmatrix_csv"),
        ("Matlab2CSV_meanfib.csv_files", "meanfib_csv"),
        ("Matlab2CSV_fibstd.csv_files", "fibstd_csv"),
        ("MergeCSVFiles_node.csv_file", "nxmergedcsv"),
        ("MergeCSVFiles_cmatrices.csv_file", "cmatrices_csv"),
		("CreateMatrix.matrix_mat_file", "cmatrix"),
		("CreateMatrix.mean_fiber_length_matrix_mat_file", "mean_fiber_length"),
		("CreateMatrix.fiber_length_std_matrix_mat_file", "fiber_length_std"),
		("CreateMatrix.matrix_file", "gpickled_network"),
		("CreateMatrix.filtered_tractography", "filtered_tracts"),
		("resampleb0.out_file", "b0_resampled"),
		("inverse_AparcAseg.out_file", "rois"),
		("inverse.out_file", "brain_overlay"),
		("inverseROIsToB0.out_file", "GM_overlay"),
		("Parcellate.roi_file", "rois_orig"),
        ("fa2nii.nifti_file", "fa"),
        ("trace2nii.nifti_file", "trace"),
		("csdeconv.spherical_harmonics_image", "odfs"),
		("inverse_AparcAseg.out_file", "warped"),
		("mri_convert_Brain.out_file", "struct")])
		])
    return connectivity
