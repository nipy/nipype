# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import pytest
from nipype.testing.fixtures import create_files_in_directory

import nipype.interfaces.spm as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab

mlab.MatlabCommand.set_default_matlab_cmd(os.getenv('MATLABCMD', 'matlab'))


def test_slicetiming():
    assert spm.SliceTiming._jobtype == 'temporal'
    assert spm.SliceTiming._jobname == 'st'


def test_slicetiming_list_outputs(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    st = spm.SliceTiming(in_files=filelist[0])
    assert st._list_outputs()['timecorrected_files'][0][0] == 'a'


def test_realign():
    assert spm.Realign._jobtype == 'spatial'
    assert spm.Realign._jobname == 'realign'
    assert spm.Realign().inputs.jobtype == 'estwrite'


def test_realign_list_outputs(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    rlgn = spm.Realign(in_files=filelist[0])
    assert rlgn._list_outputs()['realignment_parameters'][0].startswith('rp_')
    assert rlgn._list_outputs()['realigned_files'][0].startswith('r')
    assert rlgn._list_outputs()['mean_image'].startswith('mean')


def test_coregister():
    assert spm.Coregister._jobtype == 'spatial'
    assert spm.Coregister._jobname == 'coreg'
    assert spm.Coregister().inputs.jobtype == 'estwrite'


def test_coregister_list_outputs(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    coreg = spm.Coregister(source=filelist[0])
    assert coreg._list_outputs()['coregistered_source'][0].startswith('r')
    coreg = spm.Coregister(source=filelist[0], apply_to_files=filelist[1])
    assert coreg._list_outputs()['coregistered_files'][0].startswith('r')


def test_normalize():
    assert spm.Normalize._jobtype == 'spatial'
    assert spm.Normalize._jobname == 'normalise'
    assert spm.Normalize().inputs.jobtype == 'estwrite'


def test_normalize_list_outputs(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    norm = spm.Normalize(source=filelist[0])
    assert norm._list_outputs()['normalized_source'][0].startswith('w')
    norm = spm.Normalize(source=filelist[0], apply_to_files=filelist[1])
    assert norm._list_outputs()['normalized_files'][0].startswith('w')


def test_normalize12():
    assert spm.Normalize12._jobtype == 'spatial'
    assert spm.Normalize12._jobname == 'normalise'
    assert spm.Normalize12().inputs.jobtype == 'estwrite'


def test_normalize12_list_outputs(create_files_in_directory):
    filelist, outdir = create_files_in_directory
    norm12 = spm.Normalize12(image_to_align=filelist[0])
    assert norm12._list_outputs()['normalized_image'][0].startswith('w')
    norm12 = spm.Normalize12(
        image_to_align=filelist[0], apply_to_files=filelist[1])
    assert norm12._list_outputs()['normalized_files'][0].startswith('w')


@pytest.mark.skipif(no_spm(), reason="spm is not installed")
def test_segment():
    if spm.Info.name() == "SPM12":
        assert spm.Segment()._jobtype == 'tools'
        assert spm.Segment()._jobname == 'oldseg'
    else:
        assert spm.Segment()._jobtype == 'spatial'
        assert spm.Segment()._jobname == 'preproc'


@pytest.mark.skipif(no_spm(), reason="spm is not installed")
def test_newsegment():
    if spm.Info.name() == "SPM12":
        assert spm.NewSegment()._jobtype == 'spatial'
        assert spm.NewSegment()._jobname == 'preproc'
    else:
        assert spm.NewSegment()._jobtype == 'tools'
        assert spm.NewSegment()._jobname == 'preproc8'


def test_smooth():
    assert spm.Smooth._jobtype == 'spatial'
    assert spm.Smooth._jobname == 'smooth'


def test_dartel():
    assert spm.DARTEL._jobtype == 'tools'
    assert spm.DARTEL._jobname == 'dartel'


def test_dartelnorm2mni():
    assert spm.DARTELNorm2MNI._jobtype == 'tools'
    assert spm.DARTELNorm2MNI._jobname == 'dartel'
