#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
==========================
fMRI: SPM Auditory dataset
==========================

Introduction
============

The fmri_spm_auditory.py recreates the classical workflow described in the SPM8 manual (http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf)
using auditory dataset that can be downloaded from http://www.fil.ion.ucl.ac.uk/spm/data/auditory/:

    python fmri_spm_auditory.py

Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.matlab as mlab      # how to run matlabimport nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model specification
import os                                    # system functions

"""

Preliminaries
-------------

"""

# Set the way matlab should be called
mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")

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

"""We strongly encourage to use 4D files insteead of series of 3D for fMRI analyses
for many reasons (cleanness and saving and filesystem inodes are among them). However,
the the workflow presented in the SPM8 manual which this tutorial is based on
uses 3D files. Therefore we leave converting to 4D as an option. We are using `merge_to_4d`
variable, because switching between 3d and 4d requires some additional steps (explauned later on).
Use :class:`nipype.interfaces.fsl.Merge` to merge a series of 3D files along the time
dimension creating a 4d file.
"""

merge_to_4d = True

if merge_to_4d:
    merge = pe.Node(interface=fsl.Merge(), name="merge")
    merge.inputs.dimension="t"

"""Use :class:`nipype.interfaces.spm.Realign` for motion correction
and register all images to the mean image.
"""

realign = pe.Node(interface=spm.Realign(), name="realign")


"""Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
body registration of the functional data to the structural data.
"""

coregister = pe.Node(interface=spm.Coregister(), name="coregister")
coregister.inputs.jobtype = 'estimate'



segment = pe.Node(interface=spm.Segment(), name="segment")

"""Uncomment the following line for faster execution
"""

#segment.inputs.gaussians_per_class = [1, 1, 1, 4]

"""Warp functional and structural data to SPM's T1 template using
:class:`nipype.interfaces.spm.Normalize`.  The tutorial data set
includes the template image, T1.nii.
"""

normalize_func = pe.Node(interface=spm.Normalize(), name = "normalize_func")
normalize_func.inputs.jobtype = "write"

normalize_struc = pe.Node(interface=spm.Normalize(), name = "normalize_struc")
normalize_struc.inputs.jobtype = "write"


"""Smooth the functional data using
:class:`nipype.interfaces.spm.Smooth`.
"""

smooth = pe.Node(interface=spm.Smooth(), name = "smooth")

"""`write_voxel_sizes` is the input of the normalize interface that is recommended to be set to
the voxel sizes of the target volume. There is no need to set it manually since we van infer it from data
using the following function:
"""

def get_vox_dims(volume):
    import nibabel as nb
    if isinstance(volume, list):
        volume = volume[0]
    nii = nb.load(volume)
    hdr = nii.get_header()
    voxdims = hdr.get_zooms()
    return [float(voxdims[0]), float(voxdims[1]), float(voxdims[2])]

"""Here we are connecting all the nodes together. Notice that we add the merge node only if you choose
to use 4D. Also `get_vox_dims` function is passed along the input volume of normalise to set the optimal
voxel sizes.
"""

if merge_to_4d:
    preproc.connect([(merge, realign,[('merged_file', 'in_files')])])

