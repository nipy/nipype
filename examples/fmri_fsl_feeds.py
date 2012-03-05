#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
=================
fMRI: FEEDS - FSL
=================

A pipeline example that data from the FSL FEEDS set. Single subject, two
stimuli.

You can find it at http://www.fmrib.ox.ac.uk/fsl/feeds/doc/index.html

"""

import os                                    # system functions

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation


"""
Preliminaries
-------------

Setup any package specific configuration. The output file format for FSL
routines is being set to compressed NIFTI.
"""

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

"""
Setting up workflows
--------------------

In this tutorial we will be setting up a hierarchical workflow for fsl
analysis. This will demonstrate how pre-defined workflows can be setup and
shared across users, projects and labs.


Setup preprocessing workflow
----------------------------

This is a generic fsl feat preprocessing workflow encompassing skull stripping,
motion correction and smoothing operations.

"""

preproc = pe.Workflow(name='preproc')

"""
Set up a node to define all inputs required for the preprocessing workflow
"""

inputnode = pe.Node(interface=util.IdentityInterface(fields=['func',
                                                             'struct',]),
                    name='inputspec')

"""
Convert functional images to float representation. Since there can be more than
one functional run we use a MapNode to convert each run.
"""

img2float = pe.MapNode(interface=fsl.ImageMaths(out_data_type='float',
                                             op_string = '',
                                             suffix='_dtype'),
                       iterfield=['in_file'],
                       name='img2float')
preproc.connect(inputnode, 'func', img2float, 'in_file')

"""
Extract the middle volume of the first run as the reference
"""

extract_ref = pe.Node(interface=fsl.ExtractROI(t_size=1),
                      name = 'extractref')

"""
Define a function to pick the first file from a list of files
"""

def pickfirst(files):
    if isinstance(files, list):
        return files[0]
    else:
        return files

preproc.connect(img2float, ('out_file', pickfirst), extract_ref, 'in_file')

"""
Define a function to return the 1 based index of the middle volume
"""

def getmiddlevolume(func):
    from nibabel import load
    funcfile = func
    if isinstance(func, list):
        funcfile = func[0]
    _,_,_,timepoints = load(funcfile).get_shape()
    return (timepoints/2)-1

preproc.connect(inputnode, ('func', getmiddlevolume), extract_ref, 't_min')

"""
Realign the functional runs to the middle volume of the first run
"""

motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_mats = True,
                                                  save_plots = True),
                            name='realign',
                            iterfield = ['in_file'])
preproc.connect(img2float, 'out_file', motion_correct, 'in_file')
preproc.connect(extract_ref, 'roi_file', motion_correct, 'ref_file')

"""
Extract the mean volume of the first functional run
"""

meanfunc = pe.Node(interface=fsl.ImageMaths(op_string = '-Tmean',
                                            suffix='_mean'),
                   name='meanfunc')
preproc.connect(motion_correct, ('out_file', pickfirst), meanfunc, 'in_file')

"""
Strip the skull from the mean functional to generate a mask
"""

meanfuncmask = pe.Node(interface=fsl.BET(mask = True,
                                         no_output=True,
                                         frac = 0.3),
                       name = 'meanfuncmask')
preproc.connect(meanfunc, 'out_file', meanfuncmask, 'in_file')

"""
Mask the functional runs with the extracted mask
"""

maskfunc = pe.MapNode(interface=fsl.ImageMaths(suffix='_bet',
                                               op_string='-mas'),
                      iterfield=['in_file'],
                      name = 'maskfunc')
preproc.connect(motion_correct, 'out_file', maskfunc, 'in_file')
preproc.connect(meanfuncmask, 'mask_file', maskfunc, 'in_file2')


"""
Determine the 2nd and 98th percentile intensities of each functional run
"""

getthresh = pe.MapNode(interface=fsl.ImageStats(op_string='-p 2 -p 98'),
                       iterfield = ['in_file'],
                       name='getthreshold')
preproc.connect(maskfunc, 'out_file', getthresh, 'in_file')


"""
Threshold the first run of the functional data at 10% of the 98th percentile
"""

threshold = pe.Node(interface=fsl.ImageMaths(out_data_type='char',
                                             suffix='_thresh'),
                       name='threshold')
preproc.connect(maskfunc, ('out_file', pickfirst), threshold, 'in_file')

"""
Define a function to get 10% of the intensity
"""

def getthreshop(thresh):
    return '-thr %.10f -Tmin -bin'%(0.1*thresh[0][1])
preproc.connect(getthresh, ('out_stat', getthreshop), threshold, 'op_string')

"""
Determine the median value of the functional runs using the mask
"""

medianval = pe.MapNode(interface=fsl.ImageStats(op_string='-k %s -p 50'),
                       iterfield = ['in_file'],
                       name='medianval')
preproc.connect(motion_correct, 'out_file', medianval, 'in_file')
preproc.connect(threshold, 'out_file', medianval, 'mask_file')

"""
Dilate the mask
"""

dilatemask = pe.Node(interface=fsl.ImageMaths(suffix='_dil',
                                              op_string='-dilF'),
                       name='dilatemask')
preproc.connect(threshold, 'out_file', dilatemask, 'in_file')

"""
Mask the motion corrected functional runs with the dilated mask
"""

maskfunc2 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                op_string='-mas'),
                      iterfield=['in_file'],
                      name='maskfunc2')
preproc.connect(motion_correct, 'out_file', maskfunc2, 'in_file')
preproc.connect(dilatemask, 'out_file', maskfunc2, 'in_file2')

"""
Determine the mean image from each functional run
"""

meanfunc2 = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                suffix='_mean'),
                       iterfield=['in_file'],
                       name='meanfunc2')
preproc.connect(maskfunc2, 'out_file', meanfunc2, 'in_file')

"""
Merge the median values with the mean functional images into a coupled list
"""

mergenode = pe.Node(interface=util.Merge(2, axis='hstack'),
                    name='merge')
preproc.connect(meanfunc2,'out_file', mergenode, 'in1')
preproc.connect(medianval,'out_stat', mergenode, 'in2')


"""
Smooth each run using SUSAN with the brightness threshold set to 75% of the
median value for each run and a mask consituting the mean functional
"""

smooth = pe.MapNode(interface=fsl.SUSAN(),
                    iterfield=['in_file', 'brightness_threshold','usans'],
                    name='smooth')

"""
Define a function to get the brightness threshold for SUSAN
"""

def getbtthresh(medianvals):
    return [0.75*val for val in medianvals]

def convert_th(x):
    return [[tuple([val[0],0.75*val[1]])] for val in x]

preproc.connect(maskfunc2, 'out_file', smooth, 'in_file')
preproc.connect(medianval, ('out_stat', getbtthresh), smooth, 'brightness_threshold')
preproc.connect(mergenode, ('out', convert_th), smooth, 'usans')

"""
Mask the smoothed data with the dilated mask
"""

maskfunc3 = pe.MapNode(interface=fsl.ImageMaths(suffix='_mask',
                                                op_string='-mas'),
                      iterfield=['in_file'],
                      name='maskfunc3')
preproc.connect(smooth, 'smoothed_file', maskfunc3, 'in_file')
preproc.connect(dilatemask, 'out_file', maskfunc3, 'in_file2')

"""
Scale each volume of the run so that the median value of the run is set to 10000
"""

intnorm = pe.MapNode(interface=fsl.ImageMaths(suffix='_intnorm'),
                      iterfield=['in_file','op_string'],
                      name='intnorm')
preproc.connect(maskfunc3, 'out_file', intnorm, 'in_file')

"""
Define a function to get the scaling factor for intensity normalization
"""

def getinormscale(medianvals):
    return ['-mul %.10f'%(10000./val) for val in medianvals]
preproc.connect(medianval, ('out_stat', getinormscale), intnorm, 'op_string')

"""
Perform temporal highpass filtering on the data
"""

highpass = pe.MapNode(interface=fsl.ImageMaths(suffix='_tempfilt'),
                      iterfield=['in_file'],
                      name='highpass')
preproc.connect(intnorm, 'out_file', highpass, 'in_file')

"""
Generate a mean functional image from the first run
"""

meanfunc3 = pe.MapNode(interface=fsl.ImageMaths(op_string='-Tmean',
                                                suffix='_mean'),
                       iterfield=['in_file'],
                      name='meanfunc3')
preproc.connect(highpass, ('out_file', pickfirst), meanfunc3, 'in_file')

"""
Strip the structural image a coregister the mean functional image to the
structural image
"""

nosestrip = pe.Node(interface=fsl.BET(frac=0.3),
                    name = 'nosestrip')
skullstrip = pe.Node(interface=fsl.BET(mask = True),
                     name = 'stripstruct')

coregister = pe.Node(interface=fsl.FLIRT(dof=6),
                     name = 'coregister')

preproc.connect([(inputnode, nosestrip,[('struct','in_file')]),
                 (nosestrip, skullstrip, [('out_file','in_file')]),
                 (skullstrip, coregister,[('out_file','in_file')]),
                 (meanfunc2, coregister,[(('out_file',pickfirst),'reference')]),
                 ])

"""
Set up model fitting workflow
-----------------------------

