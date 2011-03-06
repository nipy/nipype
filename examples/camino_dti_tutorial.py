import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import os                                    # system functions

subject_list = ['subj1']
fsl.FSLCommand.set_default_output_type('NIFTI')


"""
Map field names to individual subject runs
"""

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']],
            seed_file = [['subject_id','MASK_average_thal_right']],
            target_masks = [['subject_id',['MASK_average_M1_right',
                                           'MASK_average_S1_right',
                                           'MASK_average_occipital_right',
                                           'MASK_average_pfc_right',
                                           'MASK_average_pmc_right',
                                           'MASK_average_ppc_right',
                                           'MASK_average_temporal_right']]])

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

datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz',
                                        seed_file="%s.bedpostX/%s.nii.gz",
                                        target_masks="%s.bedpostX/%s.nii.gz",
                                        )
datasource.inputs.template_args = info

"""
Setup for Diffusion Tensor Computation
--------------------------------------
Here we will create a generic workflow for DTI computation
"""

convertTest = pe.Workflow(name='convertTest')
inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals"]), name="inputnode")


camino2trackvis = pe.Node(interface=cam2trk.Camino2Trackvis(), name="camino2trk")
camino2trackvis.inputs.min_length = 30
#camino2trackvis.inputs.data_dims = [96,96,60]
#camino2trackvis.inputs.voxel_dims = [1,1,1]
camino2trackvis.inputs.data_dims = '96,96,60'
camino2trackvis.inputs.voxel_dims = '1,1,1'
camino2trackvis.inputs.voxel_order = 'LAS'

                      
trk2camino = pe.Node(interface=cam2trk.Trackvis2Camino(), name="trk2camino")

vtkstreamlines = pe.Node(interface=camino.VtkStreamlines(), name="vtkstreamlines")
# vtkstreamlines.inputs.inputmodel = 'raw' #raw or voxels 
# vtkstreamlines.inputs.voxeldims = '1 1 1'
# vtkstreamlines.inputs.seed_file = 
# vtkstreamlines.inputs.target_file = 
# vtkstreamlines.inputs.scalar_file = 
# vtkstreamlines.inputs.colourorient = True
# vtkstreamlines.inputs.interpolatescalars = True
# vtkstreamlines.inputs.interpolate = True

procstreamlines = pe.Node(interface=camino.ProcStreamlines(), name="procstreamlines")
procstreamlines.inputs.outputtracts = 'oogl'

dtlutgen = pe.Node(interface=camino.DTLUTGen(), name="dtlutgen")
dtlutgen.inputs.snr = 16.0
dtlutgen.inputs.inversion = 1

picopdfs = pe.Node(interface=camino.PicoPDFs(), name="picopdfs")
picopdfs.inputs.inputmodel = 'dt'

image2voxel = pe.Node(interface=camino.Image2Voxel(), name="image2voxel")
bet = pe.Node(interface=fsl.BET(), name="bet")
bet.inputs.mask = True

fsl2scheme = pe.Node(interface=camino.FSL2Scheme(), name="fsl2scheme")
fsl2scheme.inputs.usegradmod = True

dtifit = pe.Node(interface=camino.DTIFit(),name='dtifit')

track = pe.Node(interface=camino.Track(), name="track")
track.inputs.inputmodel = 'pico'
track.inputs.iterations = 1
#track.inputs.data_dims = [96,96,60]
#track.inputs.voxel_dims = [1,1,1]
#track.inputs.outputtracts = 'oogl'

convertTest.connect([(inputnode, bet,[("dwi","in_file")])])
convertTest.connect([(bet, track,[("mask_file","seed_file")])])

convertTest.connect([(inputnode, image2voxel, [("dwi", "in_file")]),
                       (inputnode, fsl2scheme, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")]),
                       
                       (image2voxel, dtifit,[['voxel_order','in_file']]),
                       (fsl2scheme, dtifit,[['scheme','scheme_file']])
                      ])
                      
convertTest.connect([(fsl2scheme, dtlutgen,[("scheme","scheme_file")])])
convertTest.connect([(dtlutgen, picopdfs,[("dtLUT","luts")])])
convertTest.connect([(dtifit, picopdfs,[("tensor_fitted","in_file")])])
convertTest.connect([(picopdfs, track,[("pdfs","in_file")])])

#This line is commented out because the ProcStreamlines node keeps throwing nemory errors
#convertTest.connect([(track, procstreamlines,[("tracked","in_file")])])

convertTest.connect([(track, camino2trackvis, [('tracked','in_file')]),                    
                       (track, vtkstreamlines,[['tracked','in_file']]),
                       (camino2trackvis, trk2camino,[['trackvis','in_file']])
                      ])

dwiproc = pe.Workflow(name="dwiproc")
dwiproc.base_dir = os.path.abspath('camino_streamline_tutorial')
dwiproc.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,convertTest,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ])
                ])

dwiproc.run()
dwiproc.write_graph()