# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
======================================
fMRI - Famous vs non-famous faces, SPM
======================================

Introduction
============

The spm_face_tutorial.py recreates the classical workflow described in the SPM8 manual (http://www.fil.ion.ucl.ac.uk/spm/doc/manual.pdf)
using auditory dataset that can be downloaded from http://www.fil.ion.ucl.ac.uk/spm/data/face_rep/face_rep_SPM5.html:

    python spm_tutorial.py

Import necessary modules from nipype."""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
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
# If SPM is not in your MATLAB path you should add it here
# mlab.MatlabCommand.set_default_paths('/path/to/your/spm8')


"""
Setting up workflows
--------------------

In this tutorial we will be setting up a hierarchical workflow for spm
analysis. It one is slightly different then the one used in spm_tutorial2.


Setup preprocessing workflow
----------------------------

This is a generic preprocessing workflow that can be used by different analyses

"""

preproc = pe.Workflow(name='preproc')


"""Use :class:`nipype.interfaces.spm.Realign` for motion correction
and register all images to the mean image.
"""

realign = pe.Node(interface=spm.Realign(), name="realign")

slice_timing = pe.Node(interface=spm.SliceTiming(), name="slice_timing")


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

preproc.connect([(realign,coregister,[('mean_image', 'target')]),
                 (coregister, segment,[('coregistered_source','data')]),
                 (segment, normalize_func, [('transformation_mat','parameter_file')]),
                 (segment, normalize_struc, [('transformation_mat','parameter_file'),
                                             ('modulated_input_image', 'apply_to_files'),
                                             (('modulated_input_image', get_vox_dims), 'write_voxel_sizes')]),
                 (realign, slice_timing, [('realigned_files', 'in_files')]),
                 (slice_timing, normalize_func, [('timecorrected_files', 'apply_to_files'),
                                            (('timecorrected_files', get_vox_dims), 'write_voxel_sizes')]),
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

def pickfirst(l):
    return l[0]

l1analysis.connect([(modelspec,level1design,[('session_info','session_info')]),
                  (level1design,level1estimate,[('spm_mat_file','spm_mat_file')]),
                  (level1estimate,contrastestimate,[('spm_mat_file','spm_mat_file'),
                                                  ('beta_images','beta_images'),
                                                  ('residual_image','residual_image')]),
                  (contrastestimate, threshold,[('spm_mat_file','spm_mat_file'),
                                                    (('spmT_images', pickfirst), 'stat_image')]),
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

def makelist(item):
    return [item]
l1pipeline.connect([(preproc, l1analysis, [(('smooth.smoothed_files',makelist),
                                            'modelspec.functional_runs')])])


"""
Data specific components
------------------------

In this tutorial there is only one subject `M03953`.

Below we set some variables to inform the ``datasource`` about the
layout of our data.  We specify the location of the data, the subject
sub-directories and a dictionary that maps each run to a mnemonic (or
field) for the run type (``struct`` or ``func``).  These fields become
the output fields of the ``datasource`` node in the pipeline.
"""

# Specify the location of the data downloaded from http://www.fil.ion.ucl.ac.uk/spm/data/face_rep/face_rep_SPM5.html
data_dir = os.path.abspath('spm_face_data')
# Specify the subject directories
subject_list = ['M03953']
# Map field names to individual subject runs.
info = dict(func=[['RawEPI', 'subject_id', 5, ["_%04d"%i for i in range(6,357)]]],
            struct=[['Structural', 'subject_id', 7, '']])

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
:class:`nipype.pipeline.NodeWrapper` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
"""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/s%s_%04d%s.img'
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

"""We're importing the onset times from a mat file (found on
http://www.fil.ion.ucl.ac.uk/spm/data/face_rep/face_rep_SPM5.html
"""

from scipy.io.matlab import loadmat
mat = loadmat(os.path.join(data_dir, "sots.mat"), struct_as_record=False)
sot = mat['sot'][0]
itemlag = mat['itemlag'][0]

subjectinfo = [Bunch(conditions=['N1', 'N2', 'F1', 'F2'],
                            onsets=[sot[0], sot[1], sot[2], sot[3]],
                            durations=[[0], [0], [0], [0]],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None)]

"""Setup the contrast structure that needs to be evaluated. This is a
list of lists. The inner list specifies the contrasts and has the
following format - [Name,Stat,[list of condition names],[weights on
those conditions]. The condition names must match the `names` listed
in the `subjectinfo` function described above.
"""

cond1 = ('positive effect of condition','T', ['N1*bf(1)','N2*bf(1)','F1*bf(1)','F2*bf(1)'],[1,1,1,1])
cond2 = ('positive effect of condition_dtemo','T', ['N1*bf(2)','N2*bf(2)','F1*bf(2)','F2*bf(2)'],[1,1,1,1])
cond3 = ('positive effect of condition_ddisp','T', ['N1*bf(3)','N2*bf(3)','F1*bf(3)','F2*bf(3)'],[1,1,1,1])
# non-famous > famous
fam1 = ('positive effect of Fame','T', ['N1*bf(1)','N2*bf(1)','F1*bf(1)','F2*bf(1)'],[1,1,-1,-1])
fam2 = ('positive effect of Fame_dtemp','T', ['N1*bf(2)','N2*bf(2)','F1*bf(2)','F2*bf(2)'],[1,1,-1,-1])
fam3 = ('positive effect of Fame_ddisp','T', ['N1*bf(3)','N2*bf(3)','F1*bf(3)','F2*bf(3)'],[1,1,-1,-1])
# rep1 > rep2
rep1 = ('positive effect of Rep','T', ['N1*bf(1)','N2*bf(1)','F1*bf(1)','F2*bf(1)'],[1,-1,1,-1])
rep2 = ('positive effect of Rep_dtemp','T', ['N1*bf(2)','N2*bf(2)','F1*bf(2)','F2*bf(2)'],[1,-1,1,-1])
rep3 = ('positive effect of Rep_ddisp','T', ['N1*bf(3)','N2*bf(3)','F1*bf(3)','F2*bf(3)'],[1,-1,1,-1])
int1 = ('positive interaction of Fame x Rep','T', ['N1*bf(1)','N2*bf(1)','F1*bf(1)','F2*bf(1)'],[-1,-1,-1,1])
int2 = ('positive interaction of Fame x Rep_dtemp','T', ['N1*bf(2)','N2*bf(2)','F1*bf(2)','F2*bf(2)'],[1,-1,-1,1])
int3 = ('positive interaction of Fame x Rep_ddisp','T', ['N1*bf(3)','N2*bf(3)','F1*bf(3)','F2*bf(3)'],[1,-1,-1,1])

contf1 = ['average effect condition','F', [cond1, cond2, cond3]]
contf2 = ['main effect Fam', 'F', [fam1, fam2, fam3]]
contf3 = ['main effect Rep', 'F', [rep1, rep2, rep3]]
contf4 = ['interaction: Fam x Rep', 'F', [int1, int2, int3]]
contrasts = [cond1, cond2, cond3, fam1, fam2, fam3, rep1, rep2, rep3, int1, int2, int3, contf1, contf2,contf3,contf4]

"""Setting up nodes inputs
"""

num_slices = 24
TR = 2.

slice_timingref = l1pipeline.inputs.preproc.slice_timing
slice_timingref.num_slices = num_slices
slice_timingref.time_repetition = TR
slice_timingref.time_acquisition = TR - TR/float(num_slices)
slice_timingref.slice_order = range(num_slices,0,-1)
slice_timingref.ref_slice = num_slices/2

l1pipeline.inputs.preproc.smooth.fwhm = [8, 8, 8]

# set up node specific inputs
modelspecref = l1pipeline.inputs.analysis.modelspec
modelspecref.input_units             = 'scans'
modelspecref.output_units            = 'scans'
modelspecref.time_repetition         = TR
modelspecref.high_pass_filter_cutoff = 120

l1designref = l1pipeline.inputs.analysis.level1design
l1designref.timing_units       = modelspecref.output_units
l1designref.interscan_interval = modelspecref.time_repetition
l1designref.microtime_resolution = slice_timingref.num_slices
l1designref.microtime_onset = slice_timingref.ref_slice
l1designref.bases = {'hrf':{'derivs': [1,1]}}

"""
The following lines automatically inform SPM to create a default set of
contrats for a factorial design.
"""

#l1designref.factor_info = [dict(name = 'Fame', levels = 2),
#                           dict(name = 'Rep', levels = 2)]

l1pipeline.inputs.analysis.modelspec.subject_info = subjectinfo
l1pipeline.inputs.analysis.contrastestimate.contrasts = contrasts
l1pipeline.inputs.analysis.threshold.contrast_index = 1

"""
Use derivative estimates in the non-parametric model
"""

l1pipeline.inputs.analysis.contrastestimate.use_derivs = True

"""
Setting up parametricvariation of the model
"""

subjectinfo_param = [Bunch(conditions=['N1', 'N2', 'F1', 'F2'],
                            onsets=[sot[0], sot[1], sot[2], sot[3]],
                            durations=[[0], [0], [0], [0]],
                            amplitudes=None,
                            tmod=None,
                            pmod=[None,
                                  Bunch(name=['Lag'],
                                        param=itemlag[1].tolist(),
                                        poly=[2]),
                                  None,
                                  Bunch(name=['Lag'],
                                        param=itemlag[3].tolist(),
                                        poly=[2])],
                            regressor_names=None,
                            regressors=None)]

cont1 = ('Famous_lag1','T', ['F2xLag^1'],[1])
cont2 = ('Famous_lag2','T', ['F2xLag^2'],[1])
fcont1 = ('Famous Lag', 'F', [cont1, cont2])
paramcontrasts = [cont1, cont2, fcont1]

paramanalysis = l1analysis.clone(name='paramanalysis')

paramanalysis.inputs.level1design.bases = {'hrf':{'derivs': [0,0]}}
paramanalysis.inputs.modelspec.subject_info = subjectinfo_param
paramanalysis.inputs.contrastestimate.contrasts = paramcontrasts
paramanalysis.inputs.contrastestimate.use_derivs = False

l1pipeline.connect([(preproc, paramanalysis, [('realign.realignment_parameters',
                                            'modelspec.realignment_parameters'),
                                            (('smooth.smoothed_files',makelist),
                                                'modelspec.functional_runs')])])

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
level1.base_dir = os.path.abspath('spm_face_tutorial/workingdir')

level1.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                (datasource,l1pipeline,[('struct', 'preproc.coregister.source'),
                                        ('func','preproc.realign.in_files')])
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
datasink.inputs.base_directory = os.path.abspath('spm_auditory_tutorial/l1output')

def getstripdir(subject_id):
    import os
    return os.path.join(os.path.abspath('spm_auditory_tutorial/workingdir'),'_subject_id_%s' % subject_id)

# store relevant outputs from various stages of the 1st level analysis
level1.connect([(infosource, datasink,[('subject_id','container'),
                                       (('subject_id', getstripdir),'strip_dir')]),
                (l1pipeline, datasink,[('analysis.contrastestimate.con_images','contrasts.@con'),
                                       ('analysis.contrastestimate.spmT_images','contrasts.@T'),
                                       ('paramanalysis.contrastestimate.con_images','paramcontrasts.@con'),
                                       ('paramanalysis.contrastestimate.spmT_images','paramcontrasts.@T')]),
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

