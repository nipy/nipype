"""
==================================================
Using MRtrix for advanced diffusion analysis
==================================================

Introduction
============

This script, mrtrix_dti_tutorial.py, demonstrates the ability to perform advanced diffusion analysis
in a Nipype pipeline.

    python mrtrix_dti_tutorial.py

We perform this analysis using the FSL course data, which can be acquired from here:
    
    http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

Import necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.mrtrix as mrtrix   #<---- The important new part!
import nipype.interfaces.fsl as fsl
import nibabel as nb
import os, os.path as op                     # system functions

"""
We import the voxel-, data-, and affine-grabbing functions from the Camino DTI processing workflow
"""

from nipype.workflows.camino.diffusion import get_vox_dims, get_data_dims, get_affine

subject_list = ['subj1']
fsl.FSLCommand.set_default_output_type('NIFTI')

info = dict(dwi=[['subject_id', 'dwi']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', subject_list)

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"
datasource.inputs.base_directory = os.path.abspath('exdata')

datasource.inputs.field_template = dict(dwi='%s/%s.nii')
datasource.inputs.template_args = info

"""
An inputnode is used to pass the data obtained by the data grabber to the actual processing functions
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")

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

tractography.connect([(inputnode, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")])])
tractography.connect([(inputnode, dwi2tensor,[("dwi","in_file")])])
tractography.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

tractography.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                       (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                       (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                      ])

tractography.connect([(inputnode, MRconvert,[("dwi","in_file")])])
tractography.connect([(MRconvert, threshold_b0,[("converted","in_file")])])
tractography.connect([(threshold_b0, median3d,[("out_file","in_file")])])
tractography.connect([(median3d, erode_mask_firstpass,[("out_file","in_file")])])
tractography.connect([(erode_mask_firstpass, erode_mask_secondpass,[("out_file","in_file")])])

tractography.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])
tractography.connect([(erode_mask_secondpass, MRmult_merge,[("out_file","in2")])])
tractography.connect([(MRmult_merge, MRmultiply,[("out","in_files")])])
tractography.connect([(MRmultiply, threshold_FA,[("out_file","in_file")])])
tractography.connect([(threshold_FA, estimateresponse,[("out_file","mask_image")])])

tractography.connect([(inputnode, bet,[("dwi","in_file")])])
tractography.connect([(inputnode, gen_WM_mask,[("dwi","in_file")])])
tractography.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
tractography.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])

tractography.connect([(inputnode, estimateresponse,[("dwi","in_file")])])
tractography.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])

tractography.connect([(inputnode, csdeconv,[("dwi","in_file")])])
tractography.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
tractography.connect([(estimateresponse, csdeconv,[("response","response_file")])])
tractography.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

tractography.connect([(gen_WM_mask, threshold_wmmask,[("WMprobabilitymap","in_file")])])
tractography.connect([(threshold_wmmask, probCSDstreamtrack,[("out_file","seed_file")])])
tractography.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])

tractography.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
tractography.connect([(inputnode, tracks2prob,[("dwi","template_file")])])

tractography.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])
tractography.connect([(inputnode, tck2trk,[("dwi","image_file")])])

"""
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('mrtrix_dti_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,tractography,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ])
                ])

dwiproc.run()
dwiproc.write_graph()
