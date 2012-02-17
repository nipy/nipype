"""
==================
Diffusion - Camino
==================

Introduction
============

This script, camino_dti_tutorial.py, demonstrates the ability to perform basic diffusion analysis
in a Nipype pipeline.

    python camino_dti_tutorial.py

We perform this analysis using the FSL course data, which can be acquired from here:
http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz

Import necessary modules from nipype.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.algorithms.misc as misc
import os                                    # system functions

"""
We use the following functions to scrape the voxel and data dimensions of the input images. This allows the
pipeline to be flexible enough to accept and process images of varying size. The SPM Face tutorial
(spm_face_tutorial.py) also implements this inferral of voxel size from the data.
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

subject_list = ['subj1']
fsl.FSLCommand.set_default_output_type('NIFTI')


"""
Map field names to individual subject runs
"""

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")

"""Here we set up iteration over all the subjects. The following line
is a particular example of the flexibility of the system.  The
``datasource`` attribute ``iterables`` tells the pipeline engine that
it should repeat the analysis on each of the items in the
``subject_list``. In the current example, the entire first level
preprocessing and estimation will be repeated for each subject
contained in subject_list.
"""

infosource.iterables = ('subject_id', subject_list)

"""
Now we create a :class:`nipype.interfaces.io.DataGrabber` object and
fill in the information from above about the layout of our data.  The
:class:`nipype.pipeline.engine.Node` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"

# This needs to point to the fdt folder you can find after extracting
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
datasource.inputs.base_directory = os.path.abspath('fsl_course_data/fdt/')

datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz')
datasource.inputs.template_args = info

"""
An inputnode is used to pass the data obtained by the data grabber to the actual processing functions
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")

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
PICo tractography requires an estimate of the fibre direction and a model of its
uncertainty in each voxel; this is produced using the following node.
"""

picopdfs = pe.Node(interface=camino.PicoPDFs(), name="picopdfs")
picopdfs.inputs.inputmodel = 'dt'

"""
An FSL BET node creates a brain mask is generated from the diffusion image for seeding the PICo tractography.
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
Currently, the best program for visualizing tracts is TrackVis. For this reason, a node is included to
convert the raw tract data to .trk format. Solely for testing purposes, another node is added to perform the reverse.
"""

cam2trk_dt = pe.Node(interface=cam2trk.Camino2Trackvis(), name="cam2trk_dt")
cam2trk_dt.inputs.min_length = 30
cam2trk_dt.inputs.voxel_order = 'LAS'

cam2trk_pico = pe.Node(interface=cam2trk.Camino2Trackvis(), name="cam2trk_pico")
cam2trk_pico.inputs.min_length = 30
cam2trk_pico.inputs.voxel_order = 'LAS'

trk2camino = pe.Node(interface=cam2trk.Trackvis2Camino(), name="trk2camino")

"""
Tracts can also be converted to VTK and OOGL formats, for use in programs such as GeomView and Paraview,
using the following two nodes. For VTK use VtkStreamlines.
"""

procstreamlines = pe.Node(interface=camino.ProcStreamlines(), name="procstreamlines")
procstreamlines.inputs.outputtracts = 'oogl'


"""
We can also produce a variety of scalar values from our fitted tensors. The following nodes generate the
fractional anisotropy and diffusivity trace maps and their associated headers.
"""

fa = pe.Node(interface=camino.ComputeFractionalAnisotropy(),name='fa')
trace = pe.Node(interface=camino.ComputeTensorTrace(),name='trace')
dteig = pe.Node(interface=camino.ComputeEigensystem(), name='dteig')

analyzeheader_fa = pe.Node(interface= camino.AnalyzeHeader(), name = "analyzeheader_fa")
analyzeheader_fa.inputs.datatype = "double"
analyzeheader_trace = analyzeheader_fa.clone('analyzeheader_trace')

fa2nii = pe.Node(interface=misc.CreateNifti(),name='fa2nii')
trace2nii = fa2nii.clone("trace2nii")

"""
Since we have now created all our nodes, we can now define our workflow and start making connections.
"""

tractography = pe.Workflow(name='tractography')

tractography.connect([(inputnode, bet,[("dwi","in_file")])])

"""
File format conversion
"""

tractography.connect([(inputnode, image2voxel, [("dwi", "in_file")]),
                      (inputnode, fsl2scheme, [("bvecs", "bvec_file"),
                                               ("bvals", "bval_file")])
                      ])

"""
Tensor fitting
"""

tractography.connect([(image2voxel, dtifit,[['voxel_order','in_file']]),
                      (fsl2scheme, dtifit,[['scheme','scheme_file']])
                     ])

"""
Workflow for applying DT streamline tractogpahy
"""

tractography.connect([(bet, trackdt,[("mask_file","seed_file")])])
tractography.connect([(dtifit, trackdt,[("tensor_fitted","in_file")])])

"""
Workflow for applying PICo
"""

tractography.connect([(bet, trackpico,[("mask_file","seed_file")])])
tractography.connect([(fsl2scheme, dtlutgen,[("scheme","scheme_file")])])
tractography.connect([(dtlutgen, picopdfs,[("dtLUT","luts")])])
tractography.connect([(dtifit, picopdfs,[("tensor_fitted","in_file")])])
tractography.connect([(picopdfs, trackpico,[("pdfs","in_file")])])

# ProcStreamlines might throw memory errors - comment this line out in such case
tractography.connect([(trackdt, procstreamlines,[("tracked","in_file")])])


"""
Connecting the Fractional Anisotropy and Trace nodes is simple, as they obtain their input from the
tensor fitting.

