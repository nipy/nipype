import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.fsl as fsl
import nipype.interfaces.mrtrix as mrtrix
import os, os.path as op
from nipype.workflows.camino.diffusion import get_data_dims, get_affine
 
def get_vox_dims_as_tuple(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()
    return tuple([float(voxdims[0]), float(voxdims[1]), float(voxdims[2])])

def create_mrtrix_dti_pipeline(name="dtiproc"):
    """Creates a pipeline that does the same diffusion processing as in the
    mrtrix_dti_tutorial example script. Given a diffusion-weighted image,
    b-values, and b-vectors, the workflow will return the tractography
    computed from spherical deconvolution and probabilistic streamline tractography

    Example
    -------

    >>> from nipype.workflows.mrtrix import create_mrtrix_dti_pipeline
    >>> dti = create_mrtrix_dti_pipeline("mrtrix_dti")
    >>> dti.inputs.inputnode.dwi = 'data.nii'
    >>> dti.inputs.inputnode.bvals = 'bvals'
    >>> dti.inputs.inputnode.bvecs = 'bvecs'
    >>> dti.run()                  # doctest: +SKIP

    Inputs::

        inputnode.dwi
        inputnode.bvecs
        inputnode.bvals

    Outputs::

        outputnode.fa
        outputnode.tdi
        outputnode.tracts_tck
        outputnode.tracts_trk
        outputnode.csdeconv

    """

    inputnode_within = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode_within")

    """
    Setup for Diffusion Tensor Computation
    --------------------------------------
    In this section we create the nodes necessary for diffusion analysis.
    """
    bet = pe.Node(interface=fsl.BET(), name="bet")
    bet.inputs.mask = True

    fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(),name='fsl2mrtrix')
    fsl2mrtrix.inputs.invert_y = True

    dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(),name='dwi2tensor')

    tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(),name='tensor2vector')
    tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(),name='tensor2adc')
    tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(),name='tensor2fa')

    erode_mask_firstpass = pe.Node(interface=mrtrix.Erode(),name='erode_mask_firstpass')
    erode_mask_secondpass = pe.Node(interface=mrtrix.Erode(),name='erode_mask_secondpass')

    threshold_b0 = pe.Node(interface=mrtrix.Threshold(),name='threshold_b0')

    threshold_FA = pe.Node(interface=mrtrix.Threshold(),name='threshold_FA')
    threshold_FA.inputs.absolute_threshold_value = 0.7

    threshold_wmmask = pe.Node(interface=mrtrix.Threshold(),name='threshold_wmmask')
    threshold_wmmask.inputs.absolute_threshold_value = 0.4

    MRmultiply = pe.Node(interface=mrtrix.MRMultiply(),name='MRmultiply')
    MRmult_merge = pe.Node(interface=util.Merge(2), name='MRmultiply_merge')

    median3d = pe.Node(interface=mrtrix.MedianFilter3D(),name='median3D')

    MRconvert = pe.Node(interface=mrtrix.MRConvert(),name='MRconvert')
    MRconvert.inputs.extract_at_axis = 3
    MRconvert.inputs.extract_at_coordinate = [0]

    csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(),name='csdeconv')

    gen_WM_mask = pe.Node(interface=mrtrix.GenerateWhiteMatterMask(),name='gen_WM_mask')

    estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(),name='estimateresponse')

    probCSDstreamtrack = pe.Node(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(),name='probCSDstreamtrack')
    probCSDstreamtrack.inputs.maximum_number_of_tracks = 15000

    tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(),name='tracks2prob')
    tracks2prob.inputs.colour = True
    tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(),name='tck2trk')


    """
    Creating the workflow
    --------------------------------------
    In this section we connect the nodes for the diffusion processing.
    """

    tractography = pe.Workflow(name='tractography')

    tractography.connect([(inputnode_within, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                    ("bvals", "bval_file")])])
    tractography.connect([(inputnode_within, dwi2tensor,[("dwi","in_file")])])
    tractography.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

    tractography.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                           (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                           (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                          ])

    tractography.connect([(inputnode_within, MRconvert,[("dwi","in_file")])])
    tractography.connect([(MRconvert, threshold_b0,[("converted","in_file")])])
    tractography.connect([(threshold_b0, median3d,[("out_file","in_file")])])
    tractography.connect([(median3d, erode_mask_firstpass,[("out_file","in_file")])])
    tractography.connect([(erode_mask_firstpass, erode_mask_secondpass,[("out_file","in_file")])])

    tractography.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])
    tractography.connect([(erode_mask_secondpass, MRmult_merge,[("out_file","in2")])])
    tractography.connect([(MRmult_merge, MRmultiply,[("out","in_files")])])
    tractography.connect([(MRmultiply, threshold_FA,[("out_file","in_file")])])
    tractography.connect([(threshold_FA, estimateresponse,[("out_file","mask_image")])])

    tractography.connect([(inputnode_within, bet,[("dwi","in_file")])])
    tractography.connect([(inputnode_within, gen_WM_mask,[("dwi","in_file")])])
    tractography.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
    tractography.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])

    tractography.connect([(inputnode_within, estimateresponse,[("dwi","in_file")])])
    tractography.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])

    tractography.connect([(inputnode_within, csdeconv,[("dwi","in_file")])])
    tractography.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
    tractography.connect([(estimateresponse, csdeconv,[("response","response_file")])])
    tractography.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

    tractography.connect([(gen_WM_mask, threshold_wmmask,[("WMprobabilitymap","in_file")])])
    tractography.connect([(threshold_wmmask, probCSDstreamtrack,[("out_file","seed_file")])])
    tractography.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])

    tractography.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
    tractography.connect([(inputnode_within, tracks2prob,[("dwi","template_file")])])

    tractography.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])
    tractography.connect([(inputnode_within, tck2trk,[("dwi","image_file")])])

    inputnode = pe.Node(interface = util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")
    
    outputnode = pe.Node(interface = util.IdentityInterface(fields=["fa",
                                                                "tracts_trk",
                                                                "csdeconv",
                                                                "tracts_tck",
                                                                "tdi"]),
                                        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir=name

    workflow.connect([(inputnode, tractography, [("dwi", "inputnode_within.dwi"),
                                              ("bvals", "inputnode_within.bvals"),
                                              ("bvecs", "inputnode_within.bvecs")])])

    workflow.connect([(tractography, outputnode, [("probCSDstreamtrack.tracked", "tracts_tck"),
        ("csdeconv.spherical_harmonics_image", "csdeconv"),
        ("tensor2fa.FA", "fa"),
        ("tck2trk.out_file", "tracts_trk"),
        ("tracks2prob.tract_image", "tdi")])
        ])

    return workflow
