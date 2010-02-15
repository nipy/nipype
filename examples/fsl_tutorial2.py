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
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
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
print fsl.FSLInfo.version()
fsl.FSLInfo.outputtype('NIFTI_GZ')


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
subject_list = ['s1']#, 's3']
# The following info structure helps the DataSource module organize
# nifti files into fields/attributes of a data object. With DataSource
# this object is of type Bunch.
info = {}
info['s1'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))#,(['ref'],'func_ref'))
info['s3'] = ((['f3','f5','f7','f10'],'func'),(['struct'],'struct'))#,(['ref'],'func_ref'))

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
datasource.iterables = ('subject_id',subject_list)

## from the FLIRT web doc

extract_ref = nw.NodeWrapper(interface=fsl.ExtractRoi(tmin=42,
                                                      tsize=1),
                             name = 'middlevol.fsl',
                             diskbased=True)
# run FSL's bet
# bet my_structural my_betted_structural
skullstrip = nw.NodeWrapper(interface=fsl.Bet(mask = True,
                                              frac = 0.34),
                            name = 'struct_bet.fsl',
                            diskbased=True)

# Preprocess functionals
motion_correct = nw.NodeWrapper(interface=fsl.McFlirt(saveplots = True),
                                name='mcflirt.fsl',
                                diskbased=True)
motion_correct.iterfield = ['infile']

func_skullstrip = nw.NodeWrapper(interface=fsl.Bet(functional = True),
                                 diskbased=True,
                                 name='func_bet.fsl')
func_skullstrip.iterfield = ['infile']


# Finally do some smoothing!

smoothing = nw.NodeWrapper(interface=fsl.Smooth(), diskbased=True)
smoothing.iterfield = ['infile']
smoothing.inputs.fwhm = 5

inorm = nw.NodeWrapper(interface = fsl.ImageMaths(optstring = '-inm 10000',
                                                suffix = '_inm',
                                                outdatatype = 'float'),
                       name = 'inorm.fsl',
                       diskbased            = True)
inorm.iterfield = ['infile']

hpfilter = nw.NodeWrapper(interface=fsl.ImageMaths(),
                          name='highpass.fsl',
                          diskbased=True)
hpcutoff = 120
TR = 3.
hpfilter.inputs.suffix = '_hpf'
hpfilter.inputs.optstring = '-bptf %d -1'%(hpcutoff/TR)
hpfilter.iterfield = ['infile']

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
cont3 = ['Task','F', [cont1, cont2]]
contrasts = [cont1,cont2]

"""
   c. Use :class:`nipype.interfaces.spm.SpecifyModel` to generate
   SPM-specific design information. 
"""
modelspec = nw.NodeWrapper(interface=model.SpecifyModel(), diskbased=True)
modelspec.inputs.concatenate_runs        = False
modelspec.inputs.input_units             = 'secs'
modelspec.inputs.output_units            = 'secs'
modelspec.inputs.time_repetition         = TR
modelspec.inputs.high_pass_filter_cutoff = hpcutoff


"""
   d. Use :class:`nipype.interfaces.fsl.Level1Design` to generate a
   run specific fsf file for analysis
"""
level1design = nw.NodeWrapper(interface=fsl.Level1Design(),diskbased=True)
level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
level1design.inputs.bases = {'hrf':{'derivs': True}}
level1design.inputs.contrasts = contrasts
level1design.inputs.reg_image = fsl.FSLInfo.standard_image('MNI152_T1_2mm_brain.nii.gz')
level1design.inputs.reg_dof = 12 

"""
   e. Use :class:`nipype.interfaces.fsl.FeatModel` to generate a
   run specific mat file for use by FilmGLS
"""
featmodel = nw.NodeWrapper(interface=fsl.Feat(),diskbased=True)
featmodel.iterfield = ['fsf_file']

fedesign = nw.NodeWrapper(interface=fsl.FixedEffectsModel(num_copes=2),diskbased=True)

featfemodel = nw.NodeWrapper(interface=fsl.Feat(),
                             name='FixedEffects.feat',
                             diskbased=True)



##########################
# Setup storage of results
##########################

datasink = nw.NodeWrapper(interface=nio.DataSink())
# I'd like this one to actually be preproc, but for now, I don't want to change
# the pipeline around because of data already being on S3
datasink.inputs.base_directory = os.path.abspath('./fsl/l1output')

#####################
# Set up l1pipeline pype
#####################

l1pipeline = pe.Pipeline()
l1pipeline.config['workdir'] = os.path.abspath('./fsl/workingdir')
l1pipeline.config['use_parameterized_dirs'] = True

def pickfirst(files):
    return files[0]

l1pipeline.connect([# preprocessing in native space
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
                 (datasource,modelspec,[('subject_id','subject_id'),
                                        (('subject_id',subjectinfo),'subject_info_func')]),
                 (motion_correct,modelspec,[('parfile','realignment_parameters')]),
                 (modelspec,level1design,[('session_info','session_info')]),
                 (level1design,featmodel,[('fsf_files','fsf_file')]),
                 (featmodel,fedesign,[('featdir','feat_dirs')]),
                 (fedesign,featfemodel,[('fsf_file','fsf_file')]),
                ])

# store relevant outputs from various stages of preprocessing
l1pipeline.connect([(datasource,datasink,[('subject_id','subject_id')]),
                    (skullstrip, datasink, 
                        [('outfile', 'skullstrip.@outfile')]),
                    (func_skullstrip, datasink,
                        [('outfile', 'skullstrip.@outfile')]),
                    (motion_correct, datasink,
                        [('parfile', 'skullstrip.@parfile')]),
                    (smoothing, datasink, 
                        [('smoothedimage', 'registration.@outfile')]),
                    (featfemodel, datasink, 
                        [('featdir', 'modelestimate.@fixedeffects')]),
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
    l1pipeline.run_in_series()
#    l2pipeline.run()
