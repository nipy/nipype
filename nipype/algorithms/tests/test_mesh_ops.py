# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
from shutil import rmtree
from tempfile import mkdtemp

from nipype.testing import (assert_equal, assert_raises,
                            assert_almost_equal, example_data)

import numpy as np
import nibabel as nb
import nipype.testing as nit

from nipype.algorithms import mesh as m


def test_distances():
    tempdir = mkdtemp()
    in_surf = example_data('surf01.vtk')

    dist_ident = m.P2PDistance()
    dist_ident.inputs.surface1 = in_surf
    dist_ident.inputs.surface2 = in_surf
    dist_ident.inputs.out_file = os.path.join(tmpdir, 'distance.npy')
    res = dist_ident.run()
    yield assert_equal, res.outputs.distance, 0.0

    dist_ident.inputs.weighting = 'area'
    res = dist_ident.run()
    yield assert_equal, res.outputs.distance, 0.0

    rmtree(tempdir)
