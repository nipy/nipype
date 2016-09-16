# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Algorithms to compute statistics on :abbr:`fMRI (functional MRI)`

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__))
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

'''
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str

import numpy as np
import nilearn.input_data as nl

from .. import logging
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File)
IFLOG = logging.getLogger('interface')

class SignalExtractionInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='4-D fMRI nii file')
    label_file = File(exists=True, mandatory=True,
                      desc='a 3-D label image, with 0 denoting background, or '
                      'a 4-D file of probability maps.')
    class_labels = traits.List(mandatory=True,
                               desc='Human-readable labels for each segment '
                               'in the label file, in order. The length of '
                               'class_labels must be equal to the number of '
                               'segments (background excluded). This list '
                               'corresponds to the class labels in label_file '
                               'in ascending order')
    out_file = File('signals.tsv', usedefault=True, exists=False,
                    mandatory=False, desc='The name of the file to output to. '
                    'signals.tsv by default')
    stat = traits.Enum(('mean',), mandatory=False, default='mean',
                       usedefault=True,
                       desc='The stat you wish to calculate on each segment. '
                       'The default is finding the mean')
    detrend = traits.Bool(False, usedefault=True, mandatory=False,
                          desc='If True, perform detrending using nilearn.')

class SignalExtractionOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='tsv file containing the computed '
                    'signals, with as many columns as there are labels and as '
                    'many rows as there are timepoints in in_file, plus a '
                    'header row with values from class_labels')

class SignalExtraction(BaseInterface):
    '''
    Extracts signals over tissue classes or brain regions

    >>> seinterface = SignalExtraction()
    >>> seinterface.inputs.in_file = 'functional.nii'
    >>> seinterface.inputs.in_file = 'segmentation0.nii.gz'
    >>> seinterface.inputs.out_file = 'means.tsv'
    >>> segments = ['CSF', 'gray', 'white']
    >>> seinterface.inputs.class_labels = segments
    >>> seinterface.inputs.stat = 'mean'
    '''
    input_spec = SignalExtractionInputSpec
    output_spec = SignalExtractionOutputSpec

    def _run_interface(self, runtime):
        ins = self.inputs

        if ins.stat == 'mean': # always true for now
            nlmasker = nl.NiftiLabelsMasker(ins.label_file,
                                            detrend=ins.detrend)
            nlmasker.fit()
            region_signals = nlmasker.transform_single_imgs(ins.in_file)

            num_labels_found = region_signals.shape[1]
            if len(ins.class_labels) != num_labels_found:
                raise ValueError('The length of class_labels {} does not '
                                 'match the number of regions {} found in '
                                 'label_file {}'.format(ins.class_labels,
                                                        num_labels_found,
                                                        ins.label_file))

            output = np.vstack((ins.class_labels, region_signals.astype(str)))

            # save output
            np.savetxt(ins.out_file, output, fmt=b'%s', delimiter='\t')
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs
