# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""

Interfaces to functionality from nitime for time-series analysis of fmri data

- nitime.analysis.CoherenceAnalyzer: Coherence/y
- nitime.fmri.io:
- nitime.viz.drawmatrix_channels

"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import zip, object, open

import numpy as np
import tempfile

from ...utils.misc import package_check
from ...utils.filemanip import fname_presuffix
from .base import NitimeBaseInterface
from ..base import (TraitedSpec, File, Undefined, traits,
                    isdefined, BaseInterfaceInputSpec)

have_nitime = True
try:
    package_check('nitime')
except ImportError:
    have_nitime = False


class CoherenceAnalyzerInputSpec(BaseInterfaceInputSpec):

    # Input either csv file, or time-series object and use _xor_inputs to
    # discriminate
    _xor_inputs = ('in_file', 'in_TS')
    in_file = File(
        desc=('csv file with ROIs on the columns and '
              'time-points on the rows. ROI names at the top row'),
        exists=True,
        requires=('TR', ))

    # If you gave just a file name, you need to specify the sampling_rate:
    TR = traits.Float(
        desc=('The TR used to collect the data'
              'in your csv file <in_file>'))

    in_TS = traits.Any(desc='a nitime TimeSeries object')

    NFFT = traits.Range(
        low=32,
        value=64,
        usedefault=True,
        desc=('This is the size of the window used for '
              'the spectral estimation. Use values between '
              '32 and the number of samples in your time-series.'
              '(Defaults to 64.)'))
    n_overlap = traits.Range(
        low=0,
        value=0,
        usedefault=True,
        desc=('The number of samples which overlap'
              'between subsequent windows.(Defaults to 0)'))

    frequency_range = traits.List(
        value=[0.02, 0.15],
        usedefault=True,
        minlen=2,
        maxlen=2,
        desc=('The range of frequencies over'
              'which the analysis will average.'
              '[low,high] (Default [0.02,0.15]'))

    output_csv_file = File(
        desc=
        'File to write outputs (coherence,time-delay) with file-names: file_name_ {coherence,timedelay}'
    )

    output_figure_file = File(
        desc=
        'File to write output figures (coherence,time-delay) with file-names: file_name_{coherence,timedelay}. Possible formats: .png,.svg,.pdf,.jpg,...'
    )

    figure_type = traits.Enum(
        'matrix',
        'network',
        usedefault=True,
        desc=("The type of plot to generate, where "
              "'matrix' denotes a matrix image and"
              "'network' denotes a graph representation."
              " Default: 'matrix'"))


class CoherenceAnalyzerOutputSpec(TraitedSpec):
    coherence_array = traits.Array(
        desc=('The pairwise coherence values'
              'between the ROIs'))

    timedelay_array = traits.Array(
        desc=('The pairwise time delays between the'
              'ROIs (in seconds)'))

    coherence_csv = File(
        desc=('A csv file containing the pairwise '
              'coherence values'))

    timedelay_csv = File(
        desc=('A csv file containing the pairwise '
              'time delay values'))

    coherence_fig = File(desc=('Figure representing coherence values'))
    timedelay_fig = File(desc=('Figure representing coherence values'))


class CoherenceAnalyzer(NitimeBaseInterface):

    input_spec = CoherenceAnalyzerInputSpec
    output_spec = CoherenceAnalyzerOutputSpec

    def _read_csv(self):
        """
        Read from csv in_file and return an array and ROI names

        The input file should have a first row containing the names of the
        ROIs (strings)

        the rest of the data will be read in and transposed so that the rows
        (TRs) will becomes the second (and last) dimension of the array

        """
        # Check that input conforms to expectations:
        first_row = open(self.inputs.in_file).readline()
        if not first_row[1].isalpha():
            raise ValueError(
                "First row of in_file should contain ROI names as strings of characters"
            )

        roi_names = open(self.inputs.in_file).readline().replace(
            '\"', '').strip('\n').split(',')
        # Transpose, so that the time is the last dimension:
        data = np.loadtxt(self.inputs.in_file, skiprows=1, delimiter=',').T

        return data, roi_names

    def _csv2ts(self):
        """ Read data from the in_file and generate a nitime TimeSeries object"""
        from nitime.timeseries import TimeSeries
        data, roi_names = self._read_csv()

        TS = TimeSeries(
            data=data, sampling_interval=self.inputs.TR, time_unit='s')

        TS.metadata = dict(ROIs=roi_names)

        return TS

    # Rewrite _run_interface, but not run
    def _run_interface(self, runtime):
        import nitime.analysis as nta
        lb, ub = self.inputs.frequency_range

        if self.inputs.in_TS is Undefined:
            # get TS form csv and inputs.TR
            TS = self._csv2ts()

        else:
            # get TS from inputs.in_TS
            TS = self.inputs.in_TS

        # deal with creating or storing ROI names:
        if 'ROIs' not in TS.metadata:
            self.ROIs = ['roi_%d' % x for x, _ in enumerate(TS.data)]
        else:
            self.ROIs = TS.metadata['ROIs']

        A = nta.CoherenceAnalyzer(
            TS,
            method=dict(
                this_method='welch',
                NFFT=self.inputs.NFFT,
                n_overlap=self.inputs.n_overlap))

        freq_idx = np.where(
            (A.frequencies > self.inputs.frequency_range[0]) *
            (A.frequencies < self.inputs.frequency_range[1]))[0]

        # Get the coherence matrix from the analyzer, averaging on the last
        # (frequency) dimension: (roi X roi array)
        self.coherence = np.mean(A.coherence[:, :, freq_idx], -1)
        # Get the time delay from analyzer, (roi X roi array)
        self.delay = np.mean(A.delay[:, :, freq_idx], -1)
        return runtime

    # Rewrite _list_outputs (look at BET)
    def _list_outputs(self):
        outputs = self.output_spec().get()

        # if isdefined(self.inputs.output_csv_file):

        # write to a csv file and assign a value to self.coherence_file (a
        # file name + path)

        # Always defined (the arrays):
        outputs['coherence_array'] = self.coherence
        outputs['timedelay_array'] = self.delay

        # Conditional
        if isdefined(self.inputs.output_csv_file) and hasattr(
                self, 'coherence'):
            # we need to make a function that we call here that writes the
            # coherence values to this file "coherence_csv" and makes the
            # time_delay csv file??
            self._make_output_files()
            outputs['coherence_csv'] = fname_presuffix(
                self.inputs.output_csv_file, suffix='_coherence')

            outputs['timedelay_csv'] = fname_presuffix(
                self.inputs.output_csv_file, suffix='_delay')

        if isdefined(self.inputs.output_figure_file) and hasattr(
                self, 'coherence'):
            self._make_output_figures()
            outputs['coherence_fig'] = fname_presuffix(
                self.inputs.output_figure_file, suffix='_coherence')
            outputs['timedelay_fig'] = fname_presuffix(
                self.inputs.output_figure_file, suffix='_delay')

        return outputs

    def _make_output_files(self):
        """
        Generate the output csv files.
        """
        for this in zip([self.coherence, self.delay], ['coherence', 'delay']):
            tmp_f = tempfile.mkstemp()[1]
            np.savetxt(tmp_f, this[0], delimiter=',')

            fid = open(
                fname_presuffix(
                    self.inputs.output_csv_file, suffix='_%s' % this[1]), 'w+')
            # this writes ROIs as header line
            fid.write(',' + ','.join(self.ROIs) + '\n')
            # this writes ROI and data to a line
            for r, line in zip(self.ROIs, open(tmp_f)):
                fid.write('%s,%s' % (r, line))
            fid.close()

    def _make_output_figures(self):
        """
        Generate the desired figure and save the files according to
        self.inputs.output_figure_file

        """
        import nitime.viz as viz
        if self.inputs.figure_type == 'matrix':
            fig_coh = viz.drawmatrix_channels(
                self.coherence, channel_names=self.ROIs, color_anchor=0)

            fig_coh.savefig(
                fname_presuffix(
                    self.inputs.output_figure_file, suffix='_coherence'))

            fig_dt = viz.drawmatrix_channels(
                self.delay, channel_names=self.ROIs, color_anchor=0)

            fig_dt.savefig(
                fname_presuffix(
                    self.inputs.output_figure_file, suffix='_delay'))
        else:
            fig_coh = viz.drawgraph_channels(
                self.coherence, channel_names=self.ROIs)

            fig_coh.savefig(
                fname_presuffix(
                    self.inputs.output_figure_file, suffix='_coherence'))

            fig_dt = viz.drawgraph_channels(
                self.delay, channel_names=self.ROIs)

            fig_dt.savefig(
                fname_presuffix(
                    self.inputs.output_figure_file, suffix='_delay'))
