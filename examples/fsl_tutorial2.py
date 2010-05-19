"""
   A pipeline example that uses intergrates several interfaces to
   perform a first and second level analysis on a two-subject data
   set. 
"""


"""
1. Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility 
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
fsl.FSLCommand.set_default_outputtype('NIFTI_GZ')


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

extract_ref = pe.Node(interface=fsl.ExtractRoi(tmin=42,
                                               tsize=1),
                      name = 'extractref')

# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = pe.Node(interface=fsl.Bet(mask = True,
                                       frac = 0.34),
                     name = 'stripstruct')

refskullstrip = pe.Node(interface=fsl.Bet(mask = True,
                                       frac = 0.34),
                     name = 'stripref')

coregister = pe.Node(interface=fsl.Flirt(dof=6),
                     name = 'coregister')

# Preprocess functionals
motion_correct = pe.MapNode(interface=fsl.McFlirt(saveplots = True),
                            name='realign',
                            iterfield = ['infile'])

func_skullstrip = pe.MapNode(interface=fsl.Bet(functional = True),
                             name='stripfunc',
                             iterfield = ['infile'])


# Finally do some smoothing!

smoothing = pe.MapNode(interface=fsl.Smooth(),
                       name="smooth",
                       iterfield = ['infile'])

inorm = pe.MapNode(interface = fsl.ImageMaths(optstring = '-inm 10000',
                                              suffix = '_inm',
                                              outdatatype = 'float'),
                       name = 'inorm',
                       iterfield = ['infile'])

hpfilter = pe.MapNode(interface=fsl.ImageMaths(),
                      name='highpass',
                      iterfield = ['infile'])

preproc.add_nodes([extract_ref, skullstrip])
preproc.connect([(extract_ref, motion_correct,[('outfile', 'reffile')]),
                 (extract_ref, refskullstrip,[('outfile', 'infile')]),
                 (skullstrip, coregister,[('maskfile','infile')]),
                 (refskullstrip, coregister,[('outfile','reference')]),
                 (motion_correct, func_skullstrip, [('outfile', 'infile')]),
                 (func_skullstrip, smoothing, [('outfile', 'infile')]),
                 (smoothing,inorm,[('smoothedimage','infile')]),
                 (inorm,hpfilter,[('outfile','infile')]),
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
                           iterfield = ['design_file','infile'])

"""
   f. Use :class:`nipype.interfaces.fsl.ContrastMgr` to generate contrast
   estimates 
"""
conestimate = pe.MapNode(interface=fsl.ContrastMgr(), name='conestimate',
                         iterfield = ['tcon_file','stats_dir'])

modelfit.connect([
   (modelspec,level1design,[('session_info','session_info')]),
   (level1design,modelgen,[('fsf_files','fsf_file')]),
   (modelgen,modelestimate,[('designfile','design_file')]),
   (modelgen,conestimate,[('confile','tcon_file')]),
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
                       iterfield=['infiles'],
                       name="copemerge")

varcopemerge = pe.MapNode(interface=fsl.Merge(dimension='t'),
                       iterfield=['infiles'],
                       name="varcopemerge")


# Use :class:`nipype.interfaces.fsl.L2Model` to generate subject and
# condition specific level 2 model design files
level2model = pe.Node(interface=fsl.L2Model(),
                      name='l2model')

"""
Use :class:`nipype.interfaces.fsl.FLAMEO` to estimate a second level
model
"""
flameo = pe.MapNode(interface=fsl.FLAMEO(runmode='fe'), name="flameo",
                    iterfield=['copefile','varcopefile'])

fixed_fx.connect([(copemerge,flameo,[('outfile','copefile')]),
                  (varcopemerge,flameo,[('outfile','varcopefile')]),
                  (level2model,flameo, [('design_mat','designfile'),
                                        ('design_con','tconfile'),
                                        ('design_grp','covsplitfile')]),
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
firstlevel.connect([(preproc, modelfit, [('highpass.outfile', 'modelspec.functional_runs')]),
                    (preproc, fixed_fx, [('coregister.outfile', 'flameo.maskfile')]),
                    (modelfit, fixed_fx,[(('conestimate.cope_files', sort_copes),'copemerge.infiles'),
                                         (('conestimate.varcope_files', sort_copes),'varcopemerge.infiles'),
                                         (('conestimate.cope_files', num_copes),'l2model.num_copes'),
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


firstlevel.inputs.preproc.smooth.fwhm = 5
hpcutoff = 120
TR = 3.
firstlevel.inputs.preproc.highpass.suffix = '_hpf'
firstlevel.inputs.preproc.highpass.optstring = '-bptf %d -1'%(hpcutoff/TR)


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
                    (datasource, firstlevel, [('struct','preproc.stripstruct.infile'),
                                              ('func', 'preproc.realign.infile'),
                                              (('func', pickfirst), 'preproc.extractref.infile'),
                                              ('func', 'modelfit.modelestimate.infile')
                                              ]),
                    ])

'''





##########################
# Setup storage of results
##########################

datasink = pe.Node(interface=nio.DataSink(), name="datasink")
# I'd like this one to actually be preproc, but for now, I don't want to change
# the pipeline around because of data already being on S3
datasink.inputs.base_directory = os.path.abspath('./fsl/l1output')

#####################
# Set up l1pipeline pype
#####################

l1pipeline = pe.Workflow(name= "level1")
l1pipeline.base_dir = os.path.abspath('./fsl/workingdir')

def pickfirst(files):
    return files[0]

l1pipeline.connect([# preprocessing in native space
                    (infosource, datasource, [('subject_id', 'subject_id')]),
                 (datasource, skullstrip, [('struct','infile')]),
                 (datasource, motion_correct, [('func', 'infile')]),
                 (datasource, extract_ref, [(('func', pickfirst), 'infile')]),
                 (extract_ref, motion_correct,[('outfile', 'reffile')]),
                 (motion_correct, func_skullstrip, [('outfile', 'infile')]),
                 # Smooth :\
                 (func_skullstrip, smoothing, [('outfile', 'infile')]),
                 #(smoothing,inorm,[('smoothedimage','infile')]),
                 #(inorm,hpfilter,[('outfile','infile')]),
                 (smoothing,hpfilter,[('smoothedimage','infile')]),
                 # Model design
                 (hpfilter,modelspec,[('outfile','functional_runs')]),
                 (infosource,modelspec,[('subject_id','subject_id'),
                                        (('subject_id',subjectinfo),'subject_info')]),
                 (motion_correct,modelspec,[('parfile','realignment_parameters')]),
                 (modelspec,level1design,[('session_info','session_info')]),
                 (level1design,featmodel,[('fsf_files','fsf_file')]),
                ])

# store relevant outputs from various stages of preprocessing
l1pipeline.connect([(infosource,datasink,[('subject_id','subject_id')]),
                    (skullstrip, datasink, 
                        [('outfile', 'skullstrip.@outfile')]),
                    (func_skullstrip, datasink,
                        [('outfile', 'skullstrip.@outfile')]),
                    (motion_correct, datasink,
                        [('parfile', 'skullstrip.@parfile')]),
                    (smoothing, datasink, 
                        [('smoothedimage', 'registration.@outfile')]),
                    ])
"""
                    (featfemodel, datasink, 
                        [('featdir', 'modelestimate.@fixedeffects')]),
"""


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
'''
