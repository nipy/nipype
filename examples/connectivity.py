import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.camino as camino
import nipype.interfaces.fsl as fsl
import nipype.interfaces.camino2trackvis as cam2trk
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.nipy as nipy      # how to run matlab
import nibabel as nb
import os                                    # system functions

def get_vox_dims(volume):
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]

def get_data_dims(volume):
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    datadims = hdr.get_data_shape()
    return [int(datadims[0]), int(datadims[1]), int(datadims[2])]

fsl.FSLCommand.set_default_output_type('NIFTI')

# This needs to point to the freesurfer subjects directory (Recon-all must have been run on subj1 from the FSL course data)
# The freesurfer subj1 directory can be downloaded here: 
# If there is already another example dataset with both DWI and a Freesurfer directory, we can switch this tutorial to use
# that instead...

#subjects_dir = os.path.abspath('/usr/local/freesurfer/subjects/')
subjects_dir = os.path.abspath('freesurfer')

# This needs to point to the fdt folder you can find after extracting 
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
data_dir = os.path.abspath('fsl_course_data/fdt/')

fs.FSCommand.set_default_subjects_dir(subjects_dir)

subject_list = ['subj1']

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subject_list)

info = dict(dwi=[['subject_id', 'dwi']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])
datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"
datasource.inputs.base_directory = data_dir
datasource.inputs.field_template = dict(dwi='%s/%s.nii')
datasource.inputs.template_args = info
datasource.inputs.base_directory = data_dir

FreeSurferSource = pe.Node(interface=nio.FreeSurferSource(), name='fssource')
FreeSurferSource.inputs.subjects_dir = subjects_dir

		
# FSL: Brain Extraction on b0 image
b0Strip = pe.Node(interface=fsl.BET(mask = True), name = 'bet_b0')

# FSL: Coregistration
coregister = pe.Node(interface=fsl.FLIRT(dof=6), name = 'coregister')
coregister.inputs.cost = ('corratio')

# FSL: Inversion of FLIRT transformation matrix
convertxfm = pe.Node(interface=fsl.ConvertXFM(), name = 'convertxfm')
convertxfm.inputs.invert_xfm = True

# FSL: Inverse Matrix application
inverse = pe.Node(interface=fsl.FLIRT(), name = 'inverse')
inverse.inputs.interp = ('nearestneighbour')

mri_convert_Brain = pe.Node(interface=fs.MRIConvert(), name='mri_convert_Brain')
mri_convert_Brain.inputs.out_type = 'nii'

mri_convert_WMParc = pe.Node(interface=fs.MRIConvert(), name='mri_convert_WMParc')
mri_convert_WMParc.inputs.out_type = 'nii'

tractshred = pe.Node(interface=camino.TractShredder(), name='tractshred')
tractshred.inputs.offset = 0
tractshred.inputs.bunchsize = 2
tractshred.inputs.space = 1

conmap = pe.Node(interface=camino.Conmap(), name='conmap')
conmap.inputs.threshold = 100

conmaptxt2mat = pe.Node(interface=camino.ConmapTxt2Mat(), name='conmaptxt2mat')

FreeSurferSourceLH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceLH')
FreeSurferSourceLH.inputs.subjects_dir = subjects_dir
FreeSurferSourceLH.inputs.hemi = 'lh'

FreeSurferSourceRH = pe.Node(interface=nio.FreeSurferSource(), name='fssourceRH')
FreeSurferSourceRH.inputs.subjects_dir = subjects_dir
FreeSurferSourceRH.inputs.hemi = 'rh'

mapping = pe.Workflow(name='mapping')

inputnode = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name='inputnode')

mris_convertLH = pe.Node(interface=fs.MRIsConvert(), name='mris_convertLH')
mris_convertLH.inputs.out_datatype = 'gii'
mris_convertRH = pe.Node(interface=fs.MRIsConvert(), name='mris_convertRH')
mris_convertRH.inputs.out_datatype = 'gii'

inputnode = pe.Node(interface=util.IdentityInterface(fields=["dwi", "bvecs", "bvals", "subject_id"]), name="inputnode")

camino2trackvis = pe.Node(interface=cam2trk.Camino2Trackvis(), name="camino2trk")
camino2trackvis.inputs.min_length = 30
#Would like to use get_data_dims here, but camino2trackvis requires comma separated values... Ideas?
camino2trackvis.inputs.data_dims = '128,104,64'
camino2trackvis.inputs.voxel_dims = '1,1,1'
camino2trackvis.inputs.voxel_order = 'LAS'

                      
trk2camino = pe.Node(interface=cam2trk.Trackvis2Camino(), name="trk2camino")

vtkstreamlines = pe.Node(interface=camino.VtkStreamlines(), name="vtkstreamlines")

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

analyzeheader_fa = pe.Node(interface=camino.AnalyzeHeader(),name='analyzeheader_fa')
analyzeheader_fa.inputs.datatype = 'double'

