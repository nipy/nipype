import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import numpy as np
import os                                    # system functions

inputnode = pe.Node(interface = util.IdentityInterface(fields=["dwi", "mask"]), name="inputnode")

mask_dwi = pe.Node(interface = fsl.ImageMaths(op_string = "-mas"), name="mask_dwi")
slice_dwi = pe.Node(interface = fsl.Split(dimension="z"), name="slice_dwi")
slice_mask = pe.Node(interface = fsl.Split(dimension="z"), name="slice_mask")

preproc = pe.Workflow(name="preproc")

preproc.connect([(inputnode, mask_dwi, [('dwi', 'in_file')]),
                 (inputnode, mask_dwi, [('mask', 'in_file2')]),
                 (mask_dwi, slice_dwi, [('out_file', 'in_file')]),
                 (inputnode, slice_mask, [('mask', 'in_file')])
                 ])

xfibres = pe.MapNode(interface=fsl.XFibres(), name="xfibres", iterfield=['dwi', 'mask'])

# Dummy set of parameters that run fast
xfibres.inputs.n_fibres = 2 
xfibres.inputs.fudge = 1 
xfibres.inputs.burn_in = 0 
xfibres.inputs.n_jumps = 20 
xfibres.inputs.sample_every = 2
xfibres.inputs.model = 1

# Normal set of parameters
xfibres.inputs.n_fibres = 2 
xfibres.inputs.fudge = 1 
xfibres.inputs.burn_in = 1000 
xfibres.inputs.n_jumps = 1250 
xfibres.inputs.sample_every = 25
xfibres.inputs.model = 1

merge_thsamples = pe.MapNode(fsl.Merge(dimension="z"), name="merge_th_samples", iterfield=['in_files'])
merge_phsamples = pe.MapNode(fsl.Merge(dimension="z"), name="merge_ph_samples", iterfield=['in_files'])
merge_fsamples = pe.MapNode(fsl.Merge(dimension="z"), name="merge_f_samples", iterfield=['in_files'])
merge_dyads = pe.MapNode(fsl.Merge(dimension="z"), name="merge_dyads", iterfield=['in_files'])

merge_mean_dsamples = pe.Node(fsl.Merge(dimension="z"), name="merge_mean_dsamples")

mean_thsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"), name="mean_th_samples", iterfield=['in_file'])
mean_phsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"), name="mean_ph_samples", iterfield=['in_file'])
mean_fsamples = pe.MapNode(fsl.ImageMaths(op_string="-Tmean"), name="mean_f_samples", iterfield=['in_file'])

subject_list = ['subj1']

"""
Map field names to individual subject runs
"""

info = dict(dwi=[['subject_id', 'data']],
            bvecs=[['subject_id','bvecs']],
            bvals=[['subject_id','bvals']])

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=info.keys()),
                     name = 'datasource')

datasource.inputs.template = "%s/%s"

# This needs to point to the fdt folder you can find after extracting 
# http://www.fmrib.ox.ac.uk/fslcourse/fsl_course_data2.tar.gz
datasource.inputs.base_directory = os.path.abspath('fsl_course_data/fdt/')

datasource.inputs.field_template = dict(dwi='%s/%s.nii.gz')
datasource.inputs.template_args = info

datasource.iterables = ('subject_id', subject_list)

"""
extract the volume with b=0 (nodif_brain)
"""

fslroi = pe.Node(interface=fsl.ExtractROI(),name='fslroi')
fslroi.inputs.t_min=0
fslroi.inputs.t_size=1

"""
create a brain mask from the nodif_brain
"""

bet = pe.Node(interface=fsl.BET(),name='bet')
bet.inputs.mask=True
bet.inputs.frac=0.34

bedpostx = pe.Workflow(name="bedpostx")
bedpostx.base_dir = os.path.abspath('bedpostx_tutorial')

def transpose(samples_over_fibres):
    a = np.array(samples_over_fibres)
    if len(a.shape)==1:
        a = a.reshape(-1,1)
    return a.T.tolist()

bedpostx.connect([(datasource, fslroi, [('dwi', 'in_file')]),
                  (fslroi,bet,[('roi_file','in_file')]),
                  (bet, preproc, [('mask_file', 'inputnode.mask')]),
                  (datasource, preproc, [('dwi', 'inputnode.dwi')]),
                  
                  (preproc, xfibres, [('slice_dwi.out_files', 'dwi'),
                                      ('slice_mask.out_files', 'mask')]),
                  (datasource, xfibres, [('bvals', 'bvals')]),
                  (datasource, xfibres, [('bvecs', 'bvecs')]),
                  
                  (xfibres, merge_thsamples, [(('thsamples',transpose), 'in_files')]),
                  (xfibres, merge_phsamples, [(('phsamples',transpose), 'in_files')]),
                  (xfibres, merge_fsamples, [(('fsamples',transpose), 'in_files')]),
                  (xfibres, merge_dyads, [(('dyads',transpose), 'in_files')]),
                  (xfibres, merge_mean_dsamples, [('mean_dsamples', 'in_files')]),
                  
                  (merge_thsamples, mean_thsamples, [('merged_file', 'in_file')]),
                  (merge_phsamples, mean_phsamples, [('merged_file', 'in_file')]),
                  (merge_fsamples, mean_fsamples, [('merged_file', 'in_file')])
                  ])



bedpostx.run()
                        