preproc.connect([(realign,coregister,[('mean_image', 'target')]),
                 (coregister, segment,[('coregistered_source','data')]),
                 (segment, normalize_func, [('transformation_mat','parameter_file')]),
                 (segment, normalize_struc, [('transformation_mat','parameter_file'),
                                             ('modulated_input_image', 'apply_to_files'),
                                             (('modulated_input_image', get_vox_dims), 'write_voxel_sizes')]),
                 (realign, normalize_func, [('realigned_files', 'apply_to_files'),
                                            (('realigned_files', get_vox_dims), 'write_voxel_sizes')]),
                 (normalize_func, smooth, [('normalized_files', 'in_files')]),
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

threshold = pe.Node(interface=spm.Threshold(), name="threshold")


"""Use :class:`nipype.interfaces.spm.EstimateContrast` to estimate the
first level contrasts specified in a few steps above.
"""

contrastestimate = pe.Node(interface = spm.EstimateContrast(), name="contrastestimate")

l1analysis.connect([(modelspec,level1design,[('session_info','session_info')]),
                  (level1design,level1estimate,[('spm_mat_file','spm_mat_file')]),
                  (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                  ('beta_images','beta_images'),
                                                  ('residual_image','residual_image')]),
                  (contrastestimate, threshold,[('spm_mat_file','spm_mat_file'),
                                                    ('spmT_images', 'stat_image')]),
                  ])

"""
Preproc + Analysis pipeline
---------------------------

"""



l1pipeline = pe.Workflow(name='firstlevel')
l1pipeline.connect([(preproc, l1analysis, [('realign.realignment_parameters',
                                            'modelspec.realignment_parameters')])])

"""Pluging in `functional_runs` is a bit more complicated, because model spec expects a list of `runs`.
Every run can be a 4D file or a list of 3D files. Therefore for 3D analysis we need a list of lists and
to make one we need a helper function.
"""

if merge_to_4d:
    l1pipeline.connect([(preproc, l1analysis, [('smooth.smoothed_files',
                                                'modelspec.functional_runs')])])
else:
    def makelist(item):
        return [item]
    l1pipeline.connect([(preproc, l1analysis, [(('smooth.smoothed_files',makelist),
                                                'modelspec.functional_runs')])])



"""
Data specific components
------------------------

In this tutorial there is only one subject `M00223`.

Below we set some variables to inform the ``datasource`` about the
layout of our data.  We specify the location of the data, the subject
sub-directories and a dictionary that maps each run to a mnemonic (or
field) for the run type (``struct`` or ``func``).  These fields become
the output fields of the ``datasource`` node in the pipeline.
"""

# Specify the location of the data downloaded from http://www.fil.ion.ucl.ac.uk/spm/data/auditory/
data_dir = os.path.abspath('spm_auditory_data')
# Specify the subject directories
subject_list = ['M00223']
# Map field names to individual subject runs.
info = dict(func=[['f', 'subject_id', 'f', 'subject_id', range(16,100)]],
            struct=[['s', 'subject_id', 's', 'subject_id', 2]])

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
datasource.inputs.template = '%s%s/%s%s_%03d.img'
datasource.inputs.template_args = info



"""
Experimental paradigm specific components
-----------------------------------------

Here we create a structure that provides information
about the experimental paradigm. This is used by the
:class:`nipype.interfaces.spm.SpecifyModel` to create the information
necessary to generate an SPM design matrix.
"""

from nipype.interfaces.base import Bunch
subjectinfo = [Bunch(conditions=['Task'],
                            onsets=[range(6,84,12)],
                            durations=[[6]])]

"""Setup the contrast structure that needs to be evaluated. This is a
list of lists. The inner list specifies the contrasts and has the
following format - [Name,Stat,[list of condition names],[weights on
those conditions]. The condition names must match the `names` listed
in the `subjectinfo` function described above.
"""

cont1 = ('active > rest','T', ['Task'],[1])
contrasts = [cont1]

# set up node specific inputs
modelspecref = l1pipeline.inputs.analysis.modelspec
modelspecref.input_units             = 'scans'
modelspecref.output_units            = 'scans'
modelspecref.time_repetition         = 7
modelspecref.high_pass_filter_cutoff = 120

l1designref = l1pipeline.inputs.analysis.level1design
l1designref.timing_units       = modelspecref.output_units
l1designref.interscan_interval = modelspecref.time_repetition

l1pipeline.inputs.preproc.smooth.fwhm = [6, 6, 6]
l1pipeline.inputs.analysis.modelspec.subject_info = subjectinfo
l1pipeline.inputs.analysis.contrastestimate.contrasts = contrasts
l1pipeline.inputs.analysis.threshold.contrast_index = 1

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
level1.base_dir = os.path.abspath('spm_auditory_tutorial/workingdir')

level1.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (datasource,l1pipeline,[('struct', 'preproc.coregister.source')])
                ])
if merge_to_4d:
    level1.connect([(datasource,l1pipeline,[('func','preproc.merge.in_files')])])
else:
    level1.connect([(datasource,l1pipeline,[('func','preproc.realign.in_files')])])


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
datasink.inputs.base_directory = os.path.abspath('spm_auditory_tutorial/l1output')

def getstripdir(subject_id):
    import os
    return os.path.join(os.path.abspath('spm_auditory_tutorial/workingdir'),'_subject_id_%s' % subject_id)

# store relevant outputs from various stages of the 1st level analysis
level1.connect([(infosource, datasink,[('subject_id','container'),
                                       (('subject_id', getstripdir),'strip_dir')]),
                (l1pipeline, datasink,[('analysis.contrastestimate.con_images','contrasts.@con'),
                                       ('analysis.contrastestimate.spmT_images','contrasts.@T')]),
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