analyzeheader_trace = pe.Node(interface=camino.AnalyzeHeader(),name='analyzeheader_trace')
analyzeheader_trace.inputs.datatype = 'double'

fa = pe.Node(interface=camino.FA(),name='fa')
md = pe.Node(interface=camino.MD(),name='md')
trd = pe.Node(interface=camino.TrD(),name='trd')

track = pe.Node(interface=camino.Track(), name="track")
track.inputs.inputmodel = 'pico'
track.inputs.iterations = 1

mapping.connect([(inputnode, b0Strip,[('dwi','in_file')])])
mapping.connect([(FreeSurferSource, mri_convert_WMParc,[('wmparc','in_file')])])
mapping.connect([(FreeSurferSource, mri_convert_Brain,[('wmparc','in_file')])])

mapping.connect([(b0Strip, coregister,[('out_file','in_file')])])
mapping.connect([(mri_convert_Brain, coregister,[('out_file','reference')])])

mapping.connect([(coregister, convertxfm,[('out_matrix_file','in_file')])])

mapping.connect([(b0Strip, inverse,[('out_file','reference')])])
mapping.connect([(convertxfm, inverse,[('out_file','in_matrix_file')])])
mapping.connect([(mri_convert_WMParc, inverse,[('out_file','in_file')])])
mapping.connect([(inverse, conmap,[('out_file','roi_file')])])

                      
mapping.connect([(inputnode, bet,[("dwi","in_file")])])
mapping.connect([(bet, track,[("mask_file","seed_file")])])

mapping.connect([(inputnode, image2voxel, [("dwi", "in_file")]),
                       (inputnode, fsl2scheme, [("bvecs", "bvec_file"),
                                                ("bvals", "bval_file")]),
                       
                       (image2voxel, dtifit,[['voxel_order','in_file']]),
                       (fsl2scheme, dtifit,[['scheme','scheme_file']])
                      ])
                      
mapping.connect([(fsl2scheme, dtlutgen,[("scheme","scheme_file")])])
mapping.connect([(dtlutgen, picopdfs,[("dtLUT","luts")])])
mapping.connect([(dtifit, picopdfs,[("tensor_fitted","in_file")])])

mapping.connect([(dtifit, fa,[("tensor_fitted","in_file")])])
mapping.connect([(fa, analyzeheader_fa,[('fa','in_file')])])
mapping.connect([(inputnode, analyzeheader_fa,[(('dwi', get_vox_dims), 'voxel_dims'),
(('dwi', get_data_dims), 'data_dims')])])

mapping.connect([(dtifit, trd,[("tensor_fitted","in_file")])])
mapping.connect([(trd, analyzeheader_trace,[("trace","in_file")])])
mapping.connect([(inputnode, analyzeheader_trace,[(('dwi', get_vox_dims), 'voxel_dims'),
(('dwi', get_data_dims), 'data_dims')])])

                      
#These lines are commented out the Camino mean diffusivity function appears to be broken.
#mapping.connect([(dtifit, md,[("tensor_fitted","in_file")])])
#mapping.connect([(md, analyzeheader2,[("md","in_file")])])

mapping.connect([(picopdfs, track,[("pdfs","in_file")])])

#Memory errors were fixed by shredding tracts. ProcStreamlines now runs fine, but I am still unable to open the OOGl file in Geomview. Could someone else try this on their machine? (output file is around 1gb!)
#mapping.connect([(tractshred, procstreamlines,[("shredded","in_file")])])

mapping.connect([(track, camino2trackvis, [('tracked','in_file')]),                    
                       (track, vtkstreamlines,[['tracked','in_file']]),
                       (camino2trackvis, trk2camino,[['trackvis','in_file']])
                      ])

mapping.connect([(track, tractshred,[("tracked","in_file")])])
mapping.connect([(tractshred, conmap,[("shredded","in_file")])])
#mapping.connect([(conmap, conmaptxt2mat,[("conmap_txt","in_file")])])

mapping.connect([(inputnode, FreeSurferSource,[("subject_id","subject_id")])])
mapping.connect([(inputnode, FreeSurferSourceLH,[("subject_id","subject_id")])])
mapping.connect([(inputnode, FreeSurferSourceRH,[("subject_id","subject_id")])])
mapping.connect([(FreeSurferSourceLH, mris_convertLH,[("pial","in_file")])])
mapping.connect([(FreeSurferSourceRH, mris_convertRH,[("pial","in_file")])])

connectivity = pe.Workflow(name="dwiproc")
connectivity.base_dir = os.path.abspath('connectivity')
connectivity.connect([
                    (infosource,datasource,[('subject_id', 'subject_id')]),
                    (datasource,mapping,[('dwi','inputnode.dwi'),
                                               ('bvals','inputnode.bvals'),
                                               ('bvecs','inputnode.bvecs')
                                               ]),
		(infosource,mapping,[('subject_id','inputnode.subject_id')])
                ])

connectivity.run()
connectivity.write_graph()
