# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fix module provides classes for interfacing with the `FSL FIX
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/index.html>` command line tools.

This was written to work with FSL version v5.0

The following example assumes that melodic has already been run, so
the datagrabber is configured to start from there (a list of melodic
output directories). If no hand_labels_noise.txt exists already, this
will fail and comment on that.

EXAMPLE:
subject_list = ['1', '2', '3']

fix_pipeline = pe.Workflow(name='fix_pipeline')
fix_pipeline.base_dir = os.path.abspath('./')

info = dict(mel_ica=[['subject_id']])

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'], outfields=['mel_ica']), name='datasource')
datasource.inputs.base_directory = os.path.abspath('<path_to_base_directory>')
datasource.inputs.template = '%s/<path_to_melodic_ica>'
datasource.inputs.template_args = info
datasource.inputs.subject_id =  subject_list
datasource.inputs.sort_filelist = True
datasource.iterables = ('subject_id', subject_list)

# create training set by looking into which mel_icas have hand_labels_noise.txt files in them
create_training_set = pe.JoinNode(interface=fix.TrainingSetCreator(), joinfield=['mel_icas_in'], joinsource='datasource', name='trainingset_creator')

# train the classifier
train_node = pe.Node(interface=fix.Training(trained_wts_filestem='foo'), name='train_node')

# test accuracy. Probably not necessary, and also failing on my setup because of fix itself (no error msg)
accuracy_tester = pe.Node(interface=fix.AccuracyTester(output_directory='more_foo'), name='accuracy_tester')

# classify components
classify_node = pe.Node(interface=fix.Classifier(), name='classify')

# apply cleanup
cleaner_node = pe.Node(interface=fix.Cleaner(), name='cleaner')

fix_pipeline.connect(datasource, 'mel_ica', create_training_set, 'mel_icas_in')
fix_pipeline.connect(create_training_set, 'mel_icas_out', train_node, 'mel_icas')
fix_pipeline.connect(train_node, 'trained_wts_file', accuracy_tester, 'trained_wts_file')
fix_pipeline.connect(datasource, 'mel_ica', accuracy_tester, 'mel_icas')
fix_pipeline.connect(train_node, 'trained_wts_file', classify_node, 'trained_wts_file')
fix_pipeline.connect(datasource, 'mel_ica', classify_node, 'mel_ica')
fix_pipeline.connect(classify_node, 'artifacts_list_file', cleaner_node, 'artifacts_list_file')

fix_pipeline.write_graph()
outgraph = fix_pipeline.run()

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ..base import (TraitedSpec, CommandLineInputSpec, CommandLine,
                    InputMultiPath, OutputMultiPath, BaseInterface,
                    BaseInterfaceInputSpec, traits, Directory, File, isdefined)
import os


class TrainingSetCreatorInputSpec(BaseInterfaceInputSpec):
    mel_icas_in = InputMultiPath(
        Directory(exists=True),
        copyfile=False,
        desc='Melodic output directories',
        argstr='%s',
        position=-1)


class TrainingSetCreatorOutputSpec(TraitedSpec):
    mel_icas_out = OutputMultiPath(
        Directory(exists=True),
        copyfile=False,
        desc='Hand labels for noise vs signal',
        argstr='%s',
        position=-1)


class TrainingSetCreator(BaseInterface):
    '''Goes through set of provided melodic output directories, to find all
    the ones that have a hand_labels_noise.txt file in them.

    This is outsourced as a separate class, so that the pipeline is
    rerun everytime a handlabeled file has been changed, or a new one
    created.

    '''
    input_spec = TrainingSetCreatorInputSpec
    output_spec = TrainingSetCreatorOutputSpec
    _always_run = True

    def _run_interface(self, runtime):
        mel_icas = []
        for item in self.inputs.mel_icas_in:
            if os.path.exists(os.path.join(item, 'hand_labels_noise.txt')):
                mel_icas.append(item)

        if len(mel_icas) == 0:
            raise Exception(
                '%s did not find any hand_labels_noise.txt files in the following directories: %s'
                % (self.__class__.__name__, mel_icas))

        return runtime

    def _list_outputs(self):
        mel_icas = []
        for item in self.inputs.mel_icas_in:
            if os.path.exists(os.path.join(item, 'hand_labels_noise.txt')):
                mel_icas.append(item)
        outputs = self._outputs().get()
        outputs['mel_icas_out'] = mel_icas
        return outputs


class FeatureExtractorInputSpec(CommandLineInputSpec):
    mel_ica = Directory(
        exists=True,
        copyfile=False,
        desc='Melodic output directory or directories',
        argstr='%s',
        position=-1)


class FeatureExtractorOutputSpec(TraitedSpec):
    mel_ica = Directory(
        exists=True,
        copyfile=False,
        desc='Melodic output directory or directories',
        argstr='%s',
        position=-1)


class FeatureExtractor(CommandLine):
    '''
    Extract features (for later training and/or classifying)
    '''
    input_spec = FeatureExtractorInputSpec
    output_spec = FeatureExtractorOutputSpec
    cmd = 'fix -f'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['mel_ica'] = self.inputs.mel_ica
        return outputs


class TrainingInputSpec(CommandLineInputSpec):
    mel_icas = InputMultiPath(
        Directory(exists=True),
        copyfile=False,
        desc='Melodic output directories',
        argstr='%s',
        position=-1)

    trained_wts_filestem = traits.Str(
        desc=
        'trained-weights filestem, used for trained_wts_file and output directories',
        argstr='%s',
        position=1)

    loo = traits.Bool(
        argstr='-l',
        desc='full leave-one-out test with classifier training',
        position=2)


class TrainingOutputSpec(TraitedSpec):
    trained_wts_file = File(exists=True, desc='Trained-weights file')


class Training(CommandLine):
    '''
    Train the classifier based on your own FEAT/MELODIC output directory.
    '''
    input_spec = TrainingInputSpec
    output_spec = TrainingOutputSpec
    cmd = 'fix -t'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.trained_wts_filestem):
            outputs['trained_wts_file'] = os.path.abspath(
                self.inputs.trained_wts_filestem + '.RData')
        else:
            outputs['trained_wts_file'] = os.path.abspath(
                'trained_wts_file.RData')
        return outputs


class AccuracyTesterInputSpec(CommandLineInputSpec):
    mel_icas = InputMultiPath(
        Directory(exists=True),
        copyfile=False,
        desc='Melodic output directories',
        argstr='%s',
        position=3,
        mandatory=True)

    trained_wts_file = File(
        desc='trained-weights file', argstr='%s', position=1, mandatory=True)

    output_directory = Directory(
        desc=
        'Path to folder in which to store the results of the accuracy test.',
        argstr='%s',
        position=2,
        mandatory=True)


class AccuracyTesterOutputSpec(TraitedSpec):
    output_directory = Directory(
        desc=
        'Path to folder in which to store the results of the accuracy test.',
        argstr='%s',
        position=1)


class AccuracyTester(CommandLine):
    '''
    Test the accuracy of an existing training dataset on a set of hand-labelled subjects.
    Note: This may or may not be working. Couldn't presently not confirm because fix fails on this (even outside of nipype) without leaving an error msg.
    '''
    input_spec = AccuracyTesterInputSpec
    output_spec = AccuracyTesterOutputSpec
    cmd = 'fix -C'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if isdefined(self.inputs.output_directory):
            outputs['output_directory'] = Directory(
                exists=False, value=self.inputs.output_directory)
        else:
            outputs['output_directory'] = Directory(
                exists=False, value='accuracy_test')
        return outputs


class ClassifierInputSpec(CommandLineInputSpec):
    mel_ica = Directory(
        exists=True,
        copyfile=False,
        desc='Melodic output directory or directories',
        argstr='%s',
        position=1)

    trained_wts_file = File(
        exists=True,
        desc='trained-weights file',
        argstr='%s',
        position=2,
        mandatory=True,
        copyfile=False)

    thresh = traits.Int(
        argstr='%d',
        desc='Threshold for cleanup.',
        position=-1,
        mandatory=True)

    artifacts_list_file = File(
        desc=
        'Text file listing which ICs are artifacts; can be the output from classification or can be created manually'
    )


class ClassifierOutputSpec(TraitedSpec):
    artifacts_list_file = File(
        desc=
        'Text file listing which ICs are artifacts; can be the output from classification or can be created manually'
    )


class Classifier(CommandLine):
    '''
    Classify ICA components using a specific training dataset (<thresh> is in the range 0-100, typically 5-20).
    '''
    input_spec = ClassifierInputSpec
    output_spec = ClassifierOutputSpec
    cmd = 'fix -c'

    def _gen_artifacts_list_file(self, mel_ica, thresh):

        _, trained_wts_file = os.path.split(self.inputs.trained_wts_file)
        trained_wts_filestem = trained_wts_file.split('.')[0]
        filestem = 'fix4melview_' + trained_wts_filestem + '_thr'

        fname = os.path.join(mel_ica, filestem + str(thresh) + '.txt')
        return fname

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['artifacts_list_file'] = self._gen_artifacts_list_file(
            self.inputs.mel_ica, self.inputs.thresh)

        return outputs


class CleanerInputSpec(CommandLineInputSpec):
    artifacts_list_file = File(
        exists=True,
        argstr='%s',
        position=1,
        mandatory=True,
        desc=
        'Text file listing which ICs are artifacts; can be the output from classification or can be created manually'
    )

    cleanup_motion = traits.Bool(
        argstr='-m',
        desc=
        'cleanup motion confounds, looks for design.fsf for highpass filter cut-off',
        position=2)

    highpass = traits.Float(
        100,
        argstr='-m -h %f',
        usedefault=True,
        desc='cleanup motion confounds',
        position=2)

    aggressive = traits.Bool(
        argstr='-A',
        desc=
        'Apply aggressive (full variance) cleanup, instead of the default less-aggressive (unique variance) cleanup.',
        position=3)

    confound_file = traits.File(
        argstr='-x %s', desc='Include additional confound file.', position=4)

    confound_file_1 = traits.File(
        argstr='-x %s', desc='Include additional confound file.', position=5)

    confound_file_2 = traits.File(
        argstr='-x %s', desc='Include additional confound file.', position=6)


class CleanerOutputSpec(TraitedSpec):
    cleaned_functional_file = File(exists=True, desc='Cleaned session data')


class Cleaner(CommandLine):
    '''
    Extract features (for later training and/or classifying)
    '''
    input_spec = CleanerInputSpec
    output_spec = CleanerOutputSpec
    cmd = 'fix -a'

    def _get_cleaned_functional_filename(self, artifacts_list_filename):
        ''' extract the proper filename from the first line of the artifacts file '''
        artifacts_list_file = open(artifacts_list_filename, 'r')
        functional_filename, extension = artifacts_list_file.readline().split(
            '.')
        artifacts_list_file_path, artifacts_list_filename = os.path.split(
            artifacts_list_filename)

        return (os.path.join(artifacts_list_file_path,
                             functional_filename + '_clean.nii.gz'))

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs[
            'cleaned_functional_file'] = self._get_cleaned_functional_filename(
                self.inputs.artifacts_list_file)
        return outputs
