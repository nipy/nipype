"""
   A pipeline example that uses intergrates several interfaces to
   perform a first and second level analysis on a two-subject data
   set. 
"""


"""
1. Tell python where to find the appropriate functions.
"""

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

"""
1b. Confirm package dependencies are installed.  (This is only for the
tutorial, rarely would you put this in your own code.)
"""
from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')

"""
2. Setup any package specific configuration. The output file format
   for FSL routines is being set to uncompressed NIFTI and a specific
   version of matlab is being used. The uncompressed format is
   required because SPM does not handle compressed NIFTI.
"""

# Tell fsl to generate all output in uncompressed nifti format
print fsl.fsl_info.version
fsl.fsl_info.outputtype('NIFTI')

# setup the way matlab should be called
mlab.MatlabCommandLine.matlab_cmd = "matlab -nodesktop -nosplash"

"""
3. The following lines of code sets up the necessary information
   required by the datasource module. It provides a mapping between
   run numbers (nifti files) and the mnemonic ('struct', 'func',
   etc.,.)  that particular run should be called. These mnemonics or
   fields become the output fields of the datasource module. In the
   example below, run 'f3' is of type 'func'. The 'f3' gets mapped to
   a nifti filename through a template '%s.nii'. So 'f3' would become
   'f3.nii'.
"""

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

"""
4. Setup various nodes for preprocessing the data. 
"""

"""
   a. Setting up an instance of the interface
   :class:`nipype.interfaces.io.DataSource`. This node looks into the
   directory containing Nifti files and returns pointers to the files
   in a structured format as determined by the field/attribute names
   provided in the info structure above. The
   :class:`nipype.pipeline.NodeWrapper` module wraps the interface
   object and provides additional housekeeping and pipeline specific
   functionality. 
"""
datasource = nw.NodeWrapper(interface=nio.DataSource())
datasource.inputs.base_directory   = data_dir
datasource.inputs.subject_template = '%s'
datasource.inputs.file_template    = '%s.nii'
datasource.inputs.subject_info     = info


"""
   b. Setting up iteration over all subjects. The following line is a
   particular example of the flexibility of the system.  The  variable
   `iterables` for datasource tells the pipeline engine that it should
   repeat any of the processes that are descendents of the datasource
   process on each of the iterable items. In the current example, the
   entire first level preprocessing and estimation will be repeated
   for each subject contained in subject_list.
"""
datasource.iterables = dict(subject_id=lambda:subject_list)


"""
   c. Use :class:`nipype.interfaces.spm.Realign` for motion correction
   and register all images to the mean image. 
"""
realign = nw.NodeWrapper(interface=spm.Realign(),diskbased=True)
realign.inputs.register_to_mean = True

"""
   d. Use :class:`nipype.algorithms.rapidart` to determine which of
   the images in the functional series are outliers based on
   deviations in intensity or movement.
"""
art = nw.NodeWrapper(interface=ra.ArtifactDetect(),diskbased=True)
art.inputs.use_differences      = [True,True]
art.inputs.use_norm             = True
art.inputs.norm_threshold       = 0.5
art.inputs.zintensity_threshold = 3
art.inputs.mask_type            = 'file'


"""
   e. Use :class:`nipype.interfaces.fsl.Bet` for skull strip
   structural images. 
"""
skullstrip = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)
skullstrip.inputs.mask = True


"""
   f. Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
   body registration of the functional data to the structural
   data. Setting `write` to False ensures that the output of
   coregister is not resampled. Only the header information is
   updated. 
"""
coregister = nw.NodeWrapper(interface=spm.Coregister(),diskbased=True)
coregister.inputs.write = False


"""
   g. Use :class:`nipype.interfaces.spm.Normalize` to warp functional
   and structural data to SPM's T1 template.
"""
normalize = nw.NodeWrapper(interface=spm.Normalize(),diskbased=True)
normalize.inputs.template = os.path.abspath('data/T1.nii')


"""
   h. Use :class:`nipype.interfaces.spm.Smooth` to smooth the
   functional data.
"""
smooth = nw.NodeWrapper(interface=spm.Smooth(),diskbased=True)
smooth.inputs.fwhm = [6,6,8]

#######################################################################
# setup analysis components
#######################################################################


"""
   a. Setup a function that returns subject-specific information about
   the experimental paradigm. This is used by the
   :class:`nipype.interfaces.spm.SpecifyModel` to create the
   information necessary to generate an SPM design matrix. In this
   tutorial, the same paradigm was used for every participant. Other
   examples of this function are available in the `doc/examples`
   folder. Note: Python knowledge required here.
"""
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

