import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.algorithms.misc as misc
import nipype.interfaces.mrtrix as mrtrix
import os, os.path as op
from nipype.workflows.camino.diffusion import get_vox_dims, get_data_dims, get_affine
 
def create_mrtrix_dti_pipeline(name="dtiproc"):
    """Creates a pipeline that does the same diffusion processing as in the
    camino_dti_tutorial example script. Given a diffusion-weighted image,
    b-values, and b-vectors, the workflow will return the tractography
    computed from diffusion tensors and from PICo probabilistic tractography.

    Example
    -------

    >>> import os
    >>> import nipype.workflows.mrtrix as mrwork                     # doctest: +SKIP
    >>> nipype_mrtrix_dti = cmonwk.mrtrix_dti_processing.create_mrtrix_dti_pipeline("nipype_mrtrix_dti")                     # doctest: +SKIP
    >>> nipype_mrtrix_dti.inputs.inputnode.dwi = os.path.abspath('dwi.nii')                   # doctest: +SKIP
    >>> nipype_mrtrix_dti.inputs.inputnode.bvecs = os.path.abspath('bvecs')                   # doctest: +SKIP
    >>> nipype_mrtrix_dti.inputs.inputnode.bvals = os.path.abspath('bvals')                  # doctest: +SKIP
    >>> nipype_mrtrix_dti.run()                  # doctest: +SKIP

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

    inputnode1 = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode1")

    """
    Setup for Diffusion Tensor Computation
    --------------------------------------
    In this section we create the nodes necessary for diffusion analysis.
    """
    bet = pe.Node(interface=fsl.BET(), name="bet")
    bet.inputs.mask = True

    dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(),name='dwi2tensor')
    dwi2tensor.inputs.debug = True
    fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(),name='fsl2mrtrix')
    fsl2mrtrix.inputs.invert_y = True
    tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(),name='tensor2vector')
    tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(),name='tensor2adc')
    tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(),name='tensor2fa')
    erode1 = pe.Node(interface=mrtrix.Erode(),name='erode1')
    erode2 = pe.Node(interface=mrtrix.Erode(),name='erode2')
    threshold1 = pe.Node(interface=mrtrix.Threshold(),name='threshold1')
    threshold2 = pe.Node(interface=mrtrix.Threshold(),name='threshold2')
    threshold2.inputs.absolute_threshold_value = 0.7
    threshold3 = pe.Node(interface=mrtrix.Threshold(),name='threshold3')
    threshold3.inputs.absolute_threshold_value = 0.4

    MRmultiply = pe.Node(interface=mrtrix.MRMultiply(),name='MRmultiply')
    median3d = pe.Node(interface=mrtrix.MedianFilter3D(),name='median3D')
    MRconvert = pe.Node(interface=mrtrix.MRConvert(),name='MRconvert')

    MRview = pe.Node(interface=mrtrix.MRTrixViewer(),name='MRview')
    MRinfo = pe.Node(interface=mrtrix.MRTrixInfo(),name='MRinfo')
    csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(),name='csdeconv')
    trackdensity = pe.Node(interface=mrtrix.Tracks2Prob(),name='trackdensity')
    gen_WM_mask = pe.Node(interface=mrtrix.GenerateWhiteMatterMask(),name='gen_WM_mask')
    estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(),name='estimateresponse')
    estimateresponse.inputs.debug = True
    dwi2SH = pe.Node(interface=mrtrix.DWI2SphericalHarmonicsImage(),name='dwi2SH')
    probCSDstreamtrack = pe.Node(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(),name='probCSDstreamtrack')
    probCSDstreamtrack.inputs.inputmodel = 'SD_PROB'
    probCSDstreamtrack.inputs.maximum_number_of_tracks = 100000
    probSHstreamtrack = probCSDstreamtrack.clone(name="probSHstreamtrack")
    tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(),name='tracks2prob')
    tracks2prob.inputs.colour = True
    tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(),name='tck2trk')

    MRconvert_vector = MRconvert.clone(name="MRconvert_vector")
    MRconvert_ADC = MRconvert.clone(name="MRconvert_ADC")
    MRconvert_FA = MRconvert.clone(name="MRconvert_FA")
    MRconvert_TDI = MRconvert.clone(name="MRconvert_TDI")
    MRmultiply = pe.Node(interface=mrtrix.MRMultiply(),name='MRmultiply')

    tractography = pe.Workflow(name='tractography')

    tractography.connect([(inputnode1, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                    ("bvals", "bval_file")])])
    tractography.connect([(inputnode1, dwi2tensor,[("dwi","in_file")])])
    tractography.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

    tractography.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                           (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                           (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                          ])

    tractography.connect([(inputnode1, MRconvert,[("dwi","in_file")])])
    MRconvert.inputs.extract_at_axis = 3
    MRconvert.inputs.extract_at_coordinate = [0]
    MRmult_merge = pe.Node(interface=util.Merge(2), name="MRmultiply_merge")

    tractography.connect([(MRconvert, threshold1,[("converted","in_file")])])
    tractography.connect([(threshold1, median3d,[("out_file","in_file")])])
    tractography.connect([(median3d, erode1,[("out_file","in_file")])])
    tractography.connect([(erode1, erode2,[("out_file","in_file")])])
    tractography.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])
    tractography.connect([(erode2, MRmult_merge,[("out_file","in2")])])
    tractography.connect([(MRmult_merge, MRmultiply,[("out","in_files")])])
    tractography.connect([(MRmultiply, threshold2,[("out_file","in_file")])])
    tractography.connect([(threshold2, estimateresponse,[("out_file","mask_image")])])

    #### For Testing Purposes ####
    #tractography.connect([(tensor2fa, MRview,[("FA","in_files")])])
    #tractography.connect([(tensor2adc, MRview,[("ADC","in_files")])])
    #tractography.connect([(tensor2vector, MRview,[("vector","in_files")])])
    ##############################

    tractography.connect([(inputnode1, bet,[("dwi","in_file")])])
    tractography.connect([(inputnode1, gen_WM_mask,[("dwi","in_file")])])
    tractography.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
    tractography.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])

    tractography.connect([(inputnode1, estimateresponse,[("dwi","in_file")])])
    tractography.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])

    tractography.connect([(inputnode1, csdeconv,[("dwi","in_file")])])
    tractography.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
    tractography.connect([(estimateresponse, csdeconv,[("response","response_file")])])
    tractography.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

    tractography.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])
    tractography.connect([(gen_WM_mask, probCSDstreamtrack,[("WMprobabilitymap","seed_file")])])

    tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(),name='tracks2prob')
    tracks2prob.inputs.colour = True
    tractography.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
    tractography.connect([(inputnode1, tracks2prob,[("dwi","template_file")])])

    tck2trk = pe.Node(interface=mrtrix.MRTrix2TrackVis(),name='tck2trk')
    tractography.connect([(inputnode1, tck2trk,[(('dwi', get_vox_dims), 'voxel_dims'),
    (('dwi', get_data_dims), 'data_dims')])])

    tractography.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])

    inputnode= pe.Node(interface = util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")

    outputnode = pe.Node(interface = util.IdentityInterface(fields=["fa",
                                                                "tracts_trk",
                                                                "csdeconv",
                                                                "tracts_tck",
                                                                "tdi"]),
                                        name="outputnode")

    workflow = pe.Workflow(name=name)
    workflow.base_output_dir=name

    workflow.connect([(inputnode, tractography, [("dwi", "inputnode1.dwi"),
                                              ("bvals", "inputnode1.bvals"),
                                              ("bvecs", "inputnode1.bvecs")])])

    workflow.connect([(tractography, outputnode, [("probCSDstreamtrack.tracked", "tracts_tck"),
        ("csdeconv.spherical_harmonics_image", "csdeconv"),
        ("tensor2fa.FA", "fa"),
        ("tck2trk.out_file", "tracts_trk"),
        ("tracks2prob.tract_image", "tdi")])
        ])

    return workflow
