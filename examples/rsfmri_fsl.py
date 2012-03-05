#!/usr/bin/env python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
===========================
rsfMRI: FSL - CSF regressed
===========================

A pipeline example that uses intergrates several interfaces to
perform a first and second level analysis on a two-subject data
set.


1. Tell python where to find the appropriate functions.
"""

import numpy as np

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation
import os                                    # system functions

#####################################################################
# Preliminaries

"""
2. Setup any package specific configuration. The output file format
   for FSL routines is being set to uncompressed NIFTI and a specific
   version of matlab is being used. The uncompressed format is
   required because SPM does not handle compressed NIFTI.
"""

# Tell fsl to generate all output in compressed nifti format
print fsl.Info.version()
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


extract_ref = pe.Node(interface=fsl.ExtractROI(t_min=42,
                                               t_size=1),
                      name = 'extractref')

# run FSL's bet
# bet my_structural my_betted_structural
"""
in the provided data set, the nose is behind the head and causes problems for
segmentation routines
"""

nosestrip = pe.Node(interface=fsl.BET(frac=0.3),
                    name = 'nosestrip')
skullstrip = pe.Node(interface=fsl.BET(mask = True),
                     name = 'stripstruct')

refskullstrip = pe.Node(interface=fsl.BET(mask = True),
                        name = 'stripref')

coregister = pe.Node(interface=fsl.FLIRT(dof=6),
                     name = 'coregister')

# Preprocess functionals
motion_correct = pe.Node(interface=fsl.MCFLIRT(save_plots = True),
                         name='realign')
                            #iterfield = ['in_file'])

"""
skull strip functional data
"""

func_skullstrip = pe.Node(interface=fsl.BET(functional = True),
                          name='stripfunc')
                             #iterfield = ['in_file'])

"""
Run FAST on T1 anatomical image to obtain CSF mask.
Create mask for three tissue types.
"""

getCSFmasks = pe.Node(interface=fsl.FAST(no_pve=True,segments=True),
                      name = 'segment')

"""
Apply registration matrix to CSF segmentation mask.
"""

applyReg2CSFmask = pe.Node(interface=fsl.ApplyXfm(apply_xfm=True),
                           name = 'applyreg2csfmask')

"""
Threshold CSF segmentation mask from  .90 to 1
"""

threshCSFseg = pe.Node(interface = fsl.ImageMaths(op_string = ' -thr .90 -uthr 1 -bin '),
                       name = 'threshcsfsegmask')

"""
Extract CSF timeseries
"""

avgCSF = pe.Node(interface = fsl.ImageMeants(), name='extractcsfts')


def pickfirst(files):
    return files[0]


"""
Create the workflow
"""

csffilter = pe.Workflow(name='csffilter')
csffilter.connect([(extract_ref, motion_correct,[('roi_file', 'ref_file')]),
                   (extract_ref, refskullstrip,[('roi_file', 'in_file')]),
                   (nosestrip, skullstrip, [('out_file','in_file')]),
                   (skullstrip, getCSFmasks,[('out_file','in_files')]),
                   (skullstrip, coregister,[('mask_file','in_file')]),
                   (refskullstrip, coregister,[('out_file','reference')]),
                   (motion_correct, func_skullstrip, [('out_file', 'in_file')]),
                   (getCSFmasks, applyReg2CSFmask,[(('tissue_class_files',pickfirst),'in_file')]),
                   (refskullstrip, applyReg2CSFmask,[('out_file','reference')]),
                   (coregister, applyReg2CSFmask,[('out_matrix_file','in_matrix_file')]),
                   (applyReg2CSFmask,threshCSFseg,[('out_file','in_file')]),
                   (func_skullstrip,avgCSF,[('out_file','in_file')]),
                   (threshCSFseg,avgCSF,[('out_file','mask')]),
                   ])

modelfit = pe.Workflow(name='modelfit')

"""
   c. Use :class:`nipype.interfaces.spm.SpecifyModel` to generate
   SPM-specific design information.
