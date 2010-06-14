"""
A workflow that uses fsl to perform a first level analysis on the nipype
tutorial data set::

python fsl_tutorial2.py


First tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.modelgen as model   # model generation
import os                                    # system functions


"""
Preliminaries
-------------

Confirm package dependencies are installed.  (This is only for the tutorial,
rarely would you put this in your own code.)
"""

from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')

"""
Setup any package specific configuration. The output file format for FSL
routines is being set to compressed NIFTI.
"""

fsl.FSLCommand.set_default_output_type('NIFTI_GZ')

"""
Setting up workflows
--------------------

In this tutorial we will be setting up a hierarchical workflow for fsl
analysis. This will demonstrate how pre-defined workflows can be setup
and shared across users, projects and labs.


Setup preprocessing workflow
----------------------------

This is a generic fsl preprocessing workflow encompassing skull stripping,
motion correction and smoothing operations.

"""

preproc = pe.Workflow(name='preproc')

extract_ref = pe.Node(interface=fsl.ExtractROI(t_min=42,
                                               t_size=1),
                      name = 'extractref')

# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = pe.Node(interface=fsl.BET(mask = True,
                                       frac = 0.34),
                     name = 'stripstruct')

refskullstrip = pe.Node(interface=fsl.BET(mask = True,
                                       frac = 0.34),
                     name = 'stripref')

coregister = pe.Node(interface=fsl.FLIRT(dof=6),
                     name = 'coregister')

# Preprocess functionals
motion_correct = pe.MapNode(interface=fsl.MCFLIRT(save_plots = True),
                            name='realign',
                            iterfield = ['in_file'])

func_skullstrip = pe.MapNode(interface=fsl.BET(functional = True),
                             name='stripfunc',
                             iterfield = ['in_file'])


# Finally do some smoothing!

smoothing = pe.MapNode(interface=fsl.Smooth(),
                       name="smooth",
                       iterfield = ['in_file'])

inorm = pe.MapNode(interface = fsl.ImageMaths(op_string = '-inm 10000',
                                              suffix = '_inm',
                                              out_data_type = 'float'),
                       name = 'inorm',
                       iterfield = ['in_file'])

hpfilter = pe.MapNode(interface=fsl.ImageMaths(),
                      name='highpass',
                      iterfield = ['in_file'])

preproc.add_nodes([extract_ref, skullstrip])
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
modelspec.inputs.concatenate_runs = False

"""
   d. Use :class:`nipype.interfaces.fsl.Level1Design` to generate a
   run specific fsf file for analysis
"""

level1design = pe.Node(interface=fsl.Level1Design(), name="level1design")

"""
   e. Use :class:`nipype.interfaces.fsl.FEATModel` to generate a
   run specific mat file for use by FILMGLS
"""

modelgen = pe.MapNode(interface=fsl.FEATModel(), name='modelgen',
                      iterfield = ['fsf_file'])

"""
   f. Use :class:`nipype.interfaces.fsl.FILMGLS` to estimate a model
   specified by a mat file and a functional run
"""

modelestimate = pe.MapNode(interface=fsl.FILMGLS(), name='modelestimate',
                           iterfield = ['design_file','in_file'])

"""
   f. Use :class:`nipype.interfaces.fsl.ContrastMgr` to generate contrast
   estimates
"""

conestimate = pe.MapNode(interface=fsl.ContrastMgr(), name='conestimate',
                         iterfield = ['tcon_file','stats_dir'])

modelfit.connect([
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files','fsf_file')]),
   (modelgen,modelestimate,[('design_file','design_file')]),
   (modelgen,conestimate,[('con_file','tcon_file')]),
   (modelestimate,conestimate,[('results_dir','stats_dir')]),
   ])

"""
Set up fixed-effects workflow
-----------------------------

"""

fixed_fx = pe.Workflow(name='fixedfx')

# Use :class:`nipype.interfaces.fsl.Merge` to merge the copes and
# varcopes for each condition
copemerge    = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="copemerge")

varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['in_files'],
                       name="varcopemerge")


# Use :class:`nipype.interfaces.fsl.L2Model` to generate subject and
# condition specific level 2 model design files
level2model = pe.Node(interface=fsl.L2Model(),
                      name='l2model')

"""
Use :class:`nipype.interfaces.fsl.FLAMEO` to estimate a second level
model
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
#firstlevel.add_nodes([preproc])
firstlevel.connect([(preproc, modelfit, [('highpass.out_file', 'modelspec.functional_runs')]),
                    (preproc, fixed_fx, [('coregister.out_file', 'flameo.mask_file')]),
                    (modelfit, fixed_fx,[(('conestimate.copes', sort_copes),'copemerge.in_files'),
                                         (('conestimate.varcopes', sort_copes),'varcopemerge.in_files'),
                                         (('conestimate.copes', num_copes),'l2model.num_copes'),
                                         ])
                    ])


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
subject_list = ['s1', 's3']
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

"""
Use the get_node function to retrieve an internal node by name.
"""

smoothnode = firstlevel.get_node('preproc.smooth')
assert(str(smoothnode)=='smooth')
smoothnode.iterables = ('fwhm', [5,10])

firstlevel.inputs.preproc.smooth.fwhm = 5
hpcutoff = 120
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
cont3 = ['Task','F', [cont1, cont2]]
contrasts = [cont1,cont2]

firstlevel.inputs.modelfit.modelspec.input_units = 'secs'
firstlevel.inputs.modelfit.modelspec.output_units = 'secs'
firstlevel.inputs.modelfit.modelspec.time_repetition = TR
firstlevel.inputs.modelfit.modelspec.high_pass_filter_cutoff = hpcutoff


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
l1pipeline.base_dir = os.path.abspath('./fsl/workingdir')


def pickfirst(files):
    return files[0]

l1pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                    (infosource, firstlevel, [(('subject_id', subjectinfo), 'modelfit.modelspec.subject_info')]),
                    (datasource, firstlevel, [('struct','preproc.stripstruct.in_file'),
                                              ('func', 'preproc.realign.in_file'),
                                              (('func', pickfirst), 'preproc.extractref.in_file'),
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
    l1pipeline.write_graph(graph2use='flat')


