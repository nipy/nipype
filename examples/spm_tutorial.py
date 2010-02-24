"""
Using SPM for analysis
=======================

The spm_tutorial.py integrates several interfaces to perform a first
and second level analysis on a two-subject data set.  The tutorial can
be found in the examples folder.  Run the tutorial from inside the
nipype tutorial directory:
"""

    python spm_tutorial.py

"""Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.algorithms.modelgen as model   # model specification
import os                                    # system functions

"""

Preliminaries
-------------

Confirm package dependencies are installed.  (This is only for the
tutorial, rarely would you put this in your own code.)
"""

from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')

"""Set any package specific configuration. The output file format
for FSL routines is being set to uncompressed NIFTI and a specific
version of matlab is being used. The uncompressed format is required
because SPM does not handle compressed NIFTI.
"""

# Tell fsl to generate all output in uncompressed nifti format
print fsl.FSLInfo.version()
fsl.FSLInfo.outputtype('NIFTI')

# Set the way matlab should be called
mlab.MatlabCommandLine.matlab_cmd = "matlab -nodesktop -nosplash"

"""The nipype tutorial contains data for two subjects.  Subject data
is in two subdirectories, ``s1`` and ``s2``.  Each subject directory
contains four functional volumes: f3.nii, f5.nii, f7.nii, f10.nii. And
one anatomical volume named struct.nii.

Below we set some variables to inform the ``datasource`` about the
layout of our data.  We specify the location of the data, the subject
sub-directories and a dictionary that maps each run to a mnemonic (or
field) for the run type (``struct`` or ``func``).  These fields become
the output fields of the ``datasource`` node in the pipeline.

In the example below, run 'f3' is of type 'func' and gets mapped to a
nifti filename through a template '%s.nii'. So 'f3' would become
'f3.nii'.

"""

# Specify the location of the data.
data_dir = os.path.abspath('data')
# Specify the subject directories
subject_list = ['s1','s3']
# Map field names to individual subject runs.
info = {}
info['s1'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))
info['s3'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))

"""
Preprocessing pipeline nodes
----------------------------

Now we create a :class:`nipype.interfaces.io.DataSource` object and
fill in the information from above about the layout of our data.  The
:class:`nipype.pipeline.NodeWrapper` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = nw.NodeWrapper(interface=nio.DataSource(),diskbased=False)
datasource.inputs.base_directory   = data_dir
datasource.inputs.subject_template = '%s'
datasource.inputs.file_template    = '%s.nii'
datasource.inputs.subject_info     = info


"""Here we set up iteration over all the subjects. The following line
is a particular example of the flexibility of the system.  The
``datasource`` attribute ``iterables`` tells the pipeline engine that
it should repeat the analysis on each of the items in the
``subject_list``. In the current example, the entire first level
preprocessing and estimation will be repeated for each subject
contained in subject_list.
"""

datasource.iterables = ('subject_id', subject_list)

"""Use :class:`nipype.interfaces.spm.Realign` for motion correction
and register all images to the mean image.
"""

realign = nw.NodeWrapper(interface=spm.Realign(),diskbased=True)
realign.inputs.register_to_mean = True

"""Use :class:`nipype.algorithms.rapidart` to determine which of the
images in the functional series are outliers based on deviations in
intensity or movement.
"""

art = nw.NodeWrapper(interface=ra.ArtifactDetect(),diskbased=True)
art.inputs.use_differences      = [True,True]
art.inputs.use_norm             = True
art.inputs.norm_threshold       = 0.5
art.inputs.zintensity_threshold = 3
art.inputs.mask_type            = 'file'

"""Skull strip structural images using
:class:`nipype.interfaces.fsl.Bet`.
"""

skullstrip = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)
skullstrip.inputs.mask = True

"""Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
body registration of the functional data to the structural data.
"""

coregister = nw.NodeWrapper(interface=spm.Coregister(),diskbased=True)
coregister.inputs.jobtype = 'estimate'


"""Warp functional and structural data to SPM's T1 template using
:class:`nipype.interfaces.spm.Normalize`.  The tutorial data set
includes the template image, T1.nii.
"""

normalize = nw.NodeWrapper(interface=spm.Normalize(),diskbased=True)
normalize.inputs.template = os.path.abspath('data/T1.nii')


"""Smooth the functional data using
:class:`nipype.interfaces.spm.Smooth`.
"""

smooth = nw.NodeWrapper(interface=spm.Smooth(),diskbased=True)
#smooth.inputs.fwhm = [6,6,8]
smooth.iterables = ('fwhm',[4,8])

