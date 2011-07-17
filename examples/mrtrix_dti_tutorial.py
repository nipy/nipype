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
import nipype.interfaces.camino as camino
import nipype.interfaces.mrtrix as mrtrix   #<---- The important new part!
import nipype.interfaces.fsl as fsl
import nipype.interfaces.freesurfer as fs
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.algorithms.misc as misc
import nibabel as nb
import os                                    # system functions

"""
We import the voxel-, data-, and affine-grabbing functions from the Camino DTI processing workflow
"""
from nipype.workflows.camino.camino_dti_processing import get_vox_dims, get_data_dims, get_affine

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

# This needs to point to the fdt folder you can find after extracting
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
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

dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(),name='dwi2tensor')
dwi2tensor.inputs.debug = True
fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(),name='fsl2mrtrix')
tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(),name='tensor2vector')
tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(),name='tensor2adc')
tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(),name='tensor2fa')

MRmultiply = pe.Node(interface=mrtrix.MRMultiply(),name='MRmultiply')
MRview = pe.Node(interface=mrtrix.MRTrixViewer(),name='MRview')
MRinfo = pe.Node(interface=mrtrix.MRTrixInfo(),name='MRinfo')
csdeconv = pe.Node(interface=mrtrix.ConstrainedSphericalDeconvolution(),name='csdeconv')
trackdensity = pe.Node(interface=mrtrix.Tracks2Prob(),name='trackdensity')
gen_WM_mask = pe.Node(interface=mrtrix.GenerateWhiteMatterMask(),name='gen_WM_mask')
estimateresponse = pe.Node(interface=mrtrix.EstimateResponseForSH(),name='estimateresponse')
estimateresponse.inputs.debug = True
dwi2SH = pe.Node(interface=mrtrix.DWI2SphericalHarmonicsImage(),name='dwi2SH')

convertTest = pe.Workflow(name='convertTest')

convertTest.connect([(inputnode, fsl2mrtrix, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")])])
convertTest.connect([(inputnode, dwi2tensor,[("dwi","in_file")])])
convertTest.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

convertTest.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
                       (dwi2tensor, tensor2adc,[['tensor','in_file']]),
                       (dwi2tensor, tensor2fa,[['tensor','in_file']]),
                      ])

#### For Testing Purposes ####
#convertTest.connect([(tensor2fa, MRview,[("FA","in_files")])])
#convertTest.connect([(tensor2adc, MRview,[("ADC","in_files")])])
#convertTest.connect([(tensor2vector, MRview,[("vector","in_files")])])
##############################

convertTest.connect([(inputnode, bet,[("dwi","in_file")])])
convertTest.connect([(inputnode, gen_WM_mask,[("dwi","in_file")])])
convertTest.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
convertTest.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])

convertTest.connect([(inputnode, estimateresponse,[("dwi","in_file")])])
convertTest.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])
convertTest.connect([(gen_WM_mask, estimateresponse,[("WMprobabilitymap","mask_image")])])

convertTest.connect([(inputnode, csdeconv,[("dwi","in_file")])])
convertTest.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
convertTest.connect([(estimateresponse, csdeconv,[("response","response_file")])])
convertTest.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

"""
probCSDstreamtrack = pe.Node(interface=mrtrix.ProbabilisticSphericallyDeconvolutedStreamlineTrack(),name='probCSDstreamtrack')
probCSDstreamtrack.inputs.inputmodel = 'SD_PROB'
probCSDstreamtrack.inputs.maximum_number_of_tracks = 150000
convertTest.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])
convertTest.connect([(gen_WM_mask, probCSDstreamtrack,[("WMprobabilitymap","mask_file")])])
convertTest.connect([(gen_WM_mask, probCSDstreamtrack,[("WMprobabilitymap","seed_file")])])

probSHstreamtrack = probCSDstreamtrack.clone(name="probSHstreamtrack")
convertTest.connect([(inputnode, dwi2SH,[("dwi","in_file")])])
convertTest.connect([(fsl2mrtrix, dwi2SH,[("encoding_file","encoding_file")])])
convertTest.connect([(dwi2SH, probSHstreamtrack,[("spherical_harmonics_image","in_file")])])
convertTest.connect([(gen_WM_mask, probSHstreamtrack,[("WMprobabilitymap","mask_file")])])
convertTest.connect([(gen_WM_mask, probSHstreamtrack,[("WMprobabilitymap","seed_file")])])


tracks2prob = pe.Node(interface=mrtrix.Tracks2Prob(),name='tracks2prob')
tracks2prob.inputs.colour = True
convertTest.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
convertTest.connect([(inputnode, tracks2prob,[("dwi","template_file")])])
"""

SH2camino = pe.Node(interface=camino.MRTrixSphericalHarmonics2Camino(),name='SH2camino')
MRconvert = pe.Node(interface=mrtrix.MRConvert(),name='MRconvert')
MRconvert.inputs.output_datatype = 'float'
convertTest.connect([(csdeconv, MRconvert,[("spherical_harmonics_image","in_file")])])
convertTest.connect([(MRconvert, SH2camino,[("converted","in_file")])])


"""
Finally, we create another higher-level workflow to connect our mapping workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""
dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('mrtrix_dti_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,convertTest,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ])
                ])

dwiproc.run()
dwiproc.write_graph()
