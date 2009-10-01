# Telling python where to look for things
import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
import os                                    # system functions

#####################################################################
# Preliminaries

# Tell fsl to generate all output in uncompressed nifti format
print fsl.fslversion()
fsl.fsloutputtype('NIFTI')

# setup the way matlab should be called
mlab.MatlabCommandLine.matlab_cmd = "matlab -nodesktop -nosplash"

# The following lines create some information about location of your
# data. 
data_dir = os.path.abspath('data')
subject_list = ['s1','s3']
# The following info structure helps the DataSource module organize
# nifti files into fields/attributes of a data object. With DataSource
# this object is of type Bunch.
info = {}
info['s1'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))
info['s3'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))

######################################################################
# Setup preprocessing pipeline nodes

# This node looks into the directory containing Nifti files and
# returns pointers to the files in a structured format as determined
# by the runtype names provided in the info structure above 
datasource = nw.NodeWrapper(interface=nio.DataSource())
datasource.inputs.base_directory = data_dir
datasource.inputs.subject_id = 's1'
datasource.inputs.subject_template = '%s'
datasource.inputs.file_template = '%s.nii'
datasource.inputs.subject_info = info

# iterables provides a mechanism to execute part of the processing
# over multiple instances of the parameter. In the following example
# iterables allows DataSource node and its descendants to be executed
# for multiple subjects.  
datasource.iterables = dict(subject_id=lambda:subject_list)

# run SPM realign
realign = nw.NodeWrapper(interface=spm.Realign(),diskbased=True)
realign.inputs.register_to_mean = True

# run artifact detection
art = nw.NodeWrapper(interface=ra.ArtifactDetect(),diskbased=True)
art.inputs.use_differences = True
art.inputs.use_norm = True
art.inputs.norm_threshold = 0.5
art.inputs.zintensity_threshold = 3
art.inputs.mask_type = 'file'

# run FSL's bet
skullstrip = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)
skullstrip.inputs.mask = True

# run SPM's coregistration
coregister = nw.NodeWrapper(interface=spm.Coregister(),diskbased=True)
coregister.inputs.write = False

# run SPM's normalization
normalize = nw.NodeWrapper(interface=spm.Normalize(),diskbased=True)
normalize.inputs.template = '/software/spm5_1782/templates/T1.nii'

# run SPM's smoothing
smooth = nw.NodeWrapper(interface=spm.Smooth(),diskbased=True)
smooth.inputs.fwhm = [6,6,8]

#######################################################################
# setup analysis components

#define a function that reads a matlab file and returns subject
#specific condition information
from nipype.interfaces.base import Bunch
from copy import deepcopy
def subjectinfo(subject_id):
    print "Subject ID: %s\n"%str(subject_id)
    output = []
    names = ['Task-Odd','Task-Even']
    for r in range(4):
        onsets = [range(15,240,60),range(45,240,60)]
        output.insert(r,
                      Bunch(conditions=names,
                            onsets=deepcopy(onsets),
                            durations=[[15] for s in names],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None))
    return output

# Set up all the contrasts that should be evaluated
cont1 = ['Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5]]
cont2 = ['Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1]]
contrasts = [cont1,cont2]

# Setup model and spm estimation options
modelspec = nw.NodeWrapper(interface=spm.SpecifyModel())
modelspec.inputs.subject_info_func = subjectinfo
modelspec.inputs.concatenate_runs = True
modelspec.inputs.input_units = 'secs'
modelspec.inputs.output_units = 'secs'
modelspec.inputs.time_repetition = 3.
modelspec.inputs.high_pass_filter_cutoff = 120

# create the SPM model
level1design = nw.NodeWrapper(interface=spm.Level1Design(),diskbased=True)
level1design.inputs.timing_units = modelspec.inputs.output_units
level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}

# setup the estimator for the model
level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(),diskbased=True)
level1estimate.inputs.estimation_method = {'Classical' : 1}

# setup the contrast estimator
contrastestimate = nw.NodeWrapper(interface=spm.EstimateContrast(),diskbased=True)
contrastestimate.inputs.contrasts = contrasts

#################################################################################
# Setup pipeline
l1pipeline = pe.Pipeline()
l1pipeline.config['workdir'] = os.path.abspath('./workingdir')
l1pipeline.config['use_parameterized_dirs'] = True

l1pipeline.connect([(datasource,realign,[('func','infile')]),
                  (realign,coregister,[('mean_image', 'source'),
                                       ('realigned_files','apply_to_files')]),
		  (datasource,coregister,[('struct', 'target')]),
		  (datasource,normalize,[('struct', 'source')]),
		  (coregister, normalize, [('coregistered_files','apply_to_files')]),
		  (normalize, smooth, [('normalized_files', 'infile')]),
                  (datasource,modelspec,[('subject_id','subject_id')]),
                  (realign,modelspec,[('realignment_parameters','realignment_parameters')]),
                  (smooth,modelspec,[('smoothed_files','functional_runs')]),
                  (normalize,skullstrip,[('normalized_source','infile')]),
                  (realign,art,[('realignment_parameters','realignment_parameters')]),
                  (normalize,art,[('normalized_files','realigned_files')]),
                  (skullstrip,art,[('maskfile','mask_file')]),
                  (art,modelspec,[('outlier_files','outlier_files')]),
                  (modelspec,level1design,[('session_info','session_info')]),
                  (skullstrip,level1design,[('maskfile','mask_image')]),
                  (level1design,level1estimate,[('spm_mat_file','spm_design_file')]),
                  (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                  ('beta_images','beta_images'),
                                                  ('residual_image','residual_image'),
                                                  ('RPVimage','RPVimage')]),
                  ])

######################################################################
# Setup storage of results

datasink = nw.NodeWrapper(interface=nio.DataSink())
datasink.inputs.base_directory = os.path.abspath('l1output')

# store relevant outputs from various stages of the 1st level analysis
l1pipeline.connect([(datasource,datasink,[('subject_id','subject_id')]),
                    (realign,datasink,[('mean_image','realign.@mean'),
                                       ('realignment_parameters','realign.@param')]),
                    (art,datasink,[('outlier_files','art.@outliers'),
                                   ('statistic_files','art.@stats')]),
                    (level1design,datasink,[('spm_mat_file','model.pre-estimate')]),
                    (level1estimate,datasink,[('spm_mat_file','model.@spm'),
                                              ('beta_images','model.@beta'),
                                              ('mask_image','model.@mask'),
                                              ('residual_image','model.@res'),
                                              ('RPVimage','model.@rpv')]),
                    (contrastestimate,datasink,[('con_images','contrasts.@con'),
                                                  ('spmT_images','contrasts.@T')]),
                    ])

#########################################################################
# setup level 2 pipeline

# collect all the con images for each contrast.
contrast_ids = range(1,len(contrasts)+1)
l2source = nw.NodeWrapper(nio.DataGrabber())
l2source.inputs.file_template=os.path.abspath('l1output/*/con*/con_%04d.img')
l2source.inputs.template_argnames=['con']

# iterate over all contrast images
l2source.iterables = dict(con=lambda:contrast_ids)

# setup a 1-sample t-test node
onesamplettest = nw.NodeWrapper(interface=spm.OneSampleTTest(),diskbased=True)

# setup the pipeline
l2pipeline = pe.Pipeline()
l2pipeline.config['workdir'] = os.path.abspath('l2output')
l2pipeline.config['use_parameterized_dirs'] = True
l2pipeline.connect([(l2source,onesamplettest,[('file_list','con_images')])])


#if __name__ == '__main__':
#    l1pipeline.run()
#    l2pipeline.run()
