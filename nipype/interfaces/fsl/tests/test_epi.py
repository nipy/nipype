# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

from tempfile import mkdtemp
from shutil import rmtree

import numpy as np

import nibabel as nb

from nipype.testing import ( assert_equal, assert_not_equal,
                             assert_raises, skipif)
import nipype.interfaces.fsl.epi as fsl
from nipype.interfaces.fsl import no_fsl

def create_files_in_directory():
    outdir = os.path.realpath(mkdtemp())
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


# test eddy_correct
@skipif(no_fsl)
def test_eddy_correct2():
    filelist, outdir, cwd = create_files_in_directory()
    eddy = fsl.EddyCorrect()

    # make sure command gets called
    yield assert_equal, eddy.cmd, 'eddy_correct'

    # test raising error with mandatory args absent
    yield assert_raises, ValueError, eddy.run

    # .inputs based parameters setting
    eddy.inputs.in_file = filelist[0]
    eddy.inputs.out_file = 'foo_eddc.nii'
    eddy.inputs.ref_num = 100
    yield assert_equal, eddy.cmdline, 'eddy_correct %s foo_eddc.nii 100'%filelist[0]

    # .run based parameter setting
    eddy2 = fsl.EddyCorrect(in_file=filelist[0], out_file='foo_ec.nii', ref_num=20)
    yield assert_equal, eddy2.cmdline, 'eddy_correct %s foo_ec.nii 20'%filelist[0]

    # test arguments for opt_map
    # eddy_correct class doesn't have opt_map{}
    clean_directory(outdir, cwd)



