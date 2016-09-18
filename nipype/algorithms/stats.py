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

import numpy as np
import nibabel as nb

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

    functions = {
        'mean': np.mean
    }

    def _run_interface(self, runtime):
        label_data, fmri_data, fun, n_volumes, labels = self._get_inputs()

        # empty array to fill with output
        signals = np.ndarray((n_volumes, len(labels)))

        for time in range(n_volumes):
            volume_data = fmri_data[:, :, :, time]
            for label in range(1, len(labels) + 1): # skip 0 (background)
                voxels = volume_data[label_data == label]
                signals[time, label - 1] = fun(voxels)

        output = np.vstack((labels, signals.astype(str)))

        # save output
        np.savetxt(self.inputs.out_file, output, fmt=b'%s', delimiter='\t')
        return runtime

    def _get_inputs(self):
        ''' manipulate self.inputs values into useful form; check validity '''
        ins = self.inputs

        label_data = self._load_label_data()
        fmri_data = nb.load(ins.in_file).get_data()
        fun = self.functions[ins.stat]
        n_volumes = fmri_data.shape[3]
        labels = ins.class_labels
        # assuming consecutive int labels
        if len(labels) != np.amax(label_data):
            raise ValueError('The length of class_labels {} does not '
                             'match the number of regions, {}, found in '
                             'label_file {}'.format(labels,
                                                    np.amax(label_data),
                                                    ins.label_file))
        return label_data, fmri_data, fun, n_volumes, labels

    def _load_label_data(self):
        ''' retrieves label data from self.inputs.label_file,
        todo 4d-ifies if 3d '''
        label_data = nb.load(self.inputs.label_file).get_data()
        return label_data

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs
