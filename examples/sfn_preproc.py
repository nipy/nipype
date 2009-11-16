import os
from glob import glob

import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.algorithms.rapidart as ra      # artifact detection


# Tell fsl to generate all output in uncompressed nifti format
print fsl.fsl_info.version
# I actually like gzipping
# fsl.fsloutputtype('NIFTI')

# The following lines create some information about location of your
# data. 
data_dir = os.path.abspath('./nifti')
subject_list = ['sfn0%d' % i for i in range(1,8)]

# The following info structure helps the DataSource module organize
# nifti files into fields/attributes of a data object. With DataSource
# this object is of type Bunch.
info = {}

# The current data structure for info is not very nice for incremental
# construction

# Would be nice to put centers for Bet in here. Right now, I've hacked around
# when necessary. Certainly for the tutorial!
for s in subject_list:
    subj_dir = os.path.join(data_dir, s)
    func = sorted(glob(subj_dir + '/ep2d*.nii.gz')) # should be '/ep2dneuro96*.nii.gz'))
    func = [os.path.basename(f) for f in func]
    struct = glob(subj_dir + '/cot1*.nii.gz')[0:1] # keep a list of 1 item
    struct = [os.path.basename(f) for f in struct]
    func_ref = glob(subj_dir + '/ep2dneuroREF.nii.gz')[0:1]
    func_ref = [os.path.basename(f) for f in func_ref]
    # much nicer would be {'func': func, 'struct': struct}
    info[s] = ((func,'func'), (struct,'struct'), (func_ref, 'func_ref'))

######################################################################
# Setup preprocessing pipeline nodes

# This node looks into the directory containing Nifti files and
# returns pointers to the files in a structured format as determined
# by the runtype names provided in the info structure above 
datasource = nw.NodeWrapper(interface=nio.DataSource())
datasource.inputs.update(base_directory = data_dir,
                         # subject_id = 's1',
                         subject_template = '%s',
                         file_template = '%s',
                         subject_info = info,)

# iterables provides a mechanism to execute part of the processing
# over multiple instances of the parameter. In the following example
# iterables allows DataSource node and its descendants to be executed
# for multiple subjects.  
datasource.iterables = {'subject_id': lambda:subject_list}

# Not using this for now, but would like to include in final tutorial pipeline
# run artifact detection
# art = nw.NodeWrapper(interface=ra.ArtifactDetect(),diskbased=True)
# art.inputs.use_differences = True
# art.inputs.use_norm = True
# art.inputs.norm_threshold = 0.5
# art.inputs.zintensity_threshold = 3
# art.inputs.mask_type = 'file'

## from the FLIRT web doc

# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)
skullstrip.inputs.update(mask = True,
                         frac = 0.34)

# Preprocess functionals
motion_correct = nw.NodeWrapper(interface=fsl.McFlirt(), diskbased=True)
motion_correct.inputs.update(saveplots = True)
# Note- only one iterfield is currently supported
motion_correct.iterfield = ['infile']

func_skullstrip = nw.NodeWrapper(interface=fsl.Bet(), diskbased=True,
                                 name='func_Bet.fsl')
func_skullstrip.inputs.update(functional = True)
func_skullstrip.iterfield = ['infile']

ref_skullstrip = nw.NodeWrapper(interface=fsl.Bet(), diskbased=True,
                                name='ref_Bet.fsl')
ref_skullstrip.inputs.update(functional = True)


## Now for registration

target_image = fsl.fsl_info.standard_image('MNI152_T1_2mm')

# For structurals
# flirt -ref ${FSLDIR}/data/standard/MNI152_T1_2mm_brain -in my_betted_structural -omat my_affine_transf.mat

t1reg2std = nw.NodeWrapper(interface=fsl.Flirt(), diskbased=True)
t1reg2std.inputs.update(reference = target_image,
                        outmatrix = 't1reg2std.xfm')

# It may seem that these should be able to be run in one step. But, then you get
# an empty "fnirted" image.
# they would be faster (I think) to do together, but the applywarp is super-fast
# anyway.
# fnirt --in=my_structural --aff=my_affine_transf.mat --cout=my_nonlinear_transf --config=T1_2_MNI152_2mm
# applywarp --ref=${FSLDIR}/data/standard/MNI152_T1_2mm --in=my_structural --warp=my_nonlinear_transf --out=my_warped_structural

