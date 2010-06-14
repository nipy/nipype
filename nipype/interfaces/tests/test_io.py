# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import shutil
from tempfile import mkdtemp
from nipype.testing import assert_equal, assert_true
import nipype.interfaces.io as nio
from nipype.interfaces.base import Undefined 

def test_datagrabber():
    dg = nio.DataGrabber()
    yield assert_equal, dg.inputs.template, Undefined
    yield assert_equal, dg.inputs.base_directory, Undefined
    yield assert_equal, dg.inputs.template_args,{'outfiles': []} 

def test_datasink():
    ds = nio.DataSink()
    yield assert_true, ds.inputs.parameterization
    yield assert_equal, ds.inputs.base_directory, Undefined
    yield assert_equal, ds.inputs.strip_dir, Undefined
    yield assert_equal, ds.inputs._outputs, {}
    ds = nio.DataSink(base_directory = 'foo')
    yield assert_equal, ds.inputs.base_directory, 'foo'


def test_freesurfersource():
    fss = nio.FreeSurferSource()
    yield assert_equal, fss.inputs.hemi, 'both'
    yield assert_equal, fss.inputs.subject_id, Undefined
    yield assert_equal, fss.inputs.subjects_dir, Undefined