"""

modelspec = pe.Node(interface=model.SpecifyModel(),  name="modelspec")

"""
   d. Use :class:`nipype.interfaces.fsl.Level1Design` to generate a
   run specific fsf file for analysis
"""

level1design = pe.Node(interface=fsl.Level1Design(), name="fsfdesign")

"""
   e. Use :class:`nipype.interfaces.fsl.FEATModel` to generate a
   run specific mat file for use by FILMGLS
"""

modelgen = pe.Node(interface=fsl.FEATModel(), name='modelgen')

"""
   f. Use :class:`nipype.interfaces.fsl.FILMGLS` to estimate a model
   specified by a mat file and a functional run
"""

modelestimate = pe.Node(interface=fsl.FILMGLS(), name='modelestimate')
                           #iterfield = ['design_file','in_file'])

modelfit.connect([(modelspec,level1design,[('session_info','session_info')]),
                  (level1design,modelgen,[('fsf_files','fsf_file'),
                                          ('ev_files', 'ev_files')]),
                  (modelgen,modelestimate,[('design_file','design_file')]),
                  ])

"""
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
subject_list = ['s1']
# Map field names to individual subject runs.
info = dict(func=[['subject_id', ['f3',]]], #'f5','f7','f10']]],
            struct=[['subject_id','struct']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")

"""
Here we set up iteration over all the subjects. The following line
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


"""
   a. Setup a function that returns subject-specific information about
   the experimental paradigm. This is used by the
   :class:`nipype.modelgen.SpecifyModel` to create the
   information necessary to generate an SPM design matrix. In this
   tutorial, the same paradigm was used for every participant. Other
   examples of this function are available in the `doc/examples`
   folder. Note: Python knowledge required here.
"""

def subjectinfo(meantsfile):
    import numpy as np
    from nipype.interfaces.base import Bunch
    ts = np.loadtxt(meantsfile)
    output = [Bunch(regressor_names=['MeanIntensity'],
                    regressors=[ts.tolist()])]
    return output

hpcutoff = np.inf
TR = 3.

modelfit.inputs.modelspec.input_units = 'secs'
modelfit.inputs.modelspec.time_repetition = TR
modelfit.inputs.modelspec.high_pass_filter_cutoff = hpcutoff


modelfit.inputs.fsfdesign.interscan_interval = TR
modelfit.inputs.fsfdesign.bases = {'none': None}
modelfit.inputs.fsfdesign.model_serial_correlations = False

modelfit.inputs.modelestimate.autocorr_noestimate = True


"""
Band pass filter the data to remove frequencies below .1 Hz
"""

bandPassFilterData = pe.Node(interface=fsl.ImageMaths(op_string = ' -bptf 128 12.5 '),
                             name='bandpassfiltermcdata_fslmaths')


"""
Set up complete workflow
========================
"""

l1pipeline = pe.Workflow(name= "resting")
l1pipeline.base_dir = os.path.abspath('./fslresting/workingdir')
l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                    (datasource, csffilter, [('struct','nosestrip.in_file'),
                                             ('func', 'realign.in_file'),
                                             #(('func', pickfirst), 'extractref.in_file'),
                                             ('func', 'extractref.in_file'),
                                              ]),
                    (csffilter, modelfit, [('stripfunc.out_file', 'modelspec.functional_runs'),
                                           ('realign.par_file', 'modelspec.realignment_parameters'),
                                           (('extractcsfts.out_file', subjectinfo),'modelspec.subject_info'),
                                           ('stripfunc.out_file', 'modelestimate.in_file')
                                           ]),
                    (modelfit, bandPassFilterData, [('modelestimate.residual4d', 'in_file')]),
                    ])

if __name__ == '__main__':
    l1pipeline.run()
    l1pipeline.write_graph()
