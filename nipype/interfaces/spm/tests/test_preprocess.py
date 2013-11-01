# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

from nipype.testing import (assert_equal, assert_false, assert_true,
                            assert_raises, skipif)
import nibabel as nb
import nipype.interfaces.spm as spm
from nipype.interfaces.spm import no_spm
import nipype.interfaces.matlab as mlab

try:
    matlab_cmd = os.environ['MATLABCMD']
except:
    matlab_cmd = 'matlab'

mlab.MatlabCommand.set_default_matlab_cmd(matlab_cmd)


def create_files_in_directory():
    outdir = mkdtemp()
    cwd = os.getcwd()
    os.chdir(outdir)
    filelist = ['a.nii','b.nii']
    for f in filelist:
        hdr = nb.Nifti1Header()
        shape = (3,3,3,4)
        hdr.set_data_shape(shape)
        img = np.random.random(shape)
        nb.save(nb.Nifti1Image(img,np.eye(4),hdr),
                 os.path.join(outdir,f))
    return filelist, outdir, cwd

def clean_directory(outdir, old_wd):
    if os.path.exists(outdir):
        rmtree(outdir)
    os.chdir(old_wd)

def test_slicetiming():
    yield assert_equal, spm.SliceTiming._jobtype, 'temporal'
    yield assert_equal, spm.SliceTiming._jobname, 'st'

def test_slicetiming_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    st = spm.SliceTiming(in_files=filelist[0])
    yield assert_equal, st._list_outputs()['timecorrected_files'][0][0], 'a'
    clean_directory(outdir, cwd)

def test_realign():
    yield assert_equal, spm.Realign._jobtype, 'spatial'
    yield assert_equal, spm.Realign._jobname, 'realign'
    yield assert_equal, spm.Realign().inputs.jobtype, 'estwrite'

def test_realign_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    rlgn = spm.Realign(in_files=filelist[0])
    yield assert_true, rlgn._list_outputs()['realignment_parameters'][0].startswith('rp_')
    yield assert_true, rlgn._list_outputs()['realigned_files'][0].startswith('r')
    yield assert_true, rlgn._list_outputs()['mean_image'].startswith('mean')
    clean_directory(outdir, cwd)

def test_coregister():
    yield assert_equal, spm.Coregister._jobtype, 'spatial'
    yield assert_equal, spm.Coregister._jobname, 'coreg'
    yield assert_equal, spm.Coregister().inputs.jobtype, 'estwrite'

def test_coregister_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    coreg = spm.Coregister(source=filelist[0])
    yield assert_true, coreg._list_outputs()['coregistered_source'][0].startswith('r')
    coreg = spm.Coregister(source=filelist[0],apply_to_files=filelist[1])
    yield assert_true, coreg._list_outputs()['coregistered_files'][0].startswith('r')
    clean_directory(outdir, cwd)

def test_normalize():
    yield assert_equal, spm.Normalize._jobtype, 'spatial'
    yield assert_equal, spm.Normalize._jobname, 'normalise'
    yield assert_equal, spm.Normalize().inputs.jobtype, 'estwrite'

def test_normalize_list_outputs():
    filelist, outdir, cwd = create_files_in_directory()
    norm = spm.Normalize(source=filelist[0])
    yield assert_true, norm._list_outputs()['normalized_source'][0].startswith('w')
    norm = spm.Normalize(source=filelist[0],apply_to_files=filelist[1])
    yield assert_true, norm._list_outputs()['normalized_files'][0].startswith('w')
    clean_directory(outdir, cwd)

def test_segment():
    yield assert_equal, spm.Segment._jobtype, 'spatial'
    yield assert_equal, spm.Segment._jobname, 'preproc'

def test_newsegment():
    yield assert_equal, spm.NewSegment._jobtype, 'tools'
    yield assert_equal, spm.NewSegment._jobname, 'preproc8'

def test_smooth():
    yield assert_equal, spm.Smooth._jobtype, 'spatial'
    yield assert_equal, spm.Smooth._jobname, 'smooth'

def test_dartel():
    yield assert_equal, spm.DARTEL._jobtype, 'tools'
    yield assert_equal, spm.DARTEL._jobname, 'dartel'

def test_dartelnorm2mni():
    yield assert_equal, spm.DARTELNorm2MNI._jobtype, 'tools'
    yield assert_equal, spm.DARTELNorm2MNI._jobname, 'dartel'
