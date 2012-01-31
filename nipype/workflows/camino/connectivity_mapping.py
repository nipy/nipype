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
import os.path as op

from .diffusion import (get_vox_dims, get_data_dims, get_affine)


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



def create_connectivity_pipeline(name="connectivity"):
    """Creates a pipeline that does the same connectivity processing as in the
    connectivity_tutorial example script. Given a subject id (and completed Freesurfer reconstruction)
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
        inputnode.roi_LUT_file

    Outputs::

        outputnode.connectome
        outputnode.cmatrix
        outputnode.gpickled_network
        outputnode.fa
        outputnode.struct
        outputnode.trace
        outputnode.tracts
        outputnode.tensors

    """

    inputnode1 = pe.Node(interface=util.IdentityInterface(fields=["subject_id",
                                                                  "dwi",
                                                                  "bvecs",
                                                                  "bvals",
                                                                  "subjects_dir",
                                                                  "resolution_network_file",
                                                                  "roi_LUT_file"
                                                                  ]),
                         name="inputnode1")

    FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='fssource')

    FreeSurferSourceLH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceLH')
    FreeSurferSourceLH.inputs.hemi = 'lh'

    FreeSurferSourceRH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceRH')
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
    coregister.inputs.cost = ('normmi')

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
    This tutorial demonstrates two methods of connectivity mapping. The first uses the conmap function of Camino.
    The problem with this method is that it can be very memory intensive. To deal with this, we add a "shredding" node
    which removes roughly half of the tracts in the file.
    """

    tractshred = pe.Node(interface=camino.TractShredder(), name='tractshred')
    tractshred.inputs.offset = 0
    tractshred.inputs.bunchsize = 2
    tractshred.inputs.space = 1

    """
    Here we create the Camino-based connectivity mapping node. For visualization, it can be beneficial to set a
    threshold for the minimum number of fiber connections that are required for an edge to be drawn on the graph.
    """

    conmap = pe.Node(interface=camino.Conmap(), name='conmap')
    conmap.inputs.threshold = 100

    """
    Currently, the best program for visualizing tracts is TrackVis. For this reason, a node is included to
    convert the raw tract data to .trk format. Solely for testing purposes, another node is added to perform the reverse.
    """

    camino2trackvis = pe.Node(interface=cam2trk.Camino2Trackvis(), name="camino2trackvis")
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

    """
    The CreateMatrix interface takes in the remapped aparc+aseg image as well as the label dictionary and fiber tracts
    and outputs a number of different files. The most important of which is the connectivity network itself, which is stored
    as a 'gpickle' and can be loaded using Python's NetworkX package (see CreateMatrix docstring). Also outputted are various
    NumPy arrays containing detailed tract information, such as the start and endpoint regions, and statistics on the mean and
    standard deviation for the fiber length of each connection. These matrices can be used in the ConnectomeViewer to plot the
    specific tracts that connect between user-selected regions.
    """

    creatematrix = pe.Node(interface=cmtk.CreateMatrix(), name="CreateMatrix")

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


    mapping.connect([(inputnode1, FreeSurferSource,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode1, FreeSurferSource,[("subject_id","subject_id")])])

    mapping.connect([(inputnode1, FreeSurferSourceLH,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode1, FreeSurferSourceLH,[("subject_id","subject_id")])])

    mapping.connect([(inputnode1, FreeSurferSourceRH,[("subjects_dir","subjects_dir")])])
    mapping.connect([(inputnode1, FreeSurferSourceRH,[("subject_id","subject_id")])])

    """
    Required conversions for processing in Camino:
    """

    mapping.connect([(inputnode1, image2voxel, [("dwi", "in_file")]),
                           (inputnode1, fsl2scheme, [("bvecs", "bvec_file"),
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

    mapping.connect([(inputnode1, b0Strip,[('dwi','in_file')])])
    mapping.connect([(inputnode1, b0Strip,[('dwi','t2_guided')])]) # Added to improve damaged brain extraction
    mapping.connect([(b0Strip, coregister,[('out_file','in_file')])])
    mapping.connect([(mri_convert_Brain, coregister,[('out_file','reference')])])
    mapping.connect([(coregister, convertxfm,[('out_matrix_file','in_file')])])
    mapping.connect([(b0Strip, inverse,[('out_file','reference')])])
    mapping.connect([(convertxfm, inverse,[('out_file','in_matrix_file')])])
    mapping.connect([(mri_convert_WMParc, inverse,[('out_file','in_file')])])
    #mapping.connect([(inverse, conmap,[('out_file','roi_file')])])

    """
    The tractography pipeline consists of the following nodes. Further information about the tractography
    can be found in nipype/examples/camino_dti_tutorial.py.
    """

    mapping.connect([(b0Strip, track,[("mask_file","seed_file")])])
    mapping.connect([(fsl2scheme, dtlutgen,[("scheme","scheme_file")])])
    mapping.connect([(dtlutgen, picopdfs,[("dtLUT","luts")])])
    mapping.connect([(dtifit, picopdfs,[("tensor_fitted","in_file")])])
    mapping.connect([(picopdfs, track,[("pdfs","in_file")])])

    """
    The tractography is passed to the shredder in preparation for connectivity mapping.
    Again, the required conmap connection is left commented out.
    """

    mapping.connect([(track, tractshred,[("tracked","in_file")])])
    #mapping.connect([(tractshred, conmap,[("shredded","in_file")])])

    """
    Connecting the Fractional Anisotropy and Trace nodes is simple, as they obtain their input from the
    tensor fitting. This is also where our voxel- and data-grabbing functions come in. We pass these functions,
    along with the original DWI image from the input node, to the header-generating nodes. This ensures that the
    files will be correct and readable.
    """

    mapping.connect([(dtifit, fa,[("tensor_fitted","in_file")])])
    mapping.connect([(fa, analyzeheader_fa,[("fa","in_file")])])
    mapping.connect([(inputnode1, analyzeheader_fa,[(('dwi', get_vox_dims), 'voxel_dims'),
        (('dwi', get_data_dims), 'data_dims')])])
    mapping.connect([(fa, fa2nii,[('fa','data_file')])])
    mapping.connect([(inputnode1, fa2nii,[(('dwi', get_affine), 'affine')])])
    mapping.connect([(analyzeheader_fa, fa2nii,[('header', 'header_file')])])


    mapping.connect([(dtifit, trace,[("tensor_fitted","in_file")])])
    mapping.connect([(trace, analyzeheader_trace,[("trace","in_file")])])
    mapping.connect([(inputnode1, analyzeheader_trace,[(('dwi', get_vox_dims), 'voxel_dims'),
        (('dwi', get_data_dims), 'data_dims')])])
    mapping.connect([(trace, trace2nii,[('trace','data_file')])])
    mapping.connect([(inputnode1, trace2nii,[(('dwi', get_affine), 'affine')])])
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
    mapping.connect([(inputnode1, camino2trackvis,[(('dwi', get_vox_dims), 'voxel_dims'),
        (('dwi', get_data_dims), 'data_dims')])])

    """
    Here the CMTK connectivity mapping nodes are connected.
    The original aparc+aseg image is converted to NIFTI, then registered to
    the diffusion image and delivered to the ROIGen node. The remapped parcellation,
    original tracts, and label file are then given to CreateMatrix.
    """

    mapping.connect(inputnode1, 'roi_LUT_file',
                    roigen, 'LUT_file')
    mapping.connect(inputnode1, 'resolution_network_file',
                    creatematrix, 'resolution_network_file')
    mapping.connect([(FreeSurferSource, mri_convert_AparcAseg, [(('aparc_aseg', select_aparc), 'in_file')])])

    mapping.connect([(b0Strip, inverse_AparcAseg,[('out_file','reference')])])
    mapping.connect([(convertxfm, inverse_AparcAseg,[('out_file','in_matrix_file')])])
    mapping.connect([(mri_convert_AparcAseg, inverse_AparcAseg,[('out_file','in_file')])])

    mapping.connect([(inverse_AparcAseg, roigen,[("out_file","aparc_aseg_file")])])
    mapping.connect([(roigen, creatematrix,[("roi_file","roi_file")])])
    mapping.connect([(roigen, creatematrix,[("dict_file","dict_file")])])
    mapping.connect([(camino2trackvis, creatematrix,[("trackvis","tract_file")])])
    mapping.connect([(inputnode1, creatematrix,[("subject_id","out_matrix_file")])])
    mapping.connect([(inputnode1, creatematrix,[("subject_id","out_matrix_mat_file")])])

    """
    The merge nodes defined earlier are used here to create lists of the files which are
    destined for the CFFConverter.
    """

    #mapping.connect([(creatematrix, gpickledNetworks,[("matrix_file","in1")])])

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
    mapping.connect([(inputnode1, niftiVolumes,[("dwi","in2")])])
    mapping.connect([(mri_convert_Brain, niftiVolumes,[("out_file","in3")])])

    mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file","in1")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("endpoint_file_mm","in2")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("fiber_length_file","in3")])])
    mapping.connect([(creatematrix, fiberDataArrays,[("fiber_label_file","in4")])])

    """
    This block actually connects the merged lists to the CFF converter. We pass the surfaces
    and volumes that are to be included, as well as the tracts and the network itself. The currently
    running pipeline (connectivity_tutorial.py) is also scraped and included in the CFF file. This
    makes it easy for the user to examine the entire processing pathway used to generate the end
    product.
    """

    CFFConverter.inputs.script_files = op.abspath(inspect.getfile(inspect.currentframe()))
    mapping.connect([(giftiSurfaces, CFFConverter,[("out","gifti_surfaces")])])
    mapping.connect([(giftiLabels, CFFConverter,[("out","gifti_labels")])])
    mapping.connect([(creatematrix, CFFConverter,[("matrix_file","gpickled_networks")])])

    mapping.connect([(niftiVolumes, CFFConverter,[("out","nifti_volumes")])])
    mapping.connect([(fiberDataArrays, CFFConverter,[("out","data_files")])])
    mapping.connect([(camino2trackvis, CFFConverter,[("trackvis","tract_files")])])
    mapping.connect([(inputnode1, CFFConverter,[("subject_id","title")])])

    """
    Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
    declared at the beginning. Our tutorial can is now extensible to any arbitrary number of subjects by simply adding
    their names to the subject list and their data to the proper folders.
    """

    inputnode = pe.Node(interface=util.IdentityInterface(fields=["subject_id", "dwi", "bvecs", "bvals", "subjects_dir"]), name="inputnode")

    outputnode = pe.Node(interface = util.IdentityInterface(fields=["fa",
                                                                "struct",
                                                                "trace",
                                                                "tracts",
                                                                "connectome",
                                                                "cmatrix",
                                                                "gpickled_network",
                                                                "rois",
                                                                "mean_fiber_length",
                                                                "fiber_length_std",
                                                                "tensors"]),
                                        name="outputnode")

    connectivity = pe.Workflow(name="connectivity")
    connectivity.base_output_dir=name

    connectivity.connect([(inputnode, mapping, [("dwi", "inputnode1.dwi"),
                                              ("bvals", "inputnode1.bvals"),
                                              ("bvecs", "inputnode1.bvecs"),
                                              ("subject_id", "inputnode1.subject_id"),
                                              ("subjects_dir", "inputnode1.subjects_dir")])
                                              ])

    connectivity.connect([(mapping, outputnode, [("camino2trackvis.trackvis", "tracts"),
        ("CFFConverter.connectome_file", "connectome"),
        ("CreateMatrix.matrix_mat_file", "cmatrix"),
        ("CreateMatrix.mean_fiber_length_matrix_mat_file", "mean_fiber_length"),
        ("CreateMatrix.fiber_length_std_matrix_mat_file", "fiber_length_std"),
        ("fa2nii.nifti_file", "fa"),
        ("CreateMatrix.matrix_file", "gpickled_network"),
        ("ROIGen.roi_file", "rois"),
        ("mri_convert_Brain.out_file", "struct"),
        ("trace2nii.nifti_file", "trace"),
        ("dtifit.tensor_fitted", "tensors")])
        ])

    return connectivity
