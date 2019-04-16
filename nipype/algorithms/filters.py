# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Signal processing tools
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

from ..utils.filemanip import fname_presuffix
from ..interfaces.base import (traits, TraitedSpec, SimpleInterface,
                               BaseInterfaceInputSpec, File)


class BandpassInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='functional data')
    freq_low = traits.Range(0.0, min=0.0, usedefault=True,
                            desc='low frequency cutoff (in Hz); '
                                 'the default of 0 sets low pass cutoff to Nyquist')
    freq_hi = traits.Range(0.0, min=0.0, usedefault=True,
                           desc='high frequency cutoff (in Hz); '
                                'the default of 0 sets high pass cutoff to 0')
    repetition_time = traits.Either(None, traits.Range(
        0.0, min=0.0, exclude_low=True), desc='repetition_time')


class BandpassOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='bandpass filtered functional data')


class Bandpass(SimpleInterface):
    """
    Bandpass filtering for functional MRI timeseries
    """
    input_spec = BandpassInputSpec
    output_spec = BandpassOutputSpec

    def _run_interface(self, runtime):
        self._results['out_file'] = _bandpass_filter(
            in_file=self.inputs.in_file,
            tr=self.inputs.repetition_time,
            freq_low=self.inputs.freq_low,
            freq_hi=self.inputs.freq_hi,
            out_file=fname_presuffix(
                self.inputs.in_file,
                suffix='_filtered', newpath=runtime.cwd),
        )
        return runtime


def _bandpass_filter(in_file, tr=None, freq_low=0, freq_hi=0, out_file=None):
    """
    Bandpass filter the input files

    Parameters
    ----------
        files : str
            4D NIfTI file
        freq_low : float
            cutoff frequency for the low pass filter (in Hz)
            the default of 0 sets low pass cutoff to Nyquist
        freq_hi : float
            cutoff frequency for the high pass filter (in Hz)
            the default of 0 sets high pass cutoff to 0
        tr : float
            repetition time (in seconds)
        out_file : str
            output file name

    """
    import numpy as np
    import nibabel as nb

    if freq_hi > 0 and freq_low >= freq_hi:
        raise ValueError("Low-cutoff frequency can't be greater than the high-cutoff")

    img = nb.load(in_file)
    timepoints = img.shape[-1]
    F = np.zeros((timepoints))

    if tr is None:  # If TR is not set, find in the image file header
        tr = img.header.get_zooms()[3]

    sampling_rate = 1. / tr

    lowidx = timepoints // 2 + 1  # "/" replaced by "//"
    if freq_low > 0:
        # "np.round(..." replaced by "int(np.round(..."
        lowidx = int(np.round(freq_low / sampling_rate * timepoints))

    highidx = 0
    if freq_hi > 0:
        highidx = int(np.round(freq_hi / sampling_rate * timepoints))  # same

    F[highidx:lowidx] = 1
    F = ((F + F[::-1]) > 0).astype(int)
    try:
        data = img.get_fdata()
    except AttributeError:
        data = img.get_data()

    if np.all(F):
        filtered_data = data
        return in_file

    filtered_data = np.real(np.fft.ifftn(np.fft.fftn(data) * F))
    img_out = nb.Nifti1Image(filtered_data, img.affine, img.header)
    img_out.to_filename(out_file)
    return out_file