This is also where our voxel- and data-grabbing functions come in. We pass these functions, along with
the original DWI image from the input node, to the header-generating nodes. This ensures that the files
will be correct and readable.
"""

tractography.connect([(dtifit, fa,[("tensor_fitted","in_file")])])
tractography.connect([(fa, analyzeheader_fa,[("fa","in_file")])])
tractography.connect([(inputnode, analyzeheader_fa,[(('dwi', get_vox_dims), 'voxel_dims'),
(('dwi', get_data_dims), 'data_dims')])])
tractography.connect([(fa, fa2nii,[('fa','data_file')])])
tractography.connect([(inputnode, fa2nii,[(('dwi', get_affine), 'affine')])])
tractography.connect([(analyzeheader_fa, fa2nii,[('header', 'header_file')])])


tractography.connect([(dtifit, trace,[("tensor_fitted","in_file")])])
tractography.connect([(trace, analyzeheader_trace,[("trace","in_file")])])
tractography.connect([(inputnode, analyzeheader_trace,[(('dwi', get_vox_dims), 'voxel_dims'),
(('dwi', get_data_dims), 'data_dims')])])
tractography.connect([(trace, trace2nii,[('trace','data_file')])])
tractography.connect([(inputnode, trace2nii,[(('dwi', get_affine), 'affine')])])
tractography.connect([(analyzeheader_trace, trace2nii,[('header', 'header_file')])])

tractography.connect([(dtifit, dteig,[("tensor_fitted","in_file")])])

tractography.connect([(trackpico, cam2trk_pico, [('tracked','in_file')])])
tractography.connect([(trackdt, cam2trk_dt, [('tracked','in_file')])])
tractography.connect([(inputnode, cam2trk_pico,[(('dwi', get_vox_dims), 'voxel_dims'),
                                                (('dwi', get_data_dims), 'data_dims')])])

tractography.connect([(inputnode, cam2trk_dt,[(('dwi', get_vox_dims), 'voxel_dims'),
                                              (('dwi', get_data_dims), 'data_dims')])])


"""
Finally, we create another higher-level workflow to connect our tractography workflow with the info and datagrabbing nodes
declared at the beginning. Our tutorial can is now extensible to any arbitrary number of subjects by simply adding
their names to the subject list and their data to the proper folders.
"""

workflow = pe.Workflow(name="workflow")
workflow.base_dir = os.path.abspath('camino_dti_tutorial')
workflow.connect([(infosource,datasource,[('subject_id', 'subject_id')]),
                  (datasource,tractography,[('dwi','inputnode.dwi'),
                                            ('bvals','inputnode.bvals'),
                                            ('bvecs','inputnode.bvecs')
                                           ])
                 ])
"""
The following functions run the whole workflow and produce a .dot and .png graph of the processing pipeline.
"""

if __name__ == '__main__':
    workflow.run()
    workflow.write_graph()

"""
You can choose the format of the experted graph with the ``format`` option. For example ``workflow.write_graph(format='eps')``

"""