t1warp2std = nw.NodeWrapper(interface=fsl.Fnirt(), diskbased=True)
t1warp2std.inputs.update(configfile = 'T1_2_MNI152_2mm',
                         fieldcoeff_file = 't1warp2std',
                         logfile = 't1warp2std.log')

t1applywarp = nw.NodeWrapper(interface=fsl.ApplyWarp(), diskbased=True)
t1applywarp.inputs.update(reference = target_image,
                          outfile = 't1_warped')

# For functionals - refers to some files above
# flirt -ref my_betted_structural -in my_functional -dof 7 -omat func2struct.mat

ref2t1 = nw.NodeWrapper(interface=fsl.Flirt(), diskbased=True, 
                         name='ref_Flirt.fsl')
ref2t1.inputs.update(outmatrix = 'ref2t1.xfm',
                     dof = 6)

# applywarp --ref=${FSLDIR}/data/standard/MNI152_T1_2mm --in=my_functional --warp=my_nonlinear_transf --premat=func2struct.mat --out=my_warped_functional

funcapplywarp = nw.NodeWrapper(interface=fsl.ApplyWarp(), diskbased=True,
                               name='func_ApplyWarp.fsl')
funcapplywarp.iterfield = ['infile']
funcapplywarp.inputs.update(reference = target_image)

# Finally do some smoothing!

smoothing = nw.NodeWrapper(interface=fsl.FSLSmooth(), diskbased=True)
smoothing.iterfield = ['infile']
smoothing.inputs.fwhm = 5

# We won't be using the bits from SPM for now... these should be removed when
# the FSL pype is finished
# run SPM's coregistration
# coregister = nw.NodeWrapper(interface=spm.Coregister(),diskbased=True)
# coregister.inputs.write = False
# 
# # run SPM's normalization
# normalize = nw.NodeWrapper(interface=spm.Normalize(),diskbased=True)
# normalize.inputs.template = '/software/spm5_1782/templates/T1.nii'
# 
# # run SPM's smoothing
# smooth = nw.NodeWrapper(interface=spm.Smooth(),diskbased=True)
# smooth.inputs.fwhm = [6,6,8]
# 
# #######################################################################
# # setup analysis components
# 
# #define a function that reads a matlab file and returns subject
# #specific condition information
# from nipype.interfaces.base import Bunch
# from copy import deepcopy
# def subjectinfo(subject_id):
#     print "Subject ID: %s\n"%str(subject_id)
#     output = []
#     names = ['Task-Odd','Task-Even']
#     for r in range(4):
#         onsets = [range(15,240,60),range(45,240,60)]
#         output.insert(r,
#                       Bunch(conditions=names,
#                             onsets=deepcopy(onsets),
#                             durations=[[15] for s in names],
#                             amplitudes=None,
#                             tmod=None,
#                             pmod=None,
#                             regressor_names=None,
#                             regressors=None))
#     return output
# 
# # Set up all the contrasts that should be evaluated
# cont1 = ['Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5]]
# cont2 = ['Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1]]
# contrasts = [cont1,cont2]
# 
# # Setup model and spm estimation options
# modelspec = nw.NodeWrapper(interface=spm.SpecifyModel())
# modelspec.inputs.subject_info_func = subjectinfo
# modelspec.inputs.concatenate_runs = True
# modelspec.inputs.input_units = 'secs'
# modelspec.inputs.output_units = 'secs'
# modelspec.inputs.time_repetition = 3.
# modelspec.inputs.high_pass_filter_cutoff = 120
# 
# # create the SPM model
# level1design = nw.NodeWrapper(interface=spm.Level1Design(),diskbased=True)
# level1design.inputs.timing_units = modelspec.inputs.output_units
# level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
# level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}
# 
# # setup the estimator for the model
# level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(),diskbased=True)
# level1estimate.inputs.estimation_method = {'Classical' : 1}
# 
# # setup the contrast estimator
# contrastestimate = nw.NodeWrapper(interface=spm.EstimateContrast(),diskbased=True)
# contrastestimate.inputs.contrasts = contrasts