"""

modelfit = pe.Workflow(name='modelfit')

"""
Use :class:`nipype.algorithms.modelgen.SpecifyModel` to generate design information.
"""

modelspec = pe.Node(interface=model.SpecifyModel(),  name="modelspec")

"""
Use :class:`nipype.interfaces.fsl.Level1Design` to generate a run specific fsf
file for analysis
"""

level1design = pe.Node(interface=fsl.Level1Design(), name="level1design")

"""
Use :class:`nipype.interfaces.fsl.FEATModel` to generate a run specific mat
file for use by FILMGLS
"""

modelgen = pe.MapNode(interface=fsl.FEATModel(), name='modelgen',
                      iterfield = ['fsf_file', 'ev_files'])

"""
Use :class:`nipype.interfaces.fsl.FILMGLS` to estimate a model specified by a
mat file and a functional run
"""

modelestimate = pe.MapNode(interface=fsl.FILMGLS(smooth_autocorr=True,
                                                 mask_size=5,
                                                 threshold=1000),
                           name='modelestimate',
                           iterfield = ['design_file','in_file'])

"""
Use :class:`nipype.interfaces.fsl.ContrastMgr` to generate contrast estimates
"""

conestimate = pe.MapNode(interface=fsl.ContrastMgr(), name='conestimate',
                         iterfield = ['fcon_file', 'tcon_file','param_estimates',
                                      'sigmasquareds', 'corrections',
                                      'dof_file'])

modelfit.connect([
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files','fsf_file'),
                           ('ev_files', 'ev_files')]),
   (modelgen,modelestimate,[('design_file','design_file')]),
   (modelgen,conestimate,[('con_file','tcon_file')]),
   (modelgen,conestimate,[('fcon_file','fcon_file')]),
   (modelestimate,conestimate,[('param_estimates','param_estimates'),
                               ('sigmasquareds', 'sigmasquareds'),
                               ('corrections','corrections'),
                               ('dof_file','dof_file')]),
   ])

"""
Set up fixed-effects workflow
-----------------------------