"""
Set up analysis components
--------------------------

Here we create a function that returns subject-specific information
about the experimental paradigm. This is used by the
:class:`nipype.interfaces.spm.SpecifyModel` to create the information
necessary to generate an SPM design matrix. In this tutorial, the same
paradigm was used for every participant.
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

"""Setup the contrast structure that needs to be evaluated. This is a
list of lists. The inner list specifies the contrasts and has the
following format - [Name,Stat,[list of condition names],[weights on
those conditions]. The condition names must match the `names` listed
in the `subjectinfo` function described above.
"""

cont1 = ['Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5]]
cont2 = ['Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1]]
contrasts = [cont1,cont2]

"""Generate SPM-specific design information using
:class:`nipype.interfaces.spm.SpecifyModel`.
"""

modelspec = nw.NodeWrapper(interface=model.SpecifyModel(),diskbased=True)
modelspec.inputs.concatenate_runs        = True
modelspec.inputs.input_units             = 'secs'
modelspec.inputs.output_units            = 'secs'
modelspec.inputs.time_repetition         = 3.
modelspec.inputs.high_pass_filter_cutoff = 120

"""Generate a first level SPM.mat file for analysis
:class:`nipype.interfaces.spm.Level1Design`.
"""

level1design = nw.NodeWrapper(interface=spm.Level1Design(),diskbased=True)
level1design.inputs.timing_units       = modelspec.inputs.output_units
level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
level1design.inputs.bases              = {'hrf':{'derivs': [0,0]}}


"""Use :class:`nipype.interfaces.spm.EstimateModel` to determine the
parameters of the model.
"""

level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(),diskbased=True)
level1estimate.inputs.estimation_method = {'Classical' : 1}

"""Use :class:`nipype.interfaces.spm.EstimateContrast` to estimate the
first level contrasts specified in a few steps above.
"""

contrastestimate = nw.NodeWrapper(interface = spm.EstimateContrast(),
                                  diskbased=True)
contrastestimate.inputs.contrasts = contrasts

"""
Setup the pipeline
------------------

The nodes created above do not describe the flow of data. They merely
describe the parameters used for each function. In this section we
setup the connections between the nodes such that appropriate outputs
from nodes are piped into appropriate inputs of other nodes.

Use the :class:`nipype.pipeline.engine.Pipeline` to create a
graph-based execution pipeline for first level analysis. The config
options tells the pipeline engine to use `workdir` as the disk
location to use when running the processes and keeping their
outputs. The `use_parameterized_dirs` tells the engine to create
sub-directories under `workdir` corresponding to the iterables in the
pipeline. Thus for this pipeline there will be subject specific
sub-directories.

The ``nipype.pipeline.engine.Pipeline.connect`` function creates the
links between the processes, i.e., how data should flow in and out of
the processing nodes.
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
                  (datasource,modelspec,[('subject_id','subject_id'),
                                         (('subject_id', subjectinfo),
                                          'subject_info_func')]),
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


"""

Setup storage results
---------------------

Use :class:`nipype.interfaces.io.DataSink` to store selected outputs
from the pipeline in a specific location. This allows the user to
selectively choose important output bits from the analysis and keep
them.

The first step is to create a datasink node and then to connect
outputs from the modules above to storage locations. These take the
following form directory_name[.[@]subdir] where parts between [] are
optional. For example 'realign.@mean' below creates a directory called
realign in 'l1output/subject_id/' and stores the mean image output
from the Realign process in the realign directory. If the @ is left
out, then a sub-directory with the name 'mean' would be created and
the mean image would be copied to that directory.
"""

datasink = nw.NodeWrapper(interface=nio.DataSink(),diskbased=False)
#datasink.inputs.base_directory = os.path.abspath('spm/l1output')
datasink.inputs.subject_directory = os.path.abspath('spm/l1output')

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
                                                ('spmT_images','contrasts.@T'),
                                                ('parameterization','parameterization')]),
                    ])


"""
Setup level 2 pipeline
----------------------

Use :class:`nipype.interfaces.io.DataGrabber` to extract the contrast
images across a group of first level subjects. Unlike the previous
pipeline that iterated over subjects, this pipeline will iterate over
contrasts.
"""

# collect all the con images for each contrast.
contrast_ids = range(1,len(contrasts)+1)
l2source = nw.NodeWrapper(nio.DataGrabber())
l2source.inputs.file_template=os.path.abspath('spm/l1output/*/_fwhm_%d/con*/con_%04d.img')
l2source.inputs.template_argnames=['fwhm','con']
# iterate over all contrast images
l2source.iterables = [('fwhm',[4,8]),
                      ('con',contrast_ids)]


"""Use :class:`nipype.interfaces.spm.OneSampleTTest` to perform a
simple statistical analysis of the contrasts from the group of
subjects (n=2 in this example).
"""

# setup a 1-sample t-test node
onesamplettest = nw.NodeWrapper(interface=spm.OneSampleTTest(), diskbased=True)


"""As before, we setup a pipeline to connect these two nodes (l2source
-> onesamplettest).
"""

l2pipeline = pe.Pipeline()
l2pipeline.config['workdir'] = os.path.abspath('spm/l2output')
l2pipeline.config['use_parameterized_dirs'] = True
l2pipeline.connect([(l2source,onesamplettest,[('file_list','con_images')])])

"""
Execute the pipeline
--------------------

The code discussed above sets up all the necessary data structures
with appropriate parameters and the connectivity between the
processes, but does not generate any output. To actually run the
analysis on the data the ``nipype.pipeline.engine.Pipeline.Run``
function needs to be called.
"""

if __name__ == '__main__':
    l1pipeline.run()
    l2pipeline.run()
