# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            with_setup, TraitError, parametric, skipif)

from nipype.testing import example_data

import nipype.interfaces.nitime as nitime 

def test_read_csv():
    """Test that reading the data from csv file gives you back a reasonable
    time-series object """

    CA = nitime.CoherenceAnalyzer()
    CA.inputs.TR = 1.89 # bogus value just to pass traits test
    CA.inputs.in_file = example_data('fmri_timeseries_nolabels.csv')
    yield assert_raises,ValueError,CA._read_csv 

    CA.inputs.in_file = example_data('fmri_timeseries.csv')
    rec_array = CA._read_csv()
    yield assert_equal, rec_array['wm'][0],10125.9