"""

fixed_fx = pe.Workflow(name='fixedfx')

"""
Use :class:`nipype.interfaces.fsl.Merge` to merge the copes and
varcopes for each condition
"""

copemerge    = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="copemerge")

varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="varcopemerge")

"""
Use :class:`nipype.interfaces.fsl.L2Model` to generate subject and condition
specific level 2 model design files
"""

level2model = pe.Node(interface=fsl.L2Model(),
                      name='l2model')

"""
Use :class:`nipype.interfaces.fsl.FLAMEO` to estimate a second level model
"""

flameo = pe.MapNode(interface=fsl.FLAMEO(run_mode='fe'), name="flameo",
                    iterfield=['cope_file','var_cope_file'])

fixed_fx.connect([(copemerge,flameo,[('merged_file','cope_file')]),
                  (varcopemerge,flameo,[('merged_file','var_cope_file')]),
                  (level2model,flameo, [('design_mat','design_file'),
                                        ('design_con','t_con_file'),
                                        ('design_grp','cov_split_file')]),
                  ])


"""
Set up first-level workflow
---------------------------

"""

def sort_copes(files):
    numelements = len(files[0])
    outfiles = []
    for i in range(numelements):
        outfiles.insert(i,[])
        for j, elements in enumerate(files):
            outfiles[i].append(elements[i])
    return outfiles

def num_copes(files):
    return len(files)

firstlevel = pe.Workflow(name='firstlevel')
firstlevel.connect([(preproc, modelfit, [('highpass.out_file', 'modelspec.functional_runs'),
                                         ('highpass.out_file','modelestimate.in_file')]),
                    (preproc, fixed_fx, [('coregister.out_file', 'flameo.mask_file')]),
                    (modelfit, fixed_fx,[(('conestimate.copes', sort_copes),'copemerge.in_files'),
                                         (('conestimate.varcopes', sort_copes),'varcopemerge.in_files'),
                                         (('conestimate.copes', num_copes),'l2model.num_copes'),
                                         ])
                    ])


"""
Experiment specific components
------------------------------

