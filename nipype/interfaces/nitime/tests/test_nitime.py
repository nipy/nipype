# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil
from matplotlib import mlab.csv2rec as csv2rec

from nipype.testing import (assert_equal, assert_not_equal, assert_raises,
                            with_setup, TraitError, parametric, skipif)


def test_read_csv():
    """Test that reading the data from csv file gives you back a reasonable
    time-series object """

    #XXX need to finish this:
    data_rec = csv2rec('data/fmri_timeseries.csv')
    
    
