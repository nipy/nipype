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
import nipype.interfaces.spm as spm          # spm
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
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

# Tell fsl to generate all output in uncompressed nifti format
print fsl.fsl_info.version
fsl.fsl_info.outputtype('NIFTI')


"""
3. The following lines of code sets up the necessary information
   required by the datasource module. It provides a mapping between
   run numbers (nifti files) and the mnemonic ('struct', 'func',
   etc.,.)  that particular run should be called. These mnemonics or
   fields become the output fields of the datasource module. In the
   example below, run 'f3' is of type 'func'. The 'f3' gets mapped to
   a nifti filename through a template '%s.nii'. So 'f3' would become
   'f3.nii'.
"""

# The following lines create some information about location of your
# data. 
data_dir = os.path.abspath('data')
subject_list = ['s1','s3']
# The following info structure helps the DataSource module organize
# nifti files into fields/attributes of a data object. With DataSource
# this object is of type Bunch.
info = {}
info['s1'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'),(['ref'],'func_ref'))
info['s3'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'),(['ref'],'func_ref'))

######################################################################
# Setup preprocessing pipeline nodes

"""
4. Setup various nodes for preprocessing the data. 
"""

"""
   a. Setting up an instance of the interface
   :class:`nipype.interfaces.io.DataSource`. This node looks into the
   directory containing Nifti files and returns pointers to the files
   in a structured format as determined by the field/attribute names
   provided in the info structure above. The
   :class:`nipype.pipeline.NodeWrapper` module wraps the interface
   object and provides additional housekeeping and pipeline specific
   functionality. 
"""
datasource = nw.NodeWrapper(interface=nio.DataSource())
datasource.inputs.base_directory   = data_dir
datasource.inputs.subject_template = '%s'
datasource.inputs.file_template    = '%s.nii'
datasource.inputs.subject_info     = info


"""
   b. Setting up iteration over all subjects. The following line is a
   particular example of the flexibility of the system.  The  variable
   `iterables` for datasource tells the pipeline engine that it should
   repeat any of the processes that are descendents of the datasource
   process on each of the iterable items. In the current example, the
   entire first level preprocessing and estimation will be repeated
   for each subject contained in subject_list.
"""
datasource.iterables = dict(subject_id=lambda:subject_list)

## from the FLIRT web doc

# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = nw.NodeWrapper(interface=fsl.Bet(),diskbased=True)
skullstrip.inputs.update(mask = True,
                         frac = 0.34)

# Preprocess functionals
motion_correct = nw.NodeWrapper(interface=fsl.McFlirt(), diskbased=True)
motion_correct.inputs.update(saveplots = True)
# Note- only one iterfield is currently supported
motion_correct.iterfield = ['infile']

func_skullstrip = nw.NodeWrapper(interface=fsl.Bet(), diskbased=True,
                                 name='func_Bet.fsl')
func_skullstrip.inputs.update(functional = True)
func_skullstrip.iterfield = ['infile']

ref_skullstrip = nw.NodeWrapper(interface=fsl.Bet(), diskbased=True,
                                name='ref_Bet.fsl')
ref_skullstrip.inputs.update(functional = True)


## Now for registration

target_image = fsl.fsl_info.standard_image('MNI152_T1_2mm')

# For structurals
# flirt -ref ${FSLDIR}/data/standard/MNI152_T1_2mm_brain -in my_betted_structural -omat my_affine_transf.mat

t1reg2std = nw.NodeWrapper(interface=fsl.Flirt(), diskbased=True)
t1reg2std.inputs.update(reference = target_image,
                        outmatrix = 't1reg2std.xfm')

# It may seem that these should be able to be run in one step. But, then you get
# an empty "fnirted" image.
# they would be faster (I think) to do together, but the applywarp is super-fast
# anyway.
# fnirt --in=my_structural --aff=my_affine_transf.mat --cout=my_nonlinear_transf --config=T1_2_MNI152_2mm
# applywarp --ref=${FSLDIR}/data/standard/MNI152_T1_2mm --in=my_structural --warp=my_nonlinear_transf --out
# =my_warped_structural

t1warp2std = nw.NodeWrapper(interface=fsl.Fnirt(), diskbased=True)
t1warp2std.inputs.update(configfile = 'T1_2_MNI152_2mm',
                         fieldcoeff_file = 't1warp2std',
                         logfile = 't1warp2std.log')

t1applywarp = nw.NodeWrapper(interface=fsl.ApplyWarp(), diskbased=True)
t1applywarp.inputs.update(reference = target_image,
                          outfile = 't1_warped')

# For functionals - refers to some files above
# flirt -ref my_betted_structural -in my_functional -dof 7 -omat func2struct.mat

ref2t1 = nw.NodeWrapper(interface=fsl.Flirt(), diskbased=True, 
                         name='ref_Flirt.fsl')
ref2t1.inputs.update(outmatrix = 'ref2t1.xfm',
                     dof = 6)

# applywarp --ref=${FSLDIR}/data/standard/MNI152_T1_2mm --in=my_functional --warp=my_nonlinear_transf --premat=func2struct.mat --out=my_warped_functional

funcapplywarp = nw.NodeWrapper(interface=fsl.ApplyWarp(), diskbased=True,
                               name='func_ApplyWarp.fsl')
funcapplywarp.iterfield = ['infile']
funcapplywarp.inputs.update(reference = target_image)

# Finally do some smoothing!

smoothing = nw.NodeWrapper(interface=fsl.FSLSmooth(), diskbased=True)
smoothing.iterfield = ['infile']
smoothing.inputs.fwhm = 5




#######################################################################
# setup analysis components
#######################################################################


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
contrasts = [cont1,cont2]

"""
   c. Use :class:`nipype.interfaces.spm.SpecifyModel` to generate
   SPM-specific design information. 
"""
modelspec = nw.NodeWrapper(interface=spm.SpecifyModel())
modelspec.inputs.subject_info_func       = subjectinfo
modelspec.inputs.concatenate_runs        = False
modelspec.inputs.input_units             = 'secs'
modelspec.inputs.output_units            = 'secs'
modelspec.inputs.time_repetition         = 3.
modelspec.inputs.high_pass_filter_cutoff = 120


"""
   d. Use :class:`nipype.interfaces.spm.Level1Design` to generate a
   first level SPM.mat file for analysis
"""
level1design = nw.NodeWrapper(interface=fsl.Level1Design(),diskbased=True)
level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
level1design.inputs.bases              = {'hrf':{'derivs': False}}
level1design.inputs.contrasts          = contrasts
level1design.overwrite = True


##########################
# Setup storage of results
##########################

datasink = nw.NodeWrapper(interface=nio.DataSink())
# I'd like this one to actually be preproc, but for now, I don't want to change
# the pipeline around because of data already being on S3
datasink.inputs.base_directory = os.path.abspath('./fsl/l1output')

#####################
# Set up preproc pype
#####################

preproc = pe.Pipeline()
preproc.config['workdir'] = os.path.abspath('./fsl/workingdir')
preproc.config['use_parameterized_dirs'] = True

preproc.connect([# preprocessing in native space
                 (datasource, skullstrip,[('struct','infile')]),
                 (datasource, motion_correct, 
                     [('func', 'infile'), ('func_ref', 'reffile')]),
                 (motion_correct, func_skullstrip,
                     [('outfile', 'infile')]),
                 (datasource, ref_skullstrip, [('func_ref', 'infile')]),
                 # T1 registration
                 (skullstrip, t1reg2std,[('outfile', 'infile')]),
                 (datasource, t1warp2std,[('struct', 'infile')]),
                 (t1reg2std, t1warp2std, [('outmatrix', 'affine')]),
                 (t1warp2std, t1applywarp, 
                     [('fieldcoeff_file', 'fieldfile')]),
                 # It would seem a little more parsimonious to get this from
                 # t1warp2std, but it's only an input there...
                 (datasource, t1applywarp, [('struct', 'infile')]),
                 # Functional registration
                 (ref_skullstrip, ref2t1, [('outfile', 'infile')]),
                 (skullstrip, ref2t1, [('outfile', 'reference')]),
                 (ref2t1, funcapplywarp, [('outmatrix', 'premat')]),
                 (t1warp2std, funcapplywarp,
                      [('fieldcoeff_file', 'fieldfile')]),
                 (func_skullstrip, funcapplywarp, [('outfile', 'infile')]),
                 # Smooth :\
                 (funcapplywarp, smoothing, [('outfile', 'infile')]),
                 # Model design
                 (datasource,modelspec,[('subject_id','subject_id')]),
                 (motion_correct,modelspec,[('parfile','realignment_parameters')]),
                 (smoothing,modelspec,[('smoothedimage','functional_runs')]),
                 (modelspec,level1design,[('session_info','session_info')]),                 
                ])

# store relevant outputs from various stages of preprocessing
preproc.connect([(datasource,datasink,[('subject_id','subject_id')]),
                    (skullstrip, datasink, 
                        [('outfile', 'skullstrip.@outfile')]),
                    (func_skullstrip, datasink,
                        [('outfile', 'skullstrip.@outfile')]),
                    (motion_correct, datasink,
                        [('parfile', 'skullstrip.@parfile')]),
                    # We aren't really going to look at these, are we?
                    # (t1reg2std, datasink, 
                    #     [('outmatrix', 'registration.@outmatrix')]),
                    # (t1warp2std, datasink, 
                    #     [('fieldcoeff_file', 'registration.@fieldcoeff_file')]),
                    (t1applywarp, datasink,
                        [('outfile', 'registration.@outfile')]),
                    (funcapplywarp, datasink,
                        [('outfile', 'registration.@outfile')]),
                    (smoothing, datasink, 
                        [('smoothedimage', 'registration.@outfile')]),
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
#if __name__ == '__main__':
#    l1pipeline.run()
#    l2pipeline.run()
