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
"""

from nipype.interfaces.base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    Directory,
    InputMultiPath,
    traits,
    File,
    isdefined
)

import os

class FIXInputSpec(CommandLineInputSpec):
    mel_icas = InputMultiPath(Directory(exists=True), copyfile=False,
                              desc='Melodic output directories',
                              argstr='%s', position=-1)

    mel_ica = Directory(exists=True, copyfile=False, desc='Melodic output directory or directories',
                              argstr='%s', position=1)


    # Different modes of operation, which are pretty much mutually exclusive
    _xor_inputs = ('extract_features', 'classify', 'apply_cleanup', 'train', 'test_accuracy')
    
    # /usr/local/fix/fix -f <mel.ica>
    extract_features = traits.Bool(desc='Extract features (for later training and/or classifying)',
                                   argstr='-f', xor=_xor_inputs, requires=['mel_ica'], position=0)

    # /usr/local/fix/fix -c <mel.ica> <training.RData> <thresh>
    classify = traits.Bool(desc='Classify ICA components using a specific training dataset (<thresh> is in the range 0-100, typically 5-20)',
                                   argstr='-c', xor=_xor_inputs, requires=['mel_ica', 'trained_wts_file', 'thresh'], position=0)

    # /usr/local/fix/fix -a <mel.ica/fix4melview_TRAIN_thr.txt>  [-m [-h <highpass>]]  [-A]  [-x <confound>] [-x <confound2>] etc.
    apply_cleanup = traits.Bool(desc='Apply cleanup, using artefacts listed in the .txt file',
                                   argstr='-a', xor=_xor_inputs, requires=['artifacts_list_file'], position=0) 

    # /usr/local/fix/fix -t <Training> [-l]  <Melodic1.ica> <Melodic2.ica>
    train = traits.Bool(desc='Train the classifier based on your own FEAT/MELODIC output directory',
                                   argstr='-t', xor=_xor_inputs, requires=['trained_wts_filestem', 'mel_icas'], position=0) # todo, optional args

    # /usr/local/fix/fix -C <training.RData> <output> <mel1.ica> <mel2.ica> ...
    test_accuracy = traits.Bool(desc='Test the accuracy of an existing training dataset on a set of hand-labelled subjects',
                                   argstr='-C', xor=_xor_inputs)



    # shared args for different modes
    artifacts_list_file = File(desc='Text file listing which ICs are artifacts; can be the output from classification or can be created manually', argstr='%s', position=1)  

    trained_wts_filestem = traits.Str(desc='trained-weights file', argstr='%s', position=1)  

    trained_wts_file = File(desc='trained-weights file', argstr='%s', position=2)  



    # leave-one-out cross validation
    loo = traits.Bool(argstr='-l', requires=['train'],
                            desc='full leave-one-out test with classifier training', position=2)
    
    # args for classify
    thresh = traits.Int(argstr='%d', requires=['classify'], desc='cleanup motion confounds', position=-1)


    # for apply_cleanup
    _xor_cleanup = ('cleanup_motion', 'highpass')

    cleanup_motion = traits.Bool(argstr='-m', requires=['apply_cleanup'],
                                 desc='cleanup motion confounds, looks for design.fsf for highpass filter cut-off', 
                                 xor=_xor_cleanup, position=2)

    highpass = traits.Float(argstr='-m -h %f', requires=['apply_cleanup'],
                            desc='cleanup motion confounds', value=100, xor=_xor_cleanup, position=2)

    aggressive = traits.Bool(argstr='-A', requires=['apply_cleanup'],
                             desc='Apply aggressive (full variance) cleanup, instead of the default less-aggressive (unique variance) cleanup.', position=3)

    confound_file = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                                desc='Include additional confound file.', position=4)

    confound_file_1 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                                  desc='Include additional confound file.', position=5)

    confound_file_2 = traits.File(argstr='-x %s', requires=['apply_cleanup'],
                                  desc='Include additional confound file.', position=6)

    

class FIXOutputSpec(TraitedSpec):
    output_file = File(desc = "Zip file", exists = True)

class FIX(CommandLine):
    input_spec = FIXInputSpec
    output_spec = FIXOutputSpec
    cmd = '/usr/local/fix/fix'

    def _list_outputs(self):
            outputs = self.output_spec().get()
            return outputs

if __name__ == '__main__':

    fix = FIX()
    print fix.cmdline
    fix.run()
