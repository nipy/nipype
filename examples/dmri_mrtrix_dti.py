#!/usr/bin/env python
"""
=======================
dMRI: DTI - MRtrix, FSL
=======================

Introduction
============

This script, dmri_mrtrix_dti.py, demonstrates the ability to perform advanced diffusion analysis
in a Nipype pipeline.

    python dmri_mrtrix_dti.py

We perform this analysis using the FSL course data, which can be acquired from here:

    * http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

Import necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.mrtrix as mrtrix   #<---- The important new part!
import nipype.interfaces.fsl as fsl
import nipype.algorithms.misc as misc
import os, os.path as op                     # system functions

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
An inputnode is used to pass the data obtained by the data grabber to the actual processing functions
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")

"""
Diffusion processing nodes
--------------------------

.. seealso::

    dmri_connectivity_advanced.py
        Tutorial with further detail on using MRtrix tractography for connectivity analysis

    http://www.brain.org.au/software/mrtrix/index.html
        MRtrix's online documentation

b-values and b-vectors stored in FSL's format are converted into a single encoding file for MRTrix.
"""

fsl2mrtrix = pe.Node(interface=mrtrix.FSL2MRTrix(),name='fsl2mrtrix')

"""
Tensors are fitted to each voxel in the diffusion-weighted image and from these three maps are created:
	* Major eigenvector in each voxel
	* Apparent diffusion coefficient
	* Fractional anisotropy

"""

gunzip = pe.Node(interface=misc.Gunzip(), name='gunzip')
dwi2tensor = pe.Node(interface=mrtrix.DWI2Tensor(),name='dwi2tensor')
tensor2vector = pe.Node(interface=mrtrix.Tensor2Vector(),name='tensor2vector')
tensor2adc = pe.Node(interface=mrtrix.Tensor2ApparentDiffusion(),name='tensor2adc')
tensor2fa = pe.Node(interface=mrtrix.Tensor2FractionalAnisotropy(),name='tensor2fa')

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
Creating the workflow
---------------------
In this section we connect the nodes for the diffusion processing.
"""

tractography = pe.Workflow(name='tractography')

tractography.connect([(inputnode, fsl2mrtrix, [("bvecs", "bvec_file"),
												("bvals", "bval_file")])])
tractography.connect([(inputnode, gunzip,[("dwi","in_file")])])
tractography.connect([(gunzip, dwi2tensor,[("out_file","in_file")])])
tractography.connect([(fsl2mrtrix, dwi2tensor,[("encoding_file","encoding_file")])])

tractography.connect([(dwi2tensor, tensor2vector,[['tensor','in_file']]),
					   (dwi2tensor, tensor2adc,[['tensor','in_file']]),
					   (dwi2tensor, tensor2fa,[['tensor','in_file']]),
					  ])
tractography.connect([(tensor2fa, MRmult_merge,[("FA","in1")])])

"""
This block creates the rough brain mask to be multiplied, mulitplies it with the
fractional anisotropy image, and thresholds it to get the single-fiber voxels.
"""

tractography.connect([(gunzip, MRconvert,[("out_file","in_file")])])
tractography.connect([(MRconvert, threshold_b0,[("converted","in_file")])])
tractography.connect([(threshold_b0, median3d,[("out_file","in_file")])])
tractography.connect([(median3d, erode_mask_firstpass,[("out_file","in_file")])])
tractography.connect([(erode_mask_firstpass, erode_mask_secondpass,[("out_file","in_file")])])
tractography.connect([(erode_mask_secondpass, MRmult_merge,[("out_file","in2")])])
tractography.connect([(MRmult_merge, MRmultiply,[("out","in_files")])])
tractography.connect([(MRmultiply, threshold_FA,[("out_file","in_file")])])

"""
Here the thresholded white matter mask is created for seeding the tractography.
"""

tractography.connect([(gunzip, bet,[("out_file","in_file")])])
tractography.connect([(gunzip, gen_WM_mask,[("out_file","in_file")])])
tractography.connect([(bet, gen_WM_mask,[("mask_file","binary_mask")])])
tractography.connect([(fsl2mrtrix, gen_WM_mask,[("encoding_file","encoding_file")])])
tractography.connect([(gen_WM_mask, threshold_wmmask,[("WMprobabilitymap","in_file")])])

"""
Next we estimate the fiber response distribution.
"""

tractography.connect([(gunzip, estimateresponse,[("out_file","in_file")])])
tractography.connect([(fsl2mrtrix, estimateresponse,[("encoding_file","encoding_file")])])
tractography.connect([(threshold_FA, estimateresponse,[("out_file","mask_image")])])

"""
Run constrained spherical deconvolution.
"""

tractography.connect([(gunzip, csdeconv,[("out_file","in_file")])])
tractography.connect([(gen_WM_mask, csdeconv,[("WMprobabilitymap","mask_image")])])
tractography.connect([(estimateresponse, csdeconv,[("response","response_file")])])
tractography.connect([(fsl2mrtrix, csdeconv,[("encoding_file","encoding_file")])])

"""
Connect the tractography and compute the tract density image.
"""

tractography.connect([(threshold_wmmask, probCSDstreamtrack,[("out_file","seed_file")])])
tractography.connect([(csdeconv, probCSDstreamtrack,[("spherical_harmonics_image","in_file")])])
tractography.connect([(probCSDstreamtrack, tracks2prob,[("tracked","in_file")])])
tractography.connect([(gunzip, tracks2prob,[("out_file","template_file")])])

tractography.connect([(gunzip, tck2trk,[("out_file","image_file")])])
tractography.connect([(probCSDstreamtrack, tck2trk,[("tracked","in_file")])])

"""
Finally, we create another higher-level workflow to connect our tractography workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('dmri_mrtrix_dti')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,tractography,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ])
                ])

if __name__ == '__main__':
    dwiproc.run()
    dwiproc.write_graph()
