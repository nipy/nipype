# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
===========================
fMRI - SPM nested workflows
===========================

The spm_tutorial.py integrates several interfaces to perform a first
and second level analysis on a two-subject data set.  The tutorial can
be found in the examples folder.  Run the tutorial from inside the
nipype tutorial directory:

    python spm_tutorial.py

Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.algorithms.modelgen as model   # model specification
import os                                    # system functions

"""

Preliminaries
-------------

Set any package specific configuration. The output file format
for FSL routines is being set to uncompressed NIFTI and a specific
version of matlab is being used. The uncompressed format is required
because SPM does not handle compressed NIFTI.
"""

# Tell fsl to generate all output in uncompressed nifti format
fsl.FSLCommand.set_default_output_type('NIFTI')

# Set the way matlab should be called
#mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")
#mlab.MatlabCommand.set_default_paths('/software/spm8')


"""
Setting up workflows
--------------------

In this tutorial we will be setting up a hierarchical workflow for spm
analysis. This will demonstrate how pre-defined workflows can be setup
and shared across users, projects and labs.


Setup preprocessing workflow
----------------------------

This is a generic preprocessing workflow that can be used by different analyses

"""

preproc = pe.Workflow(name='preproc')

"""Use :class:`nipype.interfaces.spm.Realign` for motion correction
and register all images to the mean image.
"""

realign = pe.Node(interface=spm.Realign(), name="realign")
realign.inputs.register_to_mean = True

"""Use :class:`nipype.algorithms.rapidart` to determine which of the
images in the functional series are outliers based on deviations in
intensity or movement.
"""

art = pe.Node(interface=ra.ArtifactDetect(), name="art")
art.inputs.use_differences      = [True, False]
art.inputs.use_norm             = True
art.inputs.norm_threshold       = 1
art.inputs.zintensity_threshold = 3
art.inputs.mask_type            = 'file'
art.inputs.parameter_source     = 'SPM'

"""Skull strip structural images using
:class:`nipype.interfaces.fsl.BET`.
"""

skullstrip = pe.Node(interface=fsl.BET(), name="skullstrip")
skullstrip.inputs.mask = True

"""Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
body registration of the functional data to the structural data.
"""

coregister = pe.Node(interface=spm.Coregister(), name="coregister")
coregister.inputs.jobtype = 'estimate'


"""Warp functional and structural data to SPM's T1 template using
:class:`nipype.interfaces.spm.Normalize`.  The tutorial data set
includes the template image, T1.nii.
"""

normalize = pe.Node(interface=spm.Normalize(), name = "normalize")
normalize.inputs.template = os.path.abspath('data/T1.nii')


"""Smooth the functional data using
:class:`nipype.interfaces.spm.Smooth`.
"""

smooth = pe.Node(interface=spm.Smooth(), name = "smooth")
fwhmlist = [4]
smooth.iterables = ('fwhm',fwhmlist)

preproc.connect([(realign,coregister,[('mean_image', 'source'),
                                      ('realigned_files','apply_to_files')]),
                 (coregister, normalize, [('coregistered_files','apply_to_files')]),
                 (normalize, smooth, [('normalized_files', 'in_files')]),
                 (normalize,skullstrip,[('normalized_source','in_file')]),
                 (realign,art,[('realignment_parameters','realignment_parameters')]),
                 (normalize,art,[('normalized_files','realigned_files')]),
                 (skullstrip,art,[('mask_file','mask_file')]),
                 ])


"""
Set up analysis workflow
------------------------

"""

l1analysis = pe.Workflow(name='analysis')

"""Generate SPM-specific design information using
:class:`nipype.interfaces.spm.SpecifyModel`.
"""

modelspec = pe.Node(interface=model.SpecifySPMModel(), name= "modelspec")
modelspec.inputs.concatenate_runs        = True

"""Generate a first level SPM.mat file for analysis
:class:`nipype.interfaces.spm.Level1Design`.
"""

level1design = pe.Node(interface=spm.Level1Design(), name= "level1design")
level1design.inputs.bases              = {'hrf':{'derivs': [0,0]}}

"""Use :class:`nipype.interfaces.spm.EstimateModel` to determine the
parameters of the model.
"""

level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
level1estimate.inputs.estimation_method = {'Classical' : 1}

"""Use :class:`nipype.interfaces.spm.EstimateContrast` to estimate the
first level contrasts specified in a few steps above.
"""

contrastestimate = pe.Node(interface = spm.EstimateContrast(), name="contrastestimate")

"""Use :class: `nipype.interfaces.utility.Select` to select each contrast for
reporting.
"""

selectcontrast = pe.Node(interface=util.Select(), name="selectcontrast")

"""Use :class:`nipype.interfaces.fsl.Overlay` to combine the statistical output of
the contrast estimate and a background image into one volume.
"""

overlaystats = pe.Node(interface=fsl.Overlay(), name="overlaystats")
overlaystats.inputs.stat_thresh = (3,10)
overlaystats.inputs.show_negative_stats=True
overlaystats.inputs.auto_thresh_bg=True

"""Use :class:`nipype.interfaces.fsl.Slicer` to create images of the overlaid
statistical volumes for a report of the first-level results.
"""

slicestats = pe.Node(interface=fsl.Slicer(), name="slicestats")
slicestats.inputs.all_axial = True
slicestats.inputs.image_width = 750

l1analysis.connect([(modelspec,level1design,[('session_info','session_info')]),
                  (level1design,level1estimate,[('spm_mat_file','spm_mat_file')]),
                  (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                  ('beta_images','beta_images'),
                                                  ('residual_image','residual_image')]),
                  (contrastestimate,selectcontrast,[('spmT_images','inlist')]),
                  (selectcontrast,overlaystats,[('out','stat_image')]),
                  (overlaystats,slicestats,[('out_file','in_file')])
                  ])

