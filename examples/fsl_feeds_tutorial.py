"""
   A pipeline example that data from the FSL FEEDS set. Single subject, two stimuli.
"""


"""
1. Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation
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

# Tell fsl to generate all output in compressed nifti format
print fsl.Info.version()
fsl.FSLCommand.set_default_output_type('NIFTI_GZ')


"""
Setting up workflows
--------------------

In this tutorial we will be setting up a hierarchical workflow for spm
analysis. This will demonstrate how pre-defined workflows can be setup
and shared across users, projects and labs.


Setup preprocessing workflow
----------------------------

This is a generic fsl preprocessing workflow that can be used by different analyses

"""

preproc = pe.Workflow(name='preproc')

extract_ref = pe.Node(interface=fsl.ExtractROI(t_min=90,
                                               t_size=1),
                      name = 'extractref')

# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = pe.Node(interface=fsl.BET(mask = True,
                                       frac = 0.3),
                     name = 'stripstruct')

refskullstrip = pe.Node(interface=fsl.BET(mask = True,
                                       frac = 0.3),
                     name = 'stripref')

coregister = pe.Node(interface=fsl.FLIRT(dof=6),
                     name = 'coregister')

# Preprocess functionals
motion_correct = pe.Node(interface=fsl.MCFLIRT(save_plots = True),
                            name='realign')

func_skullstrip = pe.Node(interface=fsl.BET(functional = True),
                             name='stripfunc')


# Finally do some smoothing!

smoothing = pe.Node(interface=fsl.Smooth(),
                       name="smooth")

inorm = pe.Node(interface = fsl.ImageMaths(op_string = '-inm 10000',
                                              suffix = '_inm',
                                              out_data_type = 'float'),
                       name = 'inorm')

hpfilter = pe.Node(interface=fsl.ImageMaths(),
                      name='highpass')

preproc.connect([(extract_ref, motion_correct,[('roi_file', 'ref_file')]),
                 (extract_ref, refskullstrip,[('roi_file', 'in_file')]),
                 (skullstrip, coregister,[('mask_file','in_file')]),
                 (refskullstrip, coregister,[('out_file','reference')]),
                 (motion_correct, func_skullstrip, [('out_file', 'in_file')]),
                 (func_skullstrip, smoothing, [('out_file', 'in_file')]),
                 (smoothing,inorm,[('smoothed_file','in_file')]),
                 (inorm,hpfilter,[('out_file','in_file')]),
                 ])


"""
Set up model fitting workflow
-----------------------------

"""

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
level1design = pe.Node(interface=fsl.Level1Design(), name="level1design")

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

"""
   f. Use :class:`nipype.interfaces.fsl.ContrastMgr` to generate contrast
   estimates
"""
conestimate = pe.Node(interface=fsl.ContrastMgr(), name='conestimate')

modelfit.connect([
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files','fsf_file')]),
   (modelgen,modelestimate,[('design_file','design_file')]),
   (modelgen,conestimate,[('con_file','tcon_file')]),
   (modelestimate,conestimate,[('results_dir','stats_dir')]),
   ])

"""
Set up first-level workflow
---------------------------

"""

firstlevel = pe.Workflow(name='firstlevel')
firstlevel.connect([(preproc, modelfit, [('highpass.out_file', 'modelspec.functional_runs')])])


"""This tutorial does a single subject analysis so we are not using infosource and iterables
"""

# Specify the location of the FEEDS data. You can find it at http://www.fmrib.ox.ac.uk/fsl/feeds/doc/index.html
feeds_data_dir = '/home/filo/data/feeds/data'
# Specify the subject directories
# Map field names to individual subject runs.
info = dict(func=[['fmri']],
            struct=[['structural_brain']])

"""
Preprocessing pipeline nodes
----------------------------

Now we create a :class:`nipype.interfaces.io.DataSource` object and
fill in the information from above about the layout of our data.  The
:class:`nipype.pipeline.Node` module wraps the interface object
and provides additional housekeeping and pipeline specific
functionality.
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
   a. Setup a function that returns subject-specific information about
   the experimental paradigm. This is used by the
   :class:`nipype.interfaces.spm.SpecifyModel` to create the
   information necessary to generate an SPM design matrix. In this
   tutorial, the same paradigm was used for every participant. Other
   examples of this function are available in the `doc/examples`
   folder. Note: Python knowledge required here.
"""
from nipype.interfaces.base import Bunch

firstlevel.inputs.modelfit.modelspec.subject_info = [Bunch(conditions=['Visual','Auditory'],
                        onsets=[range(0,180*3,60),range(45,180*TR,90)],
                        durations=[[30], [45]],
                        amplitudes=None,
                        tmod=None,
                        pmod=None,
                        regressor_names=None,
                        regressors=None)]
"""
   b. Setup the contrast structure that needs to be evaluated. This is
   a list of lists. The inner list specifies the contrasts and has the
   following format - [Name,Stat,[list of condition names],[weights on
   those conditions]. The condition names must match the `names`
   listed in the `subjectinfo` function described above.
"""
cont1 = ['Visual>Baseline','T', ['Visual','Auditory'],[1,0]]
cont2 = ['Auditory>Baseline','T', ['Visual','Auditory'],[0,1]]
cont3 = ['Task','F', [cont1, cont2]]
contrasts = [cont1,cont2]

firstlevel.inputs.modelfit.modelspec.input_units = 'secs'
firstlevel.inputs.modelfit.modelspec.output_units = 'secs'
firstlevel.inputs.modelfit.modelspec.time_repetition = TR
firstlevel.inputs.modelfit.modelspec.high_pass_filter_cutoff = hpcutoff
firstlevel.inputs.modelfit.modelspec.subject_id = 'whatever'


firstlevel.inputs.modelfit.level1design.interscan_interval = TR
firstlevel.inputs.modelfit.level1design.bases = {'dgamma':{'derivs': True}}
firstlevel.inputs.modelfit.level1design.contrasts = contrasts
firstlevel.inputs.modelfit.level1design.register = True
firstlevel.inputs.modelfit.level1design.reg_image = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
firstlevel.inputs.modelfit.level1design.reg_dof = 12

"""
Set up complete workflow
========================
"""

l1pipeline = pe.Workflow(name= "level1")
l1pipeline.base_dir = os.path.abspath('./fsl_feeds/workingdir')


l1pipeline.connect([(datasource, firstlevel, [('struct','preproc.stripstruct.in_file'),
                                              ('func', 'preproc.realign.in_file'),
                                              ('func', 'preproc.extractref.in_file'),
                                              ('func', 'modelfit.modelestimate.in_file')
                                              ]),
                    ])


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
    l1pipeline.run()
#    l2pipeline.run()