"""
   b. Setup the contrast structure that needs to be evaluated. This is
   a list of lists. The inner list specifies the contrasts and has the
   following format - [Name,Stat,[list of condition names],[weights on
   those conditions]. The condition names must match the `names`
   listed in the `subjectinfo` function described above. 
"""
cont1 = ['Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5]]
cont2 = ['Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1]]
contrasts = [cont1,cont2]

"""
   c. Use :class:`nipype.interfaces.spm.SpecifyModel` to generate
   SPM-specific design information. 
"""
modelspec = nw.NodeWrapper(interface=spm.SpecifyModel())
modelspec.inputs.subject_info_func       = subjectinfo
modelspec.inputs.concatenate_runs        = True
modelspec.inputs.input_units             = 'secs'
modelspec.inputs.output_units            = 'secs'
modelspec.inputs.time_repetition         = 3.
modelspec.inputs.high_pass_filter_cutoff = 120


"""
   d. Use :class:`nipype.interfaces.spm.Level1Design` to generate a
   first level SPM.mat file for analysis
"""
level1design = nw.NodeWrapper(interface=spm.Level1Design(),diskbased=True)
level1design.inputs.timing_units       = modelspec.inputs.output_units
level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
level1design.inputs.bases              = {'hrf':{'derivs': [0,0]}}


"""
   e. Use :class:`nipype.interfaces.spm.EstimateModel` to determine
   the parameters of the model.
"""
level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(),diskbased=True)
level1estimate.inputs.estimation_method = {'Classical' : 1}


"""
   f. Use :class:`nipype.interfaces.spm.EstimateContrast` to estimate
   the first level contrasts specified in step 5(b).
"""
contrastestimate = nw.NodeWrapper(interface=spm.EstimateContrast(),diskbased=True)
contrastestimate.inputs.contrasts = contrasts


#################################################################################
# Setup pipeline
#################################################################################

"""
   The nodes setup above do not describe the flow of data. They merely
   describe the parameters used for each function. In this section we
   setup the connections between the nodes such that appropriate
   outputs from nodes are piped into appropriate inputs of other
   nodes.  

   a. Use :class:`nipype.pipeline.engine.Pipeline` to create a
   graph-based execution pipeline for first level analysis. The config
   options tells the pipeline engine to use `workdir` as the disk
   location to use when running the processes and keeping their
   outputs. The `use_parameterized_dirs` tells the engine to create
   sub-directories under `workdir` corresponding to the iterables in
   the pipeline. Thus for this pipeline there will be subject specific
   sub-directories. 

   The ``nipype.pipeline.engine.Pipeline.connect`` function creates the
   links between the processes, i.e., how data should flow in and out
   of the processing nodes. 
"""
l1pipeline = pe.Pipeline()
l1pipeline.config['workdir'] = os.path.abspath('spm/workingdir')
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

"""
   b. Use :class:`nipype.interfaces.io.DataSink` to store selected
   outputs from the pipeline in a specific location. This allows the
   user to selectively choose important output bits from the analysis
   and keep them.

   The first step is to create a datasink node and then to connect
   outputs from the modules above to storage locations. These take the
   following form directory_name[.[@]subdir] where parts between []
   are optional. For example 'realign.@mean' below creates a
   directory called realign in 'l1output/subject_id/' and stores the
   mean image output from the Realign process in the realign
   directory. If the @ is left out, then a sub-directory with the name
   'mean' would be created and the mean image would be copied to that
   directory. 
"""
datasink = nw.NodeWrapper(interface=nio.DataSink())
datasink.inputs.base_directory = os.path.abspath('spm/l1output')

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
#########################################################################

"""
  a. Use :class:`nipype.interfaces.io.DataGrabber` to extract the
  contrast images across a group of first level subjects. Unlike the
  previous pipeline that iterated over subjects, this pipeline will
  iterate over contrasts.
"""
# collect all the con images for each contrast.
contrast_ids = range(1,len(contrasts)+1)
l2source = nw.NodeWrapper(nio.DataGrabber())
l2source.inputs.file_template=os.path.abspath('spm/l1output/*/con*/con_%04d.img')
l2source.inputs.template_argnames=['con']
# iterate over all contrast images
l2source.iterables = dict(con=lambda:contrast_ids)


"""
  b. Use :class:`nipype.interfaces.spm.OneSampleTTest` to perform a
  simple statistical analysis of the contrasts from the group of
  subjects (n=2 in this example).
"""
# setup a 1-sample t-test node
onesamplettest = nw.NodeWrapper(interface=spm.OneSampleTTest(),diskbased=True)


"""
  c. As before, we setup a pipeline to connect these two nodes
  (l2source -> onesamplettest).
"""
l2pipeline = pe.Pipeline()
l2pipeline.config['workdir'] = os.path.abspath('spm/l2output')
l2pipeline.config['use_parameterized_dirs'] = True
l2pipeline.connect([(l2source,onesamplettest,[('file_list','con_images')])])


##########################################################################
# Execute the pipeline
##########################################################################

"""
   The code discussed above sets up all the necessary data structures
   with appropriate parameters and the connectivity between the
   processes, but does not generate any output. To actually run the
   analysis on the data the ``nipype.pipeline.engine.Pipeline.Run``
   function needs to be called. 
"""
if __name__ == '__main__':
    l1pipeline.run_in_series()
    l2pipeline.run_in_series()
