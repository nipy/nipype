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
                               BaseInterfaceInputSpec, File, InputMultiPath)
IFLOG = logging.getLogger('interface')

class SignalExtractionInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='4-D fMRI nii file')
    label_files = InputMultiPath(File(exists=True), mandatory=True,
                                desc='a 3-D label image, with 0 denoting '
                                'background, or a list of 3-D probability '
                                'maps (one per label) or the equivalent 4D '
                                'file.')
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
    >>> seinterface.inputs.label_files = 'segmentation0.nii.gz'
    >>> seinterface.inputs.out_file = 'means.tsv'
    >>> segments = ['CSF', 'gray', 'white']
    >>> seinterface.inputs.class_labels = segments
    >>> seinterface.inputs.detrend = True
    '''
    input_spec = SignalExtractionInputSpec
    output_spec = SignalExtractionOutputSpec

    def _run_interface(self, runtime):
        masker = self._process_inputs()

        region_signals = masker.fit_transform(self.inputs.in_file)

        output = np.vstack((self.inputs.class_labels, region_signals.astype(str)))

        # save output
        np.savetxt(self.inputs.out_file, output, fmt=b'%s', delimiter='\t')
        return runtime

    def _process_inputs(self):
        ''' validate and  process inputs into useful form '''

        import nilearn.input_data as nl

        # determine form of label files, choose appropriate nilearn masker
        if len(self.inputs.label_files) > 1: # list of 3D nifti images
            masker = nl.NiftiMapsMasker(self.inputs.label_files)
            n_labels = len(self.inputs.label_files)
        else: # list of size one, containing either a 3d or a 4d file
            label_data = nb.load(self.inputs.label_files[0])
            if len(label_data.shape) == 4: # 4d file
                masker = nl.NiftiMapsMasker(label_data)
                n_labels = label_data.shape[3]
            else: # 3d file
                if np.amax(label_data) > 1: # 3d label file
                    masker = nl.NiftiLabelsMasker(label_data)
                    # assuming consecutive positive integers for regions
                    n_labels = np.amax(label_data.get_data())
                else: # most probably a single probability map for one label
                    masker = nl.NiftiMapsMasker(label_data)
                    n_labels = 1

        # check label list size
        if len(self.inputs.class_labels) != n_labels:
            raise ValueError('The length of class_labels {} does not '
                             'match the number of regions {} found in '
                             'label_files {}'.format(self.inputs.class_labels,
                                                    n_labels,
                                                    self.inputs.label_files))

        masker.set_params(detrend=self.inputs.detrend)
        return masker

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs
