# -*- coding: utf-8 -*-
from ....interfaces import utility as util  # utility
from ....pipeline import engine as pe  # pypeline engine
from ....interfaces import camino as camino
from ....interfaces import fsl as fsl
from ....interfaces import camino2trackvis as cam2trk
from ....algorithms import misc as misc
from ...misc.utils import get_affine, get_data_dims, get_vox_dims


def create_camino_dti_pipeline(name="dtiproc"):
    """Creates a pipeline that does the same diffusion processing as in the
    :doc:`../../users/examples/dmri_camino_dti` example script. Given a diffusion-weighted image,
    b-values, and b-vectors, the workflow will return the tractography
    computed from diffusion tensors and from PICo probabilistic tractography.

    Example
    -------

    >>> import os
    >>> nipype_camino_dti = create_camino_dti_pipeline("nipype_camino_dti")
    >>> nipype_camino_dti.inputs.inputnode.dwi = os.path.abspath('dwi.nii')
    >>> nipype_camino_dti.inputs.inputnode.bvecs = os.path.abspath('bvecs')
    >>> nipype_camino_dti.inputs.inputnode.bvals = os.path.abspath('bvals')
    >>> nipype_camino_dti.run()                  # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.bvecs
        inputnode.bvals

    Outputs::

        outputnode.fa
        outputnode.trace
        outputnode.tracts_pico
        outputnode.tracts_dt
        outputnode.tensors

    """

    inputnode1 = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]),
        name="inputnode1")
    """
    Setup for Diffusion Tensor Computation
    --------------------------------------
    In this section we create the nodes necessary for diffusion analysis.
    First, the diffusion image is converted to voxel order.
    """

    image2voxel = pe.Node(interface=camino.Image2Voxel(), name="image2voxel")
    fsl2scheme = pe.Node(interface=camino.FSL2Scheme(), name="fsl2scheme")
    fsl2scheme.inputs.usegradmod = True
    """
    Second, diffusion tensors are fit to the voxel-order data.
    """

    dtifit = pe.Node(interface=camino.DTIFit(), name='dtifit')
    """
    Next, a lookup table is generated from the schemefile and the
    signal-to-noise ratio (SNR) of the unweighted (q=0) data.
    """

    dtlutgen = pe.Node(interface=camino.DTLUTGen(), name="dtlutgen")
    dtlutgen.inputs.snr = 16.0
    dtlutgen.inputs.inversion = 1
    """
    In this tutorial we implement probabilistic tractography using the PICo algorithm.
    PICo tractography requires an estimate of the fibre direction and a model of its
    uncertainty in each voxel; this is produced using the following node.
    """

    picopdfs = pe.Node(interface=camino.PicoPDFs(), name="picopdfs")
    picopdfs.inputs.inputmodel = 'dt'
    """
    An FSL BET node creates a brain mask is generated from the diffusion image for seeding the PICo     tractography.
    """

    bet = pe.Node(interface=fsl.BET(), name="bet")
    bet.inputs.mask = True
    """
    Finally, tractography is performed.
    First DT streamline tractography.
    """

    trackdt = pe.Node(interface=camino.TrackDT(), name="trackdt")
    """
    Now camino's Probablistic Index of connectivity algorithm.
    In this tutorial, we will use only 1 iteration for time-saving purposes.
    """

    trackpico = pe.Node(interface=camino.TrackPICo(), name="trackpico")
    trackpico.inputs.iterations = 1
    """
    Currently, the best program for visualizing tracts is TrackVis. For this reason, a node is included         to convert the raw tract data to .trk format. Solely for testing purposes, another node is added to         perform the reverse.
    """

    cam2trk_dt = pe.Node(
        interface=cam2trk.Camino2Trackvis(), name="cam2trk_dt")
    cam2trk_dt.inputs.min_length = 30
    cam2trk_dt.inputs.voxel_order = 'LAS'

    cam2trk_pico = pe.Node(
        interface=cam2trk.Camino2Trackvis(), name="cam2trk_pico")
    cam2trk_pico.inputs.min_length = 30
    cam2trk_pico.inputs.voxel_order = 'LAS'
    """
    Tracts can also be converted to VTK and OOGL formats, for use in programs such as GeomView and      Paraview, using the following two nodes.
    """

    # vtkstreamlines = pe.Node(interface=camino.VtkStreamlines(), name="vtkstreamlines")
    # procstreamlines = pe.Node(interface=camino.ProcStreamlines(), name="procstreamlines")
    # procstreamlines.inputs.outputtracts = 'oogl'
    """
    We can also produce a variety of scalar values from our fitted tensors. The following nodes generate        the fractional anisotropy and diffusivity trace maps and their associated headers.
    """

    fa = pe.Node(interface=camino.ComputeFractionalAnisotropy(), name='fa')
    # md = pe.Node(interface=camino.MD(),name='md')
    trace = pe.Node(interface=camino.ComputeTensorTrace(), name='trace')
    dteig = pe.Node(interface=camino.ComputeEigensystem(), name='dteig')

    analyzeheader_fa = pe.Node(
        interface=camino.AnalyzeHeader(), name="analyzeheader_fa")
    analyzeheader_fa.inputs.datatype = "double"
    analyzeheader_trace = analyzeheader_fa.clone('analyzeheader_trace')

    # analyzeheader_md = pe.Node(interface= camino.AnalyzeHeader(), name = "analyzeheader_md")
    # analyzeheader_md.inputs.datatype = "double"
    # analyzeheader_trace = analyzeheader_md.clone('analyzeheader_trace')

    fa2nii = pe.Node(interface=misc.CreateNifti(), name='fa2nii')
    trace2nii = fa2nii.clone("trace2nii")
    """
    Since we have now created all our nodes, we can now define our workflow and start making connections.
    """

    tractography = pe.Workflow(name='tractography')

    tractography.connect([(inputnode1, bet, [("dwi", "in_file")])])
    """
    File format conversion
    """

    tractography.connect([(inputnode1, image2voxel, [("dwi", "in_file")]),
                          (inputnode1, fsl2scheme, [("bvecs", "bvec_file"),
                                                    ("bvals", "bval_file")])])
    """
    Tensor fitting
    """

    tractography.connect([(image2voxel, dtifit, [['voxel_order', 'in_file']]),
                          (fsl2scheme, dtifit, [['scheme', 'scheme_file']])])
    """
    Workflow for applying DT streamline tractogpahy
    """

    tractography.connect([(bet, trackdt, [("mask_file", "seed_file")])])
    tractography.connect([(dtifit, trackdt, [("tensor_fitted", "in_file")])])
    """
    Workflow for applying PICo
    """

    tractography.connect([(bet, trackpico, [("mask_file", "seed_file")])])
    tractography.connect([(fsl2scheme, dtlutgen, [("scheme", "scheme_file")])])
    tractography.connect([(dtlutgen, picopdfs, [("dtLUT", "luts")])])
    tractography.connect([(dtifit, picopdfs, [("tensor_fitted", "in_file")])])
    tractography.connect([(picopdfs, trackpico, [("pdfs", "in_file")])])

    # Mean diffusivity still appears broken
    # tractography.connect([(dtifit, md,[("tensor_fitted","in_file")])])
    # tractography.connect([(md, analyzeheader_md,[("md","in_file")])])
    # tractography.connect([(inputnode, analyzeheader_md,[(('dwi', get_vox_dims), 'voxel_dims'),
    # (('dwi', get_data_dims), 'data_dims')])])
    # This line is commented out because the ProcStreamlines node keeps throwing memory errors
    # tractography.connect([(track, procstreamlines,[("tracked","in_file")])])
    """
    Connecting the Fractional Anisotropy and Trace nodes is simple, as they obtain their input from the
    tensor fitting.

    This is also where our voxel- and data-grabbing functions come in. We pass these functions, along       with the original DWI image from the input node, to the header-generating nodes. This ensures that      the files will be correct and readable.
    """

    tractography.connect([(dtifit, fa, [("tensor_fitted", "in_file")])])
    tractography.connect([(fa, analyzeheader_fa, [("fa", "in_file")])])
    tractography.connect([(inputnode1, analyzeheader_fa,
                           [(('dwi', get_vox_dims), 'voxel_dims'),
                            (('dwi', get_data_dims), 'data_dims')])])
    tractography.connect([(fa, fa2nii, [('fa', 'data_file')])])
    tractography.connect([(inputnode1, fa2nii, [(('dwi', get_affine),
                                                 'affine')])])
    tractography.connect([(analyzeheader_fa, fa2nii, [('header',
                                                       'header_file')])])

    tractography.connect([(dtifit, trace, [("tensor_fitted", "in_file")])])
    tractography.connect([(trace, analyzeheader_trace, [("trace",
                                                         "in_file")])])
    tractography.connect([(inputnode1, analyzeheader_trace,
                           [(('dwi', get_vox_dims), 'voxel_dims'),
                            (('dwi', get_data_dims), 'data_dims')])])
    tractography.connect([(trace, trace2nii, [('trace', 'data_file')])])
    tractography.connect([(inputnode1, trace2nii, [(('dwi', get_affine),
                                                    'affine')])])
    tractography.connect([(analyzeheader_trace, trace2nii, [('header',
                                                             'header_file')])])

    tractography.connect([(dtifit, dteig, [("tensor_fitted", "in_file")])])

    tractography.connect([(trackpico, cam2trk_pico, [('tracked', 'in_file')])])
    tractography.connect([(trackdt, cam2trk_dt, [('tracked', 'in_file')])])
    tractography.connect([(inputnode1, cam2trk_pico,
                           [(('dwi', get_vox_dims), 'voxel_dims'),
                            (('dwi', get_data_dims), 'data_dims')])])

    tractography.connect([(inputnode1, cam2trk_dt,
                           [(('dwi', get_vox_dims), 'voxel_dims'),
                            (('dwi', get_data_dims), 'data_dims')])])

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]),
        name="inputnode")

    outputnode = pe.Node(
        interface=util.IdentityInterface(
            fields=["fa", "trace", "tracts_pico", "tracts_dt", "tensors"]),
        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir = name

    workflow.connect([(inputnode, tractography,
                       [("dwi", "inputnode1.dwi"),
                        ("bvals", "inputnode1.bvals"), ("bvecs",
                                                        "inputnode1.bvecs")])])

    workflow.connect([(tractography, outputnode,
                       [("cam2trk_dt.trackvis", "tracts_dt"),
                        ("cam2trk_pico.trackvis",
                         "tracts_pico"), ("fa2nii.nifti_file", "fa"),
                        ("trace2nii.nifti_file",
                         "trace"), ("dtifit.tensor_fitted", "tensors")])])

    return workflow
