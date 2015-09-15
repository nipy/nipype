# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=====================
Workflow from scratch
=====================

"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model specification
from nipype.interfaces.base import Bunch
import os                                    # system functions


"""In the following section, to showcase NiPyPe, we will describe how to create
and extend a typical fMRI processing pipeline. We will begin with a basic
processing layout and follow with extending it by adding/exchanging different
components.

Most fMRI pipeline can be divided into two sections - preprocessing and
modelling. First one deals with cleaning data from confounds and noise and the
second one fits a model based on the experimental design. Preprocessing stage
in our first iteration of a pipeline will consist of only two steps:
realignment and smoothing. In NiPyPe Every processing step consist of an
Interface (which defines how to execute corresponding software) encapsulated
in a Node (which defines for example a unique name). For realignment (motion
correction achieved by coregistering all volumes to the mean) and smoothing
(convolution with 3D Gaussian kernel) we will use SPM implementation.
Definition of appropriate nodes can be found in Listing 1 (TODO). Inputs
(such as register_to_mean from listing 1) of nodes are accessible through the
inputs property. Upon setting any input its type is verified to avoid errors
during the execution."""

realign = pe.Node(interface=spm.Realign(), name="realign")
realign.inputs.register_to_mean = True

smooth = pe.Node(interface=spm.Smooth(), name="smooth")
smooth.inputs.fwhm = 4

"""To connect two nodes a Workflow has to be created. connect() method of a
Workflow allows to specify which outputs of which Nodes should be connected to
which inputs of which Nodes (see Listing 2). By connecting realigned_files
output of realign to in_files input of Smooth we have created a simple
preprocessing workflow (see Figure TODO)."""

preprocessing = pe.Workflow(name="preprocessing")
preprocessing.connect(realign, "realigned_files", smooth, "in_files")

"""Creating a modelling workflow which will define the design, estimate model
and contrasts follows the same suite. We will again use SPM implementations.
NiPyPe, however, adds extra abstraction layer to model definition which allows
using the same definition for many model estimation implemantations (for
example one from FSL or nippy). Therefore we will need four nodes:
SpecifyModel (NiPyPe specific abstraction layer), Level1Design (SPM design
definition), ModelEstimate, and ContrastEstimate. The connected modelling
Workflow can be seen on Figure TODO. Model specification supports block, event
and sparse designs. Contrasts provided to ContrastEstimate are defined using
the same names of regressors as defined in the SpecifyModel."""

specify_model = pe.Node(interface=model.SpecifyModel(), name="specify_model")
specify_model.inputs.input_units             = 'secs'
specify_model.inputs.time_repetition         = 3.
specify_model.inputs.high_pass_filter_cutoff = 120
specify_model.inputs.subject_info = [Bunch(conditions=['Task-Odd','Task-Even'],
                                           onsets=[range(15,240,60),
                                                   range(45,240,60)],
                                           durations=[[15], [15]])]*4

level1design = pe.Node(interface=spm.Level1Design(), name= "level1design")
level1design.inputs.bases = {'hrf':{'derivs': [0,0]}}
level1design.inputs.timing_units = 'secs'
level1design.inputs.interscan_interval = specify_model.inputs.time_repetition

level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
level1estimate.inputs.estimation_method = {'Classical' : 1}

contrastestimate = pe.Node(interface = spm.EstimateContrast(),
                           name="contrastestimate")
cont1 = ('Task>Baseline','T', ['Task-Odd','Task-Even'],[0.5,0.5])
cont2 = ('Task-Odd>Task-Even','T', ['Task-Odd','Task-Even'],[1,-1])
contrastestimate.inputs.contrasts = [cont1, cont2]

modelling = pe.Workflow(name="modelling")
modelling.connect(specify_model, 'session_info', level1design, 'session_info')
modelling.connect(level1design, 'spm_mat_file', level1estimate, 'spm_mat_file')
modelling.connect(level1estimate,'spm_mat_file',
                  contrastestimate,'spm_mat_file')
modelling.connect(level1estimate,'beta_images', contrastestimate,'beta_images')
modelling.connect(level1estimate,'residual_image',
                  contrastestimate,'residual_image')

"""Having preprocessing and modelling workflows we need to connect them
together, add data grabbing facility and save the results. For this we will
create a master Workflow which will host preprocessing and model Workflows as
well as DataGrabber and DataSink Nodes. NiPyPe allows connecting Nodes between
Workflows. We will use this feature to connect realignment_parameters and
smoothed_files to modelling workflow."""

main_workflow = pe.Workflow(name="main_workflow")
main_workflow.base_dir = "workflow_from_scratch"
main_workflow.connect(preprocessing, "realign.realignment_parameters",
                      modelling, "specify_model.realignment_parameters")
main_workflow.connect(preprocessing, "smooth.smoothed_files",
                      modelling, "specify_model.functional_runs")


"""DataGrabber allows to define flexible search patterns which can be
parameterized by user defined inputs (such as subject ID, session etc.).
This allows to adapt to a wide range of file layouts. In our case we will
parameterize it with subject ID. In this way we will be able to run it for
different subjects. We can automate this by iterating over a list of subject
Ids, by setting an iterables property on the subject_id input of DataGrabber.
Its output will be connected to realignment node from preprocessing workflow."""

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['func']),
                     name = 'datasource')
datasource.inputs.base_directory = os.path.abspath('data')
datasource.inputs.template = '%s/%s.nii'
datasource.inputs.template_args = dict(func=[['subject_id',
                                              ['f3','f5','f7','f10']]])
datasource.inputs.subject_id = 's1'
datasource.inputs.sort_filelist = True

main_workflow.connect(datasource, 'func', preprocessing, 'realign.in_files')

"""DataSink on the other side provides means to storing selected results to a
specified location. It supports automatic creation of folder stricter and
regular expression based substitutions. In this example we will store T maps."""

datasink = pe.Node(interface=nio.DataSink(), name="datasink")
datasink.inputs.base_directory = os.path.abspath('workflow_from_scratch/output')

main_workflow.connect(modelling, 'contrastestimate.spmT_images',
                      datasink, 'contrasts.@T')

main_workflow.run()
main_workflow.write_graph()
