# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Algorithms to compute statistics on :abbr:`fMRI (functional MRI)`
'''
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
import os

import numpy as np
import nibabel as nb

from ..interfaces.base import (traits, TraitedSpec, LibraryBaseInterface,
                               SimpleInterface, BaseInterfaceInputSpec, File,
                               InputMultiPath)


class NilearnBaseInterface(LibraryBaseInterface):
    _pkg = 'nilearn'


class SignalExtractionInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='4-D fMRI nii file')
    label_files = InputMultiPath(
        File(exists=True),
        mandatory=True,
        desc='a 3-D label image, with 0 denoting '
        'background, or a list of 3-D probability '
        'maps (one per label) or the equivalent 4D '
        'file.')
    class_labels = traits.List(
        mandatory=True,
        desc='Human-readable labels for each segment '
        'in the label file, in order. The length of '
        'class_labels must be equal to the number of '
        'segments (background excluded). This list '
        'corresponds to the class labels in label_file '
        'in ascending order')
    out_file = File(
        'signals.tsv',
        usedefault=True,
        exists=False,
        desc='The name of the file to output to. '
        'signals.tsv by default')
    incl_shared_variance = traits.Bool(
        True,
        usedefault=True,
        desc='By default '
        '(True), returns simple time series calculated from each '
        'region independently (e.g., for noise regression). If '
        'False, returns unique signals for each region, discarding '
        'shared variance (e.g., for connectivity. Only has effect '
        'with 4D probability maps.')
    include_global = traits.Bool(
        False,
        usedefault=True,
        desc='If True, include an extra column '
        'labeled "GlobalSignal", with values calculated from the entire brain '
        '(instead of just regions).')
    detrend = traits.Bool(
        False,
        usedefault=True,
        desc='If True, perform detrending using nilearn.')


class SignalExtractionOutputSpec(TraitedSpec):
    out_file = File(
        exists=True,
        desc='tsv file containing the computed '
        'signals, with as many columns as there are labels and as '
        'many rows as there are timepoints in in_file, plus a '
        'header row with values from class_labels')


class SignalExtraction(NilearnBaseInterface, SimpleInterface):
    '''
    Extracts signals over tissue classes or brain regions

    >>> seinterface = SignalExtraction()
    >>> seinterface.inputs.in_file = 'functional.nii'
    >>> seinterface.inputs.label_files = 'segmentation0.nii.gz'
    >>> seinterface.inputs.out_file = 'means.tsv'
    >>> segments = ['CSF', 'GrayMatter', 'WhiteMatter']
    >>> seinterface.inputs.class_labels = segments
    >>> seinterface.inputs.detrend = True
    >>> seinterface.inputs.include_global = True
    '''
    input_spec = SignalExtractionInputSpec
    output_spec = SignalExtractionOutputSpec

    def _run_interface(self, runtime):
        maskers = self._process_inputs()

        signals = []
        for masker in maskers:
            signals.append(masker.fit_transform(self.inputs.in_file))
        region_signals = np.hstack(signals)

        output = np.vstack((self.inputs.class_labels,
                            region_signals.astype(str)))

        # save output
        self._results['out_file'] = os.path.join(runtime.cwd,
                                                 self.inputs.out_file)
        np.savetxt(
            self._results['out_file'], output, fmt=b'%s', delimiter='\t')
        return runtime

    def _process_inputs(self):
        ''' validate and  process inputs into useful form.
        Returns a list of nilearn maskers and the list of corresponding label
        names.'''
        import nilearn.input_data as nl
        import nilearn.image as nli

        label_data = nli.concat_imgs(self.inputs.label_files)
        maskers = []

        # determine form of label files, choose appropriate nilearn masker
        if np.amax(label_data.get_data()) > 1:  # 3d label file
            n_labels = np.amax(label_data.get_data())
            maskers.append(nl.NiftiLabelsMasker(label_data))
        else:  # 4d labels
            n_labels = label_data.get_data().shape[3]
            if self.inputs.incl_shared_variance:  # independent computation
                for img in nli.iter_img(label_data):
                    maskers.append(
                        nl.NiftiMapsMasker(
                            self._4d(img.get_data(), img.affine)))
            else:  # one computation fitting all
                maskers.append(nl.NiftiMapsMasker(label_data))

        # check label list size
        if not np.isclose(int(n_labels), n_labels):
            raise ValueError(
                'The label files {} contain invalid value {}. Check input.'
                .format(self.inputs.label_files, n_labels))

        if len(self.inputs.class_labels) != n_labels:
            raise ValueError('The length of class_labels {} does not '
                             'match the number of regions {} found in '
                             'label_files {}'.format(self.inputs.class_labels,
                                                     n_labels,
                                                     self.inputs.label_files))

        if self.inputs.include_global:
            global_label_data = label_data.get_data().sum(
                axis=3)  # sum across all regions
            global_label_data = np.rint(global_label_data).astype(int).clip(
                0, 1)  # binarize
            global_label_data = self._4d(global_label_data, label_data.affine)
            global_masker = nl.NiftiLabelsMasker(
                global_label_data, detrend=self.inputs.detrend)
            maskers.insert(0, global_masker)
            self.inputs.class_labels.insert(0, 'GlobalSignal')

        for masker in maskers:
            masker.set_params(detrend=self.inputs.detrend)

        return maskers

    def _4d(self, array, affine):
        ''' takes a 3-dimensional numpy array and an affine,
        returns the equivalent 4th dimensional nifti file '''
        return nb.Nifti1Image(array[:, :, :, np.newaxis], affine)
