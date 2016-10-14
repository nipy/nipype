# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fix module provides classes for interfacing with the `FSL FIX
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/index.html>`_ command line tools.  
This was written to work with FSL version v5.0
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

Example Usage:

def flatten(l):
    # turn 2D list into 1D
    l = sum(l, [])
    return(l)

# extract features
extract_features = pe.MapNode(interface=fix.FeatureExtractor(), name='extract_features', iterfield=['mel_ica'])
preproc.connect(feat, 'feat_dir', extract_features, 'mel_ica')

# the next two nodes are simply for assembling a training set for the classifier. This looks for handlabeled noise txt files in all the specified feat_dirs 
training_input = pe.JoinNode(interface=util.IdentityInterface(fields=['mel_ica']), joinfield=['mel_ica'], joinsource='datasource', name='training_input')
preproc.connect(extract_features, 'mel_ica', training_input, 'mel_ica')

create_training_set = pe.Node(interface=fix.TrainingSetCreator(), name='trainingset_creator')
preproc.connect(training_input, ('mel_ica', flatten), create_training_set, 'mel_icas_in')

# now train the classifier
train_node = pe.Node(interface=fix.Training(trained_wts_filestem='core_shell_py'), name='train_node')
preproc.connect(create_training_set, 'mel_icas_out', train_node, 'mel_icas')

# ask classifier to label ICA components as noise or signal
classify_node = pe.MapNode(interface=fix.Classifier(thresh=5), name='classify', iterfield=['mel_ica'])
preproc.connect(train_node, 'trained_wts_file', classify_node, 'trained_wts_file')
preproc.connect(feat, 'feat_dir', classify_node, 'mel_ica')

# remove noise
cleaner_node = pe.MapNode(interface=fix.Cleaner(cleanup_motion=True,), name='cleaner', iterfield=['artifacts_list_file'])
preproc.connect(classify_node, 'artifacts_list_file', cleaner_node, 'artifacts_list_file')

# extract mean func
meanfunc = pe.MapNode(interface=fsl.ImageMaths(op_string = '-Tmean', suffix='_mean'), name='meanfunc', iterfield = ['in_file'])
preproc.connect(cleaner_node, 'cleaned_functional_file', meanfunc, 'in_file')

"""

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    Directory,
    InputMultiPath,
    traits,
    File
)
import os

class FIXInputSpec(CommandLineInputSpec):
    mel_ica = InputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Melodic output directory or directories',
                              argstr='%s', position=-1)


    # Different modes of operation, which are pretty much mutually exclusive
    _xor_inputs = ('extract_features', 'classify', 'apply_cleanup', 'train', 'test_accuracy')
    
    # /usr/local/fix/fix -f <mel.ica>
    extract_features = traits.Bool(desc='Extract features (for later training and/or classifying)',
                                   argstr='-f', xor=_xor_inputs, requires='mel_ica')

    # /usr/local/fix/fix -c <mel.ica> <training.RData> <thresh>
    classify = traits.Bool(desc='Classify ICA components using a specific training dataset (<thresh> is in the range 0-100, typically 5-20)',
                                   argstr='-c', xor=_xor_inputs, requires='mel_ica')

    # /usr/local/fix/fix -a <mel.ica/fix4melview_TRAIN_thr.txt>  [-m [-h <highpass>]]  [-A]  [-x <confound>] [-x <confound2>] etc.
    apply_cleanup = traits.Bool(desc='Apply cleanup, using artefacts listed in the .txt file',
                                   argstr='-a', xor=_xor_inputs, requires='artifacts_list_file') # todo, optional args, required inputs

    train = traits.Bool(desc='Train the classifier based on your own FEAT/MELODIC output directory',
                                   argstr='-t %s', value="training", xor=_xor_inputs) # todo, optional args

    test_accuracy = traits.Bool(desc='Test the accuracy of an existing training dataset on a set of hand-labelled subjects',
                                   argstr='-C', xor=_xor_inputs)


    # shared args for different modes
    artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually', argstr='%s')  

    trained_wts_file = File(desc='trained-weights file', argstr='%s')  




    # leave-one-out cross validation
    loo = traits.Bool(argstr='-l', requires=['train'],
                            desc='full leave-one-out test with classifier training')
    
    # args for classify

    highpass = traits.Float(argstr='-m -h %f', requires=['apply_cleanup'],
                            desc='cleanup motion confounds', value=100, xor=_xor_cleanup)


    # for apply_cleanup

    _xor_cleanup = ('cleanup_motion', 'highpass_filter')

    cleanup_motion = traits.Bool(argstr='-m', requires=['apply_cleanup'],
                                 desc='cleanup motion confounds, looks for design.fsf for highpass filter cut-off', xor=_xor_cleanup)

    highpass = traits.Float(argstr='-m -h %f', requires=['apply_cleanup'],
                            desc='cleanup motion confounds', value=100, xor=_xor_cleanup)

    aggressive = traits.Bool(argstr='-A', requires=['apply_cleanup'],
                             desc='Apply aggressive (full variance) cleanup, instead of the default less-aggressive (unique variance) cleanup.')

    confound_file = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                             desc='Include additional confound file.')

    confound_file_1 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                             desc='Include additional confound file.')

    confound_file_2 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                             desc='Include additional confound file.')

    

class FIXOutputSpec(TraitedSpec):
    output_file = File(desc = "Zip file", exists = True)

class FIX(CommandLine):
    input_spec = FIXInputSpec
    output_spec = FIXOutputSpec
    cmd = 'fix'

    def _list_outputs(self):
            outputs = self.output_spec().get()
            return outputs

if __name__ == '__main__':

    fix = FIX()
    print fix.cmdline
    fix.run()
