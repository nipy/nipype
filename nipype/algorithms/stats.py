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
from __future__ import print_function, division, unicode_literals, absolute_import
from builtins import str, zip, range, open

import os
import os.path as op

import nibabel as nb
import numpy as np
from scipy import linalg
from scipy.special import legendre

from .. import logging
from ..external.due import due, Doi, BibTeX
from ..interfaces.base import (traits, TraitedSpec, BaseInterface,
                               BaseInterfaceInputSpec, File, isdefined,
                               InputMultiPath, ListStr)
IFLOG = logging.getLogger('interface')

class StatExtractionInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='4-D fMRI nii file')
    label_file = File(exists=True, mandatory=False,
                      desc='a 3-D label image, with 0 denoting background, or '
                      'a 4-D file of probability maps. If this is not '
                      'provided, this interface outputs one stat.')
    out_file = File('stats.tsv', usedefault=True, exists=False, mandatory=False,
                    desc='The name of the file to output the stats to. '
                    'stats.tsv by default')
    class_labels = ListStr(mandatory=False,
                           desc='Human-readable labels for each segment in the '
                           'label file, in order. The length of class_labels '
                           'must be equal to or less than the number of '
                           'segments.')
    stat = Enum(('mean',), mandatory=False, default='mean', usedefault=True,
                desc='The stat you wish to calculate on each segment. '
                'The default is findig the mean')

class StatExtractionOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='tsv file containing the computed stats, '
                    'with as many stats as there are labels and as many rows '
                    'as there are timepoints in in_file')

class StatExtraction(BaseInterface):
    '''
    Extracts time series stats over tissue classes or brain regions

    >>> seinterface = StatExtraction()
    >>> seinterface.inputs.in_file = 'functional.nii'
    >>> seinterface.inputs.in_file = 'segmentation0.nii'
    >>> seinterface.inputs.out_file = 'means.tsv'
    >>> segments =['background', 'CSF', 'gray', 'white']
    >>> seinterface.inputs.class_labels = segments
    >>> seinterface.inputs.stat = 'mean'
    '''
    input_spec = StatExtractionInputSpec
    output_spec = StatExtractionOutputSpec

    def _run_interface(self, runtime):
        # assert/check inputs make sense

        
        pass

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs
