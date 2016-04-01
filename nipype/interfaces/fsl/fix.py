# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The fix module provides classes for interfacing with the `FSL FIX
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/index.html>` command line tools.  

This was written to work with FSL version v5.0
"""

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    Directory,
    InputMultiPath,
    OutputMultiPath,
    traits,
    File,
    BaseInterface,
    BaseInterfaceInputSpec,
    isdefined
)

import os

# class FIXInputSpec(CommandLineInputSpec):
#     mel_icas = InputMultiPath(Directory(exists=True), copyfile=False,
#                               desc='Melodic output directories',
#                               argstr='%s', position=-1)

#     hand_labels_noise = InputMultiPath(File(exists=True), copyfile=False,
#                               desc='Hand labels for noise vs signal',
#                               argstr='%s', position=-1)

#     mel_ica = Directory(exists=True, copyfile=False, desc='Melodic output directory or directories',
#                         argstr='%s', position=1)


#     # Different modes of operation, which are pretty much mutually exclusive
#     _xor_inputs = ('extract_features', 'classify', 'apply_cleanup', 'train', 'test_accuracy')
    
#     # /usr/local/fix/fix -f <mel.ica>
#     extract_features = traits.Bool(desc='Extract features (for later training and/or classifying)', argstr='-f', xor=_xor_inputs, requires=['mel_ica'], position=0)

#     # /usr/local/fix/fix -t <Training> [-l]  <Melodic1.ica> <Melodic2.ica>
#     train = traits.Bool(desc='Train the classifier based on your own FEAT/MELODIC output directory', argstr='-t', xor=_xor_inputs, requires=['trained_wts_filestem', 'mel_icas'], position=0) # todo, optional args

#     # /usr/local/fix/fix -C <training.RData> <output> <mel1.ica> <mel2.ica> ...
#     test_accuracy = traits.Bool(desc='Test the accuracy of an existing training dataset on a set of hand-labelled subjects', argstr='-C', xor=_xor_inputs)

#     # /usr/local/fix/fix -c <mel.ica> <training.RData> <thresh>
#     classify = traits.Bool(desc='Classify ICA components using a specific training dataset (<thresh> is in the range 0-100, typically 5-20)', argstr='-c', xor=_xor_inputs, requires=['mel_ica', 'trained_wts_file', 'thresh'], position=0)

#     # /usr/local/fix/fix -a <mel.ica/fix4melview_TRAIN_thr.txt>  [-m [-h <highpass>]]  [-A]  [-x <confound>] [-x <confound2>] etc.
#     apply_cleanup = traits.Bool(desc='Apply cleanup, using artefacts listed in the .txt file', argstr='-a', xor=_xor_inputs, requires=['artifacts_list_file'], position=0) 



#     # shared args for different modes
#     artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually', argstr='%s', position=1)  

#     trained_wts_filestem = traits.Str(desc='trained-weights filestem, used for trained_wts_file and output directories', argstr='%s', position=1)  

#     trained_wts_file = File(desc='trained-weights file', argstr='%s', position=2)  



#     # leave-one-out cross validation
#     loo = traits.Bool(argstr='-l', requires=['train'],
#                             desc='full leave-one-out test with classifier training', position=2)
    
#     # args for classify
#     thresh = traits.Int(argstr='%d', requires=['classify'], desc='cleanup motion confounds', position=-1)


#     # for apply_cleanup
#     _xor_cleanup = ('cleanup_motion', 'highpass')

#     cleanup_motion = traits.Bool(argstr='-m', requires=['apply_cleanup'],
#                                  desc='cleanup motion confounds, looks for design.fsf for highpass filter cut-off', 
#                                  xor=_xor_cleanup, position=2)

#     highpass = traits.Float(argstr='-m -h %f', requires=['apply_cleanup'],
#                             desc='cleanup motion confounds', value=100, xor=_xor_cleanup, position=2)

#     aggressive = traits.Bool(argstr='-A', requires=['apply_cleanup'],
#                              desc='Apply aggressive (full variance) cleanup, instead of the default less-aggressive (unique variance) cleanup.', position=3)

#     confound_file = traits.File(argstr='-x %s', requires=['apply_cleanup'],
#                                 desc='Include additional confound file.', position=4)

#     confound_file_1 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
#                                   desc='Include additional confound file.', position=5)

#     confound_file_2 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
#                                   desc='Include additional confound file.', position=6)

    

# class FIXOutputSpec(TraitedSpec):
#     trained_wts_file = File(desc='Trained-weights file')
#     artifacts_list_file = File(desc='Melodic output directories')
#     cleaned_functional_file = File(desc='Cleaned session data')


class TrainingSetCreatorInputSpec(BaseInterfaceInputSpec):
    mel_icas_in = InputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Melodic output directories',
                              argstr='%s', position=-1)

class TrainingSetCreatorOutputSpec(TraitedSpec):
    mel_icas_out = OutputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Hand labels for noise vs signal',
                              argstr='%s', position=-1)
    

class TrainingSetCreator(BaseInterface):
    '''
    Goes through set of provided melodic output directories, to find all the ones that have a hand_labels_noise.txt file in them. 
    This is outsourced as a separate class, so that the pipeline is rerun everytime a handlabeled file has been changed, or a new one created.
    '''
    input_spec = TrainingSetCreatorInputSpec
    output_spec = TrainingSetCreatorOutputSpec
    _always_run = True

    def _run_interface(self, runtime):
        mel_icas = []
        for item in self.inputs.mel_icas_in:
            if os.path.exists(os.path.join(item,'hand_labels_noise.txt')):
                mel_icas.append(item)

        return runtime

    def _list_outputs(self):
        mel_icas = []
        for item in self.inputs.mel_icas_in:
            if os.path.exists(os.path.join(item,'hand_labels_noise.txt')):
                mel_icas.append(item)
        outputs = self._outputs().get()
        outputs['mel_icas_out'] = mel_icas
        return outputs




class FeatureExtractorInputSpec(CommandLineInputSpec):    
    mel_ica = Directory(exists=True, copyfile=False, desc='Melodic output directory or directories',
                        argstr='%s', position=1)


class FeatureExtractorOutputSpec(TraitedSpec):


class FeatureExtractor(CommandLine):
    '''
    Extract features (for later training and/or classifying)
    '''
    input_spec = FeatureExtractorInputSpec
    output_spec = FeatureExtractorOutputSpec
    cmd = '/usr/local/fix/fix -f'



class TrainerInputSpec(CommandLineInputSpec):
    mel_icas = InputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Melodic output directories',
                              argstr='%s', position=-1)

    trained_wts_filestem = traits.Str(desc='trained-weights filestem, used for trained_wts_file and output directories', argstr='%s', position=1)  

    loo = traits.Bool(argstr='-l', desc='full leave-one-out test with classifier training', position=2)


class TrainerOutputSpec(TraitedSpec):
    trained_wts_file = File(desc='Trained-weights file')


class Trainer(CommandLine):
    '''
    Train the classifier based on your own FEAT/MELODIC output directory.
    '''
    input_spec = TrainerInputSpec
    output_spec = TrainerOutputSpec
    cmd = '/usr/local/fix/fix -t'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.trained_wts_file):
            outputs['trained_wts_file'] = Directory(exists=False, value=self.inputs.trained_wts_file + 'RData')
        else:
            outputs['trained_wts_file'] = Directory(exists=False, value='trained_wts_file.RData')
        return outputs


class AccuracyTesterInputSpec(CommandLineInputSpec):
    mel_icas = InputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Melodic output directories',
                              argstr='%s', position=3)

    trained_wts_file = File(desc='trained-weights file', argstr='%s', position=1)  

    output_directory = Directory(desc='Path to folder in which to store the results of the accuracy test.', argstr='%s', position=1)  


class AccuracyTesterOutputSpec(TraitedSpec):
    output_directory = Directory(desc='Path to folder in which to store the results of the accuracy test.', argstr='%s', position=1)  


class AccuracyTester(CommandLine):
    '''
    Test the accuracy of an existing training dataset on a set of hand-labelled subjects.
    '''
    input_spec = AccuracyTesterInputSpec
    output_spec = AccuracyTesterOutputSpec
    cmd = '/usr/local/fix/fix -C'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.output_directory):
            outputs['output_directory'] = Directory(exists=False, value=self.inputs.output_directory)
        else:
            outputs['output_directory'] = Directory(exists=False, value='accuracy_test')
        return outputs


class ClassifierInputSpec(CommandLineInputSpec):
    mel_ica = Directory(exists=True, copyfile=False, desc='Melodic output directory or directories',
                        argstr='%s', position=1)

    trained_wts_file = File(desc='trained-weights file', argstr='%s', position=2)  

    thresh = traits.Int(argstr='%d', desc='Threshold for cleanup.', value=5, position=-1)

    artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually')

class ClassifierOutputSpec(TraitedSpec):
    artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually')


class Classifier(CommandLine):
    '''
    Classify ICA components using a specific training dataset (<thresh> is in the range 0-100, typically 5-20).
    '''
    input_spec = ClassifierInputSpec
    output_spec = ClassifierOutputSpec
    cmd = '/usr/local/fix/fix -c'

    def _gen_artifacts_list_file(self, mel_ica, filestem, thresh):
        return os.path.join(mel_ica, filestem + str(thresh) + '.txt')

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.artifacts_list_file):
            filestem = self.inputs.artifacts_list_file
        else:
            filestem = 'fix4melview_thr'
            outputs['artifacts_list_file'] = self._gen_artifacts_list_file(self.inputs.mel_ica, filestem, self.inputs.thresh)
        else:
            outputs['artifacts_list_file'] = File(exists=False, value='accuracy_test')
        return outputs




class CleanerInputSpec(CommandLineInputSpec):
    artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually', argstr='%s', position=1)  

    cleanup_motion = traits.Bool(argstr='-m', 
                                 desc='cleanup motion confounds, looks for design.fsf for highpass filter cut-off', 
                                 xor=_xor_cleanup, position=2)

    highpass = traits.Float(argstr='-m -h %f',
                            desc='cleanup motion confounds', value=100, xor=_xor_cleanup, position=2)

    aggressive = traits.Bool(argstr='-A',
                             desc='Apply aggressive (full variance) cleanup, instead of the default less-aggressive (unique variance) cleanup.', position=3)

    confound_file = traits.File(argstr='-x %s',
                                desc='Include additional confound file.', position=4)

    confound_file_1 = traits.File(argstr='-x %s',
                                  desc='Include additional confound file.', position=5)

    confound_file_2 = traits.File(argstr='-x %s',
                                  desc='Include additional confound file.', position=6)


class CleanerOutputSpec(TraitedSpec):
    cleaned_functional_file = File(desc='Cleaned session data')


class Cleaner(CommandLine):
    '''
    Extract features (for later training and/or classifying)
    '''
    input_spec = CleanerInputSpec
    output_spec = CleanerOutputSpec
    cmd = '/usr/local/fix/fix -a'

    def _get_cleaned_functional_filename(self, artifacts_list_filename):
        ''' extract the proper filename from the first line of the artifacts file '''
        artifacts_list_file = file(artifacts_list_filename, 'r')
        functional_filename, extension = artifacts_list_file.readline().split('.')
        return(functional_filename + '_cleaned.nii.gz')

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['cleaned_functional_file'] = self._get_cleaned_functional_filename(self.inputs.artifacts_list_file)
        return outputs


# class FIX(CommandLine):
#     input_spec = FIXInputSpec
#     output_spec = FIXOutputSpec
#     cmd = '/usr/local/fix/fix'

#     def _format_arg(self, name, spec, value):
# #        print("Value: %s" % value)
# #        print("Spec: %s" % spec)
# #        if name == 'hand_labels_noise':
# #            mel_icas = ''
# #            for item in value:
# #                path, filename = os.path.split(item)
# #                mel_icas += path + " "
# #            print "mel_icas: " + mel_icas
# #            return spec.argstr % mel_icas
#         if isdefined(self.inputs.train):
#             if name == 'mel_icas':
#                 mel_icas = ''
#                 for item in value:
#                     if os.path.exists(item):
#                         mel_icas += item + " "
#                 return spec.argstr % mel_icas
#         return super(FIX, self)._format_arg(name, spec, value)


    # def _list_outputs(self):
    #         outputs = self.output_spec().get()
    #         if isdefined(self.inputs.train):
    #             outputs['trained_wts_file'] = self.inputs.trained_wts_filestem + '.RData'
    #         elif isdefined(self.inputs.classify):
    #             outputs['artifacts_list_file'] = self._gen_artifacts_list_file(self.inputs.mel_ica, self.inputs.thresh)
    #         elif isdefined(self.inputs.apply_cleanup):
    #             outputs['cleaned_functional_file'] = self._get_cleaned_functional_filename(self.inputs.artifacts_list_file)
    #         return outputs

    # def _gen_artifacts_list_file(self, mel_ica, thresh):
    #     return os.path.join(mel_ica, 'fix4melview_core_shell_thr' + str(thresh) + '.txt')

    # def _get_cleaned_functional_filename(self, artifacts_list_filename):
    #     artifacts_list_file = file(artifacts_list_filename, 'r')
    #     functional_filename, extension = artifacts_list_file.readline().split('.')
    #     return(functional_filename + '_cleaned.nii.gz')


# if __name__ == '__main__':

#     fix = FIX()
#     print fix.cmdline
#     fix.run()