"""
Preproc + Analysis pipeline
---------------------------

"""

l1pipeline = pe.Workflow(name='firstlevel')
l1pipeline.connect([(preproc, l1analysis, [('realign.realignment_parameters',
                                            'modelspec.realignment_parameters'),
                                           ('smooth.smoothed_files',
                                            'modelspec.functional_runs'),
                                           ('art.outlier_files',
                                            'modelspec.outlier_files'),
                                           ('skullstrip.mask_file',
                                            'level1design.mask_image'),
                                           ('normalize.normalized_source',
                                            'overlaystats.background_image')]),
                  ])


"""
Data specific components
------------------------

The nipype tutorial contains data for two subjects.  Subject data
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
subject_list = ['s1', 's3']
# Map field names to individual subject runs.
info = dict(func=[['subject_id', ['f3','f5','f7','f10']]],
            struct=[['subject_id','struct']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']), name="infosource")

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
:class:`nipype.pipeline.NodeWrapper` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = info



"""
Experimental paradigm specific components
-----------------------------------------

Here we create a function that returns subject-specific information
about the experimental paradigm. This is used by the
:class:`nipype.interfaces.spm.SpecifyModel` to create the information
necessary to generate an SPM design matrix. In this tutorial, the same
paradigm was used for every participant.
"""

def subjectinfo(subject_id):
    from nipype.interfaces.base import Bunch
    from copy import deepcopy
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

cont1 = ('Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5])
cont2 = ('Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1])
contrasts = [cont1,cont2]

# set up node specific inputs
modelspecref = l1pipeline.inputs.analysis.modelspec
modelspecref.input_units             = 'secs'
modelspecref.output_units            = 'secs'
modelspecref.time_repetition         = 3.
modelspecref.high_pass_filter_cutoff = 120

l1designref = l1pipeline.inputs.analysis.level1design
l1designref.timing_units       = modelspecref.output_units
l1designref.interscan_interval = modelspecref.time_repetition


l1pipeline.inputs.analysis.contrastestimate.contrasts = contrasts


# Iterate over each contrast and create report images.
selectcontrast.iterables = ('index',[[i] for i in range(len(contrasts))])

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

level1 = pe.Workflow(name="level1")
level1.base_dir = os.path.abspath('spm_tutorial2/workingdir')

level1.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (datasource,l1pipeline,[('func','preproc.realign.in_files'),
                                        ('struct', 'preproc.coregister.target'),
                                        ('struct', 'preproc.normalize.source')]),
                (infosource,l1pipeline,[(('subject_id', subjectinfo),
                                          'analysis.modelspec.subject_info')]),
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

datasink = pe.Node(interface=nio.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.abspath('spm_tutorial2/l1output')
report = pe.Node(interface=nio.DataSink(), name='report')
report.inputs.base_directory = os.path.abspath('spm_tutorial2/report')
report.inputs.parameterization = False

def getstripdir(subject_id):
    import os
    return os.path.join(os.path.abspath('spm_tutorial2/workingdir'),'_subject_id_%s' % subject_id)

# store relevant outputs from various stages of the 1st level analysis
level1.connect([(infosource, datasink,[('subject_id','container'),
                                       (('subject_id', getstripdir),'strip_dir')]),
                (l1pipeline, datasink,[('analysis.contrastestimate.con_images','contrasts.@con'),
                                       ('analysis.contrastestimate.spmT_images','contrasts.@T')]),
                (infosource, report,[('subject_id', 'container'),
                                     (('subject_id', getstripdir),'strip_dir')]),
                (l1pipeline, report,[('analysis.slicestats.out_file', '@report')]),
                ])


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
    level1.run()
    level1.write_graph()

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
l2source = pe.Node(nio.DataGrabber(infields=['fwhm', 'con']), name="l2source")
l2source.inputs.template=os.path.abspath('spm_tutorial2/l1output/*/con*/*/_fwhm_%d/con_%04d.img')
# iterate over all contrast images
l2source.iterables = [('fwhm',fwhmlist),
                      ('con',contrast_ids)]


"""Use :class:`nipype.interfaces.spm.OneSampleTTestDesign` to perform a
simple statistical analysis of the contrasts from the group of
subjects (n=2 in this example).
"""

# setup a 1-sample t-test node
onesamplettestdes = pe.Node(interface=spm.OneSampleTTestDesign(), name="onesampttestdes")
l2estimate = pe.Node(interface=spm.EstimateModel(), name="level2estimate")
l2estimate.inputs.estimation_method = {'Classical' : 1}
l2conestimate = pe.Node(interface = spm.EstimateContrast(), name="level2conestimate")
cont1 = ('Group','T', ['mean'],[1])
l2conestimate.inputs.contrasts = [cont1]
l2conestimate.inputs.group_contrast = True


"""As before, we setup a pipeline to connect these two nodes (l2source
-> onesamplettest).
"""

l2pipeline = pe.Workflow(name="level2")
l2pipeline.base_dir = os.path.abspath('spm_tutorial2/l2output')
l2pipeline.connect([(l2source,onesamplettestdes,[('outfiles','in_files')]),
                  (onesamplettestdes,l2estimate,[('spm_mat_file','spm_mat_file')]),
                  (l2estimate,l2conestimate,[('spm_mat_file','spm_mat_file'),
                                             ('beta_images','beta_images'),
                                             ('residual_image','residual_image')]),
                    ])

"""
Execute the second level pipeline
---------------------------------

"""

if __name__ == '__main__':
    l2pipeline.run()

