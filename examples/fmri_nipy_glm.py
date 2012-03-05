#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
===================
fMRI: NiPy GLM, SPM
===================


The fmri_nipy_glm.py integrates several interfaces to perform a first level
analysis on a two-subject data set. It is very similar to the spm_tutorial with
the difference of using nipy for fitting GLM model and estimating contrasts.
The tutorial can
be found in the examples folder. Run the tutorial from inside the
nipype tutorial directory:

    python fmri_nipy_glm.py

"""
from nipype.interfaces.nipy.model import FitGLM, EstimateContrast
from nipype.interfaces.nipy.preprocess import ComputeMask


"""Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
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

# Set the way matlab should be called
mlab.MatlabCommand.set_default_matlab_cmd("matlab -nodesktop -nosplash")

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
subject_list = ['s1']
# Map field names to individual subject runs.
info = dict(func=[['subject_id', ['f3','f5','f7','f10']]],
            struct=[['subject_id','struct']])

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
Preprocessing pipeline nodes
----------------------------

Now we create a :class:`nipype.interfaces.io.DataSource` object and
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


"""Use :class:`nipype.interfaces.spm.Realign` for motion correction
and register all images to the mean image.
"""

realign = pe.Node(interface=spm.Realign(), name="realign")
realign.inputs.register_to_mean = True

compute_mask = pe.Node(interface=ComputeMask(), name="compute_mask")

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


"""Use :class:`nipype.interfaces.spm.Coregister` to perform a rigid
body registration of the functional data to the structural data.
"""

coregister = pe.Node(interface=spm.Coregister(), name="coregister")
coregister.inputs.jobtype = 'estimate'


"""Smooth the functional data using
:class:`nipype.interfaces.spm.Smooth`.
"""

smooth = pe.Node(interface=spm.Smooth(), name = "smooth")
smooth.inputs.fwhm = 4

"""
Set up analysis components
--------------------------

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

"""Generate design information using
:class:`nipype.interfaces.spm.SpecifyModel`. nipy accepts only design specified
in seconds so "output_units" has always have to be set to "secs".
"""

modelspec = pe.Node(interface=model.SpecifySPMModel(), name= "modelspec")
modelspec.inputs.concatenate_runs        = True
modelspec.inputs.input_units             = 'secs'
modelspec.inputs.output_units            = 'secs'
modelspec.inputs.time_repetition         = 3.
modelspec.inputs.high_pass_filter_cutoff = 120

"""Fit the GLM model using nipy and ordinary least square method
"""

model_estimate = pe.Node(interface=FitGLM(), name="model_estimate")
model_estimate.inputs.TR = 3.
model_estimate.inputs.model = "spherical"
model_estimate.inputs.method = "ols"

"""Estimate the contrasts. The format of the contrasts definition is the same as
for FSL and SPM
"""

contrast_estimate = pe.Node(interface=EstimateContrast(), name="contrast_estimate")
cont1 = ('Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5])
cont2 = ('Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1])
contrast_estimate.inputs.contrasts = [cont1,cont2]

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

l1pipeline = pe.Workflow(name="level1")
l1pipeline.base_dir = os.path.abspath('nipy_tutorial/workingdir')

l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                  (datasource,realign,[('func','in_files')]),
                  (realign, compute_mask, [('mean_image','mean_volume')]),
                  (realign, coregister,[('mean_image', 'source'),
                                        ('realigned_files','apply_to_files')]),
                  (datasource, coregister,[('struct', 'target')]),
                  (coregister, smooth, [('coregistered_files', 'in_files')]),
                  (realign, modelspec,[('realignment_parameters','realignment_parameters')]),
                  (smooth, modelspec,[('smoothed_files','functional_runs')]),
                  (realign, art,[('realignment_parameters','realignment_parameters')]),
                  (coregister, art,[('coregistered_files','realigned_files')]),
                  (compute_mask,art,[('brain_mask','mask_file')]),
                  (art, modelspec,[('outlier_files','outlier_files')]),
                  (infosource, modelspec, [(("subject_id", subjectinfo), "subject_info")]),
                  (modelspec, model_estimate,[('session_info','session_info')]),
                  (compute_mask, model_estimate, [('brain_mask','mask')]),
                  (model_estimate, contrast_estimate, [("beta","beta"),
                                                        ("nvbeta","nvbeta"),
                                                        ("s2","s2"),
                                                        ("dof", "dof"),
                                                        ("axis", "axis"),
                                                        ("constants", "constants"),
                                                        ("reg_names", "reg_names")])
                  ])

if __name__ == '__main__':
    l1pipeline.run()