This tutorial does a single subject analysis so we are not using infosource and
iterables
"""

# Specify the location of the FEEDS data. You can find it at http://www.fmrib.ox.ac.uk/fsl/feeds/doc/index.html
feeds_data_dir = os.path.abspath('feeds_data')
# Specify the subject directories
# Map field names to individual subject runs.
info = dict(func=[['fmri']],
            struct=[['structural']])

"""
Now we create a :class:`nipype.interfaces.io.DataSource` object and fill in the
information from above about the layout of our data.  The
:class:`nipype.pipeline.Node` module wraps the interface object and provides
additional housekeeping and pipeline specific functionality.
"""

datasource = pe.Node(interface=nio.DataGrabber(outfields=['func', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = feeds_data_dir
datasource.inputs.template = '%s.nii.gz'
datasource.inputs.template_args = info

firstlevel.inputs.preproc.smooth.fwhm = 5

hpcutoff = 100
TR = 3.
firstlevel.inputs.preproc.highpass.suffix = '_hpf'
firstlevel.inputs.preproc.highpass.op_string = '-bptf %d -1'%(hpcutoff/TR)


"""
Setup a function that returns subject-specific information about the
experimental paradigm. This is used by the
:class:`nipype.interfaces.spm.SpecifyModel` to create the information necessary
to generate an SPM design matrix. In this tutorial, the same paradigm was used
for every participant. Other examples of this function are available in the
`doc/examples` folder. Note: Python knowledge required here.
"""

from nipype.interfaces.base import Bunch

firstlevel.inputs.modelfit.modelspec.subject_info = [Bunch(conditions=['Visual','Auditory'],
                        onsets=[range(0,int(180*TR),60),range(0,int(180*TR),90)],
                        durations=[[30], [45]],
                        amplitudes=None,
                        tmod=None,
                        pmod=None,
                        regressor_names=None,
                        regressors=None)]
"""
Setup the contrast structure that needs to be evaluated. This is a list of
lists. The inner list specifies the contrasts and has the following format -
[Name,Stat,[list of condition names],[weights on those conditions]. The
condition names must match the `names` listed in the `subjectinfo` function
described above.
"""

cont1 = ['Visual>Baseline','T', ['Visual','Auditory'],[1,0]]
cont2 = ['Auditory>Baseline','T', ['Visual','Auditory'],[0,1]]
cont3 = ['Task','F', [cont1, cont2]]
contrasts = [cont1,cont2,cont3]

model_serial_correlations = True

firstlevel.inputs.modelfit.modelspec.input_units = 'secs'
firstlevel.inputs.modelfit.modelspec.time_repetition = TR
firstlevel.inputs.modelfit.modelspec.high_pass_filter_cutoff = hpcutoff


firstlevel.inputs.modelfit.level1design.interscan_interval = TR
firstlevel.inputs.modelfit.level1design.bases = {'dgamma':{'derivs': True}}
firstlevel.inputs.modelfit.level1design.contrasts = contrasts
firstlevel.inputs.modelfit.level1design.model_serial_correlations = model_serial_correlations

"""
Set up complete workflow
========================
"""

l1pipeline = pe.Workflow(name= "level1")
l1pipeline.base_dir = os.path.abspath('./fsl_feeds/workingdir')
l1pipeline.config = dict(crashdump_dir=os.path.abspath('./fsl_feeds/crashdumps'))

l1pipeline.connect([(datasource, firstlevel, [('struct','preproc.inputspec.struct'),
                                              ('func', 'preproc.inputspec.func'),
                                              ]),
                    ])

"""
Setup the datasink
"""

datasink = pe.Node(interface=nio.DataSink(parameterization=False), name="datasink")
datasink.inputs.base_directory = os.path.abspath('./fsl_feeds/l1out')
datasink.inputs.substitutions = [('dtype_mcf_mask_mean', 'meanfunc'),
                                 ('brain_brain_flirt','coregistered')]
# store relevant outputs from various stages of the 1st level analysis
l1pipeline.connect([(firstlevel, datasink,[('fixedfx.flameo.stats_dir',"fixedfx.@con"),
                                            ('preproc.coregister.out_file','coregstruct'),
                                            ('preproc.meanfunc2.out_file','meanfunc'),
                                            ('modelfit.conestimate.zstats', 'level1.@Z'),
                                            ])
                    ])


"""
Execute the pipeline
--------------------

The code discussed above sets up all the necessary data structures with
appropriate parameters and the connectivity between the processes, but does not
generate any output. To actually run the analysis on the data the
``nipype.pipeline.engine.Pipeline.Run`` function needs to be called.
"""

if __name__ == '__main__':
    l1pipeline.run()
#    l2pipeline.run()

